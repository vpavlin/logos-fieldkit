#!/bin/bash
export XDG_RUNTIME_DIR=/run/kiosk
mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"
export LIBSEAT_BACKEND=builtin
export WLR_BACKEND=drm
export WLR_DRM_DEVICES=/dev/dri/card2
export WLR_RENDERER=pixman
export WLR_SCENE_DEBUG_DAMAGE=rerender
exec cage -- chromium \
  --kiosk --noerrdialogs --disable-infobars --incognito --no-sandbox --allow-file-access-from-files \
  --ozone-platform=wayland --enable-features=UseOzonePlatform \
  --disable-gpu --in-process-gpu --window-size=480,320 \
  --user-data-dir=/tmp/chrome-kiosk \
  --app=file:///home/vpavlin/mesh-dashboard/index.html
