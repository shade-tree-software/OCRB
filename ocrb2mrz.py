import pickle
import json
from statistics import mean
import math
from text import MRZ

MRZ_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<<<<"

f = open("ocrb.pk", "rb")
untested = pickle.load(f)

# figure out how the image is oriented (rotated)
orientation_counts = [
  len([x for x in untested if x["val"] == 36]),
  len([x for x in untested if x["val"] == 37]),
  len([x for x in untested if x["val"] == 38]),
  len([x for x in untested if x["val"] == 39])
]
orientation = orientation_counts.index(max(orientation_counts))

# sort the detected characters based on image orientation
sort_chars = lambda ch: ch["x"] if orientation in [0, 2] else ch["y"]
untested.sort(key = sort_chars, reverse=orientation in [1, 2])

# figure out the average character width and height
if orientation in [0, 2]:
  avg_w = mean([x["w"] for x in untested])
  avg_h = mean([x["h"] for x in untested])
else:
  avg_w = mean([x["h"] for x in untested])
  avg_h = mean([x["w"] for x in untested])

def distance(a, b):
  x = a["x"] - b["x"]
  y = a["y"] - b["y"]
  return math.sqrt( x**2 + y**2 )

def is_nearby(a, b, max_dist):
  return distance(a, b) <= max_dist

def closest_index(a, items):
  if len(items) > 0:
    return sorted([(i, distance(a, item)) for i, item in enumerate(items)], key=lambda x: x[1])[0][0]
  else:
    return None

def mrz_char(index):
  return MRZ_CHARS[int(index)] if index >= 0 else ' '

lines = []
current = []
done = False
while not done:
  if len(untested) > 0 and len(current) == 0:
    current.append(untested[0])
    del untested[0]
  else:
    index = closest_index(current[-1], untested)
    if index is not None and is_nearby(current[-1], untested[index], 1.8 * avg_w):
      if is_nearby(current[-1], untested[index], 0.4 * avg_w):
        # too close!
        if current[-1]["conf"] > untested[index]["conf"]:
          current.append(untested[index])
          current[-1]["suppressed"] = True
          del untested[index]
        else:
          current[-1]["suppressed"] = True
          current.append(untested[index])
          del untested[index]
      else: 
        current.append(untested[index])
        del untested[index]
    else:
      conf = mean([x["conf"] for x in current])
      if conf > 0.7:
        lines.append(current)
      current = []
      if index is None:
        done = True

# stitch lines together if the last character of the first line
# is within a couple characters of the first charcater of the
# second line.
done = False
while not done:
  changed = False
  for i, a in enumerate(lines):
    for j, b in enumerate(lines):
      if i != j:
        if is_nearby(a[-1], b[0], 2.5 * avg_w):
          a.append({"val":-1})
          lines[i] = a + b
          del lines[j]
          changed = True
          break
    if changed:
      break
  if not changed:
    done = True 

sort_lines = lambda line: line[0]["y"] if orientation in [0, 2] else line[0]["x"]
lines = sorted([ line for line in lines ], key=sort_lines, reverse=orientation in [2, 3])
for line in lines:
  for ch in line:
    print(f"{mrz_char(ch['val'])} {json.dumps(ch)}")
mrz = []
for line in lines:
  mrz.append(''.join([ mrz_char(ch["val"]) for ch in line if "suppressed" not in ch]))
  print(mrz[-1])
mrz_parser = MRZ(mrz)
print(json.dumps(mrz_parser.to_dict(), indent=2))