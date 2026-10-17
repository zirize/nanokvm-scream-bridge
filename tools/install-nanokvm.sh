#!/bin/bash
# Copy the audio-bridge files onto a NanoKVM. Installs only; the mode is chosen with kvm-mode.
#   install-nanokvm.sh [host]        (default: kvm)
# Undo: ssh root@<host> 'rm /etc/init.d/S04usbaudio /usr/local/bin/uac2scream.py /boot/usb.audio'
set -euo pipefail

HOST=${1:-kvm}
SRC=$(cd "$(dirname "$0")/../nanokvm" && pwd)

ssh -o BatchMode=yes root@"$HOST" 'mkdir -p /usr/local/bin'
scp -q -o BatchMode=yes "$SRC/S04usbaudio" root@"$HOST":/etc/init.d/S04usbaudio
scp -q -o BatchMode=yes "$SRC/uac2scream.py" root@"$HOST":/usr/local/bin/uac2scream.py
ssh -o BatchMode=yes root@"$HOST" 'chmod +x /etc/init.d/S04usbaudio /usr/local/bin/uac2scream.py && sync'
echo "installed on $HOST"
