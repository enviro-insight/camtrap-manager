# read the downloaded csv files, extract the fields we want and merge into a final output csv
# also splits Location to lat and long, and formats date and time properly
# and removes all test data rows

import csv
import os
from datetime import datetime

DIR = "20260319"

fields = {
    "dataset": "dataset", # abbreviated form from the original file
	"Site ID?": "locationID",
	"Camera or song meter ID?": "deviceID",
	"Checked by?": "checkedBy",
	"Assistants?": "assistants",
	"What are you doing?": "activity",
	"Habitat type?": "habitat",
	"Date": "deploymentDate",
	"Time": "deploymentTime",
    "Latitude": "latitude",
    "Longitude":"longitude",
	"Notes / Comments": "deploymentComments",
}

# read all the files in DIR
deployments = []
print(f"Reading CSV files from {DIR}...")
test_counter = 0
for filename in os.listdir(DIR):
    if filename.endswith(".csv"):
        if filename.startswith("deployments"): # skip temp files
            continue
        dataset_name = filename.rsplit(".", 1)[0].rsplit("_", 1)[1] # get the part before the last underscore as dataset name
        with open(os.path.join(DIR, filename), "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:

                # skip test data rows
                if "test" in (row.get("Site ID?") or "").lower():
                    test_counter += 1
                    continue

                row['dataset'] = "phone_" + dataset_name

                # if the field is Location, split to lat and long
                row["Latitude"] = ""
                row["Longitude"] = ""
                if "Location" in row:
                    location = row["Location"]
                    if location:
                        try:
                            parts = location.split(", ") # sometimes there is more than one location...
                            latlong = parts[-1] if len(parts) > 1 else location
                            lat, long = latlong.split(",")
                            row["Latitude"] = lat.strip()
                            row["Longitude"] = long.strip()
                        except ValueError:
                            print(f"Warning: Could not split Location '{location}' in file {filename}")
              
                if "Date" in row:
                    date_str = row["Date"]
                    date_obj = None

                    for fmt in ("%m/%d/%Y", "%m/%d/%y"):
                        try:
                            date_obj = datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
                    if not date_obj:
                        print(f"Warning: Could not parse Date '{date_str}' in file {filename}") 
                    else:
                        row["Date"] = date_obj.strftime("%Y-%m-%d")

                if "Time" in row:
                    time_str = row["Time"]
                    if len(time_str) > 8:
                        fmt="%I:%M:%S %p"
                    else:
                        fmt="%H:%M:%S"
                    try:
                        time_obj = datetime.strptime(time_str, fmt)
                        row["Time"] = time_obj.strftime("%H:%M")
                    except ValueError:
                        print(f"Warning: Could not parse Time '{time_str}' in file {filename}")
                
                # remove any whitespace in locationID,deviceID, including newlines
                if "Site ID?" in row:
                    row["Site ID?"] = row["Site ID?"].replace(" ", "").replace("\n", "").replace("\r", "")
                if "Camera or song meter ID?" in row:
                    row["Camera or song meter ID?"] = row["Camera or song meter ID?"].replace(" ", "").replace("\n", "").replace("\r", "")

                # remove 'site' from locationID if it exists
                if "Site ID?" in row:
                    row["Site ID?"] = row["Site ID?"].replace("site", "").replace("Site", "")

                # replace any newlines in the comments with spaces
                if "Notes / Comments" in row:
                    row["Notes / Comments"] = row["Notes / Comments"].replace("\n", " ").replace("\r", " ")

                try:
                    deployment = {fields[key]: row[key].strip() for key in fields}
                    deployments.append(deployment)
                except KeyError as e:
                    print(f"Warning: Missing expected field {e} in file {filename}. Skipping row.")
                    continue

# write to output.csv
# get the last part of DIR, should be the date
d = DIR.rsplit("/", 1)[-1]
print("Writing merged data...")
outfile = os.path.join(DIR, "deployments_" + d + ".csv")
with open(outfile, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields.values())
    writer.writeheader()
    for deployment in deployments:
        writer.writerow(deployment)

print("Done!")
print(f"{len(deployments)} deployments written to {outfile}. Skipped {test_counter} test rows.")

