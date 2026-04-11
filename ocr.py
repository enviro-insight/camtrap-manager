# just testing out the ocr stuff

import re
import shutil
import cv2
import pytesseract
from pathlib import Path
from time import time

if not shutil.which("tesseract"):
    print("Tesseract is not installed or not on PATH")
    exit(1)

from tkinter import Tk
from tkinter.filedialog import askdirectory

Tk().withdraw()

folder_path = askdirectory(title="Select folder containing video files")


print("Reading camera ID from first video")
first_video = next(Path(folder_path).glob("*.mp4"), None)
if not first_video:
    print("Error: No video files found in the selected directory.")
    exit(1)
else:
    print("First video file found:", first_video)

cap = cv2.VideoCapture(str(first_video))
cap.set(cv2.CAP_PROP_POS_FRAMES, 100)
ret, frame = cap.read()
cap.release()

# crop to metadata
h, w = frame.shape[:2]

# Example: bottom-right corner (tweak these numbers)
roi = frame[int(h*0.9):h, int(w*0.4):w]
cv2.imshow("ROI", roi)
cv2.waitKey(0)

if ret:
    ocrs = set()
    start_time = time()
    for i in range(1, 100):
    
        text = pytesseract.image_to_string(roi)
        text = text.replace("CO", "C0")  # remove spaces
        match = re.search(r"C\d{3}", text)
        if match:
            camera_id = match.group(0)
            ocrs.add(camera_id)
        else:
            print("Error: Could not extract camera ID from video on iteration", i)

    end_time = time()
    # print pretty time H:M:S
    elapsed_time = end_time - start_time
    hours, rem = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(rem, 60)
    print("Time: {:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), seconds))
    print("OCR values: ", "|".join(list(ocrs)))

else:
    print("Oops, we couldn't process the image!")