# Kibble Board

A smart LED ticker board that scrolls facts from a self-hosted [Kibble](https://github.com/scottypate/kibble) instance across an 8x32 NeoPixel matrix display. Built with MicroPython on an ESP32-S3.

Interesting topics are entered by users through the Kibble web interface. Then Kibble utilizes free AI to source facts and summarize them to the user's specification. The facts are fetched over WiFi by the board, and displayed in a randomized scrolling loop that refreshes every hour.

## Hardware

### Bill of Materials

| Component | Description | Notes |
|-----------|-------------|-------|
| ESP32-S3 Devkit | Microcontroller with WiFi | Any ESP32-S3 devkit board will work |
| 8x32 WS2812B NeoPixel Matrix | BTF-LIGHTING WS2812B ECO RGB (or equivalent) | Must be **vertical serpentine** wiring layout, 5V, 256 LEDs total |
| 3.3V to 5V Logic Level Shifter | Bidirectional level shifter | Needed because ESP32 GPIO is 3.3V but WS2812B data line expects 5V |
| 5V USB-C Power Supply | High amperage (3A+ recommended) | 256 LEDs at full white draw ~15A; at low brightness 3A is sufficient |
| Jumper Wires | Male-to-female or as needed | 3 wires minimum: data, power, ground |

### Wiring

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

### Step 2: Install the `urequests` Library

The board needs the `urequests` library to make HTTP requests to your Kibble API.

1. In Thonny, ensure the ESP32-S3 is connected (you should see the MicroPython REPL at the bottom)
2. Go to **Tools > Manage packages...**
3. Search for `micropython-urequests`
4. Click **Install** to install it to the ESP32-S3
5. Close the package manager

### Step 3: Configure the Board

Edit `config.py` with your settings before uploading:

```python
# WiFi Configuration
WIFI_SSID = "YourNetworkName"
WIFI_PASSWORD = "YourPassword"

# API Configuration — point to your self-hosted Kibble instance
API_URL = "https://your-kibble-instance.com/api/v1/facts/recent"
API_KEY = "your-api-key-here"
```

**`API_URL`** should point to your Kibble instance's recent facts endpoint. The format is:
```
https://<your-kibble-domain>/api/v1/facts/recent
```

**`API_KEY`** is the Bearer token for API authentication. You can generate one from your Kibble instance's admin panel.

See the [Configuration Reference](#configuration-reference) section below for all available settings.

### Step 4: Upload Files to the ESP32-S3

1. In Thonny, make sure the ESP32-S3 is connected
2. Open `config.py` in Thonny (File > Open > This computer, navigate to the file)
3. Save it to the ESP32: **File > Save as...** > select **MicroPython device** > name it `config.py` > Save
4. Open `main.py` in Thonny
5. Save it to the ESP32: **File > Save as...** > select **MicroPython device** > name it `main.py` > Save
6. Press the **Stop/Restart** button (or Ctrl+D) to soft-reboot the ESP32

The board will immediately begin running. You should see status messages on the matrix:
- **"WiFi"** — Connecting to WiFi
- **"Load"** — Fetching facts from the API
- Then facts will begin scrolling

### Step 5: Verify via Serial Console

While the board is running, the Thonny REPL will show diagnostic output:

```
WiFi connected: ('192.168.1.100', '255.255.255.0', '192.168.1.1', '8.8.8.8')
Fetched 47 facts
```

If something goes wrong, error messages will appear here.

## Configuration Reference

All settings are in `config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `WIFI_SSID` | `"YOUR_WIFI_NETWORK"` | Your WiFi network name |
| `WIFI_PASSWORD` | `"YOUR_WIFI_PASSWORD"` | Your WiFi password |
| `API_URL` | `"YOUR_KIBBLE_URL"` | Full URL to your Kibble API's recent facts endpoint |
| `API_KEY` | `"YOUR_KIBBLE_API"` | API key (Bearer token) for authentication |
| `NEOPIXEL_PIN` | `16` | GPIO pin connected to the NeoPixel data line |
| `MATRIX_WIDTH` | `32` | Number of columns on the matrix |
| `MATRIX_HEIGHT` | `8` | Number of rows on the matrix |
| `NUM_LEDS` | `256` | Total number of LEDs (width x height) |
| `TEXT_COLOR` | `(255, 0, 0)` | RGB color tuple for the text (default: red) |
| `BRIGHTNESS` | `15` | Brightness level, 0-255 (keep low to reduce power draw) |
| `SCROLL_DELAY_MS` | `80` | Milliseconds between scroll frames (lower = faster) |
| `CHAR_SPACING` | `1` | Blank pixel columns between characters |
| `FONT_SIZE` | `"small"` | `"small"` (3x5 Tom Thumb) or `"large"` (5x8 Adafruit GFX) |
| `FACT_REFRESH_INTERVAL_MS` | `3600000` | How often to fetch new facts (default: 1 hour) |
| `WIFI_RETRY_DELAY_MS` | `5000` | Delay between WiFi connection retries |
| `WIFI_MAX_RETRIES` | `20` | Maximum WiFi connection attempts before giving up |
| `API_RETRY_DELAY_MS` | `10000` | Delay between API fetch retries |

### Color Examples

The `TEXT_COLOR` setting uses an RGB tuple `(Red, Green, Blue)` with values from 0-255:

| Color | Value |
|-------|-------|
| Red | `(255, 0, 0)` |
| Green | `(0, 255, 0)` |
| Blue | `(0, 0, 255)` |
| White | `(255, 255, 255)` |
| Yellow | `(255, 255, 0)` |
| Cyan | `(0, 255, 255)` |
| Purple | `(128, 0, 255)` |
| Orange | `(255, 128, 0)` |

### Font Options

Two font sizes are available:

- **`"small"`** — Tom Thumb 3x5 font. Compact and readable. Fits ~8 characters on screen at once. Best for longer text that you want to keep visible longer.
- **`"large"`** — Adafruit GFX 5x8 font. Uses the full height of the display. Fits ~5 characters on screen at once. Best for maximum readability at a distance.

## Kibble API

This board is designed to work with a self-hosted [Kibble](https://github.com/scottypate/kibble) instance. The board calls the following endpoint:

```
GET /api/v1/facts/recent
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
- Double-check `WIFI_SSID` and `WIFI_PASSWORD` in `config.py`
- Make sure the WiFi network is 2.4 GHz (ESP32-S3 does not support 5 GHz)
- Move the board closer to the WiFi router

### "NoAPI" stays on screen
- Verify `API_URL` points to your Kibble instance's `/api/v1/facts/recent` endpoint
- Verify `API_KEY` is correct
- Check that your Kibble instance is running and accessible from the board's network
- Check the Thonny serial console for detailed error messages

### Text looks garbled or offset
- Confirm your matrix uses a **vertical serpentine** wiring layout
- If your matrix uses a different layout (horizontal serpentine, progressive, etc.), the pixel mapping in `main.py` will need to be modified

### LEDs are too bright or too dim
- Adjust `BRIGHTNESS` in `config.py` (0-255, lower values recommended)
- At `BRIGHTNESS = 15`, power draw is very low and the display is comfortable to read indoors

### Board resets frequently
- This can happen if the power supply can't provide enough current
- Use a 5V supply rated for at least 3A
- Lower the `BRIGHTNESS` setting to reduce power draw

## Project Structure

```
kibble_board_prototype/
  config.py   — User configuration (WiFi, API, display settings)
  main.py     — Complete application (fonts, display, WiFi, API, scroll engine)
```

Both files must be uploaded to the root of the ESP32-S3's filesystem via Thonny.

## License

Font data used in this project:

- **5x8 font**: From the [Adafruit GFX Library](https://github.com/adafruit/Adafruit-GFX-Library) (BSD License)
- **3x5 font**: Tom Thumb font by Brian J. Swetland, Vassilii Khachaturov, with modifications by Robey Pointer (3-clause BSD License)
