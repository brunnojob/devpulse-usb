#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <ArduinoJson.h>
#include <SPI.h>
#include <math.h>

#include "LineFramer.h"
#include "board_config.h"

#if !BOARD_CONFIGURED
#error "Confirm display controller, pins and geometry in board_config.h first."
#endif
#if LCD_MOSI < 0 || LCD_SCLK < 0 || LCD_DC < 0
#error "Configure MOSI, SCLK and DC using your board schematic."
#endif

namespace {
constexpr uint32_t kBaud = 115200;
constexpr uint32_t kStaleAfterMs = 5000;
constexpr int kReadBudget = 512;
constexpr uint16_t kBackground = 0x10C3;
constexpr uint16_t kAccent = 0xFBA9;
constexpr uint16_t kText = 0xE73C;

Adafruit_ST7789 display(LCD_CS, LCD_DC, LCD_RST);
LineFramer<256> framer;
bool online = false;
uint32_t lastPacket = 0;

void drawChrome() {
  display.fillScreen(kBackground);
  display.setTextSize(2);
  display.setTextColor(kAccent, kBackground);
  display.setCursor(8, 6);
  display.print("DevPulse USB");
  display.drawFastHLine(8, 27, display.width() - 16, kAccent);
  display.setTextSize(1);
  display.setTextColor(kText, kBackground);
  display.setCursor(8, 146);
  display.print("brunnodev / local telemetry");
}

void message(const char* text) {
  drawChrome();
  display.setCursor(8, 48);
  display.print(text);
}

bool validMetric(JsonVariantConst value, float upper) {
  if (!value.is<float>()) return false;
  const float number = value.as<float>();
  return isfinite(number) && number >= 0 && number <= upper;
}

bool validAlert(const char* alert) {
  return !strcmp(alert, "OK") || !strcmp(alert, "CPU") ||
         !strcmp(alert, "RAM") || !strcmp(alert, "CPU+RAM");
}

void drawBar(int y, const char* label, float percent) {
  const int width = display.width() - 100;
  display.setCursor(8, y);
  display.printf("%s %3.0f%%", label, percent);
  display.drawRect(88, y - 1, width, 10, kAccent);
  const int fill = static_cast<int>((width - 2) * percent / 100.0f);
  if (fill > 0) {
    display.fillRect(89, y, fill, 8, percent >= 90 ? ST77XX_RED : kAccent);
  }
}

void formatRate(float value, char* target, size_t capacity) {
  const char* units[] = {"K", "M", "G", "T", "P"};
  size_t unit = 0;
  while (value >= 1024 && unit < 4) {
    value /= 1024;
    ++unit;
  }
  snprintf(target, capacity, "%.1f%s", value, units[unit]);
}

void receiveFrame(const char* frame, size_t length) {
  JsonDocument doc;
  if (deserializeJson(doc, frame, length, DeserializationOption::NestingLimit(2))) return;
  if (!doc["v"].is<int>() || doc["v"].as<int>() != 1) return;
  if (!validMetric(doc["cpu"], 100) || !validMetric(doc["ram"], 100) ||
      !validMetric(doc["disk"], 100) || !validMetric(doc["rx"], 1e12f) ||
      !validMetric(doc["tx"], 1e12f)) return;
  const char* alert = doc["alert"] | "";
  if (!validAlert(alert)) return;

  lastPacket = millis();
  if (!online) drawChrome();
  online = true;
  display.fillRect(0, 30, display.width(), 107, kBackground);
  display.setTextColor(kText, kBackground);
  display.setTextSize(1);
  drawBar(38, "CPU", doc["cpu"]);
  drawBar(58, "RAM", doc["ram"]);
  drawBar(78, "DSK", doc["disk"]);

  char rx[16], tx[16];
  formatRate(doc["rx"], rx, sizeof(rx));
  formatRate(doc["tx"], tx, sizeof(tx));
  display.setCursor(8, 101);
  display.printf("RX %s  TX %s iB/s", rx, tx);
  display.setCursor(8, 123);
  display.setTextColor(strcmp(alert, "OK") ? ST77XX_RED : kAccent, kBackground);
  display.printf("STATUS %s", alert);
}
}  // namespace

void setup() {
  Serial.begin(kBaud);
  SPI.begin(LCD_SCLK, -1, LCD_MOSI, LCD_CS);
  display.init(LCD_WIDTH, LCD_HEIGHT);
  display.setRotation(LCD_ROTATION);
  display.setTextWrap(false);
  if (LCD_BL >= 0) {
    pinMode(LCD_BL, OUTPUT);
    digitalWrite(LCD_BL, LCD_BL_ACTIVE);
  }
  message("Waiting for PC agent...");
}

void loop() {
  int budget = kReadBudget;
  while (Serial.available() && budget-- > 0) {
    const char byte = static_cast<char>(Serial.read());
    if (framer.push(byte) == LineFramer<256>::Result::Ready) {
      receiveFrame(framer.data(), framer.size());
    }
  }
  if (online && static_cast<uint32_t>(millis() - lastPacket) > kStaleAfterMs) {
    online = false;
    message("PC disconnected / stale data");
  }
  delay(1);
}
