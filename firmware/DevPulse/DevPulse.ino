#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <ArduinoJson.h>
#include <math.h>
#include "board_config.h"

#if !BOARD_CONFIGURED
#error "Confirm display controller, pins and geometry in board_config.h first."
#endif

Adafruit_ST7789 lcd(LCD_CS, LCD_DC, LCD_RST);
char frame[256];
size_t used = 0;
bool overflow = false;
bool online = false;
uint32_t lastPacket = 0;
const uint16_t bg = 0x0842;
const uint16_t accent = 0x07FF;

void message(const char* text) {
  lcd.fillScreen(bg);
  lcd.setCursor(8, 8);
  lcd.setTextSize(2);
  lcd.setTextColor(accent, bg);
  lcd.println("DevPulse USB");
  lcd.setTextSize(1);
  lcd.setTextColor(ST77XX_WHITE, bg);
  lcd.setCursor(8, 48);
  lcd.print(text);
}

bool metric(JsonVariantConst value, float upper) {
  if (!value.is<float>()) return false;
  float n = value.as<float>();
  return isfinite(n) && n >= 0 && n <= upper;
}

void bar(int y, const char* label, float percent) {
  int width = lcd.width() - 100;
  lcd.setCursor(8, y);
  lcd.printf("%s %3.0f%%", label, percent);
  lcd.drawRect(88, y - 1, width, 10, accent);
  int fill = (int)((width - 2) * percent / 100.0f);
  if (fill > 0) lcd.fillRect(89, y, fill, 8, percent >= 90 ? ST77XX_RED : accent);
}

void receiveFrame() {
  JsonDocument doc;
  if (deserializeJson(doc, frame, used, DeserializationOption::NestingLimit(2))) return;
  if (!doc["v"].is<int>() || doc["v"].as<int>() != 1) return;
  if (!metric(doc["cpu"], 100) || !metric(doc["ram"], 100) ||
      !metric(doc["disk"], 100) || !metric(doc["rx"], 1e12f) || !metric(doc["tx"], 1e12f)) return;
  const char* alert = doc["alert"] | "";
  if (strcmp(alert, "OK") && strcmp(alert, "CPU") && strcmp(alert, "RAM") && strcmp(alert, "CPU+RAM")) return;
  online = true;
  lastPacket = millis();
  lcd.fillScreen(bg);
  lcd.setTextColor(accent, bg);
  lcd.setTextSize(2);
  lcd.setCursor(8, 6);
  lcd.print("DevPulse USB");
  lcd.setTextSize(1);
  lcd.setTextColor(ST77XX_WHITE, bg);
  bar(38, "CPU", doc["cpu"]);
  bar(58, "RAM", doc["ram"]);
  bar(78, "DSK", doc["disk"]);
  lcd.setCursor(8, 101);
  lcd.printf("RX %.1f  TX %.1f KiB/s", doc["rx"].as<float>(), doc["tx"].as<float>());
  lcd.setCursor(8, 123);
  lcd.setTextColor(strcmp(alert, "OK") ? ST77XX_RED : accent, bg);
  lcd.printf("STATUS %s", alert);
  lcd.setTextColor(ST77XX_WHITE, bg);
  lcd.setCursor(8, 146);
  lcd.print("brunnodev | local telemetry");
}

void setup() {
  Serial.begin(115200);
  SPI.begin(LCD_SCLK, -1, LCD_MOSI, LCD_CS);
  lcd.init(LCD_WIDTH, LCD_HEIGHT);
  lcd.setRotation(LCD_ROTATION);
  if (LCD_BL >= 0) {
    pinMode(LCD_BL, OUTPUT);
    digitalWrite(LCD_BL, LCD_BL_ACTIVE);
  }
  message("Waiting for PC agent...");
}

void loop() {
  int budget = 512;
  while (Serial.available() && budget-- > 0) {
    char c = Serial.read();
    if (c == '\n') {
      if (!overflow && used) receiveFrame();
      used = 0;
      overflow = false;
    } else if (!overflow) {
      if (used < sizeof(frame) - 1) frame[used++] = c;
      else overflow = true;
    }
  }
  if (online && (uint32_t)(millis() - lastPacket) > 5000) {
    online = false;
    message("PC disconnected / stale data");
  }
  delay(1);
}
