import asyncio
import logging
import subprocess
import sys
from pathlib import Path
from typing import List

import click
import typer

import config as conf
import loggers
from db.init_db import init_db

loggers.config()

logger = logging.getLogger()

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"], ignore_unknown_options=True)


# --- db --------------------------------------------------------------------- #

db_cli = typer.Typer(help="Database Management")


@db_cli.command(help="Create a directory to manage database migrations")
def init(dir: Path = Path("src/sunstruck/db/migrations"), args: List[str] = None):
    cmd = ["alembic", "init", str(dir)] + (args or [])
    subprocess.call(cmd)


@db_cli.command(help="Create a new migration revision")
def migrate(args: List[str] = None):
    cmd = ["alembic", "revision", "--autogenerate", "--head", "head"] + (args or [])
    subprocess.call(cmd)


@db_cli.command(help="Apply pending migrations to the database")
def upgrade(args: List[str] = None):
    logger.warning("Applying database migrations")
    cmd = ["alembic", "upgrade", "head"] + (args or [])
    subprocess.call(cmd)


@db_cli.command(help="Downgrade to a previous revision of the database")
def downgrade(revision: str = "-1", args: List[str] = None):
    cmd = ["alembic", "downgrade", revision] + (args or [])
    subprocess.call(cmd)


@db_cli.command(
    help="Create the system master account using the configured master credentials",
    short_help="Create the system master account",
)
def create_superuser():
    asyncio.run(init_db())


@db_cli.command(help="Drop amd rebuild the current database")
def recreate(args: List[str] = None):  # nocover

    if conf.ENV not in ["dev", "development"]:
        logger.error(
            "Cant recreate database when not in development mode."
            + "Set ENV=development as an environment variable to enable this feature."
        )
        sys.exit(0)
    else:
        from sqlalchemy_utils import create_database, database_exists, drop_database

        url = conf.ALEMBIC_CONFIG.url
        short_url = str(url).split("@")[-1]
        if database_exists(url):
            logger.warning(f"Dropping existing database: {short_url}")
            drop_database(url)
            logger.warning(f"Recreating database at: {short_url}")
            create_database(url)
        else:
            logger.warning(f"Creating new database at: {short_url}")
            create_database(url)
        upgrade()
        create_superuser()
        logger.warning("Database recreation complete")


# --- run -------------------------------------------------------------------- #

# NOTE: typer doesn't yet support passing unknown options. The workaround below is
#       creating a click parent group and adding each typer group as a sub-group
#       of the click parent, then creating a click group to handle the commands
#       that need dynamic arguments.

run_cli = click.Group("run", help="Execution procedures")


@run_cli.command(
    help="Launch a web process to serve the api", context_settings=CONTEXT_SETTINGS,
)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def web(args):  # nocover
    cmd = ["uvicorn", "sunstruck.main:app"] + list(args)
    subprocess.call(cmd)


@run_cli.command(
    help="Launch a web process with hot reload enabled",
    context_settings=CONTEXT_SETTINGS,
)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def dev(args):  # nocover
    cmd = ["uvicorn", "sunstruck.main:app", "--reload"] + list(args)
    subprocess.call(cmd)


# --- top -------------------------------------------------------------------- #

cli = click.Group(help="sunstruck API")  # parent group


@cli.command(help="List api routes")
def routes():
    "Show active API routes"
    from main import app

    for r in app.routes:
        typer.echo(f"{r.name:<25} {r.path:<30} {r.methods}")


# --- attach groups ---------------------------------------------------------- #


cli.add_command(run_cli)
cli.add_command(typer.main.get_command(db_cli), "db")


def main(argv: List[str] = sys.argv):
    """
    Args:
        argv (list): List of arguments
    Returns:
        int: A return code
    Does stuff.
    """

    cli()


if __name__ == "__main__":
    cli()
