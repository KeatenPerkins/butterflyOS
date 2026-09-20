#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Keaten Perkins

set -u

TITLE="Butterfly Link — Experimental"
SAVE_TOOL=${BUTTERFLY_LINK_SAVE_TOOL:-/usr/bin/butterflyos-link-save}
AGENT=${BUTTERFLY_LINK_AGENT:-/usr/bin/butterflyos-link-agent}
STATE_ROOT=${BUTTERFLY_LINK_STATE_ROOT:-/storage/.config/butterflyos/link}
CONTROLLER_CONFIG=${BUTTERFLY_LINK_CONTROLLER_CONFIG:-/usr/share/butterflyos/flip-onboarding.gptk}
CONTROLLER_PID=

stop_controller_input() {
  if [[ -n "$CONTROLLER_PID" ]]; then
    kill "$CONTROLLER_PID" 2>/dev/null || true
    wait "$CONTROLLER_PID" 2>/dev/null || true
  fi
}

start_controller_input() {
  /usr/bin/control-gen_init.sh >/dev/null 2>&1 || true
  if [[ -f /storage/.config/gptokeyb/control.ini && -f "$CONTROLLER_CONFIG" ]]; then
    source /storage/.config/gptokeyb/control.ini
    get_controls
    /usr/bin/gptokeyb -c "$CONTROLLER_CONFIG" >/dev/null 2>&1 &
    CONTROLLER_PID=$!
  fi
}

message() {
  dialog --clear --title "$TITLE" --msgbox "$1" 18 64 \
    </dev/tty >/dev/tty 2>/dev/tty
}

confirm() {
  dialog --clear --title "$TITLE" --yes-label "Continue" --no-label "Cancel" \
    --yesno "$1" 19 66 </dev/tty >/dev/tty 2>/dev/tty
}

local_ip() {
  ip -4 -o addr show wlan0 2>/dev/null | awk '{split($4,a,"/"); print a[1]; exit}'
}

card_label() {
  case "$1" in
    /storage/games-external/*) printf 'Game Card' ;;
    *) printf 'OS Card' ;;
  esac
}

select_rom() {
  local path canonical name index=0
  local -a choices=()
  declare -A paths=() seen=()

  while IFS= read -r -d '' path; do
    canonical=$(readlink -f -- "$path" 2>/dev/null || true)
    [[ -n "$canonical" && -f "$canonical" && -z "${seen[$canonical]:-}" ]] || continue
    seen[$canonical]=1
    name=${canonical##*/}
    case "${name,,}" in
      *pokemon*.gb|*pokemon*.gbc|*pocket\ monsters*.gb|*pocket\ monsters*.gbc) ;;
      *) continue ;;
    esac
    index=$((index + 1))
    paths[$index]=$canonical
    choices+=("$index" "$(card_label "$canonical") — ${name%.*}")
  done < <(find /storage/roms /storage/games-external/roms \
    \( -type f -o -type l \) \( -iname '*.gb' -o -iname '*.gbc' \) -print0 2>/dev/null)

  if (( index == 0 )); then
    message "NO SUPPORTED GAMES FOUND\n\nAdd your legally obtained GB/GBC Pokémon games to either card, refresh the game library, and try again."
    return 1
  fi

  local choice
  choice=$(dialog --clear --title "$TITLE" --cancel-label "Back" \
    --menu "Choose your game. ButterflyOS never transfers ROM files." \
    21 70 13 "${choices[@]}" </dev/tty 2>&1 >/dev/tty) || return 1
  printf '%s\n' "${paths[$choice]}"
}

select_save() {
  local rom=${1:?} output line location path index=0 choice
  local -a choices=()
  declare -A paths=()

  if ! output=$($SAVE_TOOL discover "$rom" 2>&1); then
    message "SAVE SEARCH FAILED\n\n$output"
    return 1
  fi
  while IFS= read -r line; do
    [[ "$line" == selected=* ]] || continue
    location=${line#*location=}
    location=${location%%$'\t'*}
    path=${line#*path=}
    index=$((index + 1))
    paths[$index]=$path
    choices+=("$index" "${location//_/ } — ${path##*/}")
  done <<<"$output"

  choices+=("manual" "Choose another .srm or .sav file")
  choice=$(dialog --clear --title "$TITLE" --cancel-label "Back" \
    --menu "Choose the save to protect and use for this session." \
    20 70 11 "${choices[@]}" </dev/tty 2>&1 >/dev/tty) || return 1

  if [[ "$choice" == manual ]]; then
    path=$(dialog --clear --title "$TITLE" --fselect "/storage/" 18 70 \
      </dev/tty 2>&1 >/dev/tty) || return 1
    printf '%s\n' "$path"
  else
    printf '%s\n' "${paths[$choice]}"
  fi
}

prepare_save() {
  local rom save output session working original
  rom=$(select_rom) || return 1
  save=$(select_save "$rom") || return 1

  confirm "CREATE PROTECTED SESSION?\n\nGame: ${rom##*/}\nSave: ${save##*/}\nLocation: $(card_label "$(readlink -f -- "$save" 2>/dev/null || printf '%s' "$save")")\n\nThe original will be backed up and the emulator will use an isolated copy." || return 1

  if ! output=$($SAVE_TOOL begin "$rom" "$save" 2>&1); then
    message "SESSION COULD NOT START\n\n$output\n\nThe selected save was not changed."
    return 1
  fi
  session=$(sed -n 's/^session_id=//p' <<<"$output")
  working=$(sed -n 's/^working_save=//p' <<<"$output")
  original=$(sed -n 's/^original=//p' <<<"$output")
  mkdir -p "$STATE_ROOT"
  printf '%s\n' "$session" >"$STATE_ROOT/last-session"
  printf '%s\n%s\n%s\n' "$session" "$rom" "$working" >"$STATE_ROOT/local-ready"
  message "SAVE PROTECTED\n\nSession: $session\nOriginal: $original\n\nThe original remains untouched. The protected working copy is ready for Butterfly Link."
  printf '%s\n' "$session"
}

parse_field() {
  local line=${1:?} key=${2:?} value
  value=${line#*${key}=}
  [[ "$value" != "$line" ]] || return 1
  printf '%s\n' "${value%%$'\t'*}"
}

choose_peer() {
  local output line ip hostname compatible index=0 choice own_ip
  local -a choices=()
  declare -A addresses=()
  own_ip=$(local_ip)

  dialog --clear --title "$TITLE" --infobox \
    "Searching the local network for another ButterflyOS device..." 7 62 \
    </dev/tty >/dev/tty 2>/dev/tty
  output=$($AGENT discover --timeout 3 2>/dev/null || true)
  while IFS= read -r line; do
    [[ "$line" == ip=* ]] || continue
    ip=$(parse_field "$line" ip || true)
    [[ -n "$ip" && "$ip" != "$own_ip" ]] || continue
    hostname=$(parse_field "$line" hostname || printf unknown)
    compatible=$(parse_field "$line" compatible || printf no)
    index=$((index + 1))
    addresses[$index]=$ip
    choices+=("$index" "$hostname — $ip — compatible: $compatible")
  done <<<"$output"
  choices+=("manual" "Enter an IP address manually")

  choice=$(dialog --clear --title "$TITLE" --cancel-label "Back" \
    --menu "Choose the other ButterflyOS device." 18 70 9 \
    "${choices[@]}" </dev/tty 2>&1 >/dev/tty) || return 1
  if [[ "$choice" == manual ]]; then
    dialog --clear --title "$TITLE" --inputbox \
      "Enter the other device's IPv4 address:" 10 58 \
      </dev/tty 2>&1 >/dev/tty
  else
    printf '%s\n' "${addresses[$choice]}"
  fi
}

test_peer() {
  local peer=${1:-} result status
  [[ -n "$peer" ]] || peer=$(choose_peer) || return 1
  if result=$($AGENT probe "$peer" 2>&1); then
    status="COMPATIBILITY CHECK PASSED"
  else
    status="COMPATIBILITY CHECK FAILED"
  fi
  message "$status\n\nPeer: $peer\n\n${result//$'\t'/\n}\n\nA passing check confirms the discovery protocol and SameBoy core match."
  [[ "$status" == *PASSED ]]
}

host_workflow() {
  local session ip
  session=$(prepare_save) || return
  ip=$(local_ip)
  message "HOST PREPARATION COMPLETE\n\nThis device: ${ip:-not connected}\nSession: $session\n\nOn the second Flip, open Butterfly Link and choose Join a Session.\n\nThe synchronized-launch step is still experimental and is not started automatically yet."
}

join_workflow() {
  local peer session
  peer=$(choose_peer) || return
  test_peer "$peer" || return
  session=$(prepare_save) || return
  printf '%s\n' "$peer" >"$STATE_ROOT/last-peer"
  message "JOIN PREPARATION COMPLETE\n\nPeer: $peer\nSession: $session\n\nBoth the network and your protected save are ready. The synchronized-launch and save-exchange step is the next development milestone."
}

restore_backup() {
  local dir id state index=0 choice output
  local -a choices=()
  declare -A sessions=()
  [[ -d "$STATE_ROOT/sessions" ]] || {
    message "NO BACKUPS FOUND\n\nNo Butterfly Link sessions have been created on this device."
    return
  }
  for dir in "$STATE_ROOT"/sessions/*; do
    [[ -d "$dir" && -f "$dir/state" ]] || continue
    id=${dir##*/}
    state=$(tr -d '\r\n' <"$dir/state")
    index=$((index + 1))
    sessions[$index]=$id
    choices+=("$index" "$id — $state")
  done
  (( index > 0 )) || {
    message "NO BACKUPS FOUND\n\nNo recoverable Butterfly Link sessions were found."
    return
  }
  choice=$(dialog --clear --title "$TITLE" --cancel-label "Back" \
    --menu "Choose a session whose original save should be restored." \
    20 72 11 "${choices[@]}" </dev/tty 2>&1 >/dev/tty) || return
  id=${sessions[$choice]}
  confirm "RESTORE PRE-SESSION SAVE?\n\nSession: $id\n\nThe current save will be archived first, then the verified original backup will be restored atomically." || return
  if output=$($SAVE_TOOL restore "$id" 2>&1); then
    message "SAVE RESTORED\n\n$output"
  else
    message "RESTORE FAILED SAFELY\n\n$output\n\nNo unverified backup was written."
  fi
}

show_last_session() {
  local id output
  [[ -f "$STATE_ROOT/last-session" ]] || {
    message "NO RECENT SESSION\n\nPrepare a Host or Join session first."
    return
  }
  id=$(tr -d '\r\n' <"$STATE_ROOT/last-session")
  if output=$($SAVE_TOOL status "$id" 2>&1); then
    message "RECENT SESSION\n\n$output"
  else
    message "SESSION STATUS ERROR\n\n$output"
  fi
}

cancel_last_session() {
  local id output state
  [[ -f "$STATE_ROOT/last-session" ]] || {
    message "NO RECENT SESSION\n\nThere is no prepared session to cancel."
    return
  }
  id=$(tr -d '\r\n' <"$STATE_ROOT/last-session")
  output=$($SAVE_TOOL status "$id" 2>&1) || {
    message "SESSION STATUS ERROR\n\n$output"
    return
  }
  state=$(sed -n 's/^state=//p' <<<"$output")
  [[ "$state" == ACTIVE ]] || {
    message "SESSION IS NOT ACTIVE\n\nSession: $id\nState: $state\n\nNothing was changed."
    return
  }
  confirm "CANCEL PREPARED SESSION?\n\nSession: $id\n\nThe original save was never modified. The verified backup will be retained." || return
  if output=$($SAVE_TOOL abort "$id" 2>&1); then
    rm -f "$STATE_ROOT/local-ready"
    message "SESSION CANCELLED\n\n$output\n\nThe recovery backup was retained."
  else
    message "SESSION COULD NOT BE CANCELLED\n\n$output"
  fi
}

trap stop_controller_input EXIT INT TERM
start_controller_input
mkdir -p "$STATE_ROOT"

while true; do
  choice=$(dialog --clear --title "$TITLE" --cancel-label "Close" \
    --menu "Prepare a protected local-network link session. ROM files are never transferred." \
    21 70 10 \
    host "Host a Session" \
    join "Join a Session" \
    test "Connection Test" \
    status "Recent Session Status" \
    cancel "Cancel Prepared Session" \
    restore "Restore a Save Backup" \
    about "How Butterfly Link Works" \
    close "Return to Tools" \
    </dev/tty 2>&1 >/dev/tty) || break
  case "$choice" in
    host) host_workflow ;;
    join) join_workflow ;;
    test) test_peer || true ;;
    status) show_last_session ;;
    cancel) cancel_last_session ;;
    restore) restore_backup ;;
    about)
      message "BUTTERFLY LINK\n\nEach player uses legally obtained games and their own save. ButterflyOS creates verified backups and isolated working copies before networking begins.\n\nThis MVP currently validates discovery, compatibility, selection, backup, and recovery. Automated save exchange and synchronized launch are still under development."
      ;;
    close) break ;;
  esac
done

clear
