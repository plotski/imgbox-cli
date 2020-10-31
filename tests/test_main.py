from unittest.mock import Mock, call

import pytest

from imgbox import __bugtracker_url__
from imgbox._main import run


# Python 3.6 doesn't have AsyncMock
class AsyncMock(Mock):
    def __call__(self, *args, **kwargs):
        async def coro(_sup=super()):
            return _sup.__call__(*args, **kwargs)
        return coro()


@pytest.fixture
def gallery(mocker):
    return mocker.patch(
        'pyimgbox.Gallery',
        Mock(return_value=Mock(__aenter__=AsyncMock(), __aexit__=AsyncMock())),
    )


@pytest.mark.asyncio
async def test_run_with_debug_argument(mock_io, mocker, gallery):
    mocker.patch('imgbox._input.get_files')
    mocker.patch('logging.basicConfig')
    with mock_io():
        await run(args=['--debug'])
    import logging
    assert logging.basicConfig.call_args_list == [
        call(
            level=logging.DEBUG,
            format='%(module)s: %(message)s',
        ),
    ]


@pytest.mark.asyncio
async def test_run_with_get_files_raising_ValueError(mock_io, mocker, gallery):
    mocker.patch('imgbox._input.get_args')
    mocker.patch('imgbox._input.get_files', side_effect=ValueError('No'))
    with mock_io() as cap:
        await run(args=[])
    assert cap.stdout == ''
    assert cap.stderr == 'No\n'


@pytest.mark.parametrize(argnames='parameter', argvalues=('--title', '-t'))
@pytest.mark.asyncio
async def test_run_with_title_argument(parameter, mock_io, mocker, gallery):
    mocker.patch('imgbox._input.get_files')
    with mock_io():
        await run(args=[parameter, 'Foo'])
    assert gallery.call_args_list == [
        call(
            title='Foo',
            adult=False,
            thumb_width=100,
            square_thumbs=False,
            comments_enabled=False,
        )
    ]


@pytest.mark.parametrize(argnames='parameter', argvalues=('--adult', '-a'))
@pytest.mark.asyncio
async def test_run_with_adult_argument(parameter, mock_io, mocker, gallery):
    mocker.patch('imgbox._input.get_files')
    with mock_io():
        await run(args=[parameter])
    assert gallery.call_args_list == [
        call(
            title=None,
            adult=True,
            thumb_width=100,
            square_thumbs=False,
            comments_enabled=False,
        )
    ]


@pytest.mark.parametrize(argnames='parameter', argvalues=('--thumb-width', '-w'))
@pytest.mark.asyncio
async def test_run_with_thumb_width_argument(parameter, mock_io, mocker, gallery):
    mocker.patch('imgbox._input.get_files')
    with mock_io():
        await run(args=[parameter, '123'])
    assert gallery.call_args_list == [
        call(
            title=None,
            adult=False,
            thumb_width=123,
            square_thumbs=False,
            comments_enabled=False,
        )
    ]


@pytest.mark.parametrize(argnames='parameter', argvalues=('--square-thumbs', '-q'))
@pytest.mark.asyncio
async def test_run_with_square_thumbs_argument(parameter, mock_io, mocker, gallery):
    mocker.patch('imgbox._input.get_files')
    with mock_io():
        await run(args=[parameter])
    assert gallery.call_args_list == [
        call(
            title=None,
            adult=False,
            thumb_width=100,
            square_thumbs=True,
            comments_enabled=False,
        )
    ]


@pytest.mark.parametrize(argnames='parameter', argvalues=('--comments', '-c'))
@pytest.mark.asyncio
async def test_run_with_comments_argument(parameter, mock_io, mocker, gallery):
    mocker.patch('imgbox._input.get_files')
    with mock_io():
        await run(args=[parameter])
    assert gallery.call_args_list == [
        call(
            title=None,
            adult=False,
            thumb_width=100,
            square_thumbs=False,
            comments_enabled=True,
        )
    ]


@pytest.mark.parametrize(argnames='parameter', argvalues=('--json', '-j'))
@pytest.mark.asyncio
async def test_run_with_json_argument(parameter, mock_io, mocker, gallery):
    mocker.patch('imgbox._input.get_files', return_value=['foo.jpg', 'bar.png'])
    mock_output_json = mocker.patch('imgbox._output.json', AsyncMock(return_value=10))
    mock_output_text = mocker.patch('imgbox._output.text', AsyncMock(return_value=20))
    with mock_io():
        exit_code = await run(args=[parameter])
        assert exit_code == 10
    assert mock_output_json.call_args_list == [
        call(
            gallery.return_value,
            ['foo.jpg', 'bar.png']
        ),
    ]
    assert mock_output_text.call_args_list == []


@pytest.mark.asyncio
async def test_run_with_no_json_argument(mock_io, mocker, gallery):
    mocker.patch('imgbox._input.get_files', return_value=['foo.jpg', 'bar.png'])
    mock_output_json = mocker.patch('imgbox._output.json', AsyncMock(return_value=10))
    mock_output_text = mocker.patch('imgbox._output.text', AsyncMock(return_value=20))
    with mock_io():
        exit_code = await run(args=[])
        assert exit_code == 20
    assert mock_output_json.call_args_list == []
    assert mock_output_text.call_args_list == [
        call(
            gallery.return_value,
            ['foo.jpg', 'bar.png']
        ),
    ]


@pytest.mark.asyncio
async def test_run_with_output_creator_raising_exception(mock_io, mocker, gallery):
    mocker.patch('imgbox._input.get_files')
    mocker.patch('imgbox._output.json', AsyncMock(side_effect=ValueError('Foo')))
    mocker.patch('imgbox._output.text', AsyncMock(side_effect=ValueError('Bar')))
    with mock_io() as cap:
        await run(args=['--json'])
    assert cap.stdout == ''
    assert cap.stderr.startswith('Traceback')
    assert '\nValueError: Foo\n' in cap.stderr
    print(cap.stderr)
    assert cap.stderr.endswith('\n\nPlease report this as a bug: '
                               f'{__bugtracker_url__}\n')
