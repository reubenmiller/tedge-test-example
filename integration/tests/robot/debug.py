"""Robot Framework debugger which can be used to
debug test libraries (not just the keywords/steps)

You can start this file from VSCode "Debug current file".
It will prompt you for the file to debug (if no arguments are provided).
"""
import sys
from pathlib import Path

import inquirer

import robot
from robot.model import SuiteVisitor
from robot.running import TestSuiteBuilder


class TestCasesFinder(SuiteVisitor):
    def __init__(self):
        self.tests = []

    def visit_test(self, test):
        self.tests.append(test)


def find_tests(test_path: str) -> TestCasesFinder:
    builder = TestSuiteBuilder()
    testsuite = builder.build(test_path)
    finder = TestCasesFinder()
    testsuite.visit(finder)
    return finder


if __name__ == "__main__":

    options = {}

    # Get test dir (or explicit path to robot file)
    path = Path(__file__).parent.resolve()
    if len(sys.argv) > 1:
        path = sys.argv[1]

    # Find test files, and build a lookup list
    testcases = {item.longname: item for item in find_tests(path).tests}

    questions = [
        inquirer.List(
            "testcase",
            message="Which test case?",
            choices=list(testcases.keys()),
        ),
    ]

    answers = inquirer.prompt(questions)

    testcase = answers.get("testcase", "")
    if testcase:
        options["test"] = testcase
        # testcase_model = testcases.get(testcase)
        # options["test"] = testcase_model.name
        # path = testcase_model.source

    robot.run(str(path), **options)
