import json
import os
from unittest.mock import Mock, call

import pytest
from pyimgbox import Submission, MAX_FILE_SIZE

from imgbox import _output


# Python 3.6 doesn't have AsyncMock
class AsyncMock(Mock):
    def __call__(self, *args, **kwargs):
        async def coro(_sup=super()):
            return _sup.__call__(*args, **kwargs)
        return coro()


class AsyncIterator:
    def __init__(self, seq=()):
        self.iter = iter(seq)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.iter)
        except StopIteration:
            raise StopAsyncIteration


@pytest.fixture
def mock_gallery():
    return Mock(
        url='<Gallery URL>',
        edit_url='<Edit URL>',
        create=AsyncMock(),
        upload=AsyncMock(),
        add=Mock(return_value=AsyncIterator(())),
        close=AsyncMock(),
    )


def test_assert_file_ok_with_nonexisting_file():
    with pytest.raises(AssertionError, match=r'^No such file$'):
        _output._assert_file_ok('path/to/nonexisting/file.jpg')

def test_assert_file_ok_with_directory(tmp_path):
    with pytest.raises(AssertionError, match=rf'^Not a file$'):
        _output._assert_file_ok(tmp_path)

def test_assert_file_ok_with_unreadable_file(tmp_path):
    filepath = tmp_path / 'foo.jpg'
    filepath.write_bytes(b'data')
    os.chmod(filepath, 0x000)
    try:
        with pytest.raises(AssertionError, match=rf'^Not readable$'):
            _output._assert_file_ok(filepath)
    finally:
        os.chmod(filepath, 0x600)

def test_assert_file_ok_with_too_large_file(tmp_path):
    filepath = tmp_path / 'foo.jpg'
    # Create sparse file
    f = open(filepath, 'wb')
    f.truncate(MAX_FILE_SIZE + 1)
    f.close()
    with pytest.raises(AssertionError, match=rf'^File is larger than {MAX_FILE_SIZE} bytes$'):
        _output._assert_file_ok(filepath)


def test_all_files_ok_finds_no_issues(mock_io, mocker):
    mocker.patch('imgbox._output._assert_file_ok')
    with mock_io() as cap:
        _output._all_files_ok(('foo.jpg', 'bar.jpg', 'baz.jpg'))
    assert cap.stdout == ''
    assert cap.stderr == ''

def test_all_files_ok_finds_multiple_issues(mock_io, mocker):
    mocker.patch('imgbox._output._assert_file_ok', side_effect=[
        AssertionError('No file'),
        None,
        AssertionError('Bad file'),
    ])
    with mock_io() as cap:
        _output._all_files_ok(('foo.jpg', 'bar.jpg', 'baz.jpg'))
    assert cap.stdout == ''
    assert cap.stderr == (
        'foo.jpg: No file\n'
        'baz.jpg: Bad file\n'
    )


@pytest.mark.asyncio
async def test_text_fails_unless_all_files_ok(mock_io, mock_gallery, mocker):
    mock_all_files_ok = mocker.patch('imgbox._output._all_files_ok', return_value=False)
    with mock_io() as cap:
        exit_code = await _output.text(mock_gallery, ['path/to/foo.jpg'])
    assert exit_code == 1
    assert cap.stderr == ''
    assert cap.stdout == ''
    assert mock_all_files_ok.call_args_list == [call(['path/to/foo.jpg'])]
    assert mock_gallery.create.call_args_list == []
    assert mock_gallery.add.call_args_list == []

@pytest.mark.asyncio
async def test_text_creates_gallery_before_uploading(mock_io, mock_gallery, mocker):
    mocker.patch('imgbox._output._all_files_ok', return_value=True)
    calls = AsyncMock(add=Mock(return_value=AsyncIterator(())))
    mock_gallery.create = calls.create
    mock_gallery.add = calls.add
    with mock_io():
        exit_code = await _output.text(mock_gallery, ['path/to/foo.jpg'])
    assert exit_code == 0
    assert calls.mock_calls == [
        call.create(),
        call.add(['path/to/foo.jpg']),
    ]

@pytest.mark.asyncio
async def test_text_catches_ConnectionError_from_gallery_creation(mock_io, mock_gallery, mocker):
    mocker.patch('imgbox._output._all_files_ok', return_value=True)
    mock_gallery.create.side_effect = ConnectionError('Creation failed')
    with mock_io() as cap:
        exit_code = await _output.text(mock_gallery, ['path/to/foo.jpg'])
    assert exit_code == 1
    assert cap.stdout == ''
    assert cap.stderr == 'Creation failed\n'
    assert mock_gallery.create.call_args_list == [call()]
    assert mock_gallery.add.call_args_list == []

@pytest.mark.asyncio
async def test_text_handles_error_when_adding_to_gallery(mock_io, mock_gallery, mocker):
    mocker.patch('imgbox._output._all_files_ok', return_value=True)
    mock_gallery.add.return_value = AsyncIterator((
        Submission(filepath='path/to/foo.jpg', success=True,
                   image_url='img/foo', thumbnail_url='thumb/foo', web_url='web/foo',
                   gallery_url='gallery/foo', edit_url='edit/foo'),
        Submission(filepath='path/to/bar.jpg', success=False, error='Oops'),
        Submission(filepath='path/to/baz.jpg', success=True,
                   image_url='img/baz', thumbnail_url='thumb/baz', web_url='web/baz',
                   gallery_url='gallery/baz', edit_url='edit/baz'),
    ))
    with mock_io() as cap:
        exit_code = await _output.text(mock_gallery, ['path/to/foo.jpg',
                                                      'path/to/bar.jpg',
                                                      'path/to/baz.jpg'])
    assert exit_code == 1
    assert cap.stderr == ''
    assert cap.stdout == (
        'Gallery: <Gallery URL>\n'
        '   Edit: <Edit URL>\n'
        '* foo.jpg\n'
        '      Image: img/foo\n'
        '  Thumbnail: thumb/foo\n'
        '    Webpage: web/foo\n'
        '* bar.jpg\n'
        '  Oops\n'
        '* baz.jpg\n'
        '      Image: img/baz\n'
        '  Thumbnail: thumb/baz\n'
        '    Webpage: web/baz\n'
    )
    assert mock_gallery.create.call_args_list == [call()]
    assert mock_gallery.add.call_args_list == [
        call(['path/to/foo.jpg', 'path/to/bar.jpg', 'path/to/baz.jpg'])
    ]






@pytest.mark.asyncio
async def test_json_fails_unless_all_files_ok(mock_io, mock_gallery, mocker):
    mock_all_files_ok = mocker.patch('imgbox._output._all_files_ok', return_value=False)
    with mock_io() as cap:
        exit_code = await _output.json(mock_gallery, ['path/to/foo.jpg'])
    assert exit_code == 1
    assert cap.stderr == ''
    assert cap.stdout == ''
    assert mock_all_files_ok.call_args_list == [call(['path/to/foo.jpg'])]
    assert mock_gallery.create.call_args_list == []
    assert mock_gallery.add.call_args_list == []

@pytest.mark.asyncio
async def test_json_encounters_no_exceptions(mock_io, mock_gallery, mocker):
    mocker.patch('imgbox._output._all_files_ok', return_value=True)
    mock_gallery.add.return_value = AsyncIterator((
        Submission(filepath='path/to/foo.jpg', success=True,
                   image_url='img/foo', thumbnail_url='thumb/foo', web_url='web/foo',
                   gallery_url='gallery/foo', edit_url='edit/foo'),
    ))
    with mock_io() as cap:
        exit_code = await _output.json(mock_gallery, ['path/to/foo.jpg'])
    assert exit_code == 0
    assert cap.stderr == ''
    assert json.loads(cap.stdout) == [
        {
            'filename': 'foo.jpg',
            'filepath': 'path/to/foo.jpg',
            'success': True,
            'error': None,
            'image_url': 'img/foo',
            'thumbnail_url': 'thumb/foo',
            'web_url': 'web/foo',
            'gallery_url': 'gallery/foo',
            'edit_url': 'edit/foo',
        },
    ]
    assert mock_gallery.add.call_args_list == [call(['path/to/foo.jpg'])]
    assert mock_gallery.create.call_args_list == []

@pytest.mark.asyncio
async def test_json_handles_error_from_adding_to_gallery(mock_io, mock_gallery, mocker):
    mocker.patch('imgbox._output._all_files_ok', return_value=True)
    mock_gallery.add.return_value = AsyncIterator((
        Submission(filepath='path/to/foo.jpg', success=True,
                   image_url='img/foo', thumbnail_url='thumb/foo', web_url='web/foo',
                   gallery_url='gallery/foo', edit_url='edit/foo'),
        Submission(filepath='path/to/bar.jpg', success=False, error='Oops'),
        Submission(filepath='path/to/baz.jpg', success=True,
                   image_url='img/baz', thumbnail_url='thumb/baz', web_url='web/baz',
                   gallery_url='gallery/baz', edit_url='edit/baz'),
    ))
    with mock_io() as cap:
        exit_code = await _output.json(mock_gallery, ['path/to/foo.jpg',
                                                      'path/to/bar.jpg',
                                                      'path/to/baz.jpg'])
    assert exit_code == 1
    assert cap.stderr == ''
    assert json.loads(cap.stdout) == [
        {
            'filename': 'foo.jpg',
            'filepath': 'path/to/foo.jpg',
            'success': True,
            'error': None,
            'image_url': 'img/foo',
            'thumbnail_url': 'thumb/foo',
            'web_url': 'web/foo',
            'gallery_url': 'gallery/foo',
            'edit_url': 'edit/foo',
        },
        {
            'filename': 'bar.jpg',
            'filepath': 'path/to/bar.jpg',
            'success': False,
            'error': 'Oops',
            'image_url': None,
            'thumbnail_url': None,
            'web_url': None,
            'gallery_url': None,
            'edit_url': None,
        },
        {
            'filename': 'baz.jpg',
            'filepath': 'path/to/baz.jpg',
            'success': True,
            'error': None,
            'image_url': 'img/baz',
            'thumbnail_url': 'thumb/baz',
            'web_url': 'web/baz',
            'gallery_url': 'gallery/baz',
            'edit_url': 'edit/baz',
        },
    ]
    assert mock_gallery.add.call_args_list == [
        call(['path/to/foo.jpg', 'path/to/bar.jpg', 'path/to/baz.jpg']),
    ]
    assert mock_gallery.create.call_args_list == []
