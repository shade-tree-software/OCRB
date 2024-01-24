from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import math
import sys
import random
import os
import pathlib

MRZ_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<"
MRZ_MAX_CHARS = 44
FONT_HEIGHT = 18 # pixels
MRZ_CHAR_HEIGHT = 5 # height of MRZ in chars
DEFAULT_OUTPUT_DIR = "output"
DEFAULT_MAX_ANGLE = 0 # degrees
DEFAULT_NUM_COLORS = 0
DEFAULT_NUM_GRAYS = 0
BEIGE = (158, 128, 98)
GRAY = (128, 128, 128)
WHITE = (255, 255, 255)
DEFAULT_NUM_RESOLUTIONS = 1
DEFAULT_NUM_UNIQUE_STRINGS = 1

ocrb = ImageFont.truetype('/home/awhamil/.local/share/fonts/OcrB2.ttf', FONT_HEIGHT)

# output dir
try:
  dir_index = sys.argv.index("-d")
  output_dir = sys.argv[dir_index + 1]
except ValueError:
  output_dir = DEFAULT_OUTPUT_DIR
# max skew angle
# generates all angles between 0 and max skew
try:
  angle_index = sys.argv.index("-a")
  max_angle = int(sys.argv[angle_index + 1])
except ValueError:
  max_angle = DEFAULT_MAX_ANGLE
# number of background colors (variations of beige) to generate
# setting this to 2 will generate one medium beige and one light beige
try:
  colors_index = sys.argv.index("-c")
  num_colors = int(sys.argv[colors_index + 1])
except ValueError:
  num_colors = DEFAULT_NUM_COLORS
# number of background grays to generate
# setting this to 2 will generate one medium gray and one light gray
try:
  gray_index = sys.argv.index("-g")
  num_grays = int(sys.argv[gray_index + 1])
except ValueError:
  num_grays = DEFAULT_NUM_GRAYS
# the number of different resolutions to generate for each mrz
try:
  res_index = sys.argv.index("-r")
  num_resolutions = int(sys.argv[res_index + 1])
except ValueError:
  num_resolutions = DEFAULT_NUM_RESOLUTIONS
# number of unique mrz strings to generate
# set to 0 to geneate a new string for each color and angle 
try:
  unique_index = sys.argv.index("-u")
  num_unique_strings = int(sys.argv[unique_index + 1])
except ValueError:
  num_unique_strings = DEFAULT_NUM_UNIQUE_STRINGS

# less common flags
show_boxes = '--show-boxes' in sys.argv # show debugging boxes around chars
write_classes_file = '--no-classes-file' not in sys.argv # suppress classes file
white = '--no-white' not in sys.argv # do not generate white background

def colorGenerator(num_colors, start_color):
  if num_colors > 0:
    red = start_color[0]
    green = start_color[1]
    blue = start_color[2]
    red_inc = (255 - red) / num_colors
    green_inc = (255 - green) / num_colors
    blue_inc = (255 - blue) / num_colors
    while red < 255 and green < 255 and blue < 255:
      yield (round(red), round(green), round(blue))
      red += red_inc
      green += green_inc
      blue += blue_inc

def get_line1_offset(deg, cw, ch):
  rad = math.radians(deg)
  cos = math.cos(rad)
  sin = math.sin(rad)
  if sin >= 0 and cos >= 0:
    offset = (cw * cos + ch * sin, ch * cos - 2 * cw * sin)
  elif sin >= 0 and cos < 0:
    offset = (ch * sin + 2 * cw * cos, 2 * (ch * cos - cw * sin))
  elif sin < 0 and cos < 0:
    offset = (2 * cw * cos + 2 * ch * sin, 2 * ch * cos - cw * sin)
  else:
    offset = (2 * ch * sin + cw * cos, ch * cos - cw * sin)
  return offset

def get_line2_offset(deg, cw, ch):
  rad = math.radians(deg)
  cos = math.cos(rad)
  sin = math.sin(rad)
  if sin >= 0 and cos >= 0:
    offset = (cw * cos + 3 * ch * sin, 3 * ch * cos - 2 * cw * sin)
  elif sin >= 0 and cos < 0:
    offset = (3 * ch * sin + 2 * cw * cos, 4 * ch * cos - 2 * cw * sin)
  elif sin < 0 and cos < 0:
    offset = (2 * cw * cos + 4 * ch * sin, 4 * ch * cos - cw * sin)
  else:
    offset = (4 * ch * sin + cw * cos, 3 * ch * cos - cw * sin)
  return offset

def get_mrz_corner(deg, img_size, mrz_height):
  rad = math.radians(deg)
  cos = math.cos(rad)
  sin = math.sin(rad)
  if sin >= 0 and cos >= 0:
    coords = (0.0, img_size[1] - mrz_height * cos)
  elif sin >= 0 and cos < 0:
    coords = (img_size[0] - mrz_height * sin, img_size[1])
  elif sin < 0 and cos < 0:
    coords = (img_size[0], cos - mrz_height * cos)
  else:
    coords = (-mrz_height * sin, 0.0)
  return coords

def draw_line(text, deg, xf, yf, cw, ch, img):
  chars_info = []
  rad = math.radians(deg)
  for c in text:
    x = round(xf)
    y = round(yf)
    xt = cw * math.cos(rad)
    yt = cw * math.sin(rad)
    img2 = Image.new("RGBA", (cw, ch), (0,0,0,0))
    draw2 = ImageDraw.Draw(img2)
    draw2.text((0, 0), c, font=ocrb, fill=(0, 0, 0))
    img2 = img2.crop((1, 1, img2.size[0] - 1, img2.size[1]))
    img2 = img2.rotate(deg, expand=1, resample=Image.BICUBIC)
    img.paste(img2, (x, y), img2)
    draw = ImageDraw.Draw(img)
    x2 = x + img2.size[0] - 1
    y2 = y + img2.size[1] - 1
    if show_boxes:
      draw.rectangle([x, y, x2, y2], outline="red")
    x_pct = ((x2 + x) / 2) / img.size[0]
    y_pct = ((y2 + y) / 2) / img.size[1]
    w_pct = (x2 - x) / img.size[0]
    h_pct = (y2 - y) / img.size[1]
    chars_info.append(f"{MRZ_CHARS.index(c)} {x_pct} {y_pct} {w_pct} {h_pct}")
    xf = xf + xt
    yf = yf - yt
  return chars_info

def generate_line():
  chars = []
  for i in range(MRZ_MAX_CHARS):
    i = random.randrange(len(MRZ_CHARS))
    c = MRZ_CHARS[i]
    chars.append(c)
  return ''.join(chars)

def generate_mrz(lines, deg, bg_color, sizes):
  (_, _, cw, ch) = ocrb.getbbox("X")
  mrz_height = MRZ_CHAR_HEIGHT * ch
  img_size = (cw * (MRZ_MAX_CHARS + 2), mrz_height)
  img = Image.new(mode = "RGB", size = img_size, color = bg_color)
  img = img.rotate(deg, expand=1, resample=Image.BICUBIC, fillcolor="white")
  mrz_corner = get_mrz_corner(deg, img.size, mrz_height)
  line1_offset = get_line1_offset(deg, cw, ch)
  xf = mrz_corner[0] + line1_offset[0]
  yf = mrz_corner[1] + line1_offset[1]
  line1_info = draw_line(lines[0], deg, xf, yf, cw, ch, img)
  line2_offset = get_line2_offset(deg, cw, ch)
  xf = mrz_corner[0] + line2_offset[0]
  yf = mrz_corner[1] + line2_offset[1]
  line2_info = draw_line(lines[1], deg, xf, yf, cw, ch, img)

  # write output
  bg_hex = f"{bg_color[0]:02X}{bg_color[1]:02X}{bg_color[2]:02X}"
  sizes = 1 if sizes < 1 else sizes
  for size in range(sizes):
    text_path = os.path.join(output_dir, f"{lines[0][:8]}_{deg}_{size}_{bg_hex}.txt")
    with open(text_path, "wt") as f:
      for char_info in line1_info:
        f.write(f"{char_info}\n")
      for char_info in line2_info:
        f.write(f"{char_info}\n")
    img_path = os.path.join(output_dir, f"{lines[0][:8]}_{deg}_{size}_{bg_hex}.jpg")
    img.save(img_path)
    if sizes > 1:
      new_width = round(img.size[0] * 0.9)
      new_height = round(img.size[1] * 0.9)
      img = img.resize((new_width, new_height))

pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)
if num_unique_strings == 0:
  num_unique_strings = 1
  new_string_each_time = True
else:
  new_string_each_time = False
for _ in range(num_unique_strings):
  if not new_string_each_time:
    lines = [generate_line(), generate_line()]
  for d in range(max_angle + 1):
    for sign in [-1, 1]:
      if d == 0  and sign == -1:
        continue
      deg = d * sign
      colors = colorGenerator(num_colors, BEIGE)
      for color in colors:
        if new_string_each_time:
          lines = [generate_line(), generate_line()]
        generate_mrz(lines, deg, color, num_resolutions)
      grays = colorGenerator(num_grays, GRAY)
      for gray in grays:
        if new_string_each_time:
          lines = [generate_line(), generate_line()]
        generate_mrz(lines, deg, gray, num_resolutions)
      if white:
        if new_string_each_time:
          lines = [generate_line(), generate_line()]
        generate_mrz(lines, deg, WHITE, num_resolutions)

if write_classes_file:
  classes_path = os.path.join(output_dir, "classes.txt")
  with open(classes_path, "wt") as f:
    for char in MRZ_CHARS:
      f.write(f"{char}\n")