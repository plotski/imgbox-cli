from unittest.mock import Mock

import pytest

from imgbox import _input


def test_get_files_reads_files_from_stdin(mock_io):
    lines = ['foo.jpg', 'bar.jpg', 'baz.png']
    args = Mock(files=[])
    with mock_io(stdin='\n'.join(lines)):
        assert _input.get_files(args) == lines

def test_get_files_ignores_empty_lines_on_stdin(mock_io):
    lines = ['', 'foo.jpg', ' ', 'bar.jpg', '\t', 'baz.png', '\n']
    args = Mock(files=[])
    with mock_io(stdin='\n'.join(lines)):
        assert _input.get_files(args) == [line for line in lines if line.strip()]

def test_get_files_ignores_single_dash_argument(mock_io):
    lines = ['foo.jpg', 'bar.jpg', 'baz.png']
    args = Mock(files=['-'])
    with mock_io(stdin='\n'.join(lines)):
        assert _input.get_files(args) == lines

def test_get_files_reads_files_from_arguments(mocker, mock_io):
    files = ['foo.jpg', 'bar.jpg', 'baz.png']
    args = Mock(files=files)
    with mock_io():
        assert _input.get_files(args) == files

def test_get_files_does_not_find_any_files(mock_io):
    args = Mock(files=[])
    with mock_io(stdin=''):
        with pytest.raises(ValueError, match=(r'^Missing at least one image file\. '
                                              r'Run "imgbox -h" for more information\.$')):
            _input.get_files(args)
