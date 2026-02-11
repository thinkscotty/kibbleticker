# Kibble Board Configuration
# Edit these values to match your setup

# WiFi Configuration
WIFI_SSID = "YOUR_WIFI_NETWORK"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# API Configuration
API_BASE_URL = "YOUR_KIBBLE_URL"  # Base URL only, e.g. "https://your-kibble-instance.com"
API_KEY = "YOUR_KIBBLE_API"

# Hardware Configuration
NEOPIXEL_PIN = 16
MATRIX_WIDTH = 32
MATRIX_HEIGHT = 8
NUM_LEDS = 256

# I2C Configuration (for CardKB keyboard and SSD1306 OLED)
I2C_SDA_PIN = 8
I2C_SCL_PIN = 9

# Display Configuration
SCROLL_DELAY_MS = 80
CHAR_SPACING = 1

# Timing Configuration
FACT_REFRESH_INTERVAL_MS = 3600000
WIFI_RETRY_DELAY_MS = 5000
WIFI_MAX_RETRIES = 20
API_RETRY_DELAY_MS = 10000
