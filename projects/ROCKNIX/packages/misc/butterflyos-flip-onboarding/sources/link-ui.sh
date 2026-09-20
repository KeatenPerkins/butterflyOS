#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Keaten Perkins

set -u

TITLE="Butterfly Link — Experimental"
SAVE_TOOL=${BUTTERFLY_LINK_SAVE_TOOL:-/usr/bin/butterflyos-link-save}
AGENT=${BUTTERFLY_LINK_AGENT:-/usr/bin/butterflyos-link-agent}
SESSION_TOOL=${BUTTERFLY_LINK_SESSION_TOOL:-/usr/bin/butterflyos-link-session}
STATE_ROOT=${BUTTERFLY_LINK_STATE_ROOT:-/storage/.config/butterflyos/link}
CONTROLLER_CONFIG=${BUTTERFLY_LINK_CONTROLLER_CONFIG:-/usr/share/butterflyos/flip-onboarding.gptk}
CONTROLLER_PID=

stop_controller_input() {
  if [[ -n "$CONTROLLER_PID" ]]; then
    kill "$CONTROLLER_PID" 2>/dev/null || true
    wait "$CONTROLLER_PID" 2>/dev/null || true
    CONTROLLER_PID=
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
  local require_session=${1:-no} output line ip hostname compatible available index choice own_ip
  own_ip=$(local_ip)
  while true; do
    index=0
    local -a choices=()
    declare -A addresses=()
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
      available=$(parse_field "$line" session_available || printf no)
      [[ "$require_session" != yes || "$available" == yes ]] || continue
      index=$((index + 1))
      addresses[$index]=$ip
      choices+=("$index" "$hostname — $ip — compatible: $compatible")
    done <<<"$output"

    if (( index == 0 )) && [[ "$require_session" == yes ]]; then
      dialog --clear --title "$TITLE" --cancel-label "Cancel" \
        --pause "SEARCHING FOR A HOST\n\nStart Host a Session on the other Flip. This list refreshes automatically every three seconds.\n\nSelect Cancel to return." \
        13 66 3 </dev/tty >/dev/tty 2>/dev/tty || return 1
      continue
    fi

    choices+=("refresh" "Refresh device list" "manual" "Enter an IP address manually")
    choice=$(dialog --clear --title "$TITLE" --cancel-label "Back" \
      --menu "Choose the other ButterflyOS device." 18 70 9 \
      "${choices[@]}" </dev/tty 2>&1 >/dev/tty) || return 1
    case "$choice" in
      refresh) continue ;;
      manual)
        dialog --clear --title "$TITLE" --inputbox \
          "Enter the other device's IPv4 address:" 10 58 \
          </dev/tty 2>&1 >/dev/tty
        ;;
      *) printf '%s\n' "${addresses[$choice]}" ;;
    esac
    return
  done
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
  local session ip rom working output result_save host_pid output_file remaining
  session=$(prepare_save) || return
  IFS= read -r session <"$STATE_ROOT/last-session"
  rom=$(sed -n '2p' "$STATE_ROOT/local-ready")
  working=$(sed -n '3p' "$STATE_ROOT/local-ready")
  ip=$(local_ip)
  output_file=$(mktemp "$STATE_ROOT/host-output.XXXXXX")
  $SESSION_TOOL host --session "$session" --rom "$rom" --save "$working" --timeout 300 >"$output_file" 2>&1 &
  host_pid=$!
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    [[ -e /run/butterflyos-link-host.json ]] && break
    kill -0 "$host_pid" 2>/dev/null || break
    sleep 0.1
  done
  while kill -0 "$host_pid" 2>/dev/null && [[ -e /run/butterflyos-link-host.json ]]; do
    if ! dialog --clear --title "$TITLE" --cancel-label "Cancel Host" \
      --pause "WAITING FOR PLAYER 2\n\nThis device: ${ip:-not connected}\n\nOn the second Flip, choose Join a Session.\n\nThe host remains available for five minutes. Select Cancel Host to stop safely." \
      15 68 1 </dev/tty >/dev/tty 2>/dev/tty; then
      kill -TERM "$host_pid" 2>/dev/null || true
      wait "$host_pid" 2>/dev/null || true
      $SAVE_TOOL abort "$session" >/dev/null 2>&1 || true
      rm -f "$STATE_ROOT/local-ready" "$output_file"
      message "HOST CANCELLED\n\nNo game was launched and your original save was not changed."
      return
    fi
  done
  stop_controller_input
  if wait "$host_pid"; then
    output=$(cat "$output_file")
    rm -f "$output_file"
    start_controller_input
    result_save=$(sed -n 's/^result_save=//p' <<<"$output" | tail -n 1)
    finish_session "$session" "$result_save"
  else
    output=$(cat "$output_file")
    rm -f "$output_file"
    start_controller_input
    message "LINK SESSION ENDED SAFELY\n\n$output\n\nYour original save was not changed. The verified backup and working copy were retained."
  fi
}

join_workflow() {
  local peer session rom working probe token port host_session output result_save
  peer=$(choose_peer yes) || return
  if ! probe=$($AGENT probe "$peer" 2>&1); then
    message "COMPATIBILITY CHECK FAILED\n\n$probe"
    return
  fi
  [[ "$(parse_field "$probe" compatible || true)" == yes ]] || {
    message "COMPATIBILITY CHECK FAILED\n\n${probe//$'\t'/\n}"
    return
  }
  [[ "$(parse_field "$probe" session_available || true)" == yes ]] || {
    message "HOST IS NOT READY\n\nOpen Host a Session on the other Flip first, then try Join again."
    return
  }
  token=$(parse_field "$probe" session_token || true)
  port=$(parse_field "$probe" session_port || true)
  host_session=$(parse_field "$probe" session_id || true)
  [[ -n "$token" && "$port" =~ ^[0-9]+$ && -n "$host_session" ]] || {
    message "INVALID HOST SESSION\n\nThe host announcement was incomplete. Cancel and create a new host session."
    return
  }
  session=$(prepare_save) || return
  IFS= read -r session <"$STATE_ROOT/last-session"
  rom=$(sed -n '2p' "$STATE_ROOT/local-ready")
  working=$(sed -n '3p' "$STATE_ROOT/local-ready")
  printf '%s\n' "$peer" >"$STATE_ROOT/last-peer"
  dialog --clear --title "$TITLE" --infobox \
    "CONNECTING TO PLAYER 1\n\nPeer: $peer\n\nChecking local games, exchanging protected save copies, and preparing the synchronized launch..." \
    11 66 </dev/tty >/dev/tty 2>/dev/tty
  stop_controller_input
  if output=$($SESSION_TOOL join --peer "$peer" --port "$port" --token "$token" \
      --session "$session" --rom "$rom" --save "$working" 2>&1); then
    start_controller_input
    result_save=$(sed -n 's/^result_save=//p' <<<"$output" | tail -n 1)
    finish_session "$session" "$result_save"
  else
    start_controller_input
    message "LINK SESSION ENDED SAFELY\n\n$output\n\nYour original save was not changed. The verified backup and working copy were retained."
  fi
}

finish_session() {
  local session=${1:?} result_save=${2:?} output
  if confirm "LINK SESSION FINISHED\n\nSave the trade or battle results to your selected game save?\n\nContinue verifies and commits only your own updated save. Cancel leaves the original untouched."; then
    if output=$($SAVE_TOOL commit "$session" "$result_save" 2>&1); then
      rm -f "$STATE_ROOT/local-ready"
      message "RESULTS SAVED SAFELY\n\n$output\n\nThe pre-session recovery backup was retained."
    else
      message "RESULTS WERE NOT WRITTEN\n\n$output\n\nYour original save and verified backup remain available."
    fi
  else
    message "ORIGINAL SAVE UNCHANGED\n\nThe session working copy and verified backup were retained. You can inspect or cancel the session from this menu."
  fi
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
      message "BUTTERFLY LINK\n\nEach player uses legally obtained games and their own save. ROM files never cross the network. Both devices must already contain matching local copies of both selected games.\n\nButterflyOS backs up each original, exchanges isolated save copies, launches the linked session, and asks before committing each player's result."
      ;;
    close) break ;;
  esac
done

clear
