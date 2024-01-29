import pickle
import json
from statistics import mean
import math
from text import MRZ

OBJECT_NAMES = [
         'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
         'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
         'U', 'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3',
         '4', '5', '6', '7', '8', '9', '<lr', '<bt', '<rl', '<tb'
       ]
# OBJECT_NAMES = [
#          'A_lr', 'B_lr', 'C_lr', 'D_lr', 'E_lr', 'F_lr', 'G_lr', 'H_lr', 'I_lr', 'J_lr',
#          'K_lr', 'L_lr', 'M_lr', 'N_lr', 'O_lr', 'P_lr', 'Q_lr', 'R_lr', 'S_lr', 'T_lr',
#          'U_lr', 'V_lr', 'W_lr', 'X_lr', 'Y_lr', 'Z_lr', '0_lr', '1_lr', '2_lr', '3_lr',
#          '4_lr', '5_lr', '6_lr', '7_lr', '8_lr', '9_lr', '<_lr',
#          'A_bt', 'B_bt', 'C_bt', 'D_bt', 'E_bt', 'F_bt', 'G_bt', 'H_bt', 'I_bt', 'J_bt',
#          'K_bt', 'L_bt', 'M_bt', 'N_bt', 'O_bt', 'P_bt', 'Q_bt', 'R_bt', 'S_bt', 'T_bt',
#          'U_bt', 'V_bt', 'W_bt', 'X_bt', 'Y_bt', 'Z_bt', '0_bt', '1_bt', '2_bt', '3_bt',
#          '4_bt', '5_bt', '6_bt', '7_bt', '8_bt', '9_bt', '<_bt',
#          'A_rl', 'B_rl', 'C_rl', 'D_rl', 'E_rl', 'F_rl', 'G_rl', 'H_rl', 'I_rl', 'J_rl',
#          'K_rl', 'L_rl', 'M_rl', 'N_rl', 'O_rl', 'P_rl', 'Q_rl', 'R_rl', 'S_rl', 'T_rl',
#          'U_rl', 'V_rl', 'W_rl', 'X_rl', 'Y_rl', 'Z_rl', '0_rl', '1_rl', '2_rl', '3_rl',
#          '4_rl', '5_rl', '6_rl', '7_rl', '8_rl', '9_rl', '<_rl',
#          'A_tb', 'B_tb', 'C_tb', 'D_tb', 'E_tb', 'F_tb', 'G_tb', 'H_tb', 'I_tb', 'J_tb',
#          'K_tb', 'L_tb', 'M_tb', 'N_tb', 'O_tb', 'P_tb', 'Q_tb', 'R_tb', 'S_tb', 'T_tb',
#          'U_tb', 'V_tb', 'W_tb', 'X_tb', 'Y_tb', 'Z_tb', '0_tb', '1_tb', '2_tb', '3_tb',
#          '4_tb', '5_tb', '6_tb', '7_tb', '8_tb', '9_tb', '<_tb'
#        ]
ORIENTATIONS = ['lr', 'bt', 'rl', 'tb']

f = open("ocrb.pk", "rb")
untested = pickle.load(f)

# compute the character and orientation (rotation) for each detected object
orientation_counts = {}
widths = []
heights = []
for object_info in untested:
  object_index = int(object_info["val"])
  object_name = OBJECT_NAMES[object_index]
  object_info["char"] = object_name[0]
  widths.append(object_info["w"])
  heights.append(object_info["h"])
  orientation = object_name[-2:] if object_name[-2:] in ORIENTATIONS else None
  object_info["orientation"] = orientation
  if orientation:
    orientation_counts[orientation] = orientation_counts.get(orientation, 0) + 1
doc_orientation = max(orientation_counts, key=orientation_counts.get)

# sort the detected characters based on image orientation
def sort_chars(object_info):
  return object_info["x"] if doc_orientation in ["lr", "rl"] else object_info["y"]
untested.sort(key = sort_chars, reverse = doc_orientation in ["bt", "rl"])

# figure out the average character width and height
if doc_orientation in ["lr", "rl"]:
  avg_w = mean(widths)
  avg_h = mean(heights)
else:
  avg_w = mean(heights)
  avg_h = mean(widths)

def distance(a, b):
  x = a["x"] - b["x"]
  y = a["y"] - b["y"]
  return math.sqrt( x**2 + y**2 )

def is_nearby(a, b, max_dist):
  return distance(a, b) <= max_dist

def closest_index(a, items):
  if len(items) > 0:
    distances = [(i, distance(a, item)) for i, item in enumerate(items)]
    return sorted(distances, key = lambda x: x[1])[0][0]
  else:
    return None

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

# stitch lines together with a space if the last character of the first line
# is within a couple character widths of the first charcater of the second line.
done = False
while not done:
  changed = False
  for i, a in enumerate(lines):
    for j, b in enumerate(lines):
      if i != j:
        if is_nearby(a[-1], b[0], 2.5 * avg_w):
          a.append({"val": -1, "char": ' '})
          lines[i] = a + b
          del lines[j]
          changed = True
          break
    if changed:
      break
  if not changed:
    done = True 

sort_lines = lambda line: line[0]["y"] if doc_orientation in ["lr", "rl"] else line[0]["x"]
lines = sorted([ line for line in lines ], key=sort_lines, reverse=doc_orientation in ["bt", "rl"])
for line in lines:
  for object_info in line:
    print(f"{object_info['char']} {json.dumps(object_info)}")
print("object orientations:")
print(json.dumps(orientation_counts, indent=2))
print(f"assuming document orientation: {doc_orientation}")
mrz_lines = []
for line in lines:
  if len(line) >= 30:
    mrz_line = ''.join([ object_info["char"] for object_info in line if "suppressed" not in object_info])
    mrz_lines.append(mrz_line)
    print(mrz_line)
mrz_parser = MRZ(mrz_lines)
print(json.dumps(mrz_parser.to_dict(), indent=2))