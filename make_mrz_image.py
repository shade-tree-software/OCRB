from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import math
import sys
import random
import os
import pathlib

MRZ_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<<<<"
MRZ_MAX_CHARS = 44
FONT_HEIGHT = 36 # pixels
MRZ_CHAR_HEIGHT = 5 # height of MRZ in chars
DEFAULT_OUTPUT_DIR = "output"
DEFAULT_MAX_ANGLE = 0 # degrees
DEFAULT_NUM_IMAGES = 1
BEIGE = (158, 128, 98)
GRAY = (128, 128, 128)
WHITE = (255, 255, 255)

ocrb = ImageFont.truetype('/nis_home/awhamil/.local/share/fonts/OcrB2.ttf', FONT_HEIGHT)

# output dir
try:
  dir_index = sys.argv.index("-d")
  output_dir = sys.argv[dir_index + 1]
except ValueError:
  output_dir = DEFAULT_OUTPUT_DIR
# number of images to generate
try:
  image_count_index = sys.argv.index("-n")
  num_images = int(sys.argv[image_count_index + 1])
except ValueError:
  num_images = DEFAULT_NUM_IMAGES

# less common flags
show_boxes = '--show-boxes' in sys.argv # show debugging boxes around chars
write_classes_file = '--no-classes-file' not in sys.argv # suppress classes file

def colorGenerator(start_color):
    pct = random.uniform(0.0, 1.0)
    red = int(start_color[0] + (255 - start_color[0]) * pct)
    green = int(start_color[1] + (255 - start_color[1]) * pct)
    blue = int(start_color[2] + (255 - start_color[2]) * pct)
    return (red, green, blue)

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
    c_idx = MRZ_CHARS.index(c)
    if c == '<':
      if deg >= 45 and deg < 135:
        c_idx += 1
      elif deg >= 135 and deg < 225:
        c_idx += 2
      elif deg >= 225 and deg < 315:
        c_idx += 3
    chars_info.append(f"{c_idx} {x_pct} {y_pct} {w_pct} {h_pct}")
    xf = xf + xt
    yf = yf - yt
  return chars_info

def generate_line():
  chars = []
  for i in range(MRZ_MAX_CHARS - 5):
    i = random.randrange(len(MRZ_CHARS) - 3)
    c = MRZ_CHARS[i]
    chars.append(c)
  return ''.join(chars) + "<<<<<"

def generate_mrz(lines, deg, bg_color, scale=1.0):
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
  text_path = os.path.join(output_dir, f"{lines[0][:8]}_{deg}_{scale:.2f}_{bg_hex}.txt")
  with open(text_path, "wt") as f:
    for char_info in line1_info:
      f.write(f"{char_info}\n")
    for char_info in line2_info:
      f.write(f"{char_info}\n")
  img_path = os.path.join(output_dir, f"{lines[0][:8]}_{deg}_{scale:.2f}_{bg_hex}.jpg")
  if scale != 1.0:
    new_width = round(img.size[0] * scale)
    new_height = round(img.size[1] * scale)
    img = img.resize((new_width, new_height))
  img.save(img_path)

pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)
for _ in range(num_images):
  deg = random.randint(0, 359)
  color_type = random.randrange(3)
  if color_type == 0:
    color = colorGenerator(BEIGE)
  elif color_type == 1:
    color = colorGenerator(GRAY)
  else:
    color = WHITE
  lines = [generate_line(), generate_line()]
  scale = random.uniform(1.0, 0.25)
  generate_mrz(lines, deg, color, scale)

if write_classes_file:
  classes_path = os.path.join(output_dir, "classes.txt")
  if not os.path.exists(classes_path):
    with open(classes_path, "wt") as f:
      for char in MRZ_CHARS:
        f.write(f"{char}\n")
