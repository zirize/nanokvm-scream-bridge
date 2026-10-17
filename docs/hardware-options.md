# Hardware options for the phone side

Why the bridge looks the way it does, and what to use when moving it to other hardware.

## Why Scream instead of USB-to-USB

The first idea was a box that is a USB speaker to one host and a USB microphone to another.
That needs **two USB device controllers**. Pi 4 has one (only the USB-C port can be a gadget;
the USB-A ports are host-only on the VL805). NanoKVM has one. Options that do have two:
two RP2040 Picos linked by I2S, or an STM32 with OTG_FS + OTG_HS. Only that route can be
bit-perfect (both sides async UAC, the bridge's clock as master).
Using Scream for the PC side needs one device controller and reuses existing Scream receivers
on the PC. Trade-off: no clock feedback from the receiver, so
drift is absorbed by the receiver (trim/pad or resample) instead of being avoided.

## Pi 4 (planned permanent host)

- Gadget only on the USB-C port: `dtoverlay=dwc2,dr_mode=peripheral`. Raspberry Pi OS kernels
  are expected to ship `f_uac2` (not yet checked on this Pi 4: `modinfo usb_f_uac2`).
- That port is also the power input, and the 5 V rail is shared with GPIO 5 V: do **not** power
  through GPIO while a phone also supplies VBUS. A phone cannot power a Pi 4 reliably.
- Use a **USB-C power/data splitter** (`USB-C/PWR Splitter`, 8086 Consultancy design, ports
  printed `PWR` / `USB` / `RPI4`): Pi PSU -> `PWR`, Pi -> `RPI4`, phone -> `USB` (data only).

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
