#!/usr/bin/env python3
"""
Get authorization cookie for the RemoteLock API
"""

__author__ = "Dustin Rasener"
__version__ = "0.1.0"
__license__ = "MIT"

import argparse
import getpass
import requests
import json
import sys
from logzero import logger


def main(args):
    logger.setLevel(10 * (4 - args.verbose))

    # Prompt the user for their RemoteLock credentials
    username = args.email
    if (args.email is None):
        username = input("Email: ")    
    password = getpass.getpass("Password: ")

    with (open("auth-preauth-request.json", "r") as f):
        request = json.load(f)
        url = request["url"]
        logger.info(f"URL: {url}")
        method = request["method"]
        logger.debug(f"Method: {method}")
        headers = request["headers"]
        logger.debug(f"Headers: {headers}")

        response = requests.request(method, url, headers=headers)
        if response.status_code >= 400:
            logger.error(f"Response: {response.status_code} {response.reason}")
            logger.error(f"Response Headers: {response.headers}")
            logger.error(f"Response Body: {response.text}")
            sys.exit(1)
        logger.info(f"Response: {response.status_code} {response.reason}")
        logger.debug(f"Response Headers: {response.headers}")
        logger.debug(f"Response Body: {response.text}")

        # Extract the session cookie from the response
        session_cookie = response.headers["Set-Cookie"].split(";")[0]
        logger.debug(f"Session Cookie: {session_cookie}")

    with (open("auth-request.json", "r") as f):
        request = json.load(f)
        url = request["url"]
        logger.info(f"URL: {url}")
        method = request["method"]
        logger.debug(f"Method: {method}")
        headers = request["headers"]
        logger.debug(f"Headers: {headers}")
        body = request["body"]
        logger.debug(f"Body: {body}")

        headers["Cookie"] = session_cookie

        response = requests.request(method, url, headers=headers, data=body)
        if response.status_code >= 400:
            logger.error(f"Response: {response.status_code} {response.reason}")
            logger.error(f"Response Headers: {response.headers}")
            logger.error(f"Response Body: {response.text}")
            sys.exit(1)
        logger.info(f"Response: {response.status_code} {response.reason}")
        logger.debug(f"Response Headers: {response.headers}")
        logger.debug(f"Response Body: {response.text}")

        # Save the cookie to a file for use by other scripts
        with open(args.output, "w") as outfile:
            json.dump({"session_cookie": session_cookie}, outfile, indent=4)

        print("Success! You can now run collect.py to collect data from the RemoteLock API.")


if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser()

    # optional email argument
    parser.add_argument("-e", "--email", help="Email address for RemoteLock account")

    # optional argument for output file
    parser.add_argument("-o", "--output", default="rundata/cookies.json", help="Output file")

    # Optional argument which requires a parameter (eg. -d test)
    parser.add_argument("-n", "--name", action="store", dest="name")

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
