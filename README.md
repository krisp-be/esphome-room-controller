# ESPHome room controller

Open hardware and firmware to light and ventilate the rooms of a house: LED strips in cabinets
and wardrobes, extraction and cabinet fans, presence sensors, door contacts and battery wall
switches. One board per room, programmed with [ESPHome](https://esphome.io). Everything runs on
the board itself, without Home Assistant, a cloud service or an app.

**Do you live in a house with these boards?** Start with [docs/for-new-owners.md](docs/for-new-owners.md).

## What it can do

| | Per controller board |
|---|---|
| Addressable LED strips (24 V) | 4 data lines; each line can drive many strips, every strip or segment separately |
| Fans | 2 PWM channels with speed feedback: mains EC fans (isolated PWM, 1–5 kHz) or 12 V computer fans (25 kHz) |
| Plain 24 V loads | 4 MOSFET outputs, dimmable: white LED strips, solenoids, small fans |
| Sensors | 5 fast inputs (3.3 or 5 V): presence (mmWave), motion (PIR), buttons |
| Contacts and relays | 11 pins on an I/O expander: door and drawer contacts, relay modules |
| Wireless switches | socket for a 4-channel 433 MHz receiver (battery wall switches, no hub) |
| I²C | humidity, VOC, light and other sensors |

An optional **LED distribution board** splits one data line into 8 ports, with power in
parallel and data in series, so a whole wardrobe can be wired neatly.

```
             24 V power supply
                    │
   ┌────────────────┴────────────────┐            ┌──────────────────────────┐
   │        CONTROLLER BOARD         │  STRIP 1   │  LED DISTRIBUTION BOARD  │──► 8 strips
   │  Nano ESP32 + ESPHome           ├───────────►│  (power ∥, data in series)│
   │                                 │  STRIP 2-4 └──────────────────────────┘
   │                                 ├──► strips
   │                                 ├──► fans (PWM + tach), relay ──► mains fan
   │                                 ├──► 24 V loads
   │                                 ◄─── sensors, door contacts, 433 MHz switches
   └─────────────────────────────────┘
```

## Repository

| Folder | Contents |
|---|---|
| [`hardware/`](hardware) | board designs, Gerbers to order them, bills of materials, generator scripts |
| [`esphome/`](esphome) | the firmware: core config, reusable components, example rooms |
| [`docs/`](docs) | wiring guide, troubleshooting, notes for new owners |

## Getting started

1. Order and assemble the boards: [hardware/](hardware).
2. Wire the room: [docs/wiring.md](docs/wiring.md).
3. Write the configuration for the room, starting from an example, and flash it:
   [esphome/](esphome).

## Status

| Part | Status |
|---|---|
| LED distribution board v1 | design finished, ready to order |
| Controller board v2 | connections and pin map fixed, layout in progress |
| ESPHome components and examples | validated and compiled with ESPHome 2025.7 |

## License

[MIT](LICENSE): use, change and share freely, also commercially, at your own risk.
These boards switch 24 V and drive relays that may switch mains voltage: mains wiring must be
done by a qualified person and follow local regulations.
