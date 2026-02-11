import machine
import neopixel
import network
import time
import gc

try:
    import urequests
except ImportError:
    import requests as urequests

try:
    from urandom import getrandbits
except ImportError:
    from random import getrandbits

import config

# ---------------------------------------------------------------------------
# 5x8 Bitmap Font (Adafruit GFX / glcdfont)
# Column-encoded: each char = 5 bytes, each byte = 1 column, bit 0 = top row
# Covers printable ASCII 32 (space) through 126 (~)
# ---------------------------------------------------------------------------
FONT_START = 32
FONT_DATA = bytes([
    0x00, 0x00, 0x00, 0x00, 0x00,  # ' '
    0x00, 0x00, 0x5F, 0x00, 0x00,  # '!'
    0x00, 0x07, 0x00, 0x07, 0x00,  # '"'
    0x14, 0x7F, 0x14, 0x7F, 0x14,  # '#'
    0x24, 0x2A, 0x7F, 0x2A, 0x12,  # '$'
    0x23, 0x13, 0x08, 0x64, 0x62,  # '%'
    0x36, 0x49, 0x56, 0x20, 0x50,  # '&'
    0x00, 0x08, 0x07, 0x03, 0x00,  # "'"
    0x00, 0x1C, 0x22, 0x41, 0x00,  # '('
    0x00, 0x41, 0x22, 0x1C, 0x00,  # ')'
    0x2A, 0x1C, 0x7F, 0x1C, 0x2A,  # '*'
    0x08, 0x08, 0x3E, 0x08, 0x08,  # '+'
    0x00, 0x80, 0x70, 0x30, 0x00,  # ','
    0x08, 0x08, 0x08, 0x08, 0x08,  # '-'
    0x00, 0x00, 0x60, 0x60, 0x00,  # '.'
    0x20, 0x10, 0x08, 0x04, 0x02,  # '/'
    0x3E, 0x51, 0x49, 0x45, 0x3E,  # '0'
    0x00, 0x42, 0x7F, 0x40, 0x00,  # '1'
    0x72, 0x49, 0x49, 0x49, 0x46,  # '2'
    0x21, 0x41, 0x49, 0x4D, 0x33,  # '3'
    0x18, 0x14, 0x12, 0x7F, 0x10,  # '4'
    0x27, 0x45, 0x45, 0x45, 0x39,  # '5'
    0x3C, 0x4A, 0x49, 0x49, 0x31,  # '6'
    0x41, 0x21, 0x11, 0x09, 0x07,  # '7'
    0x36, 0x49, 0x49, 0x49, 0x36,  # '8'
    0x46, 0x49, 0x49, 0x29, 0x1E,  # '9'
    0x00, 0x00, 0x14, 0x00, 0x00,  # ':'
    0x00, 0x40, 0x34, 0x00, 0x00,  # ';'
    0x00, 0x08, 0x14, 0x22, 0x41,  # '<'
    0x14, 0x14, 0x14, 0x14, 0x14,  # '='
    0x00, 0x41, 0x22, 0x14, 0x08,  # '>'
    0x02, 0x01, 0x59, 0x09, 0x06,  # '?'
    0x3E, 0x41, 0x5D, 0x59, 0x4E,  # '@'
    0x7C, 0x12, 0x11, 0x12, 0x7C,  # 'A'
    0x7F, 0x49, 0x49, 0x49, 0x36,  # 'B'
    0x3E, 0x41, 0x41, 0x41, 0x22,  # 'C'
    0x7F, 0x41, 0x41, 0x41, 0x3E,  # 'D'
    0x7F, 0x49, 0x49, 0x49, 0x41,  # 'E'
    0x7F, 0x09, 0x09, 0x09, 0x01,  # 'F'
    0x3E, 0x41, 0x41, 0x51, 0x73,  # 'G'
    0x7F, 0x08, 0x08, 0x08, 0x7F,  # 'H'
    0x00, 0x41, 0x7F, 0x41, 0x00,  # 'I'
    0x20, 0x40, 0x41, 0x3F, 0x01,  # 'J'
    0x7F, 0x08, 0x14, 0x22, 0x41,  # 'K'
    0x7F, 0x40, 0x40, 0x40, 0x40,  # 'L'
    0x7F, 0x02, 0x1C, 0x02, 0x7F,  # 'M'
    0x7F, 0x04, 0x08, 0x10, 0x7F,  # 'N'
    0x3E, 0x41, 0x41, 0x41, 0x3E,  # 'O'
    0x7F, 0x09, 0x09, 0x09, 0x06,  # 'P'
    0x3E, 0x41, 0x51, 0x21, 0x5E,  # 'Q'
    0x7F, 0x09, 0x19, 0x29, 0x46,  # 'R'
    0x26, 0x49, 0x49, 0x49, 0x32,  # 'S'
    0x03, 0x01, 0x7F, 0x01, 0x03,  # 'T'
    0x3F, 0x40, 0x40, 0x40, 0x3F,  # 'U'
    0x1F, 0x20, 0x40, 0x20, 0x1F,  # 'V'
    0x3F, 0x40, 0x38, 0x40, 0x3F,  # 'W'
    0x63, 0x14, 0x08, 0x14, 0x63,  # 'X'
    0x03, 0x04, 0x78, 0x04, 0x03,  # 'Y'
    0x61, 0x59, 0x49, 0x4D, 0x43,  # 'Z'
    0x00, 0x7F, 0x41, 0x41, 0x41,  # '['
    0x02, 0x04, 0x08, 0x10, 0x20,  # '\'
    0x00, 0x41, 0x41, 0x41, 0x7F,  # ']'
    0x04, 0x02, 0x01, 0x02, 0x04,  # '^'
    0x40, 0x40, 0x40, 0x40, 0x40,  # '_'
    0x00, 0x03, 0x07, 0x08, 0x00,  # '`'
    0x20, 0x54, 0x54, 0x78, 0x40,  # 'a'
    0x7F, 0x28, 0x44, 0x44, 0x38,  # 'b'
    0x38, 0x44, 0x44, 0x44, 0x28,  # 'c'
    0x38, 0x44, 0x44, 0x28, 0x7F,  # 'd'
    0x38, 0x54, 0x54, 0x54, 0x18,  # 'e'
    0x00, 0x08, 0x7E, 0x09, 0x02,  # 'f'
    0x18, 0xA4, 0xA4, 0x9C, 0x78,  # 'g'
    0x7F, 0x08, 0x04, 0x04, 0x78,  # 'h'
    0x00, 0x44, 0x7D, 0x40, 0x00,  # 'i'
    0x20, 0x40, 0x40, 0x3D, 0x00,  # 'j'
    0x7F, 0x10, 0x28, 0x44, 0x00,  # 'k'
    0x00, 0x41, 0x7F, 0x40, 0x00,  # 'l'
    0x7C, 0x04, 0x78, 0x04, 0x78,  # 'm'
    0x7C, 0x08, 0x04, 0x04, 0x78,  # 'n'
    0x38, 0x44, 0x44, 0x44, 0x38,  # 'o'
    0xFC, 0x18, 0x24, 0x24, 0x18,  # 'p'
    0x18, 0x24, 0x24, 0x18, 0xFC,  # 'q'
    0x7C, 0x08, 0x04, 0x04, 0x08,  # 'r'
    0x48, 0x54, 0x54, 0x54, 0x24,  # 's'
    0x04, 0x04, 0x3F, 0x44, 0x24,  # 't'
    0x3C, 0x40, 0x40, 0x20, 0x7C,  # 'u'
    0x1C, 0x20, 0x40, 0x20, 0x1C,  # 'v'
    0x3C, 0x40, 0x30, 0x40, 0x3C,  # 'w'
    0x44, 0x28, 0x10, 0x28, 0x44,  # 'x'
    0x4C, 0x90, 0x90, 0x90, 0x7C,  # 'y'
    0x44, 0x64, 0x54, 0x4C, 0x44,  # 'z'
    0x00, 0x08, 0x36, 0x41, 0x00,  # '{'
    0x00, 0x00, 0x77, 0x00, 0x00,  # '|'
    0x00, 0x41, 0x36, 0x08, 0x00,  # '}'
    0x02, 0x01, 0x02, 0x04, 0x02,  # '~'
])

# ---------------------------------------------------------------------------
# 3x5 Bitmap Font (Tom Thumb / Robey Pointer)
# Column-encoded: each char = 3 bytes, each byte = 1 column, bit 0 = top row
# Vertically centered on 8-row display (rows 1-5)
# Covers printable ASCII 32 (space) through 126 (~)
# ---------------------------------------------------------------------------
FONT_SMALL_DATA = bytes([
    0x00, 0x00, 0x00,  # ' '
    0x2E, 0x00, 0x00,  # '!'
    0x06, 0x00, 0x06,  # '"'
    0x3E, 0x14, 0x3E,  # '#'
    0x14, 0x3E, 0x0A,  # '$'
    0x12, 0x08, 0x24,  # '%'
    0x1E, 0x2E, 0x38,  # '&'
    0x06, 0x00, 0x00,  # "'"
    0x1C, 0x22, 0x00,  # '('
    0x22, 0x1C, 0x00,  # ')'
    0x0A, 0x04, 0x0A,  # '*'
    0x08, 0x1C, 0x08,  # '+'
    0x20, 0x10, 0x00,  # ','
    0x08, 0x08, 0x08,  # '-'
    0x20, 0x00, 0x00,  # '.'
    0x30, 0x08, 0x06,  # '/'
    0x3C, 0x22, 0x1E,  # '0'
    0x04, 0x3E, 0x00,  # '1'
    0x32, 0x2A, 0x24,  # '2'
    0x22, 0x2A, 0x14,  # '3'
    0x0E, 0x08, 0x3E,  # '4'
    0x2E, 0x2A, 0x12,  # '5'
    0x3C, 0x2A, 0x3A,  # '6'
    0x32, 0x0A, 0x06,  # '7'
    0x3E, 0x2A, 0x3E,  # '8'
    0x2E, 0x2A, 0x1E,  # '9'
    0x14, 0x00, 0x00,  # ':'
    0x20, 0x14, 0x00,  # ';'
    0x08, 0x14, 0x22,  # '<'
    0x14, 0x14, 0x14,  # '='
    0x22, 0x14, 0x08,  # '>'
    0x02, 0x2A, 0x06,  # '?'
    0x1C, 0x2A, 0x2C,  # '@'
    0x3C, 0x0A, 0x3C,  # 'A'
    0x3E, 0x2A, 0x14,  # 'B'
    0x1C, 0x22, 0x22,  # 'C'
    0x3E, 0x22, 0x1C,  # 'D'
    0x3E, 0x2A, 0x2A,  # 'E'
    0x3E, 0x0A, 0x0A,  # 'F'
    0x1C, 0x2A, 0x3A,  # 'G'
    0x3E, 0x08, 0x3E,  # 'H'
    0x22, 0x3E, 0x22,  # 'I'
    0x10, 0x20, 0x1E,  # 'J'
    0x3E, 0x08, 0x36,  # 'K'
    0x3E, 0x20, 0x20,  # 'L'
    0x3E, 0x0C, 0x3E,  # 'M'
    0x3E, 0x1C, 0x3E,  # 'N'
    0x1C, 0x22, 0x1C,  # 'O'
    0x3E, 0x0A, 0x04,  # 'P'
    0x1C, 0x32, 0x3C,  # 'Q'
    0x3E, 0x1A, 0x2C,  # 'R'
    0x24, 0x2A, 0x12,  # 'S'
    0x02, 0x3E, 0x02,  # 'T'
    0x1E, 0x20, 0x3E,  # 'U'
    0x0E, 0x30, 0x0E,  # 'V'
    0x3E, 0x18, 0x3E,  # 'W'
    0x36, 0x08, 0x36,  # 'X'
    0x06, 0x38, 0x06,  # 'Y'
    0x32, 0x2A, 0x26,  # 'Z'
    0x3E, 0x22, 0x22,  # '['
    0x04, 0x08, 0x10,  # '\'
    0x22, 0x22, 0x3E,  # ']'
    0x04, 0x02, 0x04,  # '^'
    0x20, 0x20, 0x20,  # '_'
    0x02, 0x04, 0x00,  # '`'
    0x34, 0x2C, 0x38,  # 'a'
    0x3E, 0x24, 0x18,  # 'b'
    0x18, 0x24, 0x24,  # 'c'
    0x18, 0x24, 0x3E,  # 'd'
    0x18, 0x34, 0x2C,  # 'e'
    0x08, 0x3C, 0x0A,  # 'f'
    0x18, 0x54, 0x3C,  # 'g'
    0x3E, 0x04, 0x38,  # 'h'
    0x3A, 0x00, 0x00,  # 'i'
    0x20, 0x40, 0x3A,  # 'j'
    0x3E, 0x18, 0x24,  # 'k'
    0x22, 0x3E, 0x20,  # 'l'
    0x3C, 0x1C, 0x3C,  # 'm'
    0x3C, 0x04, 0x38,  # 'n'
    0x18, 0x24, 0x18,  # 'o'
    0x7C, 0x24, 0x18,  # 'p'
    0x18, 0x24, 0x7C,  # 'q'
    0x38, 0x04, 0x04,  # 'r'
    0x28, 0x3C, 0x14,  # 's'
    0x04, 0x3E, 0x24,  # 't'
    0x1C, 0x20, 0x3C,  # 'u'
    0x1C, 0x30, 0x1C,  # 'v'
    0x3C, 0x38, 0x3C,  # 'w'
    0x24, 0x18, 0x24,  # 'x'
    0x0C, 0x50, 0x3C,  # 'y'
    0x34, 0x3C, 0x2C,  # 'z'
    0x08, 0x36, 0x22,  # '{'
    0x36, 0x00, 0x00,  # '|'
    0x22, 0x36, 0x08,  # '}'
    0x04, 0x06, 0x02,  # '~'
])

# Select active font based on config
if getattr(config, 'FONT_SIZE', 'large') == 'small':
    _FONT = FONT_SMALL_DATA
    _FONT_WIDTH = 3
else:
    _FONT = FONT_DATA
    _FONT_WIDTH = 5

# ---------------------------------------------------------------------------
# NeoPixel Initialization
# ---------------------------------------------------------------------------
pin = machine.Pin(config.NEOPIXEL_PIN, machine.Pin.OUT)
np = neopixel.NeoPixel(pin, config.NUM_LEDS)

# Pre-compute brightness-scaled color
_r, _g, _b = config.TEXT_COLOR
_f = config.BRIGHTNESS / 255
COLOR = (int(_r * _f), int(_g * _f), int(_b * _f))
OFF = (0, 0, 0)

# ---------------------------------------------------------------------------
# Pixel Mapping — Vertical Serpentine
# Pre-computed lookup: PIXEL_MAP[col][row] = neopixel strip index
# Even columns: top-to-bottom, Odd columns: bottom-to-top
# ---------------------------------------------------------------------------
PIXEL_MAP = []
for _col in range(config.MATRIX_WIDTH):
    _column = []
    for _row in range(config.MATRIX_HEIGHT):
        if _col % 2 == 0:
            _column.append(_col * config.MATRIX_HEIGHT + _row)
        else:
            _column.append(_col * config.MATRIX_HEIGHT + (config.MATRIX_HEIGHT - 1 - _row))
    PIXEL_MAP.append(_column)

# WiFi interface (module-level for reconnection checks)
wlan = network.WLAN(network.STA_IF)

# ---------------------------------------------------------------------------
# Display Functions
# ---------------------------------------------------------------------------

def clear_display():
    np.fill(OFF)
    np.write()


def text_to_columns(text):
    """Convert a string to a list of column byte values using the active font.
    Each element is an integer where each bit = a row (bit 0 = top).
    """
    fw = _FONT_WIDTH
    font = _FONT
    num_chars = len(font) // fw
    columns = []
    for i, char in enumerate(text):
        code = ord(char)
        if FONT_START <= code < FONT_START + num_chars:
            offset = (code - FONT_START) * fw
            for c in range(fw):
                columns.append(font[offset + c])
        else:
            for c in range(fw):
                columns.append(0)
        if i < len(text) - 1:
            for _ in range(config.CHAR_SPACING):
                columns.append(0)
    return columns


def render_frame(columns, scroll_offset, color):
    """Render 32 columns of text data to the matrix at the given scroll offset."""
    for display_col in range(config.MATRIX_WIDTH):
        data_col = scroll_offset + display_col
        if 0 <= data_col < len(columns):
            col_byte = columns[data_col]
            for row in range(config.MATRIX_HEIGHT):
                if col_byte & (1 << row):
                    np[PIXEL_MAP[display_col][row]] = color
                else:
                    np[PIXEL_MAP[display_col][row]] = OFF
        else:
            for row in range(config.MATRIX_HEIGHT):
                np[PIXEL_MAP[display_col][row]] = OFF
    np.write()


def show_status(message):
    """Display a short status message centered on the matrix (non-scrolling)."""
    columns = text_to_columns(message)
    total_width = len(columns)
    start_col = max(0, (config.MATRIX_WIDTH - total_width) // 2)
    np.fill(OFF)
    for i in range(len(columns)):
        display_col = start_col + i
        if 0 <= display_col < config.MATRIX_WIDTH:
            col_byte = columns[i]
            for row in range(config.MATRIX_HEIGHT):
                if col_byte & (1 << row):
                    np[PIXEL_MAP[display_col][row]] = COLOR
    np.write()

# ---------------------------------------------------------------------------
# WiFi
# ---------------------------------------------------------------------------

def connect_wifi():
    """Connect to WiFi. Shows status on display. Returns True if connected."""
    wlan.active(True)

    if wlan.isconnected():
        return True

    show_status("WiFi")
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)

    retries = 0
    while not wlan.isconnected() and retries < config.WIFI_MAX_RETRIES:
        time.sleep_ms(config.WIFI_RETRY_DELAY_MS)
        retries += 1

    if wlan.isconnected():
        print("WiFi connected:", wlan.ifconfig())
        return True
    else:
        show_status("NoWiFi")
        return False

# ---------------------------------------------------------------------------
# API Client
# ---------------------------------------------------------------------------

def fetch_facts():
    """Fetch facts from the Kibble API. Returns list of fact strings, or None."""
    try:
        gc.collect()
        headers = {
            "Authorization": "Bearer " + config.API_KEY,
            "Accept": "application/json"
        }
        show_status("Load")
        response = urequests.get(config.API_URL, headers=headers)

        if response.status_code == 200:
            data = response.json()
            response.close()
            gc.collect()

            facts = []
            if isinstance(data, dict) and "topics" in data:
                for topic in data["topics"]:
                    for fact in topic.get("facts", []):
                        content = fact.get("content", "")
                        if content:
                            facts.append(str(content))

            print("Fetched", len(facts), "facts")
            return facts if facts else None
        else:
            print("API error:", response.status_code)
            response.close()
            gc.collect()
            return None

    except Exception as e:
        print("API error:", e)
        gc.collect()
        return None

# ---------------------------------------------------------------------------
# Random Ordering
# ---------------------------------------------------------------------------

def shuffle_list(lst):
    """Fisher-Yates shuffle in place."""
    for i in range(len(lst) - 1, 0, -1):
        j = getrandbits(16) % (i + 1)
        lst[i], lst[j] = lst[j], lst[i]

# ---------------------------------------------------------------------------
# Scroll Engine
# ---------------------------------------------------------------------------

def scroll_fact(text):
    """Scroll a single fact across the display from right to left."""
    columns = text_to_columns(text)

    for offset in range(-config.MATRIX_WIDTH, len(columns)):
        render_frame(columns, offset, COLOR)
        time.sleep_ms(config.SCROLL_DELAY_MS)

# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------

def main():
    clear_display()

    # Connect to WiFi (retry until success)
    while not connect_wifi():
        show_status("NoWiFi")
        time.sleep_ms(config.WIFI_RETRY_DELAY_MS * 2)

    # Fetch initial facts (retry until success)
    facts = None
    while facts is None:
        facts = fetch_facts()
        if facts is None:
            show_status("NoAPI")
            time.sleep_ms(config.API_RETRY_DELAY_MS)
            if not wlan.isconnected():
                while not connect_wifi():
                    time.sleep_ms(config.WIFI_RETRY_DELAY_MS * 2)

    # Main display loop
    last_refresh = time.ticks_ms()

    while True:
        shuffle_list(facts)

        for fact in facts:
            # Check hourly refresh
            elapsed = time.ticks_diff(time.ticks_ms(), last_refresh)
            if elapsed >= config.FACT_REFRESH_INTERVAL_MS:
                new_facts = fetch_facts()
                if new_facts is not None:
                    facts = new_facts
                    last_refresh = time.ticks_ms()
                    break  # Re-shuffle with new facts
                else:
                    last_refresh = time.ticks_ms()

            # Check WiFi
            if not wlan.isconnected():
                show_status("WiFi?")
                time.sleep_ms(2000)
                if not connect_wifi():
                    continue

            scroll_fact(fact)
            gc.collect()


try:
    main()
except Exception as e:
    print("Fatal error:", e)
    time.sleep(5)
    machine.reset()
