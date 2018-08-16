# pykattis

A CLI tool for solving [Kattis](https://www.kattis.com/) problems with python.

## Installation

```
pip install pykattis
```

## Usage

To create a solution for a problem, run:

```
pykattis create {problem_id}
```

where `problem_id` is the Kattis problem ID.
This creates the directory `problems/{problem_id}` in the current working directory with the files `solution.py`, an `__init__.py` file, and downloads the sample input-anwer pairs to a `samples.json` file.

The `solution.py`-file is where you will be writing the solution to the problem.
Inside it is a function `solve(input_: str) -> str:`, which you will fill out with your program as you see fit.
This function is called by the commands `kattis run` and `kattis test`.

To simply run the program as a script, run:

```
pykattis run {problem_id}
```

and to test it on the sample input-answer pairs defined in `samples.json`, run:

```
pykattis test {problem_id}
```

To upload the solution to Kattis, you can submit the problem's `solution.py` file through Kattis's web form.
However, this is a temporary solution.
In a future version, you will be able to publish your solution to Kattis directly through pykattis.

If you, for some reason, just want to download a problem's samples, you can run:

```
pykattis download_samples {problem_id}
```

It is recommended to use a VCS, like [git](https://git-scm.com/), to keep track of your solutions.
