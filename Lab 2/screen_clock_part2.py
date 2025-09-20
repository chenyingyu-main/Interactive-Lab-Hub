import time
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

# Configuration for CS and DC pins (these are FeatherWing defaults on M0/M4):
cs_pin = digitalio.DigitalInOut(board.D5) 
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

# Config for display baudrate (default max is 24mhz):
BAUDRATE = 64000000

# Setup SPI bus using hardware SPI:
spi = board.SPI()

# Create the ST7789 display:
disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=None,
    baudrate=BAUDRATE,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)
# ---------------------------
# Buttons
# ---------------------------

buttonA = digitalio.DigitalInOut(board.D23)    # A
buttonB = digitalio.DigitalInOut(board.D24)    # B
buttonA.switch_to_input(pull=digitalio.Pull.UP)
buttonB.switch_to_input(pull=digitalio.Pull.UP)

# Create blank image for drawing.
# Make sure to create image with mode 'RGB' for full color.
rotation = 90
# Use the rotation variable (not disp.rotation) to compute width/height
# because disp.image(frame, rotation) will rotate the image by this value.
if rotation % 180 == 90:
    height = disp.width
    width = disp.height
else:
    width = disp.width
    height = disp.height

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# resize image object to fit screen.
def load_and_fit(path):
    img = Image.open(path).convert("RGB")
    image_ratio = img.width / img.height
    screen_ratio = width / height
    if screen_ratio < image_ratio:
        scaled_width = img.width * height // img.height
        scaled_height = height
    else:
        scaled_width = width
        scaled_height = img.height * width // img.width
    img = img.resize((scaled_width, scaled_height), Image.BICUBIC)

    # Crop and center the image
    x = scaled_width // 2 - width // 2
    y = scaled_height // 2 - height // 2
    cropped = img.crop((x, y, x + width, y + height))
    # Defensive: ensure returned image is exactly (width, height).
    # Sometimes resizing math or rounding can produce off-by-one sizes
    # which will cause the display driver to raise a ValueError.
    if cropped.size != (width, height):
        out = Image.new("RGB", (width, height))
        out.paste(cropped, (0, 0))
        return out
    return cropped

# Alternatively load a TTF font.  Make sure the .ttf font file is in the
# same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)

def get_time_parts():
    now = datetime.now()
    # date + suffix
    month = now.strftime("%b")
    day = now.day
    suffix = "th" if 11 <= day <= 13 else {1:"st",2:"nd",3:"rd"}.get(day % 10, "th")
    # each part string
    date_str = f"{month} {day}{suffix}"                      # example: Sep 19th
    week_str = now.strftime("%a")                            # example: Fri
    hm_str   = now.strftime("%I:%M %p").lstrip("0").upper()  # example: 7:54 pm 
    sec_str  = f"{now.strftime('%S')} sec"                   # example: 43 sec 
    return date_str, week_str, hm_str, sec_str

# ------------------------
font_date_big   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
font_week_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
font_time_big   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
font_sec_small  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)



from datetime import datetime

img1 = load_and_fit("clock_imgs/morning.png")
img2 = load_and_fit("clock_imgs/noon_juice.png")  

# ---------------------------
# main loop
# ---------------------------
current_base = img1  


while True:
    frame = current_base.copy()
    draw = ImageDraw.Draw(frame)

    date_str, week_str, hm_str, sec_str = get_time_parts()

    # 先量各行高度，算出總高度以做「垂直置中」
    h_date = draw.textbbox((0,0), date_str, font=font_date_big)[3]
    h_week = draw.textbbox((0,0), week_str, font=font_week_small)[3]
    h_hm   = draw.textbbox((0,0), hm_str,   font=font_time_big)[3]
    h_sec  = draw.textbbox((0,0), sec_str,  font=font_sec_small)[3]
    gap = 2
    gap_week_to_time = 15 # make a bit larger between week and time

    total_h = h_date + gap + h_week + gap_week_to_time + h_hm + gap + h_sec
    y = (height - total_h) // 2                 # 整塊垂直置中
    x = (width // 2) - 10                          # 右半邊，左對齊，調整 6 可微調水平位置

    def draw_line(text, fnt, color):
        draw.text((x+1, y+1), text, font=fnt, fill=(0,0,0))   # 陰影
        draw.text((x, y),      text, font=fnt, fill=color)

    # 日期（大）
    draw_line(date_str, font_date_big,   (255,255,255))
    y += h_date + gap

    # 星期（小）
    draw_line(week_str, font_week_small, (200,200,200))
    y += h_week + gap_week_to_time       # ← 這裡特別加寬一點

    # 時分 + am/pm（大）
    draw_line(hm_str,   font_time_big,   (255,255,0))
    y += h_hm + gap

    # 秒 + sec（小）
    draw_line(sec_str,  font_sec_small,  (200,255,200))

    disp.image(frame, rotation)
    time.sleep(1)