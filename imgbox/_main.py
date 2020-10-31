import asyncio
import sys
import traceback

import pyimgbox

from . import __bugtracker_url__, _input, _output


def main(argv=sys.argv[1:]):
    loop = asyncio.get_event_loop()
    exit_code = loop.run_until_complete(
        run(argv)
    )
    return exit_code


async def run(args):
    args = _input.get_args(args)

    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG,
                            format='%(module)s: %(message)s')

    exit_code = 0
    try:
        files = _input.get_files(args)
    except ValueError as e:
        print(e, file=sys.stderr)
        exit_code = 1
    else:
        gallery = pyimgbox.Gallery(
            title=args.title,
            adult=args.adult,
            thumb_width=args.thumb_width,
            square_thumbs=args.square_thumbs,
            comments_enabled=args.comments,
        )

        if args.json:
            create_output = _output.json
        else:
            create_output = _output.text

        async with gallery:
            try:
                exit_code = await create_output(gallery, files)
            except Exception as e:
                exit_code = 100
                tb = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
                print(
                    f'{tb}\nPlease report this as a bug: {__bugtracker_url__}',
                    file=sys.stderr,
                )

    return exit_code
