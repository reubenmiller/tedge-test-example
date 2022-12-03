"""Project tasks"""

import os
import shutil
import sys
from invoke import task

from dotenv import load_dotenv

load_dotenv(".env")

# pylint: disable=invalid-name


@task
def lint(c):
    """Run linter"""
    c.run(f"{sys.executable} -m pylint integration")


@task(name="format")
def formatcode(c):
    """Format python code"""
    c.run(f"{sys.executable} -m black .")


@task(name="build")
def build(c, name="debian-systemd"):
    """Build the docker integration test image"""
    c.sudo(f"docker build -t {name} -f images/debian-systemd.dockerfile images")


@task
def usecontext(_c, context):
    """Change the .env file contents based on the target environment

    This is useful when running tests in the debugger

    Examples:
        # Change .env file to use the dev environment settings
        invoke usecontext dev

        # Change .env file to use the tst environment settings
        invoke usecontext tst
    """
    source_file = f".{context}.env"
    if not os.path.exists(source_file):
        print(f"Context does not exist. context={context}, file={source_file}")
        sys.exit(1)

    shutil.copy(f".{context}.env", ".env")
    print(
        f"The .env file was changed to use the {context} context (source={source_file})"
    )


@task(
    help={
        "variables": ("Variables file used to control the test"),
        "testenv": "Run tests in the test environment",
        "devenv": "Run tests in the dev environment",
        "modules": (
            "Only run tests which match this expression. "
            "This argument is passed to the -m option of pytest"
        ),
        "pattern": "Only include test where their names match the given pattern",
    }
)
def test(c, testenv=False, devenv=False, variables="", modules="", pattern=""):
    """Run tests

    Examples

        # run all tests in dev environment
        invoke test --devenv

        # run all tests in dev environment
        invoke test --testenv

        # run all tests using a given variables file
        invoke test --variables variables.tst.json

        # exclude control related tests
        invoke test --variables variables.tst.json -m "not control"

        # exclude both control and events tests
        invoke test --variables variables.tst.json -m "not measurements and not events"

        # run only measurements tests
        invoke test --variables variables.tst.json -m "measurements"

        # run only tests matching a filter
        invoke test --testenv --pattern "test_inventory_models"
    """
    # pylint: disable=too-many-arguments
    command = [
        sys.executable,
        "-m",
        "pytest",
    ]

    env_file = ".env"
    if variables:
        command.append(f"--variables={variables}")
    else:
        if devenv:
            env_file = ".dev.env"
            command.append("--variables=variables.dev.json")
        elif testenv:
            env_file = ".tst.env"
            command.append("--variables=variables.tst.json")

    if modules:
        command.append(f"-m='{modules}'")

    if pattern:
        command.append(f"-k='{pattern}'")

    if env_file:
        load_dotenv(env_file)

    command.append("--color=yes")
    command.append("integration")
    c.run(" ".join(command))
