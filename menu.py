import time
import json
from machine import Pin, SoftI2C
from ssd1306 import SSD1306_I2C
import config

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CARDKB_ADDR = 0x5F
SSD1306_ADDR = 0x3C

# CardKB key codes
KEY_UP = 0xB5
KEY_DOWN = 0xB6
KEY_LEFT = 0xB4
KEY_RIGHT = 0xB7
KEY_ENTER = 0x0D
KEY_BACK = 0x08
KEY_ESC = 0x1B

# Inactivity timeout (ms)
MENU_TIMEOUT_MS = 30000

# Color name -> RGB tuple mapping
COLOR_MAP = {
    "white": (255, 255, 255),
    "blue": (0, 0, 255),
    "green": (0, 255, 0),
    "yellow": (255, 255, 0),
    "orange": (255, 128, 0),
    "red": (255, 0, 0),
    "pink": (255, 50, 150),
    "purple": (128, 0, 255),
}

# Ordered list for menu display
COLOR_NAMES = ["white", "blue", "green", "yellow", "orange", "red", "pink", "purple"]

# Brightness 0-10 -> NeoPixel brightness value (0-255)
BRIGHTNESS_MAP = [5, 10, 20, 35, 55, 80, 110, 145, 185, 220, 255]

# Default settings (used when settings.json is missing or corrupt)
DEFAULT_SETTINGS = {
    "api_source": "recent",
    "wifi_ssid": "",
    "wifi_password": "",
    "api_key": "",
    "text_color": "white",
    "brightness": 3,
    "font_size": "large",
    "scroll_delay": 80,
}

# Screen definitions
SCREENS = [
    {
        "title": "DATA SOURCE",
        "key": "api_source",
        "type": "select",
        "options": [
            ("Recent Facts", "recent"),
            ("All Facts", "all"),
        ],
    },
    {
        "title": "WIFI & API",
        "key": None,
        "type": "text_entry",
        "fields": [
            ("WiFi SSID", "wifi_ssid"),
            ("WiFi Password", "wifi_password"),
            ("API Key", "api_key"),
        ],
    },
    {
        "title": "TEXT COLOR",
        "key": "text_color",
        "type": "select",
        "options": [(n[0].upper() + n[1:], n) for n in COLOR_NAMES],
    },
    {
        "title": "BRIGHTNESS",
        "key": "brightness",
        "type": "select",
        "options": [("Level " + str(i), i) for i in range(11)],
    },
    {
        "title": "FONT SIZE",
        "key": "font_size",
        "type": "select",
        "options": [
            ("Large", "large"),
            ("Small", "small"),
        ],
    },
    {
        "title": "SCROLL SPEED",
        "key": "scroll_delay",
        "type": "number_entry",
        "min": 5,
        "max": 500,
        "unit": "ms",
    },
]


# ---------------------------------------------------------------------------
# Settings Persistence
# ---------------------------------------------------------------------------

def load_settings():
    """Load settings from settings.json. Returns defaults if missing/corrupt."""
    try:
        with open("settings.json", "r") as f:
            saved = json.load(f)
        merged = dict(DEFAULT_SETTINGS)
        for key in DEFAULT_SETTINGS:
            if key in saved:
                merged[key] = saved[key]
        return merged
    except (OSError, ValueError):
        return dict(DEFAULT_SETTINGS)


def save_settings(settings):
    """Write settings dict to settings.json."""
    try:
        with open("settings.json", "w") as f:
            json.dump(settings, f)
    except OSError as e:
        print("Settings save error:", e)


# ---------------------------------------------------------------------------
# I2C and Hardware Init
# ---------------------------------------------------------------------------

def init_i2c():
    """Initialize I2C bus and detect devices. Returns (i2c, has_cardkb, has_oled)."""
    try:
        i2c = SoftI2C(sda=Pin(config.I2C_SDA_PIN), scl=Pin(config.I2C_SCL_PIN), freq=100000)
        devices = i2c.scan()
        has_cardkb = CARDKB_ADDR in devices
        has_oled = SSD1306_ADDR in devices
        if has_cardkb:
            print("CardKB detected at 0x5F")
        if has_oled:
            print("OLED detected at 0x3C")
        return i2c, has_cardkb, has_oled
    except Exception as e:
        print("I2C init error:", e)
        return None, False, False


def init_oled(i2c):
    """Initialize SSD1306 OLED. Returns display object or None."""
    try:
        oled = SSD1306_I2C(128, 64, i2c, addr=SSD1306_ADDR)
        oled.poweroff()
        return oled
    except Exception as e:
        print("OLED init error:", e)
        return None


# ---------------------------------------------------------------------------
# CardKB Input
# ---------------------------------------------------------------------------

def read_key(i2c):
    """Non-blocking read from CardKB. Returns key code or 0."""
    try:
        data = i2c.readfrom(CARDKB_ADDR, 1)
        return data[0]
    except OSError:
        return 0


def wait_for_key(i2c, ref_time):
    """Blocking wait for key press with timeout. Returns key code or None."""
    while True:
        key = read_key(i2c)
        if key != 0:
            return key
        if time.ticks_diff(time.ticks_ms(), ref_time) >= MENU_TIMEOUT_MS:
            return None
        time.sleep_ms(50)


# ---------------------------------------------------------------------------
# OLED Rendering
# ---------------------------------------------------------------------------

def _truncate(text, max_len):
    """Truncate text with '..' if too long."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 2] + ".."


def _format_field_value(field_key, value):
    """Format a settings field value for display."""
    if not value:
        return "(not set)"
    if field_key == "wifi_password":
        return "*" * min(len(value), 8)
    return _truncate(value, 10)


def render_screen(oled, title, items, selected_idx, checked_idx, scroll_offset, page_str):
    """Render a full menu screen to the OLED."""
    oled.fill(0)

    # Yellow zone: title (row 0) and page indicator (row 0, right-aligned)
    oled.text(title, 0, 4, 1)
    page_x = 128 - len(page_str) * 8
    oled.text(page_str, page_x, 4, 1)

    # Separator line at boundary of yellow/blue zone
    oled.hline(0, 15, 128, 1)

    # Blue zone: menu items (rows 18-55, up to 5 items)
    max_visible = 5
    for i in range(max_visible):
        item_idx = scroll_offset + i
        if item_idx >= len(items):
            break
        y = 18 + (i * 8)

        # Build prefix
        if item_idx == selected_idx and item_idx == checked_idx:
            prefix = ">"
            suffix = " *"
        elif item_idx == selected_idx:
            prefix = ">"
            suffix = ""
        elif item_idx == checked_idx:
            prefix = " "
            suffix = " *"
        else:
            prefix = " "
            suffix = ""

        label = prefix + items[item_idx]
        # Truncate to fit with possible suffix
        max_chars = 16 - len(suffix)
        label = _truncate(label, max_chars) + suffix
        oled.text(label, 0, y, 1)

    # Highlight bar behind selected item (invert)
    vis_selected = selected_idx - scroll_offset
    if 0 <= vis_selected < max_visible:
        hy = 17 + (vis_selected * 8)
        oled.fill_rect(0, hy, 128, 9, 1)
        # Redraw that item's text inverted (color=0 on white background)
        item_idx = selected_idx
        if item_idx < len(items):
            if item_idx == checked_idx:
                prefix = ">"
                suffix = " *"
            else:
                prefix = ">"
                suffix = ""
            label = prefix + items[item_idx]
            max_chars = 16 - len(suffix)
            label = _truncate(label, max_chars) + suffix
            oled.text(label, 0, 18 + (vis_selected * 8), 0)

    # Bottom bar: navigation hint
    oled.text("<L  UP/DN  R>", 8, 56, 1)

    oled.show()


def compute_scroll_offset(selected_idx, num_items, max_visible=5):
    """Compute scroll offset to keep selected item visible."""
    if num_items <= max_visible:
        return 0
    offset = max(0, selected_idx - 2)
    offset = min(offset, num_items - max_visible)
    return offset


def _get_checked_index(screen, settings):
    """Return index of the currently-active option, or -1."""
    if screen["type"] == "text_entry":
        return -1
    current_value = settings.get(screen["key"])
    for i, opt in enumerate(screen["options"]):
        if opt[1] == current_value:
            return i
    return -1


# ---------------------------------------------------------------------------
# Confirmation Dialog
# ---------------------------------------------------------------------------

def _confirm_dialog(oled, i2c):
    """Show 'ARE YOU SURE?' dialog. Returns True for YES, False for NO."""
    selected = 0
    last_activity = time.ticks_ms()

    while True:
        if time.ticks_diff(time.ticks_ms(), last_activity) >= MENU_TIMEOUT_MS:
            return False

        oled.fill(0)
        oled.text("ARE YOU SURE", 16, 4, 1)
        oled.text("YOU WANT TO", 20, 14, 1)
        oled.text("CHANGE THIS?", 16, 24, 1)

        yes_prefix = "> " if selected == 0 else "  "
        no_prefix = "> " if selected == 1 else "  "
        oled.text(yes_prefix + "YES", 40, 40, 1)
        oled.text(no_prefix + "NO", 40, 50, 1)

        oled.show()

        key = read_key(i2c)
        if key == 0:
            time.sleep_ms(50)
            continue

        last_activity = time.ticks_ms()

        if key == KEY_UP or key == KEY_DOWN:
            selected = 1 - selected
        elif key == KEY_ENTER:
            return selected == 0
        elif key == KEY_ESC:
            return False


# ---------------------------------------------------------------------------
# Text Entry Flow
# ---------------------------------------------------------------------------

def _text_entry_flow(oled, i2c, field_label, current_value):
    """Text entry dialog. Returns new string if confirmed, None if cancelled."""
    buf = list(current_value)
    cursor = len(buf)
    last_activity = time.ticks_ms()

    while True:
        if time.ticks_diff(time.ticks_ms(), last_activity) >= MENU_TIMEOUT_MS:
            return None

        oled.fill(0)
        oled.text("EDIT:", 0, 0, 1)
        oled.text(_truncate(field_label, 16), 0, 10, 1)
        oled.hline(0, 19, 128, 1)

        # Show text with sliding window around cursor
        text_str = "".join(buf)
        visible = 16
        if len(text_str) <= visible:
            display_str = text_str
            cursor_x = cursor * 8
        else:
            win_start = max(0, cursor - visible + 2)
            win_end = win_start + visible
            display_str = text_str[win_start:win_end]
            cursor_x = (cursor - win_start) * 8

        oled.text(display_str, 0, 24, 1)

        # Blinking cursor underline
        if (time.ticks_ms() // 400) % 2:
            oled.hline(cursor_x, 33, 7, 1)

        oled.text("ENT=OK", 0, 48, 1)
        oled.text("ESC=CANCEL", 0, 56, 1)
        oled.show()

        key = read_key(i2c)
        if key == 0:
            time.sleep_ms(50)
            continue

        last_activity = time.ticks_ms()

        if key == KEY_ESC:
            return None

        elif key == KEY_ENTER:
            new_value = "".join(buf)
            if _confirm_dialog(oled, i2c):
                return new_value
            else:
                return None

        elif key == KEY_BACK:
            if cursor > 0 and len(buf) > 0:
                buf.pop(cursor - 1)
                cursor -= 1

        elif key == KEY_LEFT:
            cursor = max(0, cursor - 1)

        elif key == KEY_RIGHT:
            cursor = min(len(buf), cursor + 1)

        elif 0x20 <= key <= 0x7E:
            buf.insert(cursor, chr(key))
            cursor += 1


# ---------------------------------------------------------------------------
# Number Entry Flow
# ---------------------------------------------------------------------------

def _number_entry_flow(oled, i2c, current_value, min_val, max_val, unit):
    """Number entry dialog. Returns new int if confirmed and valid, None if cancelled."""
    buf = list(str(current_value))
    cursor = len(buf)
    error_msg = ""
    last_activity = time.ticks_ms()

    while True:
        if time.ticks_diff(time.ticks_ms(), last_activity) >= MENU_TIMEOUT_MS:
            return None

        oled.fill(0)
        oled.text("SCROLL SPEED", 0, 0, 1)
        oled.text(str(min_val) + "-" + str(max_val) + unit, 0, 10, 1)
        oled.hline(0, 19, 128, 1)

        # Show current input
        text_str = "".join(buf)
        oled.text(text_str + unit, 0, 24, 1)

        # Blinking cursor underline
        if (time.ticks_ms() // 400) % 2:
            cx = cursor * 8
            oled.hline(cx, 33, 7, 1)

        if error_msg:
            oled.text(error_msg, 0, 40, 1)

        oled.text("ENT=OK", 0, 48, 1)
        oled.text("ESC=CANCEL", 0, 56, 1)
        oled.show()

        key = read_key(i2c)
        if key == 0:
            time.sleep_ms(50)
            continue

        last_activity = time.ticks_ms()
        error_msg = ""

        if key == KEY_ESC:
            return None

        elif key == KEY_ENTER:
            text_str = "".join(buf)
            try:
                val = int(text_str)
            except ValueError:
                error_msg = "Not a number!"
                continue
            if val < min_val or val > max_val:
                error_msg = str(min_val) + "-" + str(max_val) + " only!"
                continue
            return val

        elif key == KEY_BACK:
            if cursor > 0 and len(buf) > 0:
                buf.pop(cursor - 1)
                cursor -= 1

        elif key == KEY_LEFT:
            cursor = max(0, cursor - 1)

        elif key == KEY_RIGHT:
            cursor = min(len(buf), cursor + 1)

        elif 0x30 <= key <= 0x39:  # Digits 0-9 only
            buf.insert(cursor, chr(key))
            cursor += 1


# ---------------------------------------------------------------------------
# Main Settings Menu
# ---------------------------------------------------------------------------

def open_settings_menu(oled, i2c, settings):
    """
    Main settings menu loop.
    Returns True if any settings were changed, False otherwise.
    Powers off OLED on exit.
    """
    oled.poweron()
    time.sleep_ms(50)
    changed = False
    screen_idx = 0
    selected = [0] * len(SCREENS)
    last_activity = time.ticks_ms()

    while True:
        # Check inactivity timeout
        if time.ticks_diff(time.ticks_ms(), last_activity) >= MENU_TIMEOUT_MS:
            oled.fill(0)
            oled.show()
            oled.poweroff()
            return changed

        screen = SCREENS[screen_idx]
        page_str = str(screen_idx + 1) + "/" + str(len(SCREENS))

        # Build item list and find checked index
        if screen["type"] == "select":
            items = [opt[0] for opt in screen["options"]]
            checked_idx = _get_checked_index(screen, settings)
        elif screen["type"] == "number_entry":
            cur = settings.get(screen["key"], "")
            items = ["Current: " + str(cur) + screen.get("unit", ""), "Edit value"]
            checked_idx = -1
        else:
            items = []
            for label, key in screen["fields"]:
                val = _format_field_value(key, settings.get(key, ""))
                items.append(label + ":" + val)
            checked_idx = -1

        num_items = len(items)
        scroll_off = compute_scroll_offset(selected[screen_idx], num_items)

        render_screen(oled, screen["title"], items, selected[screen_idx], checked_idx, scroll_off, page_str)

        # Wait for key
        key = wait_for_key(i2c, last_activity)

        if key is None:
            oled.fill(0)
            oled.show()
            oled.poweroff()
            return changed

        last_activity = time.ticks_ms()

        # Navigation
        if key == KEY_LEFT:
            screen_idx = (screen_idx - 1) % len(SCREENS)
        elif key == KEY_RIGHT:
            screen_idx = (screen_idx + 1) % len(SCREENS)
        elif key == KEY_UP:
            selected[screen_idx] = max(0, selected[screen_idx] - 1)
        elif key == KEY_DOWN:
            selected[screen_idx] = min(num_items - 1, selected[screen_idx] + 1)
        elif key == KEY_ENTER:
            if screen["type"] == "select":
                value = screen["options"][selected[screen_idx]][1]
                settings[screen["key"]] = value
                save_settings(settings)
                changed = True
                # Brief visual feedback
                oled.fill_rect(0, 56, 128, 8, 0)
                oled.text("  Saved!", 32, 56, 1)
                oled.show()
                time.sleep_ms(500)
            elif screen["type"] == "text_entry":
                field_label, field_key = screen["fields"][selected[screen_idx]]
                current_val = settings.get(field_key, "")
                result = _text_entry_flow(oled, i2c, field_label, current_val)
                if result is not None:
                    settings[field_key] = result
                    save_settings(settings)
                    changed = True
                last_activity = time.ticks_ms()
            elif screen["type"] == "number_entry":
                cur = settings.get(screen["key"], 80)
                result = _number_entry_flow(oled, i2c, cur, screen["min"], screen["max"], screen.get("unit", ""))
                if result is not None:
                    settings[screen["key"]] = result
                    save_settings(settings)
                    changed = True
                    oled.fill_rect(0, 56, 128, 8, 0)
                    oled.text("  Saved!", 32, 56, 1)
                    oled.show()
                    time.sleep_ms(500)
                last_activity = time.ticks_ms()
        elif key == KEY_ESC:
            oled.fill(0)
            oled.show()
            oled.poweroff()
            return changed
