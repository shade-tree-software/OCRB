from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import math
import sys
import random

MRZ_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<"
MRZ_MAX_CHARS = 44
FONT_HEIGHT = 18 # pixels
MRZ_CHAR_HEIGHT = 5 # height of MRZ in chars

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

def draw_line(deg, xf, yf, cw, ch, img):
  rad = math.radians(deg)
  for i in range(MRZ_MAX_CHARS):
    c = MRZ_CHARS[random.randrange(len(MRZ_CHARS))]
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
    draw.rectangle([x, y, x + img2.size[0] - 1, y + img2.size[1] - 1], outline="red")
    xf = xf + xt
    yf = yf - yt
 
deg = int(sys.argv[1])
bg = (250, 240, 230)
ocrb = ImageFont.truetype('/home/awhamil/.local/share/fonts/OcrB2.ttf', FONT_HEIGHT)
(_, _, cw, ch) = ocrb.getbbox("X")
mrz_height = MRZ_CHAR_HEIGHT * ch
img_size = (cw * (MRZ_MAX_CHARS + 2), mrz_height)
img = Image.new(mode = "RGB", size = img_size, color = bg)
img = img.rotate(deg, expand=1, resample=Image.BICUBIC)
draw = ImageDraw.Draw(img)
mrz_corner = get_mrz_corner(deg, img.size, mrz_height)
line1_offset = get_line1_offset(deg, cw, ch)
xf = mrz_corner[0] + line1_offset[0]
yf = mrz_corner[1] + line1_offset[1]
draw.ellipse([(xf - 2, yf - 2), (xf + 2, yf + 2)], fill="blue")
draw_line(deg, xf, yf, cw, ch, img)
line2_offset = get_line2_offset(deg, cw, ch)
xf = mrz_corner[0] + line2_offset[0]
yf = mrz_corner[1] + line2_offset[1]
draw_line(deg, xf, yf, cw, ch, img)
 
img.show()
