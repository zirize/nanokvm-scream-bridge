# NanoKVM as a phone-audio bridge

Phone plays into the NanoKVM as a USB speaker; the NanoKVM forwards the PCM as Scream UDP
to a Scream receiver on a PC (port 4015 here). Verified end to end on 2026-10-17 with a NanoKVM
(hw `beta`, kernel 5.10.4, SG2002 riscv64, 158 MB RAM).

```
phone --USB-C (UAC1 speaker)--> NanoKVM --Scream UDP, wired--> PC Scream receiver :4015 --> speakers
```

## Files

| Repo path | On the device | Role |
|---|---|---|
| `nanokvm/S04usbaudio` | `/etc/init.d/S04usbaudio` | boot hook + supervisor; `start/stop/restart/kvm/status` (`stop` leaves the gadget alone) |
| `nanokvm/uac2scream.py` | `/usr/local/bin/uac2scream.py` | stdin raw PCM -> Scream packets |
| `tools/install-nanokvm.sh [host]` | — | copies the two files (no mode change) |
| `tools/kvm-mode audio [host:port] \| kvm \| status` | — | switches mode live; persists via `/boot/usb.audio` |

Mode flag: `/boot/usb.audio` (FAT partition) holding `host:port`. Present = audio mode at boot.
Recovery without network: put the SD card in a PC and delete that file.

## Facts measured on the device

- Kernel has `CONFIG_USB_CONFIGFS_F_UAC1=y` and `U_AUDIO=y`; **no `F_UAC2`**. UAC1 at
  48 kHz / 16 bit / 2 ch works; `p_chmask=0` (no mic toward the phone) is accepted.
- The UDC (`4340000.usb`, dwc2) reports `EPs: 8`. The stock gadget (3 HID + mass storage +
  RNDIS) already uses them up, so audio mode **replaces** the stock functions instead of adding
  to them. KVM and audio cannot run at once.
- The phone (Android) shows it as wired headphones; link comes up high-speed, `configured`.
- 50 s test: >8,000 packets of 288 frames = 166.7 pkt/s = exactly 48 kHz.
- UAC1 in 5.10 has no feedback endpoint: the phone's clock drives the stream; drift is absorbed
  by the receiver. Sample values are unchanged (no resampling on the device).
- The phone applies its volume digitally: at low phone volume the stream peaked at -50 dBFS.
  Keep the phone at full volume and control loudness on the PC.
- Device has `arecord`, `python3`, `setsid`, `logger`, `killall`; **no `timeout`** and no
  `/usr/local/bin` until the installer creates it.

## Latency budget

Estimated per stage (not an end-to-end measurement):

| Stage | Approx. | Note |
|---|---|---|
| Phone USB output path | 20-40 ms | Android side, not adjustable |
| `arecord` period + packet | ~27 ms | period 1024 frames (21 ms) + 288-frame packet (6 ms) |
| LAN | <1 ms | no backlog seen in the receiver's socket queue |
| Scream receiver + PipeWire | 20-50 ms | receiver target latency 20 ms |
| Bluetooth A2DP (SBC) on the PC | 150-250 ms | dominant term when the PC plays to a Bluetooth headset |

In practice, noticeable lag came from the PC's Bluetooth output. Use a wired sink when latency
matters. Untried option if Bluetooth must stay: `arecord --period-size=256 --buffer-size=2048`
in `S04usbaudio` saves roughly 15 ms.

## Traps

- `S03usbdev` is a firmware file; it is not modified. The NanoKVM web app re-runs it when USB
  settings (virtual disk, RNDIS, HID) are toggled, which restores the stock functions. The
  supervisor in `S04usbaudio` checks every 5 s and re-applies the audio gadget.
- When the gadget re-enumerates (device reboot, mode switch), Android treats it as headphones
  being unplugged and **pauses playback**. Press play again on the phone.
- Shutdown can hang: the stock `S95nanokvm stop` waits on `NanoKVM-Server`/`kvm_system`.
  Seen once at ~45 s, once stuck for minutes (2026-10-17). Not caused by `S04usbaudio`.
  Before pulling power: `sync; mount -o remount,ro /boot; mount -o remount,ro /` over ssh
  (both succeeded while stuck), then unplug.
- A phone on the USB-C port keeps powering the device. Unplugging only the external supply
  does not power it off: a half-finished shutdown then leaves it up with networking already
  stopped (invisible on the LAN). Power-cycle by removing **both** the phone and the supply.
  The phone and the supply were both feeding 5 V at that time; whether the board isolates
  the two inputs is not verified.
