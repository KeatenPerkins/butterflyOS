#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Keaten Perkins
# Standalone Tools-menu hotfix for the v1.0.0 47 FPS audio-pacing issue.
set -eu

TITLE="ButterflyOS Audio Fix"
CONTROLLER_PID=
cleanup() {
    if [[ -n "${CONTROLLER_PID}" ]]; then
        kill "${CONTROLLER_PID}" 2>/dev/null || true
        wait "${CONTROLLER_PID}" 2>/dev/null || true
    fi
}
trap cleanup EXIT

message() {
    printf '%s\n' "$1"
    if [[ "${1:-}" != "" && -t 0 ]] && command -v dialog >/dev/null 2>&1; then
        dialog --clear --title "${TITLE}" --msgbox "$1" 16 62 || true
    fi
}

if ! grep -qa "Miyoo Flip" /proc/device-tree/model 2>/dev/null || \
   [[ ! -x /usr/bin/butterflyos-game-card ]]; then
    message "This fix is for butterflyOS on the Miyoo Flip. No changes were made."
    exit 1
fi

# Provide the same controller navigation used by butterflyOS's other Tools.
if [[ -t 0 && -x /usr/bin/gptokeyb && -r /storage/.config/gptokeyb/control.ini ]]; then
    set +u
    source /storage/.config/gptokeyb/control.ini
    get_controls
    set -u
    /usr/bin/gptokeyb -c /usr/share/butterflyos/flip-onboarding.gptk >/dev/null 2>&1 &
    CONTROLLER_PID=$!
fi

CONFIG_DIR=/storage/.config/pipewire/pipewire.conf.d
CONFIG=${CONFIG_DIR}/99-butterflyos-game-audio.conf
mkdir -p "${CONFIG_DIR}"
TEMP=$(mktemp "${CONFIG_DIR}/.audio-fix.XXXXXX")
cat >"${TEMP}" <<'CONF'
# butterflyOS: keep audio cycles below a 60 Hz video frame.
# A 1024-sample cycle stalls RetroArch's 32 ms buffer at about 47 FPS.
context.properties = {
    default.clock.power-of-two-quantum = true
    default.clock.quantum = 512
    default.clock.min-quantum = 512
    default.clock.max-quantum = 512
}
CONF
if [[ -f "${CONFIG}" ]] && ! cmp -s "${TEMP}" "${CONFIG}" && \
   [[ ! -e "${CONFIG}.before-audio-fix" ]]; then
    cp -p "${CONFIG}" "${CONFIG}.before-audio-fix"
fi
chmod 0644 "${TEMP}"
mv -f "${TEMP}" "${CONFIG}"
sync

APPLIED=true
for setting in 'clock.min-quantum 512' 'clock.max-quantum 512' \
               'clock.quantum 512' 'clock.force-quantum 0'; do
    read -r key value <<<"${setting}"
    if ! pw-metadata -n settings 0 "${key}" "${value}" >/dev/null 2>&1; then
        APPLIED=false
    fi
done

if [[ "${APPLIED}" == true ]]; then
    message "Audio fix installed and applied.\n\nGB, GBA, and NES games should now run near 60 FPS. The fix stays installed after restarting.\n\nYou can return to your games."
else
    message "Audio fix installed. Restart the device to activate it.\n\nThe fix stays installed after restarting."
fi
