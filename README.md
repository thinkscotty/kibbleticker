# Kibble Board

A smart LED ticker board that scrolls facts from a self-hosted [Kibble](https://github.com/scottypate/kibble) instance across an 8x32 NeoPixel matrix display. Built with MicroPython on an ESP32-S3.

Interesting topics are entered by users through the Kibble web interface. Then Kibble utilizes free AI to source facts and summarize them to the user's specification. The facts are fetched over WiFi by the board, and displayed in a randomized scrolling loop that refreshes every hour.

An optional OLED display and mini keyboard allow on-device configuration of WiFi, API, text color, brightness, and font size — no computer required after initial setup.

## Hardware

### Bill of Materials

| Component | Description | Notes |
|-----------|-------------|-------|
| ESP32-S3 Devkit | Microcontroller with WiFi | Any ESP32-S3 devkit board will work |
| 8x32 WS2812B NeoPixel Matrix | BTF-LIGHTING WS2812B ECO RGB (or equivalent) | Must be **vertical serpentine** wiring layout, 5V, 256 LEDs total |
| 3.3V to 5V Logic Level Shifter | Bidirectional level shifter | Needed because ESP32 GPIO is 3.3V but WS2812B data line expects 5V |
| 5V USB-C Power Supply | High amperage (3A+ recommended) | 256 LEDs at full white draw ~15A; at low brightness 3A is sufficient |
| M5Stack CardKB | I2C mini QWERTY keyboard | *Optional* — enables on-device settings menu |
| SSD1306 0.96" OLED Display | 128x64 I2C OLED (bicolor yellow/blue recommended) | *Optional* — displays the settings menu |
| Jumper Wires | Male-to-female or as needed | See wiring diagrams below |

### NeoPixel Matrix Wiring

```
ESP32-S3              Level Shifter           NeoPixel Matrix
---------             -------------           ---------------
GPIO 16  ──────────>  LV Input
3.3V     ──────────>  LV (low voltage)
                      HV Output  ──────────>  DIN (data in)
                      HV (high voltage) <───  5V
GND      ──────────>  GND        ──────────>  GND
5V PSU   ─────────────────────────────────>   5V
5V PSU   ─────────────────────────────────>   GND
```

**Important notes:**

- The NeoPixel matrix **must** share a common ground with the ESP32-S3 and the power supply.
- Power the NeoPixel matrix directly from the 5V power supply, **not** through the ESP32's 5V pin (the current draw is too high).
- The level shifter converts the 3.3V data signal from GPIO 16 to the 5V expected by the WS2812B LEDs.
- If you use a different GPIO pin, update `NEOPIXEL_PIN` in `config.py`.

### I2C Wiring (CardKB + OLED)

Both the CardKB and the SSD1306 OLED share the same I2C bus (they have different addresses). Connect them in parallel:

```
ESP32-S3              CardKB (0x5F)          SSD1306 OLED (0x3C)
---------             ---------------        -------------------
GPIO 8 (SDA) ────────>  SDA  ──────────────>  SDA
GPIO 9 (SCL) ────────>  SCL  ──────────────>  SCL
3.3V         ────────>  VCC  ──────────────>  VCC
GND          ────────>  GND  ──────────────>  GND
```

**Notes:**

- Both devices run on 3.3V from the ESP32-S3. No level shifter needed for I2C.
- If you use different I2C pins, update `I2C_SDA_PIN` and `I2C_SCL_PIN` in `config.py`.
- The CardKB and OLED are optional. The board works as a scroll-only ticker without them.

### Matrix Wiring Layout

This project assumes a **vertical serpentine** LED layout, which is the most common configuration for WS2812B matrix panels:

```
Col 0    Col 1    Col 2    Col 3
(down)   (up)     (down)   (up)     ...

LED 0    LED 15   LED 16   LED 31
LED 1    LED 14   LED 17   LED 30
LED 2    LED 13   LED 18   LED 29
LED 3    LED 12   LED 19   LED 28
LED 4    LED 11   LED 20   LED 27
LED 5    LED 10   LED 21   LED 26
LED 6    LED 9    LED 22   LED 25
LED 7    LED 8    LED 23   LED 24
```

Even columns run top-to-bottom, odd columns run bottom-to-top. The code handles this mapping automatically.

## Software Setup

### Prerequisites

1. **Thonny IDE** - Download from [thonny.org](https://thonny.org)
2. **MicroPython 1.27+** firmware for ESP32-S3

### Step 1: Flash MicroPython to the ESP32-S3

1. Download the latest MicroPython firmware for ESP32-S3 from [micropython.org/download/ESP32_GENERIC_S3](https://micropython.org/download/ESP32_GENERIC_S3/)
2. Connect your ESP32-S3 to your computer via USB
3. Open Thonny and go to **Tools > Options > Interpreter**
4. Select **MicroPython (ESP32)** as the interpreter
5. Click **Install or update MicroPython (esptool)**
6. Select the correct USB port, choose the downloaded `.bin` firmware file, and click **Install**
7. Wait for the flash to complete, then close the dialog

### Step 2: Install Libraries

The board needs two libraries. Install both via Thonny:

1. In Thonny, ensure the ESP32-S3 is connected (you should see the MicroPython REPL at the bottom)
2. Go to **Tools > Manage packages...**
3. Search for `micropython-urequests` and click **Install**
4. Search for `micropython-ssd1306` and click **Install** *(only needed if using the OLED display)*
5. Close the package manager

### Step 3: Configure the Board

Edit `config.py` with your settings before uploading:

```python
# WiFi Configuration
WIFI_SSID = "YourNetworkName"
WIFI_PASSWORD = "YourPassword"

# API Configuration — point to your self-hosted Kibble instance
API_BASE_URL = "https://your-kibble-instance.com"
API_KEY = "your-api-key-here"
```

**`API_BASE_URL`** should be the base URL of your Kibble instance (just the domain, no path). The board automatically appends the correct API path.

**`API_KEY`** is the Bearer token for API authentication. You can generate one from your Kibble instance's admin panel.

See the [Configuration Reference](#configuration-reference) section below for all available settings.

**Note:** If you have a CardKB and OLED connected, you can skip editing `config.py` entirely and configure WiFi, API key, and display settings directly through the on-device settings menu.

### Step 4: Upload Files to the ESP32-S3

1. In Thonny, make sure the ESP32-S3 is connected
2. Upload each of these files to the ESP32 by opening them in Thonny (File > Open > This computer), then saving to the device (File > Save as... > select **MicroPython device**):
   - `config.py`
   - `menu.py`
   - `main.py`
3. Press the **Stop/Restart** button (or Ctrl+D) to soft-reboot the ESP32

The board will immediately begin running. You should see status messages on the matrix:
- **"WiFi"** — Connecting to WiFi
- **"Load"** — Fetching facts from the API
- Then facts will begin scrolling

### Step 5: Verify via Serial Console

While the board is running, the Thonny REPL will show diagnostic output:

```
CardKB detected at 0x5F
OLED detected at 0x3C
WiFi connected: ('192.168.1.100', '255.255.255.0', '192.168.1.1', '8.8.8.8')
Fetched 47 facts
```

If something goes wrong, error messages will appear here.

## Settings Menu

If you have a CardKB and SSD1306 OLED connected, you can configure the board without a computer.

### Opening the Menu

Press **any key** on the CardKB while facts are scrolling. The OLED display will turn on and show the settings menu. The ticker pauses while the menu is active.

After **30 seconds** of inactivity, the OLED turns off and the ticker resumes automatically. You can also press **ESC** to close the menu immediately.

### Navigation

| Key | Action |
|-----|--------|
| **LEFT / RIGHT** | Switch between the 5 settings screens |
| **UP / DOWN** | Move cursor between options on the current screen |
| **ENTER** | Select the highlighted option |
| **ESC** | Close the settings menu |

### Settings Screens

**Screen 1: Data Source** — Choose which facts the board displays:
- **Most Recent Facts** — The 100 most recent facts from each topic (default)
- **All Active Facts** — Every non-archived fact from all topics

**Screen 2: WiFi & API** — Edit connection settings:
- **WiFi SSID** — Your WiFi network name
- **WiFi Password** — Your WiFi password
- **API Key** — Your Kibble API Bearer token

Press ENTER on a field to edit it. Type the new value using the CardKB, then press ENTER to confirm. A confirmation dialog ("ARE YOU SURE?") will appear — select YES to save or NO to discard.

**Screen 3: Text Color** — Choose the scrolling text color:
- White (default), Blue, Green, Yellow, Orange, Red, Pink, Purple

**Screen 4: Brightness** — Adjust LED brightness:
- Scale of 0 (dimmest) to 10 (brightest), default 3

**Screen 5: Font Size** — Choose the text size:
- **Large** — 5x8 font, ~5 characters visible at once (default)
- **Small** — 3x5 font, ~8 characters visible at once

All settings are saved to the device and persist across reboots.

## Configuration Reference

Hardware and timing settings are in `config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `WIFI_SSID` | `"YOUR_WIFI_NETWORK"` | Your WiFi network name |
| `WIFI_PASSWORD` | `"YOUR_WIFI_PASSWORD"` | Your WiFi password |
| `API_BASE_URL` | `"YOUR_KIBBLE_URL"` | Base URL of your Kibble instance (e.g. `https://your-domain.com`) |
| `API_KEY` | `"YOUR_KIBBLE_API"` | API key (Bearer token) for authentication |
| `NEOPIXEL_PIN` | `16` | GPIO pin connected to the NeoPixel data line |
| `MATRIX_WIDTH` | `32` | Number of columns on the matrix |
| `MATRIX_HEIGHT` | `8` | Number of rows on the matrix |
| `NUM_LEDS` | `256` | Total number of LEDs (width x height) |
| `I2C_SDA_PIN` | `8` | GPIO pin for I2C data (SDA) |
| `I2C_SCL_PIN` | `9` | GPIO pin for I2C clock (SCL) |
| `SCROLL_DELAY_MS` | `80` | Milliseconds between scroll frames (lower = faster) |
| `CHAR_SPACING` | `1` | Blank pixel columns between characters |
| `FACT_REFRESH_INTERVAL_MS` | `3600000` | How often to fetch new facts (default: 1 hour) |
| `WIFI_RETRY_DELAY_MS` | `5000` | Delay between WiFi connection retries |
| `WIFI_MAX_RETRIES` | `20` | Maximum WiFi connection attempts before giving up |
| `API_RETRY_DELAY_MS` | `10000` | Delay between API fetch retries |

Display settings (text color, brightness, font size, and API data source) are managed through the on-device settings menu and saved to `settings.json`. They can also be configured by manually creating a `settings.json` file on the device:

```json
{
  "api_source": "recent",
  "wifi_ssid": "",
  "wifi_password": "",
  "api_key": "",
  "text_color": "white",
  "brightness": 3,
  "font_size": "large"
}
```

### Font Options

Two font sizes are available:

- **`"large"`** — Adafruit GFX 5x8 font. Uses the full height of the display. Fits ~5 characters on screen at once. Best for maximum readability at a distance.
- **`"small"`** — Tom Thumb 3x5 font. Compact and readable. Fits ~8 characters on screen at once. Best for longer text that you want to keep visible longer.

## Kibble API

This board is designed to work with a self-hosted [Kibble](https://github.com/scottypate/kibble) instance. The board calls one of the following endpoints based on the Data Source setting:

```
GET /api/v1/facts/recent      (100 most recent facts per topic)
GET /api/v1/facts/all          (all active facts from all topics)
Authorization: Bearer <your-api-key>
```

**Expected response format:**

```json
{
  "topics": [
    {
      "topic_id": 1,
      "topic_name": "Science",
      "facts": [
        {"id": 1, "content": "The speed of light is approximately 299,792 km/s"},
        {"id": 2, "content": "Water boils at 100 degrees Celsius at sea level"}
      ]
    },
    {
      "topic_id": 2,
      "topic_name": "History",
      "facts": [
        {"id": 3, "content": "The Great Wall of China is over 13,000 miles long"}
      ]
    }
  ]
}
```

The board collects all `content` strings from all topics and displays them in random order.

## Display Status Messages

The board shows short status messages on the matrix during startup and error conditions:

| Message | Meaning |
|---------|---------|
| **WiFi** | Connecting to WiFi... |
| **NoWiFi** | WiFi connection failed (will retry) |
| **Load** | Fetching facts from the API... |
| **NoAPI** | API request failed (will retry) |
| **WiFi?** | WiFi connection lost during operation (reconnecting) |

## Troubleshooting

### Board doesn't start / no LEDs light up
- Verify the 5V power supply is connected and providing power to the matrix
- Check that the ground is shared between the ESP32, level shifter, and matrix
- Confirm the data wire is on the correct GPIO pin (default: GPIO 16)

### "NoWiFi" stays on screen
- Double-check `WIFI_SSID` and `WIFI_PASSWORD` in `config.py` (or use the settings menu to update them)
- Make sure the WiFi network is 2.4 GHz (ESP32-S3 does not support 5 GHz)
- Move the board closer to the WiFi router

### "NoAPI" stays on screen
- Verify `API_BASE_URL` points to your Kibble instance (e.g. `https://your-domain.com`)
- Verify `API_KEY` is correct
- Check that your Kibble instance is running and accessible from the board's network
- Check the Thonny serial console for detailed error messages

### Settings menu doesn't appear
- Verify the CardKB and OLED are connected to GPIO 8 (SDA) and GPIO 9 (SCL)
- Check that both devices share a common ground with the ESP32
- Look for "CardKB detected" and "OLED detected" messages in the serial console at boot
- Both the CardKB AND the OLED must be connected for the menu to work

### Text looks garbled or offset
- Confirm your matrix uses a **vertical serpentine** wiring layout
- If your matrix uses a different layout (horizontal serpentine, progressive, etc.), the pixel mapping in `main.py` will need to be modified

### LEDs are too bright or too dim
- Use the settings menu to adjust brightness (0-10 scale)
- Level 3 is the default; at this level power draw is low and the display is comfortable to read indoors

### Board resets frequently
- This can happen if the power supply can't provide enough current
- Use a 5V supply rated for at least 3A
- Lower the brightness setting to reduce power draw

## Project Structure

```
kibble_board_prototype/
  config.py        — Hardware configuration (WiFi, API, pins, timing)
  menu.py          — Settings UI (OLED display, CardKB input, settings persistence)
  main.py          — Main application (fonts, display, WiFi, API, scroll engine)
  settings.json    — User settings (created automatically on first change)
```

All `.py` files must be uploaded to the root of the ESP32-S3's filesystem via Thonny.

## License

Font data used in this project:

- **5x8 font**: From the [Adafruit GFX Library](https://github.com/adafruit/Adafruit-GFX-Library) (BSD License)
- **3x5 font**: Tom Thumb font by Brian J. Swetland, Vassilii Khachaturov, with modifications by Robey Pointer (3-clause BSD License)
