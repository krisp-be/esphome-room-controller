# ESPHome firmware

All logic runs on the board itself: no Home Assistant, cloud or app is needed. Settings such as
fan speeds and timers are numbers on the board's own web page. Home Assistant can still be added
later: the board shows up there automatically.

## Structure

```
esphome/
├── common/board.yaml       the board itself: ESP32, Wi-Fi, web page, I²C, I/O expander, status LED
├── components/             one file per kind of output or input, reusable with variables
└── examples/               complete configurations for real rooms + secrets.yaml.example
```

A room configuration is short: the board, plus one line per thing that is connected, plus the
behaviour of that room. The pin numbers are in the component files, so a room config never
contains GPIO numbers.

```yaml
substitutions:
  name: my-room                 # host name: http://my-room.local
  friendly_name: My room

packages:
  board: !include ../common/board.yaml
  strip: !include
    file: ../components/led-strip.yaml
    vars: {channel: 1, id: main_strip, name: LED strip, num_leds: 30}
```

## Components

| File | Hardware | Variables (*optional*) |
|---|---|---|
| `led-strip.yaml` | STRIP 1..4: addressable LED strip | `channel` 1–4, `id`, `name`, `num_leds`, *`chipset`* (WS2812), *`rgb_order`* (GRB), *`is_rgbw`*, *`internal`*, *`restore_mode`* |
| `fan.yaml` | FAN 1/2: PWM fan | `channel` 1–2, `id`, `name`, *`frequency`* (25000Hz; 1000Hz for mains EC fans), *`min_power`*, *`restore_mode`* |
| `fan-tach.yaml` | FAN 1/2 TACH: speed in rpm | `channel`, `id`, `name`, *`pulses_per_revolution`* (2) |
| `dimmer.yaml` | OUT 1..4: dimmable 24 V load | `channel` 1–4, `id`, `name`, *`frequency`*, *`restore_mode`* |
| `switched-output.yaml` | OUT 1..4: on/off 24 V load | `channel` 1–4, `id`, `name`, *`restore_mode`* |
| `input.yaml` | IN 1..5: sensor or contact | `channel` 1–5, `id`, `name`, *`device_class`*, *`pullup`*, *`inverted`*, *`delayed_off`* |
| `expander-input.yaml` | IO A0..B2: contact or button | `pin` (e.g. `A3`), `id`, `name`, *`device_class`* (door), *`pullup`*, *`inverted`* |
| `expander-output.yaml` | IO A0..B2: relay module input | `pin`, `id`, `name`, *`inverted`*, *`restore_mode`* |
| `door-light.yaml` | IO A0..B2: door contact that switches a light | `pin`, `id`, `name`, `light`, *`timeout`* (15min) |
| `rf433.yaml` | 433 MHz receiver socket | none; creates `remote_a` .. `remote_d` |

Each file starts with a comment that explains the wiring and gives an example. Add behaviour to
a component with `!extend`, for example:

```yaml
binary_sensor:
  - id: !extend remote_a
    on_press:
      - light.toggle: main_strip
```

Sensors on the I²C terminal (humidity, VOC, light, …) use the normal ESPHome platforms
(`sht4x`, `sgp4x`, `bh1750`, …): the I²C bus is already set up by `board.yaml`.

## Examples

| File | Room |
|---|---|
| [`minimal.yaml`](examples/minimal.yaml) | starting point: board + one strip |
| [`laundry-room.yaml`](examples/laundry-room.yaml) | printer cabinet lights, nail table light, extraction fan that follows the light with run-on, VOC boost, presence and motion auto-off, 433 MHz wall switch |
| [`walk-in-closet.yaml`](examples/walk-in-closet.yaml) | one data line through 6 wardrobe columns with door contacts, cove light on presence, mirror light with a button, humidity-controlled computer fans in the shoe cabinet |
| [`bathroom.yaml`](examples/bathroom.yaml) | two extraction fans on a self-adjusting humidity baseline, button boost, mirror light on presence |

## Installing

You need [ESPHome](https://esphome.io/guides/installing_esphome) 2025.7 or newer (for the
`${ ... }` expressions in the component files), on a computer or as the ESPHome add-on of
Home Assistant.

1. Copy `examples/secrets.yaml.example` to `secrets.yaml` (next to the room configs) and fill it in.
   `secrets.yaml` is ignored by git.
2. Copy an example (or `minimal.yaml`) and adapt it to what is connected.
3. Check it: `esphome config my-room.yaml`.
4. **First time, over USB:** the Nano ESP32 must be in its ROM bootloader. Connect pin **B1** to
   **GND** with a jumper wire, press the reset button, remove the wire. Then
   `esphome run my-room.yaml` and choose the USB port.
   (This replaces the Arduino bootloader; Arduino's documentation explains how to restore it.)
5. **After that, over Wi-Fi:** `esphome run my-room.yaml` and choose the network address.
   The board does not need to be removed from its enclosure.

The web page of the board is at `http://<name>.local` (or its IP address). It shows every
light, fan and sensor, and the settings.

### When the Wi-Fi network changes

If the board cannot reach its network, it opens its own access point `<name>-setup` (password:
`fallback_ap_password` from `secrets.yaml`). Connect to it with a phone; a page opens where you
choose the new network. All lights and automations keep working without Wi-Fi in the meantime.
