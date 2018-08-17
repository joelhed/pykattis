"""The command-line interface of the project."""
import sys
import argparse
import pkg_resources
from pathlib import Path
from .core import Problem


DESCRIPTION = """\
A CLI tool for solving Kattis problems with python.
"""


def print_err(*args, **kwargs):
    """Print to stderr."""
    print(*args, **kwargs, file=sys.stderr)


def print_with_value(message: str, value: str):
    """Print the given message and value, possibly separated by a newline."""
    stripped_value = value.strip()
    end = "\n" if "\n" in stripped_value else "\t"
    print(message, end=end)
    print(stripped_value)


class ProblemCommand:
    """A cli command that deals with a Kattis problem."""

    command_name = None

    def __init__(self):
        """Initialize the command."""

    def __call__(self, args):
        """Run the command with the given argparse arguments."""
        problem = Problem(args.problem_id)
        return self.run(problem, args)

    def create_parser(self, subparsers):
        """Create a parser for the problem."""
        if self.__class__.command_name is None:
            raise NotImplementedError

        parser = subparsers.add_parser(
            self.__class__.command_name, description=self.__class__.__doc__
        )
        parser.add_argument("problem_id", help="The Kattis problem ID")
        parser.set_defaults(func=self)
        return parser

    def run(self, problem, args):
        """Run the command.

        This should raise for errors, but can optionally return an exit code.
        """
        raise NotImplementedError


class CreateCommand(ProblemCommand):
    """Create a problem directory from a template, and download the samples."""

    command_name = "create"

    def create_parser(self, *args, **kwargs):
        parser = super().create_parser(*args, **kwargs)
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite the contents of the solution directory",
        )
        return parser

    def run(self, problem, args):
        problem.create_directory()

        # TODO: Extract
        solution_path = problem.package_path / "solution.py"
        if solution_path.exists() and not args.overwrite:
            print_err("Solution already exists. Continuing...")
        else:
            print_err(f"Writing template solution file '{solution_path}'")
            solution_template = pkg_resources.resource_string(
                __name__, "solution_template.py"
            ).decode("utf8")
            with solution_path.open("w") as f:
                f.write(solution_template.format(problem=problem))

        problem.samples.download()
        problem.samples.save()


class RunCommand(ProblemCommand):
    """Run the solution program."""

    command_name = "run"

    def run(self, problem, args):
        input_ = sys.stdin.read()
        answer = problem.solution_module.solve(input_)
        print(answer)


class TestCommand(ProblemCommand):
    """Run a solution on its defined sample inputs and answers."""

    command_name = "test"

    def run(self, problem, args):
        for input_, expected_answer in problem.samples:
            print_with_value("Solving with input:", input_)

            answer = problem.solution_module.solve(input_)

            if answer.strip() == expected_answer.strip():
                print_with_value("Success! Output was:", answer)
            else:
                print("Failure")
                print_with_value("Expected answer:", expected_answer)
                print_with_value("Actual answer:", answer)


class DownloadSamplesCommand(ProblemCommand):
    """Download the problem's samples."""

    command_name = "download_samples"

    def create_parser(self, *args, **kwargs):
        parser = super().create_parser(*args, **kwargs)
        parser.add_argument(
            "out",
            type=argparse.FileType("w", encoding="utf8"),
            nargs="?",
            default="-",
            help="The output file, default stdout",
        )

    def run(self, problem, args):
        problem.samples.download()
        problem.samples.save(args.out)


def main():
    """The main entry point of the program.

    Returns the program's exit code.
    """
    commands = [
        CreateCommand(),
        RunCommand(),
        TestCommand(),
        DownloadSamplesCommand(),
    ]

    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.set_defaults(func=lambda args: parser.print_help())

    subparsers = parser.add_subparsers()
    for command in commands:
        command.create_parser(subparsers)

    args = parser.parse_args()

    sys.path.append(str(Path.cwd()))

    try:
        exit_code = args.func(args)
    except ValueError as e:
        print_err(e)
        return 1

    return exit_code if exit_code is not None else 0
