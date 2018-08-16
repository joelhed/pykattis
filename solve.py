#!/usr/bin/env python3.6
"""Run the solution of a given Kattis problem ID."""
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


def main():
    """The main entry point of the program.
    
    Returns None if it succeded, and an exit code otherwise
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--samples",
        action="store_true",
        help="Run the solution on its defined sample inputs and outputs",
    )
    parser.add_argument("problem_id", help="The Kattis problem ID")
    args = parser.parse_args()

    problem_package_str = f"problems.{args.problem_id}"

    try:
        solution = importlib.import_module(f"{problem_package_str}.solution")
    except ModuleNotFoundError:
        print_err(f"No solution for problem '{args.problem_id}'")
        return 1

    if args.samples:
        samples_filename = "samples.json"
        #if not pkg_resources.resource_exists(problem_package_str, samples_filename):
            #return

        samples_file = pkg_resources.resource_stream(problem_package_str, samples_filename)
        # TODO: show a friendly error message for failing to parse the file.
        samples = json.load(samples_file)

        for sample in samples:
            # TODO: show a friendly error message if the sample lacks a field
            input_, expected_output = sample["input"], sample["output"]

            # Print the iteration's input on one line if it fits
            print_with_value("Solving with input:", input_)

            output = solution.solve(input_)

            if output.strip() == expected_output.strip():
                print_with_value("Success! Output was:", output)
            else:
                print("Failure")
                print_with_value("Expected output:", expected_output)
                print_with_value("Actual output:", output)

    else:
        input_ = sys.stdin.read()
        output = solution.solve(input_)
        print(output)


if __name__ == "__main__":
    exit_code = main()
    if exit_code is not None:
        sys.exit(exit_code)
