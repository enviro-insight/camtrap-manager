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
videos = list(Path(folder_path).glob("*.mp4"))
if not videos:
    print("Error: No video files found in the selected directory.")
    exit(1)

ocrs = set()
start_time = time()

for video in videos:

    cap = cv2.VideoCapture(str(video))
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)
    ret, frame = cap.read()
    cap.release()

    # crop to metadata
    h, w = frame.shape[:2]

    # Example: bottom-right corner (tweak these numbers)
    roi = frame[int(h*0.9):h, int(w*0.4):w]
    # cv2.imshow("ROI", roi)
    # cv2.waitKey(0)

    if ret:

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        gray = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)[1]

        text = pytesseract.image_to_string(gray)
        text = text.replace("CO", "C0")  # remove spaces
        match = re.search(r"C\d{3}", text)
        if match:
            camera_id = match.group(0)
            ocrs.add(camera_id)
        else:
            print(f"Error: Could not extract camera ID from video {video}") 
            # save the roi next to the video for debugging
            cv2.imwrite(f"{video}_roi.png", roi)       

    else:
        print("Oops, we couldn't process the image!")

end_time = time()
# print pretty time H:M:S
elapsed_time = end_time - start_time
hours, rem = divmod(elapsed_time, 3600)
minutes, seconds = divmod(rem, 60)
print("Time: {:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), seconds))
print("OCR values: ", "|".join(list(ocrs)))