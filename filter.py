#!/usr/bin/env python3
"""
Filter events returned from the RemoteLock API. Provide the name of a user. By 
default, the script will return all unlocked events for that user, and the 
locked event that immediately follows the unlocked event.

Example Events:
My Cleaning Team, 2023-08-21T11:31:46Z, unlocked
Thumbturn, 2023-08-21T11:31:56Z, locked
Thumbturn, 2023-08-21T12:00:09Z, unlocked
Thumbturn, 2023-08-21T12:00:19Z, locked
Gina Giraffe, 2023-08-21T22:00:09Z, unlocked

Notes:
- after unlocking, the user may lock the lock by thumbturn; since we're 
  interested in the time spent at the property, the following locked event may
  not be enough to establish time
- in order to identify the final "locked" event, we look for the next unlock by
  pin event
- In the above example, the user "My Cleaning Team" unlocked the lock at 11:31:46Z,
  and locked it again for the last time at T12:00:19Z, meaning they spent 28 
  minutes at the property
- After the user Gina Giraffe arrives, we aren't interested in any more events
  until My Cleaning Team unlocks the lock again
- The output will consist of a number of lines like those above, each 
  representing all of the data required to establish the time spent at the 
  property by a single user
- The actual input will be a JSON array of these lines, but the above example
  is easier to read
"""

__author__ = "Dustin Rasener"
__version__ = "0.1.0"
__license__ = "MIT"

import argparse
import json
import csv
import sys
from copy import copy
from logzero import logger

EVENT_TYPES = ["locked_event", "unlocked_event"]

class DataCollector:
    def __init__(self, input_data, quiet=False) -> None:
        self.input_data = input_data
        self.quiet = quiet
        self.collected_data = []
        self.cursor = 0
        self.found_events = 0
        self.sort_events_by_time()
        self.filter_to_event_types()

    def sort_events_by_time(self):
        """Sort the input data by time ascending"""
        self.input_data.sort(key=lambda x: x['attributes']['occurred_at'])

    def filter_to_event_types(self):
        """Filter the input data to only the specified event types"""
        self.input_data = [event for event in self.input_data if event['type'] in EVENT_TYPES]

    def collect_events(self, username):
        """Collect all events for the specified user, and enough of the 
        following events to establish the time spent at the property"""
        while True:
            event = self.get_next_event()
            logger.debug(f"event: {event}")
            if event is None:
                break
            if self.is_user_event(event, username):
                self.record_events_until_next_unlock_by_pin(event, username)
                self.found_events += 1

    def is_user_event(self, event, username):
        """Return True if the event is for the specified user"""
        associated_username = None
        if 'associated_resource' in event['relationships']:
            associated_username = event['relationships']['associated_resource']['attributes']['name']
        logger.debug(f"associated_username: {associated_username} username: {username}")
        return associated_username == username
    
    def is_unlock_by_pin_event(self, event):
        """Return True if the event is an unlock by pin event"""
        return event['type'] == 'unlocked_event' and event['attributes']['method'] == 'pin'
    
    def is_unlock_event(self, event):
        """Return True if the event is an unlock event"""
        return event['type'] == 'unlocked_event'

    def record_events_until_next_unlock_by_pin(self, event, username):
        """Record all events until the next unlock by pin (i.e. not thumbturn)"""
        self.collected_data.append(event)
        while True:
            event = self.get_next_event()
            if event is None:
                break
            if not self.is_unlock_by_pin_event(event):
                self.collected_data.append(event)
                continue
            if self.is_unlock_event(event) and not self.is_user_event(event, username):
                self.collected_data.append(event)
                break
            self.collected_data.append(event)

    def get_next_event(self):
        """Return the next event in the data"""
        event = None
        if (self.cursor < len(self.input_data)):
            event = self.input_data[self.cursor]
            self.cursor += 1
        return event
    
    def get_event_data(self):
        """Return the collected data as a CSV string"""
        event_data = []
        event_row = {'username': "", 'time': "", 'event': ""}
        for event in self.collected_data:
            username = "Someone"
            if 'associated_resource' in event['relationships']:
                username = event['relationships']['associated_resource']['attributes']['name']
            event_row['username'] = username
            event_row['time'] = event['attributes']['occurred_at']
            event_row['event'] = event['type']
            event_data.append(copy(event_row))
        if not self.quiet:
            print(f"Found {self.found_events} events")
        return event_data
    

def main(args):
    logger.setLevel(10 * (4 - args.verbose))

    data = None
    with open(args.input, 'r') as f:
        data = json.load(f)
        collector = DataCollector(data, args.quiet)
        collector.collect_events(args.username)
        data = collector.get_event_data()
    
    # Write the response
    with open(args.output, "w") as outfile:
        json.dump(data, outfile, indent=4)    
        

if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser()

    parser.add_argument("username", help="Name of the user to filter events for")

    # optional input file
    parser.add_argument("-i", "--input", default="rundata/lockdata.json", help="JSON file containing events returned from the RemoteLock API generated by collect.py")

    # optional output file
    parser.add_argument("-o", "--output", default="rundata/filtered.json", help="Output file")

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
