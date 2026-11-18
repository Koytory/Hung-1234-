#!/usr/bin/env bash
# Usage: render.sh <input_video> <output.mp4> [ambient_volume=0.15]
# Edit the TIMELINE section in make_video.py and the SFX section in make_audio.py first.
set -euo pipefail
IN="$1"; OUT="$2"; AMB="${3:-0.15}"
HERE="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
export VIDEO_DUR="$(ffprobe -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 "$IN")"
python3 -I "$HERE/make_audio.py" "$TMP/music_sfx.wav"
HAS_AUDIO="$(ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$IN" | head -1)"
if [ -n "$HAS_AUDIO" ]; then
  AF="[2:a:0]volume=${AMB}[amb];[1:a][amb]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]"; EXTRA=(-i "$IN")
else
  AF="[1:a]alimiter=limit=0.95[a]"; EXTRA=()
fi
ffmpeg -v error -i "$IN" -map 0:v:0 -vf fps=30,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1 -f rawvideo -pix_fmt rgb24 - \
 | python3 -I "$HERE/make_video.py" \
 | ffmpeg -v error -y -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30 -i - -i "$TMP/music_sfx.wav" "${EXTRA[@]}" \
   -filter_complex "$AF" -map 0:v -map "[a]" -c:v libx264 -crf 19 -preset medium -pix_fmt yuv420p \
   -c:a aac -b:a 192k -movflags +faststart -shortest "$OUT"
echo "Done: $OUT"
