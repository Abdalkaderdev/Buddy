#!/bin/bash
# check-audio.sh - End-to-end USB audio diagnostic for buddy.local
# Tests: USB card detection, PipeWire default sink, speaker output, mic input.
set -u

PASS() { echo -e "\e[32m[PASS]\e[0m $*"; }
FAIL() { echo -e "\e[31m[FAIL]\e[0m $*"; }
INFO() { echo -e "\e[36m[INFO]\e[0m $*"; }
ASK()  { echo -e "\e[33m[ASK ]\e[0m $*"; }

SPEAKER_OK=0
MIC_OK=0
USB_OK=0
PW_OK=0

echo '=== 1. Detect USB sound card ==='
USB_PLAY=$(aplay  -l 2>/dev/null | grep -iE 'USB|Device' | grep -v bcm2835 | grep -v vc4 | head -1)
USB_REC=$(arecord -l 2>/dev/null | grep -iE 'USB|Device' | grep -v bcm2835 | grep -v vc4 | head -1)
if [ -n "$USB_PLAY" ]; then
  CARD_IDX=$(echo "$USB_PLAY" | sed -n 's/^card \([0-9]*\):.*/\1/p')
  CARD_NAME=$(echo "$USB_PLAY" | sed -n 's/^card [0-9]*: \([^ ]*\).*/\1/p')
  PASS "USB playback card found: index=$CARD_IDX name=$CARD_NAME"
  USB_OK=1
else
  FAIL 'No USB playback card in aplay -l. Is it plugged in?'
fi
if [ -n "$USB_REC" ]; then
  REC_IDX=$(echo "$USB_REC" | sed -n 's/^card \([0-9]*\):.*/\1/p')
  PASS "USB capture card found: index=$REC_IDX"
else
  FAIL 'No USB capture card in arecord -l.'
fi

echo
echo '=== 2. PipeWire sees USB as default sink ==='
DEFAULT_SINK=$(wpctl status | awk '/Sinks:/,/Sources:/' | grep '\*' | head -1)
echo "  Default sink line: $DEFAULT_SINK"
if echo "$DEFAULT_SINK" | grep -qiE 'USB|Device'; then
  PASS 'USB device is the default PipeWire sink.'
  PW_OK=1
elif [ $USB_OK -eq 1 ]; then
  INFO 'USB present but not default sink. Attempting to set...'
  USB_NODE=$(wpctl status | awk '/Sinks:/,/Sources:/' | grep -iE 'USB|Device' | head -1 | sed -n 's/.*\b\([0-9]\+\)\..*/\1/p')
  if [ -n "$USB_NODE" ]; then
    wpctl set-default "$USB_NODE" && PASS "Set node $USB_NODE as default" && PW_OK=1
  fi
else
  FAIL 'No USB sink in PipeWire.'
fi

echo
echo '=== 3. Crank USB card mixer to 100%, unmute ==='
if [ $USB_OK -eq 1 ]; then
  for ctl in Speaker PCM Master Headphone; do
    amixer -c "$CARD_IDX" sset "$ctl" 100% unmute >/dev/null 2>&1 && INFO "Set $ctl = 100% unmute on card $CARD_IDX"
  done
  wpctl set-volume @DEFAULT_AUDIO_SINK@ 1.0 && INFO 'PipeWire sink volume = 1.0'
  wpctl set-mute   @DEFAULT_AUDIO_SINK@ 0   && INFO 'PipeWire sink unmuted'
  PASS 'Mixer levels maxed.'
else
  FAIL 'Skipping mixer step (no USB card).'
fi

echo
echo '=== 4. Play 2-second 440Hz tone via ffplay (PipeWire default sink) ==='
ffplay -nodisp -autoexit -loglevel error -f lavfi -i 'sine=frequency=440:duration=2' </dev/null
ASK 'Did you hear a clear 440Hz tone from the speaker? [y/N]'
read -r ans
if [ "${ans,,}" = 'y' ]; then PASS 'Speaker confirmed by user.'; SPEAKER_OK=1; else FAIL 'Speaker NOT confirmed.'; fi

echo
echo '=== 5. Mic test: record 3s, play back ==='
INFO 'Speak into the mic now...'
if arecord -D default -d 3 -f S16_LE -r 16000 -c 1 /tmp/mic-test.wav 2>/dev/null; then
  PASS 'Recorded /tmp/mic-test.wav'
  INFO 'Playing back...'
  ffplay -nodisp -autoexit -loglevel error /tmp/mic-test.wav </dev/null
  ASK 'Did you hear your voice played back? [y/N]'
  read -r ans
  if [ "${ans,,}" = 'y' ]; then PASS 'Mic confirmed by user.'; MIC_OK=1; else FAIL 'Mic NOT confirmed.'; fi
else
  FAIL 'arecord failed. Mic not available.'
fi

echo
echo '=== SUMMARY ==='
[ $PW_OK      -eq 1 ] && PASS 'PipeWire OK'        || FAIL 'PipeWire NOT OK'
[ $USB_OK     -eq 1 ] && PASS 'USB card detected'  || FAIL 'USB card NOT detected'
[ $SPEAKER_OK -eq 1 ] && PASS 'Speaker test'       || FAIL 'Speaker test'
[ $MIC_OK     -eq 1 ] && PASS 'Mic test'           || FAIL 'Mic test'
