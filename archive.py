#!/usr/bin/env python3
"""
Save intermediate files from the rundata directory to the archive directory
"""

__author__ = "Dustin Rasener"
__version__ = "0.1.0"
__license__ = "MIT"

import argparse
import datetime
import zipfile
import os
from logzero import logger


def main(args):
    logger.setLevel(10 * (4 - args.verbose))

    # create zip archive
    if args.output is None:
        args.output = f"{datetime.datetime.now().strftime('%Y-%m-%d')}-lockupload"
    version = 1
    while os.path.exists(f"{args.output}.zip"):
        args.output = f"{args.output} ({version})"
        version += 1
    args.output = f"{args.output}.zip"

    logger.info(f"Output file: {args.output}")
    with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in os.listdir("rundata"):
            logger.info(f"Adding {file} to archive")
            archive.write(os.path.join("rundata", file))
        archive.close()


if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser()

    # Optional output file
    parser.add_argument("-o", "--output", help="Output file (excluding extension - .zip will be added)")
    
    # Optional verbosity counter (eg. -v, -vv, -vvv, etc.)
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Verbosity (-v, -vv, etc)")

    # Specify output of "--version"
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s (version {version})".format(version=__version__))

    args = parser.parse_args()
    main(args)
