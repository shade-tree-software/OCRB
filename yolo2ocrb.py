from PIL import Image
import sys
import pickle
import os

DEFAULT_YOLO_DIR = "/nis_home/awhamil/Dev/yolov7-mrz"
WEIGHTS_FILENAME = "yolov7-ocr-mrz.pt"
OUTPUT_PICKLE = "ocrb.pk"

image_path = sys.argv[1]
yolo_dir = sys.argv[2] if len(sys.argv) >= 3 else DEFAULT_YOLO_DIR
sys.path.append(yolo_dir)
from hubconf import custom

weights_path = os.path.join(yolo_dir, WEIGHTS_FILENAME)
OCR = custom(path_or_model = weights_path)
img = Image.open(image_path)
raw_results = OCR([img]).xywhn[0]
results = []
for raw_result in raw_results:
  items = raw_result.tolist()
  result = {
    "x": items[0],
    "y": items[1],
    "w": items[2],
    "h": items[3],
    "conf": items[4],
    "val": items[5] }
  results.append(result)
print(f"found {len(results)} OCRB characters")
f = open(OUTPUT_PICKLE, "wb")
pickle.dump(results, f)
