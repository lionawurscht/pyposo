from pathlib import Path
import os
from os import path
import sys
from itertools import chain
import subprocess as sp
import shlex
import unittest
import importlib

from doit.reporter import ConsoleReporter

termcolor_spec = importlib.util.find_spec("termcolor")
if termcolor_spec is not None:
    termcolor = termcolor_spec.loader.load_module()
else:
    termcolor = None

sys.path.insert(0, os.path.abspath("."))

package_directory = Path(path.dirname(path.abspath(__file__)))
package_name = package_directory.name

pyposo_directory = package_directory / "pyposo"
docs_directory = package_directory / "docs"
docs_build_directory = docs_directory / "build"
tests_directory = package_directory / "tests"


class ColorConsoleReporter(ConsoleReporter):
    line_length = 70
    line_char = "-"

    def execute_task(self, task):
        title = task.title()
        if termcolor is not None:
            title = termcolor.colored(title, "green")

        self.write(
            (
                "\n{title:{line_char}^{line_length}.0}\n"
                "{title:^{line_length}}\n"
                "{title:{line_char}^{line_length}.0}\n\n"
            ).format(
                title=title,
                line_char=self.line_char,
                line_length=self.line_length,
            )
        )

    def _write_failure(self, result, write_exception=True):
        task_id = result["task"].name
        exception = result["exception"].get_name()

        if termcolor is not None:
            task_id = termcolor.colored(task_id, "blue")
            exception = termcolor.colored(exception, "red")

        msg = (
            "Error in {task_id: <20}: {exception}\n"
            "{task_id:{line_char}^{line_length}.0}\n\n"
        ).format(
            task_id=task_id,
            exception=exception,
            line_char=self.line_char,
            line_length=self.line_length,
        )

        self.write(msg)
        if write_exception:
            self.write(result["exception"].get_msg())
            self.write("\n")


DOIT_CONFIG = {"reporter": ColorConsoleReporter, "verbosity": 2}


def task_run_tests():
    """Run python tests."""

    def run_tests():
        import test as test_pyposo

        suite = unittest.TestLoader().loadTestsFromModule(test_pyposo)
        unittest.TextTestRunner(verbosity=2).run(suite)

    files_ = [
        str(f)
        for f in chain(
            tests_directory.glob("**/*.py"), pyposo_directory.glob("**/*.py")
        )
    ]

    return {
        "actions": [run_tests],
        "file_dep": [package_directory / "test.py"] + files_,
    }


def task_build_docs():
    """Build the docs."""

    def build_docs():
        cmd = "make html"
        p = sp.run(
            shlex.split(cmd),
            cwd=docs_directory,
            stdout=sp.PIPE,
            stderr=sp.STDOUT,
        )

        print(p.stdout.decode("utf-8"))

    files_ = [
        str(f)
        for f in chain(
            docs_directory.glob("**/*"), pyposo_directory.glob("**/*.py")
        )
        if docs_build_directory not in f.parents and not os.path.isdir(f)
    ]

    return {"actions": [build_docs], "file_dep": files_}
