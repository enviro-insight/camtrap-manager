"""
Validate deployment sequences in a deployments CSV file.

For each deviceID, grouped by locationID:
  - There must be a set-up record before any status check or retrieval.
  - Any redeployment (a second set-up) must be preceded by a retrieval.

Usage:
    python validate.py -d <directory>
"""

import argparse
import csv
import glob
import os
from datetime import datetime

def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate deployment sequences in a deployments CSV."
    )
    parser.add_argument(
        "-d", "--dir",
        help="Directory containing the deployments CSV file."
    )
    return parser.parse_args()

SETUP_ACTIVITIES     = {"Camera set-up", "Song meter set-up"}
RETRIEVAL_ACTIVITIES = {"Camera retrieval", "Song meter retrieval"}

def is_setup(activity):     return activity in SETUP_ACTIVITIES
def is_retrieval(activity): return activity in RETRIEVAL_ACTIVITIES

def validate_sequence(records):
    """Return True if the sequence is valid, False otherwise."""
    deployed = False
    for rec in records:
        act = rec["activity"]
        if is_setup(act):
            if deployed:
                # redeployment without prior retrieval
                return False
            deployed = True
        elif is_retrieval(act):
            if not deployed:
                return False
            deployed = False
        else:
            # status check
            if not deployed:
                return False
    return True

args = parse_args()
DIR = args.dir if args.dir else datetime.now().strftime("%Y%m%d")

if not os.path.isdir(DIR):
    print(f"Error: directory not found: {DIR}")
    exit(1)

matches = glob.glob(os.path.join(DIR, "deployments*.csv"))
if not matches:
    print(f"Error: no deployments*.csv found in {DIR}")
    exit(1)

csv_file = matches[0]

records = []
with open(csv_file, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        try:
            row["_dt"] = datetime.strptime(
                f"{row['deploymentDate']} {row['deploymentTime']}", "%Y-%m-%d %H:%M"
            )
        except ValueError:
            row["_dt"] = datetime.min
        records.append(row)

# group by (deviceID, locationID)
from collections import defaultdict
groups = defaultdict(list)
for rec in records:
    groups[(rec["deviceID"], rec["locationID"])].append(rec)

invalid_devices = set()
for (device_id, location_id), recs in groups.items():
    recs.sort(key=lambda r: r["_dt"])
    if not validate_sequence(recs):
        invalid_devices.add(device_id)

for device_id in sorted(invalid_devices):
    print(device_id)
