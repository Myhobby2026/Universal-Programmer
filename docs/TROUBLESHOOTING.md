# Troubleshooting

- **PySide6 is required**: activate the virtual environment and install
  `requirements.txt`.
- **Teensy: Not connected**: check the USB cable, driver enumeration, and the
  selected COM port. The application does not simulate a connection.
- **Target operation unavailable**: confirm that firmware capabilities and the
  selected profile's support level both permit the requested operation. A
  profile-only entry is intentionally blocked.
- **Serial timeout**: close other applications holding the COM port and check
  that the firmware protocol version matches the desktop protocol.
