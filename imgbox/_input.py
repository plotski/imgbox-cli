import argparse
import sys

from . import __command_name__, __version__


def get_args(argv):
    argparser = argparse.ArgumentParser(description='Upload images to imgbox.com')

    argparser.add_argument('files', nargs='*',
                           help=('Image files to upload; newline-separated file paths '
                                 'are also read from stdin'))

    argparser.add_argument('--title', '-t', default=None,
                           help='Gallery title')

    argparser.add_argument('--thumb-width', '-w', default=100, type=int,
                           help='Thumbnail width in pixels')

    argparser.add_argument('--square-thumbs', '-q', action='store_true',
                           help='Make square thumbnails')

    argparser.add_argument('--comments', '-c', action='store_true',
                           help='Enable comments')

    argparser.add_argument('--adult', '-a', action='store_true',
                           help='Mark gallery as adult-only')

    argparser.add_argument('--json', '-j', action='store_true',
                           help='Print URLs as JSON object')

    argparser.add_argument('--version', '-V', action='version',
                           version=f'{__command_name__} {__version__}')

    argparser.add_argument('--debug', action='store_true',
                           help='Print debugging information')

    return argparser.parse_args(argv)


def get_files(args):
    # Files from stdin
    files = []
    if not sys.stdin.isatty():
        files.extend(f.rstrip('\n') for f in sys.stdin.readlines() if f.strip())

    # Files from arguments
    if args.files != ['-']:
        files.extend(args.files)

    # No files is an error
    if not files:
        raise ValueError(
            'Missing at least one image file. '
            f'Run "{__command_name__} -h" for more information.'
        )

    return files
