#!/usr/bin/env python3
"""
Collect the data from the RemoteLock API

Prior to running this script, run auth.py to get the session cookie required to 
make requests to the API.
"""

__author__ = "Dustin Rasener"
__version__ = "0.1.0"
__license__ = "MIT"

import argparse
import json
import requests
import sys
import time
import random
from logzero import logger


def parse_url(url):
    """
    Parse the device ID and publisher ID from the URL
    """
    return {"device_type": url.split("/")[4], "publisher_id": url.split("/")[5]}

def main(args):
    logger.setLevel(10 * (4 - args.verbose))
    if args.delay < 1:
        logger.error("Delay must be at least 1 second")
        sys.exit(1)

    try:
        with (open('rundata/cookies.json', 'r') as f):
            cookies = json.load(f)
            session_cookie = cookies['session_cookie']
    except:
        logger.error("No cookies.json file found. Run auth.py to generate this file.")
        sys.exit(1)

    lock = parse_url(args.event_page_url)

    with (open("config/collect-request.json", "r") as f):
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

        data = []
        for page in range(args.start, args.start + args.pages):
            headers["Referer"] = f"https://connect.remotelock.com/devices/{lock['device_type']}/{lock['publisher_id']}/events?page={page}"
        
            body = json.loads(body)
            body["page"] = page
            body["publisher_id"] = lock['publisher_id']
            body = json.dumps(body)            
        
            time.sleep(args.delay + random.random() - 0.5)

            response = requests.request(method, url, headers=headers, data=body)
            if response.status_code >= 400:
                logger.error(f"Response: {response.status_code} {response.reason}")
                logger.error("To authorize: Authenticate to the RemoteLock website, and use the inpsector to grab the cookie. (Find a call to the API and look at cookies)")
                logger.debug(f"Response Headers: {response.headers}")
                logger.debug(f"Response Body: {response.text}")
                sys.exit(1)
            if not args.quiet:
                print(f"Page {page}: {response.status_code} {response.reason}")
            logger.info(f"Response: {response.status_code} {response.reason}")
            logger.debug(f"Response Headers: {response.headers}")
            logger.debug(f"Response Body: {response.text}")

            try:
                data.extend(response.json().get("data", []))
            except json.JSONDecodeError:
                logger.error("Response was not valid JSON")
                logger.debug(f"Response Headers: {response.headers}")
                logger.debug(f"Response Body: {response.text}")
                sys.exit(1)
    
        with open(args.output, "w") as outfile:
            json.dump(data, outfile, indent=4)


if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser()

    parser.add_argument("event_page_url", help="URL of events page on RemoteLock website")
    parser.add_argument("pages", type=int, help="Number of pages to collect")

    # optional start index argument
    parser.add_argument("-s", "--start", type=int, default=1, help="Index of the first page to collect (1-based)")

    # optional request delay argument
    parser.add_argument("-d", "--delay", type=int, default=1, help="Number of seconds to delay between requests")

    # optional output file argument
    parser.add_argument("-o", "--output", default="rundata/lockdata.json", help="Output file name")

    # optional argument to suppress output
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress output")

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
