#!/usr/bin/env python3

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

EXIFTOOL_DIR = r"C:\tools\exiftool"  # folder containing exiftool.exe


def ensure_exiftool():
    if shutil.which("exiftool") is None:
        os.environ["PATH"] = EXIFTOOL_DIR + os.pathsep + os.environ["PATH"]

    if shutil.which("exiftool") is None:
        raise RuntimeError("ExifTool not found. Install it or update EXIFTOOL_DIR.")


def run_exiftool_v3(file_path: Path) -> str:
    cmd = ["exiftool", "-v3", str(file_path)]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout


def clean_atom_name(atom_name: str) -> str:
    atom_name = atom_name.strip()

    # remove leading copyright symbol if present
    if atom_name.startswith("©"):
        atom_name = atom_name[1:]

    # replace spaces and punctuation with underscores
    atom_name = re.sub(r"[^A-Za-z0-9]+", "_", atom_name).strip("_")

    return atom_name or "unknown"


def extract_udta_atoms(v3_text: str) -> dict:
    """
    Extract key-value pairs from the UserData section of exiftool -v3 output.

    Looks for patterns like:
      a9 fmt ... NOVATEK
      a9 inf ... DEMO1

    and also the summary line:
      Unknown_user = ..fmt.NOVATEK..inf.DEMO1
    """
    lines = v3_text.splitlines()
    in_udta = False
    atoms = {}

    # pattern for hex dump lines
    hex_line_re = re.compile(
        r'^\s*\|\s+[0-9a-fA-F]+:\s+(.+?)\s+\[(.*?)\]\s*$'
    )

    # collect bracket text from the udta block
    bracket_chunks = []

    for line in lines:
        if "Tag 'udta'" in line:
            in_udta = True
            continue

        if in_udta:
            if "GPSDataList" in line or "Tag 'gps '" in line:
                break

            m = hex_line_re.match(line)
            if m:
                bracket_text = m.group(2)
                bracket_chunks.append(bracket_text)

    if bracket_chunks:
        joined = "".join(bracket_chunks)

        # extract patterns like:
        # .fmt....NOVATEK
        # .inf....DEMO1.
        matches = re.findall(r'\.([A-Za-z0-9]{3,4}).*?([A-Za-z0-9_-]{3,})', joined)
        for key, value in matches:
            atoms[clean_atom_name(key)] = value

    # fallback: parse the summary line if present
    for line in lines:
        if "Unknown_user =" in line:
            summary = line.split("Unknown_user =", 1)[1].strip()
            matches = re.findall(r'\.([A-Za-z0-9]{3,4})\.([A-Za-z0-9_-]{2,})', summary)
            for key, value in matches:
                atoms[clean_atom_name(key)] = value

    return atoms


def main():
    if len(sys.argv) != 2:
        print("Usage: python extract_udta_atoms.py /path/to/video.mp4")
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.is_file():
        print(f"File not found: {file_path}")
        sys.exit(1)

    try:
        ensure_exiftool()
        v3_text = run_exiftool_v3(file_path)
        atoms = extract_udta_atoms(v3_text)

        print("Extracted UserData atoms:")
        if atoms:
            for key, value in atoms.items():
                print(f"  {key}: {value}")
        else:
            print("  No readable UserData atoms found.")

    except subprocess.CalledProcessError as e:
        print("ExifTool failed.")
        print(e.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()