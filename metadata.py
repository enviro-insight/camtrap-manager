#!/usr/bin/env python3

# generate a csv file with metadata for all the video files in a specified directory

import argparse
import json
import os
import shutil
import subprocess
import sys
import csv
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


def get_metadata(file_path: Path) -> dict:

    metadata = exiftool_metadata(file_path)
    
    # get the date and duration
    date_time = metadata.get("QuickTime:CreateDate")
    parts = date_time.split(" ") if date_time else [None, None]
    date = parts[0].replace(':', '-') if len(parts) > 0 else None
    time = parts[1] if len(parts) > 1 else None
    duration = metadata.get("QuickTime:Duration")

    # get the folder name and file name
    file_name = file_path.name
    
    dir = file_path.parent.name
    dir_parts = dir.split("-")
    if len(dir_parts) == 2:
        if DIRNAME_FORMAT == 'CS':
            camera = dir_parts[0]
            site = dir_parts[1]
        else:
            site = dir_parts[0]
            camera = dir_parts[1]
    else:
        camera = None
        site = None

    # return as a dict
    return {
        "file_name": file_name,
        "camera": camera,
        "site": site,
        "date": date,
        "time": time,
        "duration": duration
    }

def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract metadata from camera trap videos using ExifTool."
    )

    parser.add_argument(
        "-i",
        "--input",
        help="Directory containing MP4 videos"
    )

    parser.add_argument(
        "-o",
        "--output",
        default="metadata.csv",
        help="Output CSV file (default: metadata.csv)"
    )

    parser.add_argument(
        "-f",
        "--cameras-file",
        help="CSV file with camera locations"
    )

    return parser.parse_args()

# python metadata.py <directory> <cameras file>
def main():

    args = parse_args()

    if not args.input:
        print("Error: Input directory is required.")
        sys.exit(1)

    if not os.path.isdir(args.input):
        print(f"Error: Directory not found: {args.input}")
        sys.exit(1)

    if not args.cameras_file:
        print("Error: Cameras file is required.")
        sys.exit(1)

    if not os.path.isfile(args.cameras_file):
        print(f"Error: Cameras file not found: {args.cameras_file}")
        sys.exit(1)


    if len(sys.argv) != 2:
        print("Usage: metadata.py <directory>")
        sys.exit(1)

    directory = Path(args.input)

    print("Reading camera locations file... ")
    try:
        with open(args.cameras_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            camera_locations = {row["camera"]: row["location"] for row in reader}
            print(f"Camera locations loaded for {len(camera_locations)} cameras.")
    except Exception as e:
        print(f"Error reading cameras file: {e}")
        sys.exit(1)

    print("Ensuring ExifTool is available...")
    try:
        ensure_exiftool()
        print("ExifTool confirmed.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(3)

    # get all the video files in the specified directory
    video_files = list(directory.glob("*.mp4"))

    # extract metadata for each file and print it
    results = []
    print(f"Extracting metadata from {len(video_files)} files in {directory}...")
    for video_file in video_files:

        file_path = Path(video_file)

        # this should never happen since we got the file from glob, but just in case
        if not file_path.is_file():
            print(f"File not found: {file_path}")
            sys.exit(1)

        try:
            metadata = get_metadata(file_path)
            results.append(metadata)
        except subprocess.CalledProcessError as e:
            print("ExifTool failed.")
            print(e.stderr)
            sys.exit(2)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(3)


    # write to csv
    # same directory as the script, named metadata.csv
    outfile = directory / args.output

    with open(outfile, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file_name", "camera", "site", "date", "time", "duration"])
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    
    print(f"Metadata extracted for {len(results)} files and written to {outfile}")
    

if __name__ == "__main__":
    main()