# nanokvm-scream-bridge

📄 Project page: **[Hear your phone on your PC: a NanoKVM as a USB speaker that forwards audio over Scream](https://zirize.github.io/nanokvm-scream-bridge/)** · More projects: **[zirize.github.io](https://zirize.github.io/)**

Hear your phone on your PC: plug the phone into a [Sipeed NanoKVM](https://github.com/sipeed/NanoKVM)
and it shows up as a USB speaker (wired headphones on Android). Everything the phone plays is
forwarded over the LAN as [Scream](https://github.com/duncanthrax/scream) UDP packets, so any
Scream receiver on the PC plays it — 48 kHz / 16-bit stereo PCM, bit for bit, no re-encoding.

```
phone --USB-C (UAC1 speaker)--> NanoKVM --Scream UDP, wired LAN--> PC Scream receiver --> speakers
```

## What you need

- A NanoKVM (tested: full NanoKVM, hw `beta`, firmware kernel 5.10.4) reachable as
  `root@<host>` over ssh with key auth.
- A Scream receiver on the PC: the Unix receiver from
  [duncanthrax/scream](https://github.com/duncanthrax/scream) or
  [pipewire-scream](https://github.com/zirize/pipewire-scream), listening on the port you choose
  (examples use 4015). Allow that UDP port from the LAN in the PC's firewall.
- A USB-C cable from the phone to the NanoKVM's USB-C (gadget) port.

## Use

```bash
tools/install-nanokvm.sh <host>                  # copy the two device files (once)
KVM_HOST=<host> tools/kvm-mode audio <pc-ip>:4015 # switch to audio mode, persists across reboot
KVM_HOST=<host> tools/kvm-mode status
KVM_HOST=<host> tools/kvm-mode kvm                # back to the stock KVM gadget
```

Audio mode **replaces** the KVM functions (keyboard/mouse HID, virtual disk, RNDIS): the dwc2
controller has only 8 endpoints and the stock gadget already uses them all. The mode is kept in
`/boot/usb.audio` (holds `host:port`); to recover without network, take out the SD card and
delete that file.

Tips:

- Keep the phone at full volume and set loudness on the PC — the phone scales samples digitally.
- When the gadget re-enumerates (reboot, mode switch) Android pauses playback; press play again.

## Files

| Path | Installed to | Role |
|---|---|---|
| `nanokvm/S04usbaudio` | `/etc/init.d/S04usbaudio` | boot hook + supervisor: builds the UAC1 gadget, runs `arecord \| uac2scream.py`, re-applies the gadget if the NanoKVM web app rebuilds it |
| `nanokvm/uac2scream.py` | `/usr/local/bin/uac2scream.py` | raw PCM on stdin -> Scream packets (288 frames each); paced by the phone's clock |
| `tools/install-nanokvm.sh` | — | copies the two files over ssh (no mode change) |
| `tools/kvm-mode` | — | switches mode live: `audio [host:port]`, `kvm`, `status` |

The firmware's own `/etc/init.d/S03usbdev` is never modified.

## Docs

- [docs/nanokvm-bridge.md](docs/nanokvm-bridge.md) — how it works, facts measured on the
  device (UAC1 only, endpoint budget, packet rate), and traps (shutdown hang, phone back-power).
- [docs/hardware-options.md](docs/hardware-options.md) — why Scream instead of a USB-to-USB
  bridge, and notes for moving it to a Raspberry Pi 4 (power splitter, OTG charge adapters).

## Limits

- UAC1 in the 5.10 kernel has no feedback endpoint: the phone's clock drives the stream and the
  receiver absorbs any drift. No resampling happens on the device.
- No microphone toward the phone (`p_chmask=0`).
- Tested with one Android phone.

## License

MIT
