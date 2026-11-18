#!/usr/bin/env bash
# Cài phụ thuộc cho skill bds (chạy 1 lần mỗi máy mới).
set -e
python3 -c "import numpy, PIL" 2>/dev/null || pip install -q numpy pillow
# Tách người (chữ nằm sau người, chớp trắng in hình người)
python3 -c "import mediapipe" 2>/dev/null || pip install -q mediapipe
ldconfig -p | grep -q libEGL.so.1 || (apt-get update -q && apt-get install -y -q libegl1 libgles2)
echo "bds setup OK"
