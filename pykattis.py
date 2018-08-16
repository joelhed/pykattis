#!/usr/bin/env python3.6
"""A CLI tool for solving Kattis problems."""
import sys
import io
import argparse
import importlib
import pkg_resources
import json
import zipfile
from typing import NamedTuple
from pathlib import Path
import requests


def print_err(*args, **kwargs):
    """Print to stderr."""
    print(*args, **kwargs, file=sys.stderr)


def print_with_value(message: str, value: str):
    """Print the given message and value, possibly separated by a newline."""
    stripped_value = value.strip()
    end = "\n" if "\n" in stripped_value else "\t"
    print(message, end=end)
    print(stripped_value)


class Sample(NamedTuple):
    """A sample input-answer pair."""

    input: str
    answer: str

    def to_dict(self):
        return {"input": self.input, "answer": self.answer}


class Samples:
    """A list of samples for a problem."""

    def __init__(self, problem):
        self.problem = problem
        self._samples = []
        self._path = self.problem.package_path / "samples.json"

    def __iter__(self):
        if not self._samples:
            self.load()

        return iter(self._samples)

    def __len__(self):
        return len(self._samples)

    def download(self):
        """Download the problem's samples."""
        # TODO: Check the Kattis ToS section 6. Automated Access
        resp = requests.get(
            f"https://open.kattis.com/problems/{self.problem.id}"
            "/file/statement/samples.zip",
            stream=True,
        )
        if resp.status_code == 404:
            raise ValueError(
                f"The problem '{self.problem}' does not exist on kattis.com"
            )
        resp.raise_for_status()

        samples_io = io.BytesIO()
        for chunk in resp:
            samples_io.write(chunk)
        samples_io.seek(0)

        samples_zip = zipfile.ZipFile(samples_io)
        filename_list = samples_zip.namelist()
        samples = []
        for filename in sorted(filename_list):
            if not filename.endswith(".in"):
                continue
            # filename is now an input filename

            base_name = filename[:-3]  # removes the ".in", which has length 3
            answer_filename = base_name + ".ans"
            if answer_filename not in filename_list:
                # This should never happen.
                raise ValueError(
                    f"Could not find a matching '{answer_filename}' file "
                    f"for '{filename}' in the downloaded zipfile."
                )

            input_bytes = samples_zip.read(filename)
            answer_bytes = samples_zip.read(answer_filename)

            samples.append(
                Sample(input_bytes.decode("utf8"), answer_bytes.decode("utf8"))
            )

        self._samples = samples

    def file_exists(self):
        """Check wether the file exists."""
        return self._path.exists()

    def load(self):
        """Load the samples from its file."""
        if not self.file_exists():
            raise ValueError(f"The sample file at '{self._path}' doesn't exist")

        # TODO: raise with friendly error messages when failing to parse the file
        with self._path.open("r") as f:
            sample_dicts = json.load(f)

        samples = [Sample(**sample_dict) for sample_dict in sample_dicts]
        self._samples = samples

    def save(self, file_=None):
        """Save the samples to its file."""
        if file_ is None:
            if self.file_exists():
                print_err("Samples file exists. Overwriting...")
            file_ = open(self._path, "w")

        sample_dicts = [sample.to_dict() for sample in self._samples]
        with file_:
            json.dump(sample_dicts, file_, indent=4)
            file_.write("\n")


class Problem:
    """A Kattis problem-solution pair."""

    def __init__(self, id_):
        self.id = id_
        self._solution_module = None
        self.package_path = Path("problems", self.id)
        self.samples = Samples(self)

    def __repr__(self):
        return f"<Problem {self.id!r}>"

    def __str__(self):
        return self.id

    @property
    def package_str(self):
        return f"problems.{self.id}"

    @property
    def solution_module_str(self):
        return f"{self.package_str}.solution"

    @property
    def solution_module(self):
        if self._solution_module is None:
            try:
                self._solution_module = importlib.import_module(
                    self.solution_module_str
                )
            except ModuleNotFoundError:
                raise ValueError(f"No solution for problem '{self.id}'")

        return self._solution_module

    def create_directory(self):
        """Create the directory for the problem if it doesn't already exist."""
        self.package_path.mkdir(parents=True, exist_ok=True)
        (self.package_path / "__init__.py").touch()


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

    parser = argparse.ArgumentParser(description=__doc__)
    parser.set_defaults(func=lambda args: parser.print_help())

    subparsers = parser.add_subparsers()
    for command in commands:
        command.create_parser(subparsers)

    args = parser.parse_args()

    try:
        exit_code = args.func(args)
    except ValueError as e:
        print_err(e)
        return 1

    return exit_code if exit_code is not None else 0


if __name__ == "__main__":
    sys.exit(main())
