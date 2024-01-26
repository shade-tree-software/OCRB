from PIL import Image
import sys
import pickle
from hubconf import custom

WEIGHTS = "yolov7-ocr-mrz.pt"
OCR = custom(path_or_model = WEIGHTS)
img = Image.open(sys.argv[1])
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
  print(items)
f = open("ocrb.pk", "wb")
pickle.dump(results, f)
