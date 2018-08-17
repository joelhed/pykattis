"""The core functionality of the project."""
import io
import importlib
import json
import zipfile
import logging
from typing import NamedTuple
from pathlib import Path
import requests


log = logging.getLogger(__name__)


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
                log.info("Samples file exists. Overwriting...")
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
            except ModuleNotFoundError as e:
                raise e
                raise ValueError(f"No solution for problem '{self.id}'")

        return self._solution_module

    def create_directory(self):
        """Create the directory for the problem if it doesn't already exist."""
        self.package_path.mkdir(parents=True, exist_ok=True)
        (self.package_path / "__init__.py").touch()
