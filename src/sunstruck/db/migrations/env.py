""" Alembic environment setup & customization """
import logging
import sys
from logging.config import fileConfig

from alembic import context
from alembic.autogenerate import rewriter
from alembic.operations import ops
from sqlalchemy import Column, engine_from_config, pool

import loggers
from config import ALEMBIC_CONFIG
from db import db
from db.models import *  # noqa

sys.path.extend(["./"])


# To include a model in migrations, add a line here.

###############################################################################


config = context.config
config.set_main_option("sqlalchemy.url", str(ALEMBIC_CONFIG.url))
exclude_tables = config.get_section("alembic:exclude").get("tables", "").split(",")

fileConfig(config.config_file_name)
target_metadata = db

loggers.config(20, formatter="simple")
logger = logging.getLogger(__name__)


class CustomRewriter(rewriter.Rewriter):  # nocover
    """ Extends self.process_revision_directives since a standalone
        process_revision_directives function and a rewriter cant both
        be passed to the MigrationContext at the same time."""

    def process_revision_directives(self, context, revision, directives):
        if config.cmd_opts.autogenerate:
            script = directives[0]

            # Dont generate a new migration file if there are no pending operations
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.warning(
                    "No pending operations. Skipping creating an empty revision file."
                )
            else:
                # generate the new migration using the rewriter
                super().process_revision_directives(context, revision, directives)


writer = CustomRewriter()


@writer.rewrites(ops.CreateTableOp)
def order_columns(context, revision, op):  # nocover
    """ Enforce id to be the first column of the table, as well as forcing
        created_at and updated_at to be the last columns"""
    special_names = {"id": -100, "created_at": 1001, "updated_at": 1002}

    cols_by_key = [
        (
            special_names.get(col.key, index) if isinstance(col, Column) else 2000,
            col.copy(),
        )
        for index, col in enumerate(op.columns)
    ]

    columns = [col for idx, col in sorted(cols_by_key, key=lambda entry: entry[0])]
    return ops.CreateTableOp(op.table_name, columns, schema=op.schema, **op.kw)


def include_object(object, name, type_, reflected, compare_to):  # nocover
    """ Selectively include/exclude objects from autogeneration """

    if type_ == "table" and name in exclude_tables:
        return False
    else:
        return True


def render_item(type_, obj, autogen_context):  # nocover
    """Apply custom rendering for selected items."""

    # handle populating sqlalchemy_utils types when generating migration
    if type_ == "type" and obj.__class__.__module__.startswith("sqlalchemy_utils."):
        autogen_context.imports.add(f"import {obj.__class__.__module__}")
        if hasattr(obj, "choices"):
            return f"{obj.__class__.__module__}.{obj.__class__.__name__}(choices={obj.choices.__module__}.{obj.choices.__name__})"  # noqa
        else:
            return f"{obj.__class__.__module__}.{obj.__class__.__name__}()"

    # default rendering for other objects
    return False


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=ALEMBIC_CONFIG.url.__to_string__(hide_password=False),
        target_metadata=target_metadata,
        literal_binds=True,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        {"sqlalchemy.url": ALEMBIC_CONFIG.url.__to_string__(hide_password=False)},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            render_item=render_item,
            transaction_per_migration=True,
            process_revision_directives=writer,
        )

        with context.begin_transaction():
            context.execute("SET search_path TO public")
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
