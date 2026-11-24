# For new owners

You live in a house where some rooms (for example the laundry room, the walk-in closet or the
bathroom) have lights and fans controlled by these boards. This page explains what they are and
what to do when something does not work. No programming knowledge is needed for most of it.

## What is installed

In each of these rooms there is a closed box with a plug (often in a cupboard or a technical
room). It contains a 24 V power supply, a green controller board with a small Arduino Nano ESP32,
and sometimes a relay module for a fan. Inside the cabinets there may be smaller boards with 8
terminals: LED distribution boards. Every board has the address of this repository printed on it.

The boards work on their own. They do **not** need Wi-Fi, Home Assistant, an app or an
internet connection for their normal work: lights, buttons, sensors and fans keep working.
Wi-Fi is only used for the settings page and for updates.

## The settings page

Every box has a web page with all lights, fans, sensors and settings (speeds, timers, limits):

- When the box is on your Wi-Fi: `http://<room-name>.local`, for example
  `http://laundry-room.local`, or the IP address shown in your router.
- When it is not (new router, new network name): the box opens its own Wi-Fi network called
  `<room-name>-setup`. Connect to it with a phone; a page opens where you choose your network and
  enter its password. Ask the previous owner for the password of that setup network.

## Troubleshooting

| Problem | Check |
|---|---|
| Nothing works in the room | Is the box plugged in and the socket live? Is the LED of the power supply on? Unplug the box for 10 seconds and plug it in again. |
| One LED strip is dark, the others work | On a distribution board: is the strip still in its terminal, and is the "bridge=empty" jumper **not** fitted on its port? A pull-out shelf must be pushed in fully. Unplug for a minute: the PTC fuse of that port resets by itself. On the controller board: check the glass fuse (5×20 mm, 2 A) of that STRIP output. |
| All strips after a certain point are dark | The data passes from strip to strip. The first dark strip, or the one before it, has a broken data wire or is damaged. On a distribution board, fitting the jumper on that port (after removing its strip) lets the rest work again. |
| Wrong colours | The colour settings are on the settings page; a strip may also have a damaged pixel (only from that pixel onwards is wrong). |
| A light does not react to its wall switch | Replace the battery of the wall switch (often a 12 V type 27A or 23A). If that does not help, pair it again: see the next section. |
| A light goes off while someone is in the room | Raise the "off after no presence/motion" time on the settings page. |
| The fan does not run | Check the settings page: is the fan on? Is the "mains" switch of the fan on? Check the fuse of the relay/fan line. A mains fan has its own maintenance: clean it. |
| The fan is too loud or too quiet | Speeds are on the settings page. |
| The settings page cannot be reached | See "The settings page" above. The lights keep working without it. |

### Pairing a wall switch again
Open the box. On the controller board sits a small 433 MHz receiver module with a button. Hold
that button for about 2 seconds until its LED lights, then press the button on the wall switch.
The LED blinks: done.

## Replacing parts

All parts are common and through-hole: a board can be repaired with a soldering iron, or a new
one ordered from the files in [`hardware/`](../hardware). The Arduino Nano ESP32 sits in a socket
and can be pulled out and replaced; the new one must be programmed with the room's configuration
(see [`esphome/`](../esphome)). The previous owner may have left that configuration file; if not,
the example for the room in `esphome/examples` is a good starting point.

## Safety

The controller and distribution boards only carry 24 V. A relay module or a fan can carry
**mains voltage (230 V)**: unplug the box before opening it, and leave work on mains wiring to a
qualified electrician.
