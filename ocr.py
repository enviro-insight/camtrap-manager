# just testing out the ocr stuff

import re
import cv2
import pytesseract
from pathlib import Path

from tkinter import Tk
from tkinter.filedialog import askdirectory

Tk().withdraw()

folder_path = askdirectory(title="Select folder containing video files")


print("Reading camera ID from first video")
first_video = next(Path(folder_path).glob("*.mp4"), None)
if not first_video:
    print("Error: No video files found in the selected directory.")
    exit(1)

cap = cv2.VideoCapture(str(first_video))
cap.set(cv2.CAP_PROP_POS_FRAMES, 100)
ret, frame = cap.read()
cap.release()

if ret:
    text = pytesseract.image_to_string(frame)
    print("OCRd text:", text)
    # extract the string that matches format C###
    match = re.search(r"C\d{3}", text)
    if match:
        camera_id = match.group(0)
        print("Extracted camera ID:", camera_id)
    else:
        print("Error: Could not extract camera ID from video. Please specify with -c or ensure the camera ID is visible in the video frames.")