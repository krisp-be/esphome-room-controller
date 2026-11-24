# Controller board (v2)

> **Status: in design.** The layout (KiCad files, Gerbers) is being finished and will be added
> to this folder. The connections and the pin map below are fixed: the ESPHome packages in
> [`esphome/`](../../esphome) are written for them.

One generic board for every room. It runs on 24 V, carries an Arduino Nano ESP32 running
ESPHome, and drives LED strips, fans, plain 24 V loads, sensors and relays. Whatever a room does
not use stays empty. **No mains voltage on the board:** a mains fan is switched by a separate
relay module, in the same enclosure.

## Blocks

```
24V IN ─┬─ fuse 2 A ×4 ── STRIP 1..4 (+24, GND, DATA)  ◄── 74AHCT125 (3.3→5 V) + 220 Ω ◄── ESP
        ├─ fuse 4 A ───── OUT 1..4 (+24, OUT)          ◄── logic-level MOSFET (+ flyback diode) ◄── ESP PWM
        ├─ step-down 5 V ── 74AHCT125, sensors, relay module, isolated converters
        ├─ step-down 9 V ── Nano ESP32 VIN
        └─ step-down 12 V ─ FAN 1/2 supply for computer fans

FAN 1/2:  ESP PWM ── 6N137 fast optocoupler ══ PWM, GNDiso  (own isolated 5 V per channel)
          12V, GND, TACH ── 1 kΩ + clamp ── ESP pulse counter
          GND bridge: open = isolated (mains EC fan), fitted = computer fan

IN 1..5:  V, GND, SIG ── 1 kΩ + clamp to 3.3 V ── ESP   (jumper per input: V = 3.3 V or 5 V)

I²C ──┬── MCP23017 (0x20) ── IO A header: A0..A7 (+ GND pins)
      │                    └─ IO B header: B0..B7 (+ GND pins); B3..B7 = 433 MHz receiver socket
      └── I2C terminal (3V3, GND, SDA, SCL), 4.7 kΩ pull-ups on the board
MODULES header: 5V, 5V, 3V3, GND (relay module, other modules)
```

## Connections

| Terminal | Pins | Use | Notes |
|---|---|---|---|
| 24V IN | +, − | 24 V power supply | e.g. Mean Well LRS-150-24 |
| STRIP 1..4 | +24, GND, DATA | addressable 24 V LED strips, or an [LED distribution board](../led-distribution-board) | 2 A fuse (5×20 mm) per output |
| OUT 1..4 | +24, OUT | plain 24 V loads: white LED strip (dimmable), solenoid, small fan | low side switched, shared 4 A fuse |
| FAN 1/2 PWM | PWM, GNDiso | PWM input of the fan | isolated; see GND bridge |
| FAN 1/2 | 12V, GND, TACH | power and speed signal of computer fans | |
| IN 1..5 | V, GND, SIG | presence (mmWave), PIR, buttons, any 3.3/5 V signal | supply jumper per input |
| I2C | 3V3, GND, SDA, SCL | I²C sensors (humidity, VOC, light, …) | |
| IO A / IO B | pin + GND pairs | door and drawer contacts, buttons, relay inputs | MCP23017, 3.3 V logic |
| 433 MHz socket | VT, D3, D2, D1, D0, 3V3, GND | 4-channel 433 MHz receiver module | for battery wall switches |
| MODULES | 5V, 5V, 3V3, GND | power for a relay module and other modules | |

### Fan channels
- **Mains EC fan with a PWM input** (e.g. Ruck EM..EC 02, 1–5 kHz, 5–10 V): connect PWM_In and its GND to
  `PWM` and `GNDiso`, leave the **GND bridge open**. The mains of the fan goes through a relay.
- **4-pin computer fan** (25 kHz): 12V, GND and TACH on the FAN terminal, the PWM wire on `PWM`,
  **fit the GND bridge**. Two fans in parallel: connect only one tach wire.

## Pin map (Arduino Nano ESP32)

ESPHome uses the GPIO numbers.

| Nano pin | GPIO | Function |
|---|---|---|
| D5, D4, D3, D2 | 8, 7, 6, 5 | STRIP 1, 2, 3, 4 data |
| D6, D7 | 9, 10 | FAN 1, 2 PWM (inverted by the optocoupler) |
| D8, D9 | 17, 18 | FAN 1, 2 TACH |
| D10, D11, D12, A0 | 21, 38, 47, 1 | OUT 1, 2, 3, 4 (MOSFET gates) |
| A3, A6, A7, D0, D1 | 4, 13, 14, 44, 43 | IN 1, 2, 3, 4, 5 |
| A4, A5 | 11, 12 | I²C SDA, SCL |
| A1 | 2 | MCP23017 interrupt (reserved) |
| D13 | 48 | status LED |
| A2 | 3 | not used (strapping pin) |

MCP23017 pins in ESPHome: A0..A7 = 0..7, B0..B7 = 8..15.
433 MHz receiver: D0 = B7 (15), D1 = B6 (14), D2 = B5 (13), D3 = B4 (12), VT = B3 (11).

## Limits
- ESP32-S3: 4 RMT channels, so **4 data lines** at most. One line can drive many strips in
  series; split it into zones in ESPHome with `partition`.
- 8 PWM channels: 2 fans + 4 MOSFET outputs = 6 used.
- Total current: limited by the power supply (LRS-150-24: 6.5 A).
