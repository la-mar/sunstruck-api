# type: ignore
from __future__ import annotations

import asyncio
import functools
import logging
from timeit import default_timer as timer
from typing import Callable, Coroutine, Dict, List, Optional, Union

from asyncpg.exceptions import DataError, UniqueViolationError
from sqlalchemy.dialects.postgresql.dml import Insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import Constraint
from sqlalchemy.sql.base import Executable

import config as conf
import util

logger = logging.getLogger(__name__)


class BulkIOMixin(object):
    """ DML operations optimized for large datasets """

    @classmethod
    def log_prefix(cls, exc: Exception) -> str:
        """ Log record prefix generator

        Args:
            exc (Exception): any exception instance

        Returns:
            str: a stringified prefix. Example: "(ClassName) ExceptionName"
        """
        return f"({cls.__name__}) {exc.__class__.__name__}"

    @classmethod
    async def execute_statement(
        cls,
        stmt: Executable,
        records: List[Dict],
        op_name: str,
        retry_func: Optional[Callable] = None,
    ) -> int:
        """ Executes the given statement on the database

        Arguments:
            stmt {Executable} -- sqlalchemy DML operation
            records {List[Dict]} -- list of records to be used by the statement
            op_name {str} -- arbitrary name of the intended operation

        Keyword Arguments:
            retry_func {Optional[Callable]} -- callback to trigger in the
                event the operation is unsuccessful. (default: {None})

        Raises:
            IntegrityError: operation would violate a primary or foreign key
            UniqueViolationError: operation would violate a unique constraint
            Exception: all other exceptions

        Returns:
            int -- number of records affected
        """

        try:
            n = len(records)

            ts = timer()
            await stmt.gino.load(cls).all()
            exc_time = round(timer() - ts, 2)
            cls.log_operation(op_name, n, exc_time)

        except (IntegrityError, UniqueViolationError, DataError) as ie:

            if retry_func:
                if n > 1:
                    first_half = records[: n // 2]
                    second_half = records[n // 2 :]
                    first_n = len(first_half)
                    second_n = len(second_half)

                    logger.info(
                        f"{cls.log_prefix(ie)}: retrying with fractured records (first_half={first_n} second_half={second_n}) -- {ie}"  # noqa
                    )
                    await retry_func(first_half, batch_size=first_n // 4)
                    await retry_func(second_half, batch_size=second_n // 4)
                else:
                    record = util.reduce(records)
                    record = {k: v for k, v in record.items() if k in cls.pk.names}

                    # include primary key names/values in log message
                    # values can be scrubbed later, if needed
                    logger.error(
                        f"{cls.log_prefix(ie)}: {ie} -- primary_key={record}",
                        extra={"primary_key": record},
                    )

            else:  # fail whole batch
                log_records: str = ""

                if conf.DEBUG:
                    # print records to log if in debug mode
                    log_records = f"\n{util.jsontools.to_string(records)}\n"

                logger.error(f"{cls.log_prefix(ie)}:  {ie} -- {log_records}",)
                raise ie

        except Exception as e:

            log_records = ""
            if conf.DEBUG:
                # print records to log if in debug mode
                log_records = f"\n{util.jsontools.to_string(records)}\n"

            logger.exception(f"{cls.log_prefix(e)}: {e} -- {e.args} {log_records}")
            raise e

        return n

    @classmethod
    async def bulk_upsert(
        cls,
        records: List[Dict],
        batch_size: int = 500,
        conflict_action: str = "update",
        exclude_cols: Optional[List] = None,
        conflict_constraint: Union[str, Constraint] = None,
        concurrency: int = 50,
        error_strategy: str = "fracture",
    ) -> int:
        """ Persist the passed records to the database using a bulk-optimized
            upsert operation. Conflict identification and handling can be configured
            using the conflict_constraint parameter.

            The batch_size of each operation is constrained by the maximum number
            of characters allowed in the VALUES clause by the underlying database.
            Decreasing the batch_size accommodate tables with more/longer column
            names. The batch_size can be increased to optimize performance when
            few columns are included in the statement.

        Arguments:
            records {List[Dict]} -- list of records to be upserted

        Keyword Arguments:
            batch_size {int} -- maximum number of records in each emitted insert
                statement (default: 500)
            exclude_cols {Optional[List]} -- names of fields to drop from the incomming
                records prior to assembling the DML statement. (default: None)
            conflict_action {str} -- how to handle conflicting records.
                Options: ["update", "ignore"] (default: "update")
            conflict_constraint {Union[str, Constraint]} -- constraint used to identify
                conflicting records. If not specified, the underlying table's primary
                key constraint is used. (default: None)
            concurrency {int} -- maximum number of child concurrent operations allowed
                to be running simultaneously (default: 50)
            error_strategy {str} -- error handling strategy. Options: ["fracture", "raise"]
                (default: "fracture")

        Raises:
            ValueError: invalid argument value

        Returns:
            int -- number of records affected
        """
        batch_size = batch_size or len(records)
        exclude_cols = exclude_cols or []
        conflict_constraint = conflict_constraint or cls.__table__.primary_key
        coros: List[Coroutine] = []

        for idx, chunk in enumerate(util.chunks(records, batch_size)):
            op_name = "bulk_upsert"
            chunk = list(chunk)
            stmt: Insert = Insert(cls).values(chunk)

            # update these columns when a conflict is encountered
            if conflict_action == "ignore":
                stmt = stmt.on_conflict_do_nothing(constraint=conflict_constraint)

            elif conflict_action == "update":
                on_conflict_update_cols = [
                    c.name
                    for c in cls.columns
                    if c not in cls.pk and c.name not in exclude_cols
                ]
                stmt = stmt.on_conflict_do_update(
                    constraint=conflict_constraint,
                    set_={
                        k: getattr(stmt.excluded, k) for k in on_conflict_update_cols
                    },
                )

            if error_strategy == "fracture":
                partial = functools.partial(
                    cls.bulk_upsert,
                    exclude_cols=exclude_cols,
                    conflict_action=conflict_action,
                    concurrency=concurrency,
                )
            elif error_strategy == "raise":  # placeholder for later
                partial = None
                # TODO: Log failed table_name and primary keys and capture for
                #       later reprocessing (no mechanism for this exists yet)
            else:
                raise ValueError(
                    "Invalid value for 'errors': must be one of [fracture, raise]"
                )

            coros.append(
                cls.execute_statement(
                    stmt, records=chunk, op_name=op_name, retry_func=partial
                )
            )

        result: int = 0
        for idx, chunk in enumerate(util.chunks(coros, concurrency)):
            result += sum(await asyncio.gather(*chunk))

        return result

    @classmethod
    async def bulk_insert(cls, records: List[Dict], batch_size: int = 100) -> int:
        """ Persist the passed records to the database using a bulk-optimized
            insert operation.

        Arguments:
            records {List[Dict]} -- list of records

        Keyword Arguments:
            batch_size {int} -- maximum number of records in each emitted insert
                statement (default: {100})

        Returns:
            int -- number of affected records
        """

        affected: int = 0
        batch_size = batch_size or len(records)

        for chunk in util.chunks(records, batch_size):
            ts = timer()
            stmt = Insert(cls).values(chunk)
            exc_time = round(timer() - ts, 2)
            n = len(chunk)
            await stmt.gino.load(cls).all()
            cls.log_operation("insert", n, exc_time)
            affected += n

        return affected

    @classmethod
    def log_operation(cls, method: str, n: int, exc_time: float):
        """ Emit a standardized log record capturing the details of a
            database operation.

        Arguments:
            method {str} -- operation name
            n {int} -- number of records
            exc_time {float} -- total execution time
        """
        method = method.lower()

        measurements = {
            "tablename": cls.__table__.name,
            "method": method,
            f"{method}_time": exc_time,
        }

        if n > 0:
            measurements[f"{method}s"] = n

            if exc_time > 0:
                measurements[f"{method}s_per_second"] = n / exc_time or 1

        logger.debug(
            f"({cls.__name__}) {method} {n} records ({exc_time}s)", extra=measurements,
        )
