/*
 * Universal Programmer Studio controller firmware.
 *
 * This intentionally exposes only capabilities implemented in this sketch:
 * protocol discovery and safe GPIO configuration. Target programming is not
 * reported as available until a validated adapter/algorithm is added.
 */
#include <Arduino.h>

static const uint8_t MAGIC[4] = {'U', 'P', 'S', '1'};
static const uint8_t VERSION = 1;
static const uint16_t MAX_PAYLOAD = 4096;

uint16_t crc16(const uint8_t *data, size_t length) {
  uint16_t crc = 0xFFFF;
  while (length--) {
    crc ^= (uint16_t)(*data++) << 8;
    for (uint8_t bit = 0; bit < 8; ++bit)
      crc = (crc & 0x8000) ? (crc << 1) ^ 0x1021 : crc << 1;
  }
  return crc;
}

void sendFrame(uint16_t sequence, uint8_t command, uint8_t status, const uint8_t *payload, uint16_t length) {
  if (length > MAX_PAYLOAD) return;
  // The desktop protocol header is packed as magic, version, sequence, command, status, length.
  // Build its exact 11-byte representation without relying on compiler packing.
  uint8_t packet[11 + MAX_PAYLOAD + 2];
  memcpy(packet, MAGIC, 4); packet[4] = VERSION;
  packet[5] = sequence & 0xff; packet[6] = sequence >> 8;
  packet[7] = command; packet[8] = status;
  packet[9] = length & 0xff; packet[10] = length >> 8;
  if (length && payload) memcpy(packet + 11, payload, length);
  uint16_t checksum = crc16(packet, 11 + length);
  packet[11 + length] = checksum & 0xff; packet[12 + length] = checksum >> 8;
  Serial.write(packet, 13 + length);
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  // A production adapter may add target engines here. Until then, the board
  // only answers discovery and never fabricates target-identification results.
  if (Serial.available() < 11) return;
  uint8_t header[11];
  Serial.readBytes(header, sizeof(header));
  if (memcmp(header, MAGIC, 4) != 0 || header[4] != VERSION) return;
  uint16_t sequence = header[5] | ((uint16_t)header[6] << 8);
  uint8_t command = header[7];
  uint16_t length = header[9] | ((uint16_t)header[10] << 8);
  if (length > MAX_PAYLOAD) return;
  uint8_t payload[MAX_PAYLOAD];
  if (Serial.readBytes(payload, length) != length) return;
  uint8_t crcBytes[2];
  if (Serial.readBytes(crcBytes, 2) != 2) return;
  uint8_t receivedPacket[11 + MAX_PAYLOAD];
  memcpy(receivedPacket, header, 11);
  if (length) memcpy(receivedPacket + 11, payload, length);
  uint16_t receivedCrc = crcBytes[0] | ((uint16_t)crcBytes[1] << 8);
  if (crc16(receivedPacket, 11 + length) != receivedCrc) return;
  if (command == 2) {
    const char info[] = "firmware=0.1.0;board=Teensy 4.1;capabilities=gpio,protocol-discovery";
    sendFrame(sequence, command, 1, (const uint8_t*)info, sizeof(info) - 1);
  } else if (command == 1) {
    sendFrame(sequence, command, 1, nullptr, 0);
  } else {
    sendFrame(sequence, command, 5, nullptr, 0); // NOT_SUPPORTED
  }
}
