# USB protocol

The desktop and Teensy use little-endian, version 1 frames:

| Offset | Size | Field |
|---:|---:|---|
| 0 | 4 | ASCII `UPS1` magic |
| 4 | 1 | protocol version (`1`) |
| 5 | 2 | request sequence |
| 7 | 1 | command |
| 8 | 1 | response status (`0` for request) |
| 9 | 2 | payload length |
| 11 | N | payload |
| 11+N | 2 | CRC-16/CCITT-FALSE over header and payload |

The maximum payload is 4096 bytes. The initial firmware implements `PING` and
`GET_INFO`, and reports only GPIO/protocol-discovery capabilities. A serial
connection alone does not imply support for a target programming algorithm.
