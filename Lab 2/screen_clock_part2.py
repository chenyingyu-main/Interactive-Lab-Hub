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

# Get current time parts
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

# Draw clock function
def draw_clock(base_image, font_color):
    """Draw clock display on base image and return the frame"""
    font_date_big   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 20)
    font_week_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 18)
    font_time_big   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 23)
    font_sec_small  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 16)

    frame = base_image.copy()
    draw = ImageDraw.Draw(frame)
    
    date_str, week_str, hm_str, sec_str = get_time_parts()

    # Calculate text heights for vertical centering
    h_date = draw.textbbox((0,0), date_str, font=font_date_big)[3]
    h_week = draw.textbbox((0,0), week_str, font=font_week_small)[3]
    h_hm   = draw.textbbox((0,0), hm_str,   font=font_time_big)[3]
    h_sec  = draw.textbbox((0,0), sec_str,  font=font_sec_small)[3]
    
    gap = 2
    gap_week_to_time = 15
    total_h = h_date + gap + h_week + gap_week_to_time + h_hm + gap + h_sec
    
    y = (height - total_h) // 2  # Vertical center
    x = (width // 2) - 5         # Right half, left align

    # Draw date
    draw.text((x, y), date_str, font=font_date_big, fill=font_color)
    y += h_date + gap

    # Draw weekday
    draw.text((x, y), week_str, font=font_week_small, fill=font_color)
    y += h_week + gap_week_to_time

    # Draw time
    draw.text((x, y), hm_str, font=font_time_big, fill=font_color)
    y += h_hm + gap

    # Draw seconds
    draw.text((x, y), sec_str, font=font_sec_small, fill=font_color)
    
    return frame

# Draw message function
def draw_message(base_image,font_size=18, msg="Random",font_color="#793d3d"):
    """Draw custom message on base image and return the frame"""

    font_hello = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", font_size)
    frame = base_image.copy()
    draw = ImageDraw.Draw(frame)
    
    # Split message into lines
    lines = msg.split('\n')
    
    # Calculate total height and max width of all lines
    line_heights = []
    line_widths = []
    line_spacing = 10  # Space between lines
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_hello)
        line_width = bbox[2] - bbox[0]
        line_height = bbox[3] - bbox[1]
        line_heights.append(line_height)
        line_widths.append(line_width)
    
    # Calculate total height including line spacing
    total_height = sum(line_heights) + line_spacing * (len(lines) - 1)
    max_width = max(line_widths) if line_widths else 0
    
    # Position in right half of screen, vertically centered
    x_base = (width // 2) + 10  # Same as clock position
    y_start = (height - total_height) // 2  # Vertically center the entire text block
    
    # Draw each line
    current_y = y_start
    for i, line in enumerate(lines):
        # Each line is left-aligned at x_base (like the clock)
        draw.text((x_base, current_y), line, font=font_hello, fill=font_color)
        current_y += line_heights[i] + line_spacing
    
    return frame

from datetime import datetime

# get current time period for image selection
def get_current_time_period():
    """Get current time period: morning, noon, or night"""
    now = datetime.now()
    hour = now.hour
    
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "noon"
    else:
        return "night"

image_configs = {
    "morning": [
        {"image_path": "clock_imgs/morning.png", "message": "Good\nMorning", "font_color": "#793d3d"},
        {"image_path": "clock_imgs/morning_americano.png", "message": "Americano", "font_color": "#793d3d"},
        {"image_path": "clock_imgs/morning_latte.png", "message": "  Latte", "font_color": "#793d3d"},
        {"image_path": "clock_imgs/morning_romano.png", "message": "Romano", "font_color": "#793d3d"}
    ],
    "noon": [
        {"image_path": "clock_imgs/noon.png", "message": "Good\nAfternoon", "font_color": "#112756"},
        {"image_path": "clock_imgs/noon_juice.png", "message": "  Fresh\n  Juice", "font_color": "#112756"},
        {"image_path": "clock_imgs/noon_tapioca.png", "message": "Tapioca\nMilk Tea", "font_color": "#112756"},
        {"image_path": "clock_imgs/noon_tea.png", "message": "   Iced\n   Tea", "font_color": "#112756"},
    ],
    "night": [
        {"image_path": "clock_imgs/night.png", "message": "Good\nEvening", "font_color": "#f4efef"},
        {"image_path": "clock_imgs/night_milk.png", "message": "Warm\nMilk", "font_color": "#f4efef"},
        {"image_path": "clock_imgs/night_tea.png", "message": "Herbal\nTea", "font_color": "#f4efef"},
    ]
}

# Load all images at startup
def load_all_images():
    """Load all images for all time periods"""
    loaded_configs = {}
    for period, configs in image_configs.items():
        loaded_configs[period] = []
        for config in configs:
            try:
                loaded_image = load_and_fit(config["image_path"])
                loaded_config = {
                    "image": loaded_image,
                    "message": config["message"],
                    "font_color": config["font_color"]
                }
                loaded_configs[period].append(loaded_config)
            except Exception as e:
                print(f"Failed to load {config['image_path']}: {e}")
                # Skip this image if it fails to load
                continue
    return loaded_configs

# ---------------------------
# main loop
# ---------------------------
# Load all images
loaded_image_configs = load_all_images()

# Initialize state
current_time_period = get_current_time_period()
current_config_index = 0  # Start with first config in current time period
show_clock = False  # True: show clock, False: show message

# Button states for debouncing
button_a_last_state = True
button_b_last_state = True

# Set TESTING_MODE to True to enable manual time testing
TESTING_MODE = True 
MANUAL_HOUR = 8  # Change this to test different hours (0-23)
# Examples: 8 = morning, 14 = noon, 20 = night

while True:
    # Check if time period has changed (optional - only check periodically)
    new_time_period = get_current_time_period()
    if new_time_period != current_time_period and not TESTING_MODE:
        current_time_period = new_time_period
        current_config_index = 0  # Reset to first image of new period

    if TESTING_MODE:
        # Override current_time_period based on MANUAL_HOUR
        if 6 <= MANUAL_HOUR < 12:
            current_time_period = "morning"
        elif 12 <= MANUAL_HOUR < 18:
            current_time_period = "noon"
        else:
            current_time_period = "night"

    
    # Check button A state change (switch to next drink in current time period)
    button_a_current = buttonA.value
    if button_a_last_state and not button_a_current:  # Button pressed (high to low)
        current_configs = loaded_image_configs[current_time_period]
        current_config_index = (current_config_index + 1) % len(current_configs)
        time.sleep(0.2)  # Debounce
    button_a_last_state = button_a_current
    
    # Check button B state change (toggle between clock and message)
    button_b_current = buttonB.value
    if button_b_last_state and not button_b_current:  # Button pressed (high to low)
        show_clock = not show_clock  # Toggle between clock and message
        time.sleep(0.2)  # Debounce
    button_b_last_state = button_b_current
    
    # Get current configuration
    current_configs = loaded_image_configs[current_time_period]
    current_config = current_configs[current_config_index]
    current_base = current_config["image"]
    current_message = current_config["message"]
    font_color = current_config["font_color"]
    
    # Generate and display frame
    if show_clock:
        frame = draw_clock(current_base, font_color)
    else:
        frame = draw_message(current_base, msg=current_message, font_color=font_color)
    
    disp.image(frame, rotation)
    time.sleep(0.1)