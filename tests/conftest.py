import io
import sys

import pytest


@pytest.fixture
def mock_io():
    class MockIO():
        def __init__(self, stdin=''):
            self._stdout = io.StringIO()
            self._stderr = io.StringIO()
            self._stdin = io.StringIO(stdin)

        def __enter__(self):
            sys.stdout = self._stdout
            sys.stderr = self._stderr
            sys.stdin = self._stdin
            return self

        def __exit__(self, _, __, ___):
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            sys.stdin = sys.__stdin__

        @property
        def stdout(self):
            self._stdout.seek(0)
            return self._stdout.read()

        @property
        def stderr(self):
            self._stderr.seek(0)
            return self._stderr.read()

    return MockIO
