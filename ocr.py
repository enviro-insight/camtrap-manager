# just testing out the ocr stuff

import re
import shutil
import cv2
import pytesseract
from pathlib import Path
from time import time
import numpy as np
from tkinter import Tk
from tkinter.filedialog import askdirectory
from dims import dims
from collage import make_collage

if not shutil.which("tesseract"):
    print("Tesseract is not installed or not on PATH")
    exit(1)

Tk().withdraw()

folder_path = askdirectory(title="Select folder containing video files")
videos = list(Path(folder_path).glob("*.mp4"))
if not videos:
    print("Error: No video files found in the selected directory.")
    exit(1)

ocrs = set()
start_time = time()

imgs = []

for video in videos:

    cap = cv2.VideoCapture(str(video))
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)
    ret, frame = cap.read()
    cap.release()

    # crop to metadata
    h, w = frame.shape[:2]

    # Example: bottom-right corner (tweak these numbers)
    roi = frame[int(h*dims["spartan"]["heightStart"]):int(h*dims["spartan"]["heightEnd"]), int(w*dims["spartan"]["widthStart"]):int(w*dims["spartan"]["widthEnd"])]
    # cv2.imshow("ROI", roi)
    # cv2.waitKey(0)
    # exit(0)

    if ret:

        config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=C0123456789'
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        _, proc = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # ocr_img = cv2.bitwise_not(roi)
        imgs.append(proc)
        # cv2.imshow("ROI", roi)
        # cv2.imshow("OCR", ocr_img)
        # cv2.waitKey(0)
        
        text = pytesseract.image_to_string(proc, config=config).strip()

        if text:
            ocrs.add(text)
        else:
            print(f"Error: Could not extract camera ID from video {video}") 

    else:
        print("Oops, we couldn't process the image!")

collage = make_collage(imgs, max_cols=4)
if collage is not None:
    cv2.imshow("Collage", collage)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

end_time = time()
# print pretty time H:M:S
elapsed_time = end_time - start_time
hours, rem = divmod(elapsed_time, 3600)
minutes, seconds = divmod(rem, 60)
print("Time: {:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), seconds))
print("OCR values: ", "|".join(list(ocrs)))