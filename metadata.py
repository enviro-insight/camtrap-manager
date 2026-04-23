#!/usr/bin/env python3

# generate a csv file with metadata for all the video files in a specified directory

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import csv
from tkinter import Tk
from tkinter.filedialog import askdirectory, askopenfilename
from pathlib import Path
from datetime import date

DIRNAME_FORMAT = 'SC' # CS for camera - site or SC for site - camera

EXIFTOOL_DIR = r"C:\tools\exiftool"  # folder containing exiftool.exe

def ensure_exiftool():
    if shutil.which("exiftool") is None:
        os.environ["PATH"] = EXIFTOOL_DIR + os.pathsep + os.environ["PATH"]

    if shutil.which("exiftool") is None:
        raise RuntimeError(
            "ExifTool not found. Install it or update EXIFTOOL_DIR."
        )

def exiftool_metadata(file_path: Path) -> dict:
    cmd = [
        "exiftool",
        "-json",
        "-G1",
        "-a",
        "-s",
        "-u",
        "-U",
        "-ee3",
        "-api",
        "RequestAll=3",
        str(file_path),
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True
    )

    data = json.loads(result.stdout)
    return data[0] if data else {}

def get_file_metadata(file_path: Path) -> dict:

    metadata = exiftool_metadata(file_path)
    
    # get the date and duration
    date_time = metadata.get("QuickTime:CreateDate")
    parts = date_time.split(" ") if date_time else [None, None]
    date = parts[0].replace(':', '-') if len(parts) > 0 else None
    time = parts[1] if len(parts) > 1 else None
    duration = metadata.get("QuickTime:Duration")

    # get the folder name and file name
    file_name = file_path.name

    # return as a dict
    return {
        "file_name": file_name,
        "camera": "",
        "site": "",
        "latitude": "",
        "longitude": "",
        "date": date,
        "time": time,
        "duration": duration
    }

def get_last_deployment() -> dict:
    # this is a placeholder function that would need to be implemented to get the last deployment info from the google sheet
    return {
        "camera": "SC01",
        "site": "SiteA"
    }

# TODO could add file format later if needed
def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract metadata from camera trap videos using ExifTool."
    )

    parser.add_argument(
        "-c",
        "--camera-id",
        help="The ID number of the camera, e.g. C027"
    )

    return parser.parse_args()

# python metadata.py <directory> <cameras file>
def main():

    args = parse_args()

    if 'input' not in args or not args.input:

        Tk().withdraw()
        directory = askdirectory(title="Select folder containing video files")
        if not directory:
            print("Error: No directory selected.")
            sys.exit(1)
        else:
            directory = Path(directory)
    else:
        directory = Path(args.input)

    if not os.path.isdir(directory):
        print(f"Error: Input directory does not exist: {args.input}")
        sys.exit(1)

    if not args.camera_id:
        print("Camera ID is required, use -c with camera ID i.e. python metadata.py -c C027")
        sys.exit(1)
    camera_id = args.camera_id

    if 'deployments_file' not in args or not args.deployments_file:
        Tk().withdraw()
        deployments_file = askopenfilename(title="Select deployments file", filetypes=[("CSV files", "*.csv")])

        if not deployments_file:
            print("No deployments file selected. Camera and site fields will be left blank in the output dataset.")
        else:
            deployments_file = Path(deployments_file)
            if not deployments_file.is_file():
                print(f"Error: Deployments file does not exist: {deployments_file}")
                sys.exit(1)

    # confirm the camera ID on the command line
    print(f"Please type in the camera ID again to confirm it is correct (entered: {camera_id}): ", end="")
    confirm_camera_id = input().strip()
    if confirm_camera_id != camera_id:
        print("Error: Camera IDs do not match. Please start again...")
        sys.exit(1)


    print("Reading metadata from video files in directory:", directory, "for camera ID:", camera_id)

    print("Ensuring ExifTool is available...")
    try:
        ensure_exiftool()
        print("ExifTool confirmed.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(3)

    device_deployments = []
    if (deployments_file):
        print("Reading deployments file... ")
        try:
            with open(deployments_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                device_deployments = [
                    row for row in reader
                    if row["deviceID"] == camera_id
                    and (row["activity"] == "Camera set-up" or row["activity"] == "Camera retrieval")
                ]
                
                # order by deploymentDate and deploymentTime
                device_deployments = sorted(device_deployments, key=lambda x: (x["deploymentDate"], x["deploymentTime"]), reverse=True)
                
                if not device_deployments:
                    print(f"Error: No deployments found for camera {camera_id} in deployments file.")
                    sys.exit(1)
        except Exception as e:
            print(f"Error reading deployments file: {e}")
            sys.exit(1)
        
    # get all the video files in the specified directory, mp4 and avi
    video_files = [
        f
        for ext in ("*.mp4", "*.avi")
        for f in directory.glob(ext, case_sensitive=False)
    ]

    # extract metadata for each file and print it
    results = []
    old_name_new_name_map = {}
    print(f"Extracting metadata from {len(video_files)} files in {directory}...")
    for i, video_file in enumerate(video_files, start=1):
        percent = (i / len(video_files)) * 100
        dots = int(percent // 5)
        print(f"\rProgress: {percent:.1f}% {'.' * dots}", end='', flush=True)

        file_path = Path(video_file)

        # this should never happen since we got the file from glob, but just in case
        if not file_path.is_file():
            print(f"Oops! Something went wrong for file: {file_path}")
            sys.exit(1)

        try:
            metadata = get_file_metadata(file_path)
            metadata["camera"] = camera_id
            metadata["site"] = None
            metadata["latitude"] = None
            metadata["longitude"] = None

            compressed_date = metadata['date'].replace('-', '') if metadata['date'] else 'unknown_date'
            compressed_time = metadata['time'].replace(':', '') if metadata['time'] else 'unknown_time'
            # file extension
            ext = file_path.suffix
            new_file_name = f"{metadata['camera']}_{compressed_date}{compressed_time}{ext}"
            old_name_new_name_map[file_path.name] = new_file_name

            # use metadata date and time to find the most recent deployment that occurred before the video was taken
            if (device_deployments):
                video_datetime = f"{metadata['date']} {metadata['time']}"
                deployment = next((d for d in device_deployments if f"{d['deploymentDate']} {d['deploymentTime']}" <= video_datetime), None)
                if deployment:
                    if deployment["activity"] == "Camera retrieval":
                        print(f"Warning: No active deployment for camera {camera_id} at {video_datetime} found (file {file_path}). Last record was a retrieval from site {deployment['locationID']} on {deployment['deploymentDate']} at {deployment['deploymentTime']}. This may indicate that the camera was moved or redeployed without a camera setup record. Location fields will be blank in the dataset.")
                    else:
                        metadata["site"] = deployment["locationID"]
                        metadata["latitude"] = deployment["latitude"]
                        metadata["longitude"] = deployment["longitude"]
                else:
                    print(f"Warning: No matching deployment found for video {file_path}. Camera and site will be left blank.")

            metadata["file_name"] = new_file_name
            results.append(metadata)
        except subprocess.CalledProcessError as e:
            print("ExifTool failed.")
            print(e.stderr)
            sys.exit(2)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(3)

    # sort results by date and time
    results = sorted(results, key=lambda x: (x["date"], x["time"]))

    # write to csv
    # same directory as the script, named metadata.csv
    # get the last date in the dataset for the filename else today's date
    last_date = results[-1]["date"] if results else date.today().isoformat()
    outfile = directory / f"metadata_{camera_id}_{last_date}.csv"

    print(f"Writing metadata to {outfile}...")  
    with open(outfile, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file_name", "camera", "site", "date", "time", "duration", "latitude", "longitude", "species", "identifiedBy", "identifiedDate", "notes"])
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    
    print(os.linesep) # print a newline after the progress bar

    print("Renaming files...")
    for old_name, new_name in old_name_new_name_map.items():
        old_path = directory / old_name
        new_path = directory / new_name
        if new_path.exists():
            print(f"Warning: Cannot rename {old_path} to {new_path} because the target file already exists. Skipping.")
        else:
            try:
                old_path.rename(new_path)
            except Exception as e:
                print(f"Error renaming {old_path} to {new_path}: {e}")

    print(f"All done!")
    
if __name__ == "__main__":
    main()