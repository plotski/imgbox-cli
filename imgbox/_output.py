import os
import sys

import pyimgbox


# https://stackoverflow.com/a/55930068
async def _async_enumerate(async_iter, start=0):
    n = start
    async for item in async_iter:
        yield n, item
        n += 1


def _assert_file_ok(filepath):
    if not os.path.exists(filepath):
        raise AssertionError(f'No such file')
    if not os.path.isfile(filepath):
        raise AssertionError(f'Not a file')
    if not os.access(filepath, os.R_OK):
        raise AssertionError(f'Not readable')
    if os.path.getsize(filepath) > pyimgbox.MAX_FILE_SIZE:
        raise AssertionError(f'File is larger than {pyimgbox.MAX_FILE_SIZE} bytes')


def _all_files_ok(filepaths):
    # We want to check file readability before creating the gallery.
    # Gallery.add() calls create() automatically, but we don't want to wait for
    # the first file upload to finish before printing the gallery URL.
    ok = True
    for filepath in filepaths:
        try:
            _assert_file_ok(filepath)
        except AssertionError as e:
            ok = False
            print(f'{filepath}: {e}', file=sys.stderr)
    return ok


async def text(gallery, filepaths):
    exit_code = 0
    if not _all_files_ok(filepaths):
        exit_code = 1
    else:
        try:
            await gallery.create()
            print(f'Gallery: {gallery.url}')
            print(f'   Edit: {gallery.edit_url}')
        except ConnectionError as e:
            exit_code = 1
            print(str(e), file=sys.stderr)
        else:
            async for sub in gallery.add(filepaths):
                print(f'* {sub.filename}')
                if sub.success:
                    print(f'      Image: {sub.image_url}')
                    print(f'  Thumbnail: {sub.thumbnail_url}')
                    print(f'    Webpage: {sub.web_url}')
                else:
                    print(f'  {sub.error}')
                    exit_code = 1
    return exit_code


async def json(gallery, filepaths):
    exit_code = 0
    if not _all_files_ok(filepaths):
        exit_code = 1
    else:
        submissions = []
        async for sub in gallery.add(filepaths):
            submissions.append(sub)
            if not sub.success:
                exit_code = 1
        import json
        print(json.dumps(submissions, indent=4))
    return exit_code
