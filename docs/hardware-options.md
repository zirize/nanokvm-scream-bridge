# Hardware options for the phone side

Why the bridge looks the way it does, and what to use when moving it to other hardware.

## Why Scream instead of USB-to-USB

The first idea was a box that is a USB speaker to one host and a USB microphone to another.
That needs **two USB device controllers**. Pi 4 has one (only the USB-C port can be a gadget;
the USB-A ports are host-only on the VL805). NanoKVM has one. Options that do have two:
two RP2040 Picos linked by I2S, or an STM32 with OTG_FS + OTG_HS. Only that route can be
bit-perfect (both sides async UAC, the bridge's clock as master).
Using Scream for the PC side needs one device controller and reuses existing Scream receivers on
the PC. Trade-off: no clock feedback from the receiver, so drift is absorbed by the receiver
(trim/pad or resample) instead of being avoided.

## Pi 4 (planned permanent host)

- Gadget only on the USB-C port: `dtoverlay=dwc2,dr_mode=peripheral`. Raspberry Pi OS kernels
  are expected to ship `f_uac2` (not yet checked on this Pi 4: `modinfo usb_f_uac2`).
- That port is also the power input, and the 5 V rail is shared with GPIO 5 V: do **not** power
  through GPIO while a phone also supplies VBUS. A phone cannot power a Pi 4 reliably.
- Use a **USB-C power/data splitter** (`USB-C/PWR Splitter`, 8086 Consultancy design, ports
  printed `PWR` / `USB` / `RPI4`): Pi PSU -> `PWR`, Pi -> `RPI4`, phone -> `USB` (data only).

## Other hosts at a glance

Only the NanoKVM is built and measured. The rest is what the hardware allows; nothing below
the first row has been run yet.

| Host | Gadget port | Also the power input? | Network to the PC | Phone-side wiring | Software |
|---|---|---|---|---|---|
| NanoKVM (done) | USB-C | yes | wired | plain C-to-C cable | `nanokvm/` (UAC1, kernel 5.10) |
| Pi 4 (planned) | USB-C | **yes** | wired | splitter (+ OTG 2-in-1 to charge the phone) | Linux configfs gadget + `arecord` + `uac2scream.py`, as on the NanoKVM |
| Pi Zero 2 W | micro-USB `USB` (separate `PWR IN`) | no, separate port | Wi-Fi only | OTG cable/adapter | same Linux approach |
| Pico W / Pico 2 W | micro-USB | yes, but a phone can power it | Wi-Fi only (2.4 GHz) | OTG cable/adapter; OTG 2-in-1 to charge the phone | **new firmware** (TinyUSB UAC2 + lwIP UDP), not written |

- Linux boards reuse `uac2scream.py` unchanged; only the gadget setup (`S04usbaudio` is
  NanoKVM-specific: it relies on the firmware's `g0` gadget and `S03usbdev`) has to be rewritten.
- Pi Zero 2 W: the data port's VBUS is believed to be tied to the board's 5 V rail like on the
  Pi 4, so a phone may back-feed it; not checked.

## Pico W (RP2040 + CYW43439)

- The RP2040 has one USB 1.1 full-speed device controller: enough for 48 kHz / 16 bit / stereo
  (192 bytes per 1 ms frame). TinyUSB ships UAC2 speaker examples, including one with an
  asynchronous feedback endpoint, so the Pico can pace the phone to its own crystal.
- Scream over Wi-Fi is about 1.5 Mbit/s (1157-byte packets, 166.7 per second); lwIP UDP on the
  CYW43439 handles that, but Wi-Fi jitter has to be absorbed by the receiver's buffer.
- Power: the phone, as USB host, supplies VBUS; a Pico W draws tens of mA plus Wi-Fi (not
  measured), so no external supply or splitter is needed. The phone's battery pays for it; an
  OTG 2-in-1 adapter lets a charger feed the phone at the same time.
- Nothing here exists yet: it needs its own firmware, not the scripts in this repo.

## Splitter and adapter findings (2026-10-17)

- WeAct Studio "USB Power Splitter" (AliExpress 1005011968467720): schematic in the listing
  shows the data port J3 carries **D+/D- and GND only, no CC**. A phone will not switch to host
  mode on a plain C-to-C cable into it. Works with a PC via USB-A-to-C, or with a phone through
  an OTG adapter that provides the CC pull-down.
- "OTG 2-in-1" adapters (USB-C male -> USB-A female OTG + USB-C PD charge input), e.g.
  AliExpress 1005006136587634: phone
  charges and stays USB host at the same time (buyer review confirms charge + OTG). Whether the
  USB-A port outputs 5 V while charging is not documented.
- Combined for a Pi 4: phone <- OTG 2-in-1 (charger on its PD port) <- A-to-C cable <- splitter
  `USB`; Pi PSU -> splitter `PWR`; splitter `RPI4` -> Pi. The adapter supplies the CC the
  splitter lacks; the splitter keeps the phone's 5 V off the Pi.
- NanoKVM Lite (LicheeRV Nano based): powering through header pins is undocumented and the
  VSYS/VBUS power path was not verified; it runs fine on phone or PC USB power (draw not measured; estimated 0.2-0.3 A).
