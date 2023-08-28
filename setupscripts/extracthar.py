#!/usr/bin/env python3
"""
Extract the request data from a HAR file
"""

__author__ = "Dustin Rasener"
__version__ = "0.1.0"
__license__ = "MIT"

import argparse
import json
from logzero import logger


def main(args):
    logger.setLevel(10 * (4 - args.verbose))

    with open(args.harfile, 'r') as f:
        har = json.load(f)

        # Extract the URL and headers from the first request
        url = har['log']['entries'][args.request_index]['request']['url']
        logger.info(f"URL: {url}")
        headers = har['log']['entries'][args.request_index]['request']['headers']
        headers = {header['name']: header['value'] for header in headers}
        logger.debug(f"Headers: {headers}")

        # Extract the request method and body from the first request
        method = har['log']['entries'][args.request_index]['request']['method']
        logger.debug(f"Method: {method}")
        if method == 'GET':
            body = None
        else:
            body = har['log']['entries'][args.request_index]['request']['postData']['text']

        # write a JSON file with the request data
        with open(args.output, 'w') as outfile:
            request_data = {'url': url, 'method': method, 'headers': headers}
            if body is not None:
                request_data['body'] = body
            json.dump(request_data, outfile, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("harfile", help="HAR file containing request made to the RemoteLock API")
    parser.add_argument("request_index", type=int, help="Index of the request to extract from the HAR file")

    parser.add_argument("-o", "--output", default="request.json", help="Output file for the request data")

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
