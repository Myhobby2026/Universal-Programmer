# Hardware and safety

Teensy 4.1 GPIO is 3.3 V logic. Do not connect 5 V target signals directly,
and do not power a target from the board unless an external, current-limited
power circuit and voltage monitoring have been designed and validated.

The shipped firmware supports protocol discovery only. SWD, JTAG, NAND, SPI
flash, I²C EEPROM, and UART target programming require a documented adapter,
appropriate level shifting, target-specific timing, and a tested algorithm.
The application therefore keeps those operations disabled for the included
profile-only catalog entries.
