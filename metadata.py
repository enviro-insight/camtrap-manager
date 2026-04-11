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

    parser.add_argument(
        "-o",
        "--output-file",
        default="metadata.csv",
        help="Output CSV file (default: metadata.csv); will be added to same directory as the input videos (optional)"
    )

    return parser.parse_args()

# python metadata.py <directory> <cameras file>
def main():

    args = parse_args()

    if not args.input:
        print("Error: Input directory is required (-h for help).")
        sys.exit(1)

    if not os.path.isdir(args.input):

        Tk.withdraw()
        directory = askdirectory(title="Select folder containing video files")
        if not directory:
            print("Error: No directory selected.")
            sys.exit(1)
        else:
            directory = Path(directory)
    else:
        directory = Path(args.input)

    if not args.camera_id:
        print("Camera ID is required, use -c with camera ID i.e. python metadata.py -c C027")
        sys.exit(1)
    camera_id = args.camera_id

    if not args.deployments_file:
        Tk.withdraw()
        deployments_file = askopenfilename(title="Select deployments file", filetypes=[("CSV files", "*.csv")])

        if not deployments_file:
            print("No deployments file selected. Camera and site fields will be left blank in the output dataset.")
        else:
            deployments_file = Path(deployments_file)
            if not deployments_file.is_file():
                print(f"Error: Deployments file does not exist: {deployments_file}")
                sys.exit(1)

    output_file = Path(args.output_file)

    # make sure output file is a csv
    if output_file.suffix.lower() != ".csv":
        print("Error: Output file must have a .csv extension.")
        sys.exit(1)

    # make sure the output file is not already open somewhere
    if output_file.exists():
        try:
            with open(output_file, "a"):
                pass
        except PermissionError:
            print(f"Error: Output file is open in another program: {output_file}. Please close it and try again, or specify a different output file name with -o.")
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
        

    # get all the video files in the specified directory
    video_files = list(directory.glob("*.mp4"))

    # extract metadata for each file and print it
    results = []
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

            # use metadata date and time to find the most recent deployment that occurred before the video was taken
            if (device_deployments):
                video_datetime = f"{metadata['date']} {metadata['time']}"
                deployment = next((d for d in device_deployments if f"{d['deploymentDate']} {d['deploymentTime']}" <= video_datetime), None)
                if deployment:
                    if deployment["activity"] == "Camera retrieval":
                        print(f"Warning: No active deployment for camera {camera_id} at {video_datetime} found (file {file_path}). Last record was a retrieval from site {deployment['locationID']} on {deployment['deploymentDate']} at {deployment['deploymentTime']}. This may indicate that the camera was moved or redeployed without a camera setup record. Location fields will be blank in the dataset.")
                    else:
                        metadata["camera"] = deployment["deviceID"]
                        metadata["site"] = deployment["locationID"]
                        metadata["latitude"] = deployment["latitude"]
                        metadata["longitude"] = deployment["longitude"]
                else:
                    print(f"Warning: No matching deployment found for video {file_path}. Camera and site will be left blank.")

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
    outfile = directory / output_file

    with open(outfile, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file_name", "camera", "site", "date", "time", "duration", "latitude", "longitude", "species", "identifiedBy", "identifiedDate", "notes"])
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    
    print(os.linesep) # print a newline after the progress bar
    print(f"Metadata extracted for {len(results)} files and written to {outfile}")
    

if __name__ == "__main__":
    main()