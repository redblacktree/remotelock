#!/usr/bin/env python3
"""
Consume the results of filter.py and calculate the time between events
"""

__author__ = "Dustin Rasener"
__version__ = "0.1.0"
__license__ = "MIT"

import argparse
import datetime
import json
import csv
from logzero import logger


class REPStrackerData:
    def __init__(self, property_address, team_member, description=None, activity_group=None) -> None:
        self.fields = [
            "Date",
            "Description",
            "Hours",
            "Minutes",
            "Property Address",
            "Team Member",
            "Activity Group",
        ]
        self.property_address = property_address
        self.team_member = team_member
        self.description = description
        self.activity_group = activity_group        
        if description is None:
            self.fields.remove("Description")
        if activity_group is None:
            self.fields.remove("Activity Group")
        
    def get_fields(self):
        return self.fields

    def get_dict(self, date, minutes):
        # date in the format 01/01/1970
        minutes = round(minutes)
        data = {
            "Date": datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ").strftime("%m/%d/%Y"),
            "Hours": minutes // 60,
            "Minutes": minutes % 60,
            "Property Address": self.property_address,
            "Team Member": self.team_member,            
        }
        if self.description is not None:
            data["Description"] = self.description
        if self.activity_group is not None:
            data["Activity Group"] = self.activity_group
        return data


def find_next_event_index_for_user(events, start_index, username):
    """
    Find the next event for a given user
    """
    start_event = events[start_index]
    start_time = start_event["time"]
    start_username = start_event["username"]
    start_event_type = start_event["event"]

    # find the next event for the same user
    for i in range(start_index + 1, len(events)):
        event = events[i]
        if event["username"] == username:
            return i

def find_end_event(events, start_index):
    """
    Find the end event for a given start event
    """
    start_event = events[start_index]
    start_time = start_event["time"]
    start_username = start_event["username"]
    start_event_type = start_event["event"]

    # find the next unlock event for a user that isn't "Someone"
    for i in range(start_index + 1, len(events)):
        event = events[i]
        if event["event"] == "unlocked_event" and event["username"] != "Someone":
            return events[i-1]

def calculate_time_between_events(start_event, end_event):
    """
    Calculate the time between two events
    """
    start_time = start_event["time"]
    end_time = end_event["time"]
    return datetime.datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%SZ") - datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")            

def get_summary(start_event, end_event):
    """
    Get a summary of the events
    """
    logger.debug(f"start_event: {start_event}")
    logger.debug(f"end_event: {end_event}")
    start_time = start_event["time"]
    end_time = end_event["time"]
    username = start_event["username"]
    time_between_events = calculate_time_between_events(start_event, end_event)
    return {
        "username": username,
        "start_time": start_time,
        "end_time": end_time,
        "time_between_events": time_between_events.total_seconds() / 60
    }

def main(args):
    logger.setLevel(10 * (4 - args.verbose))
    
    if args.team_member is None:
        args.team_member = args.username

    with open(args.input, "r") as f:
        events = json.load(f)
    
    # Make sure events are sorted by time
    events = sorted(events, key=lambda k: k["time"])

    # Find the first event for the given user
    start_index = find_next_event_index_for_user(events, 0, args.username)
    if start_index is None:
        logger.error("No events found for user: {}".format(args.username))
        exit(1)
    
    visits = []
    while True:
        start_event = events[start_index]
        end_event = find_end_event(events, start_index)
        if end_event is None:
            logger.error("No end event found for user: {}".format(args.username))            
        visits.append(get_summary(start_event, end_event))
        start_index = find_next_event_index_for_user(events, start_index, args.username)
        if start_index is None:
            break

    with open(args.output, "w") as f:
        json.dump(visits, f, indent=4)

    with open(args.csv, "w") as f:
        reps_data = REPStrackerData(args.property_address, args.team_member, args.description, args.activity_group)
        writer = csv.DictWriter(f, fieldnames=reps_data.get_fields(), lineterminator='\n')
        writer.writeheader()
        for clean in visits:
            writer.writerow(reps_data.get_dict(clean.get("start_time"), clean.get("time_between_events")))

    if not args.quiet:
        print(f"Found {len(visits)} visits, averaging {round(sum([clean['time_between_events'] for clean in visits]) / len(visits))} minutes.")


if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser()

    parser.add_argument("username", help="Username to summarize time for")

    # "Property Address" argument for output file
    parser.add_argument("property_address", help="Property Address to be used for entries in the CSV file. (You can also use the property nickname defined on REPStracker)") 

    # required description argument for output file
    parser.add_argument("-d", "--description", help="Description to be used for entries in the CSV file")

    # "Activity Group" argument for output file
    parser.add_argument("-a", "--activity_group", help="Activity Group to be used for entries in the CSV file")

    # optional "Team Member" argument for output file
    parser.add_argument("-t", "--team_member", default=None, help="Team Member to be used for entries in the CSV file. Defaults to username")

    # optional input file
    parser.add_argument("-i", "--input", default="rundata/filtered.json", help="JSON file with event output from filter.py")

    # optional argument for output file
    parser.add_argument("-o", "--output", default="rundata/summary.json", help="Output file")

    # optional argument for csv output
    parser.add_argument("-c", "--csv", default="rundata/summary.csv", help="CSV output file")
    
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
