# Wiring guide

## Power

- One 24 V power supply per controller board, sized for all strips and loads together, with
  margin (e.g. Mean Well LRS-150-24: 150 W, 6.5 A).
- Put the power supply, the controller board and any relay module in **one closed enclosure**,
  away from steam and out of an air duct. Give the enclosure a mains cord with a plug, so the whole
  thing is an appliance and can be unplugged.
- Thick wire (1.5 mm²) from the power supply to 24V IN of the controller board and of every LED
  distribution board. Chain the data between boards, not the power.

## LED strips

- **24 V strips only.** 24 V needs less current than 5 or 12 V, so there is less voltage drop
  along a long strip.
- **Pixels, not LEDs:** on most 24 V strips one driver IC controls a group of 3 or 6 LEDs. In
  ESPHome, `num_leds` is the number of ICs. Check "pixels per metre" on the product page.
- **Chipset and colour order** differ per strip. Start with the values from the example, then
  set the strip to pure red on the web page: if it shows green, swap the order (`GRB` ↔ `RGB`).
  RGBW strips (WS2814, SK6812) need `is_rgbw: "true"` and usually `chipset: SK6812`.
- **Data cable:** keep the wire from the board to the first pixel short (a few metres at most).
  Each strip regenerates the signal, so a long chain is fine as long as each hop is short.
- **Several strips on one output:** connect them in series (DO of one to DI of the next), or use
  an LED distribution board. In ESPHome, split the line into zones with `partition`.
- **Pull-out parts** (shelves with pogo or magnetic connectors) at the end of a chain, or on their
  own output: a removed part breaks the data for everything after it.
- **Feed power in again** on long runs: connect +24 V and GND at both ends of a long strip.

## Fans

- **Mains EC fan with a PWM input** (e.g. Ruck EM..EC 02): mains through a relay module (relay
  input on an IO pin), PWM_In and its GND on `PWM` / `GNDiso`, **GND bridge open**. The relay
  switches the fan off completely; the PWM sets the speed.
- **4-pin computer fans:** 12V, GND, TACH and PWM to the FAN terminals, **GND bridge fitted**,
  25 kHz. Several fans in parallel are fine (watch the 12 V current); connect only one tach wire.
- **3-pin or plain 24 V fans:** on a MOSFET output (OUT 1..4) as a dimmer or a switch.

## Sensors

| Sensor | Where | Connection |
|---|---|---|
| LD2410C mmWave presence | IN 1..5 | V = 5 V, OUT pin to SIG. Detects people who sit still (a PIR does not). |
| PIR (e.g. AM312) | IN 1..5 | V = 3.3 V |
| Push button, switch | IN 1..5 or IO pin | between SIG/pin and GND; `pullup: "true"`, `inverted: "true"` on IN |
| Door/drawer reed contact | IO pin | between the pin and the GND pin next to it |
| Humidity (SHT4x), VOC (SGP40/41) | I2C | 3V3, GND, SDA, SCL; keep the cable under about 1 m |

The fast inputs accept 3.3 V and 5 V signals: the board clamps them for the ESP32.

## Relay modules

Use a module that switches on a **high** input and works with **3.3 V** logic (many 5 V modules
have a "high/low trigger" jumper: choose high). Power it from the 5V/GND pins of the MODULES header
and connect its inputs to IO pins. Mains wiring of the relay: by a qualified person.

## 433 MHz wall switches

A battery wall switch (the transmitter from a remote control set, built into a wall plate) and the
matching 4-channel receiver in the socket on the board. Pair each button once (see
`esphome/components/rf433.yaml`). Range through one or two walls is fine; the receiver antenna
must not lie flat against the power supply.
