#!/usr/bin/env python3
"""Read raw S16_LE stereo 48 kHz PCM on stdin, send it as Scream UDP packets.

Pacing comes from the input: arecord blocks on the USB gadget, so the phone's
clock drives the stream. No sleeping here.

usage: arecord -D hw:UAC1Gadget -f S16_LE -r 48000 -c 2 -t raw | uac2scream.py HOST PORT
"""
import socket
import sys

FRAMES = 288                 # standard Scream payload: 1152 bytes of 16-bit stereo
CHUNK = FRAMES * 2 * 2
# rate byte: bit7=0 -> 48 kHz base, multiplier 1; 16 bit; 2 ch; channel mask FL|FR
HEADER = bytes([0x01, 16, 2, 0x03, 0x00])


def main():
    host, port = sys.argv[1], int(sys.argv[2])
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    src = sys.stdin.buffer
    buf = b""
    sent = 0
    while True:
        data = src.read(CHUNK - len(buf))
        if not data:
            break
        buf += data
        if len(buf) < CHUNK:
            continue
        sock.sendto(HEADER + buf, (host, port))
        buf = b""
        sent += 1
        if sent % 1000 == 0:
            print(f"sent {sent} packets", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
