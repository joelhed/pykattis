#!/usr/bin/env python3.6
""""""
import sys
import argparse
import importlib
import pkg_resources
import json


def print_err(*args, **kwargs):
    """Print to stderr."""
    print(*args, **kwargs, file=sys.stderr)


def print_with_value(message: str, value: str):
    """Print the given message and value, possibly separated by a newline."""
    stripped_value = value.strip()
    end = "\n" if "\n" in stripped_value else "\t"
    print(message, end=end)
    print(stripped_value)


class Problem:
    """A Kattis problem-solution pair."""

    def __init__(self, id_):
        self.id = id_

        if not importlib.util.find_spec(self.solution_module_str):
            raise ValueError(f"No solution for problem '{self.id}'")

    @property
    def package_str(self):
        return f"problems.{self.id}"

    @property
    def solution_module_str(self):
        return f"{self.package_str}.solution"

    def get_solution_module(self):
        return importlib.import_module(self.solution_module_str)

    def samples(self):
        """A generator for the samples of the problem.

        This yields a 2-tuple of the input and the answer as strings.
        """
        samples_filename = "samples.json"
        # if not pkg_resources.resource_exists(problem_package_str, samples_filename):
        #     return

        samples_file = pkg_resources.resource_stream(self.package_str, samples_filename)

        # TODO: show a friendly error message when failing to parse the file.
        samples = json.load(samples_file)

        for sample in samples:
            # TODO: show a friendly error message if the sample lacks a field
            input_, answer = sample["input"], sample["answer"]

            yield input_, answer


class ProblemCommand:
    """A cli command that deals with a Kattis problem."""

    command_name = None

    def __init__(self):
        """Initialize the command."""

    def __call__(self, args):
        """Run the command with the given argparse arguments."""
        problem = Problem(args.problem_id)
        self.run(problem, args)

    def create_parser(self, subparsers):
        """Create a parser for the problem."""
        if self.__class__.command_name is None:
            raise NotImplementedError

        parser = subparsers.add_parser(
            self.__class__.command_name, help=self.__class__.__doc__
        )
        parser.set_defaults(func=self)
        return parser

    def run(self, problem, args):
        """Run the command."""
        raise NotImplementedError


class RunCommand(ProblemCommand):
    """Run the solution program."""

    command_name = "run"

    def run(self, problem, args):
        input_ = sys.stdin.read()
        answer = problem.get_solution_module().solve(input_)
        print(answer)


class SamplesCommand(ProblemCommand):
    """Run a solution on its defined sample inputs and answers."""

    command_name = "samples"

    def run(self, problem, args):
        solution_module = problem.get_solution_module()

        for input_, expected_answer in problem.samples():
            print_with_value("Solving with input:", input_)

            answer = solution_module.solve(input_)

            if answer.strip() == expected_answer.strip():
                print_with_value("Success! Output was:", answer)
            else:
                print("Failure")
                print_with_value("Expected answer:", expected_answer)
                print_with_value("Actual answer:", answer)


def main():
    """The main entry point of the program.

    Returns None if it succeded, and an exit code otherwise
    """
    # kattis.py run planina
    run = RunCommand()
    # kattis.py samples planina
    samples = SamplesCommand()
    # kattis.py generate_script planina output.py

    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers()

    samples.create_parser(subparsers)
    run.create_parser(subparsers)

    parser.add_argument("problem_id", help="The Kattis problem ID")

    args = parser.parse_args()

    try:
        args.func(args)
    except ValueError as e:
        print_err(e)
        return 1


if __name__ == "__main__":
    exit_code = main()
    if exit_code is not None:
        sys.exit(exit_code)
