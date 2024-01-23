from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import math
import sys
import random

def get_start_coords(rad, img_size, cw, ch):
  cos = math.cos(rad)
  sin = math.sin(rad)
  if sin >= 0 and cos >= 0:
    coords = (0.0, img_size[1] - (3 * ch) * cos)
    offset = (cw * cos + ch * sin, ch * cos - 2 * cw * sin)
  elif sin >= 0 and cos < 0:
    coords = (img_size[0] - (3 * ch) * sin, img_size[1])
    offset = (ch * sin + 2 * cw * cos, 2 * (ch * cos - cw * sin))
  elif sin < 0 and cos < 0:
    coords = (img_size[0], (-3 * ch) * cos)
    offset = (2 * cw * cos + 2 * ch * sin, 2 * ch * cos - cw * sin)
  else:
    coords = ((-3 * ch) * sin, 0.0)
    offset = (2 * ch * sin + cw * cos, ch * cos - cw * sin)
  return (round(coords[0] + offset[0]), round(coords[1] + offset[1]))
 
MRZ_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<"
MRZ_MAX_CHARS = 40
deg = int(sys.argv[1])
rad = math.radians(deg)
bg = (250, 240, 230)
h = 40
ocrb = ImageFont.truetype('/home/awhamil/.local/share/fonts/OcrB2.ttf', h)
(_, _, cw, ch) = ocrb.getbbox("X")
img_size = (cw * (MRZ_MAX_CHARS + 2), ch * 3)
img1 = Image.new(mode = "RGB", size = img_size, color = bg)
img1 = img1.rotate(deg, expand=1)
draw1 = ImageDraw.Draw(img1)
(xf, yf) = get_start_coords(rad, img1.size, cw, ch)
draw1.ellipse([(xf-2,yf-2),(xf+2,yf+2)], fill="blue")
for i in range(MRZ_MAX_CHARS):
  c = MRZ_CHARS[random.randrange(len(MRZ_CHARS))]
  x = round(xf)
  y = round(yf)
  xt = cw * math.cos(rad)
  yt = cw * math.sin(rad)
  img2 = Image.new("RGBA", (cw, ch), (0,0,0,0))
  draw2 = ImageDraw.Draw(img2)
  draw2.text((0, 0), c, font=ocrb, fill =(0, 0, 0))
  img2 = img2.crop((1, 1, img2.size[0] - 1, img2.size[1]))
  img2 = img2.rotate(deg, expand=1, resample=Image.BICUBIC)
  img1.paste(img2, (x, y), img2)
  draw1 = ImageDraw.Draw(img1)
  draw1.rectangle([x, y, x + img2.size[0] - 1, y + img2.size[1] - 1], outline="red")
  xf = xf + xt
  yf = yf - yt
 
img1.show()
