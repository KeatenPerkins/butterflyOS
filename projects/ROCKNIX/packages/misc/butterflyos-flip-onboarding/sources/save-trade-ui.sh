#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Keaten Perkins

set -u

TITLE="Butterfly Link"
BACKTITLE="ButterflyOS  •  Butterfly Link"
# Dialog used a fixed 24x64 box, which left a large unused area on the Flip
# and made the list feel detached from the rest of the ButterflyOS UI.  Size
# each screen from the actual terminal while leaving a one-cell safe margin.
read -r _TERM_ROWS _TERM_COLS < <(stty size </dev/tty 2>/dev/null || printf '30 80')
_TERM_ROWS=${_TERM_ROWS:-30}
_TERM_COLS=${_TERM_COLS:-80}
UI_HEIGHT=$(( _TERM_ROWS > 4 ? _TERM_ROWS - 2 : 0 ))
UI_WIDTH=$(( _TERM_COLS > 4 ? _TERM_COLS - 2 : 0 ))
MENU_LIST_HEIGHT=$(( UI_HEIGHT > 12 ? UI_HEIGHT - 8 : 8 ))
SAVE_TOOL=${BUTTERFLY_SAVE_TRADE_TOOL:-/usr/bin/butterflyos-save-trade}
SPRITE_CACHE_TOOL=${BUTTERFLY_GEN3_SPRITE_CACHE_TOOL:-/usr/bin/butterflyos-gen3-sprite-cache.py}
GB_SPRITE_CACHE_TOOL=${BUTTERFLY_GB_SPRITE_CACHE_TOOL:-/usr/bin/butterflyos-gb-sprite-cache.py}
STATE_ROOT=${BUTTERFLY_SAVE_TRADE_STATE_ROOT:-/storage/.config/butterflyos/save-trade}
CONTROLLER_CONFIG=/usr/share/butterflyos/flip-onboarding.gptk
SAVE_TRADE_CONTROLLER_CONFIG=${BUTTERFLY_SAVE_TRADE_CONTROLLER_CONFIG:-/usr/share/butterflyos/save-trade.gptk}
CONTROLLER_PID=
DIALOGRC_PATH=/usr/share/butterflyos/save-trade.dialogrc

if [[ -f "${DIALOGRC_PATH}" ]]; then
  export DIALOGRC="${DIALOGRC_PATH}"
fi

stop_controller_input() {
  if [[ -n "${CONTROLLER_PID}" ]]; then
    kill -9 "${CONTROLLER_PID}" 2>/dev/null || true
    wait "${CONTROLLER_PID}" 2>/dev/null || true
  fi
}

start_controller_input() {
  /usr/bin/control-gen_init.sh >/dev/null 2>&1 || true
  if [[ -f /storage/.config/gptokeyb/control.ini && -f "${SAVE_TRADE_CONTROLLER_CONFIG}" ]]; then
    source /storage/.config/gptokeyb/control.ini
    get_controls
    /usr/bin/gptokeyb -c "${SAVE_TRADE_CONTROLLER_CONFIG}" >/dev/null 2>&1 &
    CONTROLLER_PID=$!
  fi
}

message() {
  dialog --clear --backtitle "${BACKTITLE}" --title "${TITLE}" --ok-label "Continue" --msgbox "$1" "${UI_HEIGHT}" "${UI_WIDTH}" \
    </dev/tty >/dev/tty 2>/dev/tty
}

confirm() {
  dialog --clear --backtitle "${BACKTITLE}" --title "${TITLE}" \
    --yes-label "Continue" --no-label "Cancel" \
    --yesno "$1" "${UI_HEIGHT}" "${UI_WIDTH}" </dev/tty >/dev/tty 2>/dev/tty
}

menu() {
  local prompt=$1; shift
  dialog --clear --backtitle "${BACKTITLE}" --title "${TITLE}" \
    --no-shadow --ok-label "Select" --cancel-label "Back" --menu "${prompt}" "${UI_HEIGHT}" "${UI_WIDTH}" "${MENU_LIST_HEIGHT}" "$@" \
    </dev/tty 2>&1 >/dev/tty
}

card_label() {
  case "$1" in
    /storage/games-external/*) printf 'Game Card' ;;
    *) printf 'OS Card' ;;
  esac
}

save_list_file() {
  local list="$STATE_ROOT/save-list"
  local path canonical index=0
  local -A seen=()
  mkdir -p "${STATE_ROOT}"
  : >"${list}"
  while IFS= read -r -d '' path; do
    canonical=$(readlink -f -- "$path" 2>/dev/null || true)
    [[ -n "${canonical}" && -f "${canonical}" ]] || continue
    [[ -z "${seen[$canonical]:-}" ]] || continue
    seen[$canonical]=1
    index=$((index + 1))
    printf '%s\t%s\n' "${index}" "${canonical}" >>"${list}"
  done < <(find /storage/roms /storage/games-external/roms \
    \( -type f -o -type l \) \( -iname '*.srm' -o -iname '*.sav' \) \
    -print0 2>/dev/null)
  printf '%s\n' "${list}"
}

inspect_raw() {
  "${SAVE_TOOL}" inspect --save "$1" 2>&1
}

field() {
  local data=$1 key=$2
  awk -F= -v key="${key}" '$1 == key {sub(/^[^=]*=/, ""); print; exit}' <<<"${data}"
}

pokemon_name() {
  local nickname=$1 species=$2
  case "${nickname}" in
    ""|"(none)"|Unknown) printf 'Species #%s' "${species}" ;;
    *) printf '%s' "${nickname}" ;;
  esac
}

save_descriptor() {
  local path=$1 data type trainer occupied
  data=$(inspect_raw "${path}") || return 1
  type=$(field "${data}" save_type)
  trainer=$(field "${data}" trainer_name)
  occupied=$(field "${data}" box_occupied)
  printf '%s | %s | %s | PC:%s' \
    "$(card_label "${path}")" "${type:-unknown}" "${trainer:-Unknown}" "${occupied:-0}"
}

select_save() {
  local gen3_only=${1:-0} generation_filter=${2:-} list path index choice data descriptor
  local -a choices=()
  declare -A paths=()
  list=$(save_list_file)
  while IFS=$'\t' read -r index path; do
    [[ -n "${index}" && -f "${path}" ]] || continue
    data=$(inspect_raw "${path}" 2>/dev/null) || continue
    if (( gen3_only )) && [[ "$(field "${data}" generation)" != 3 ]]; then
      continue
    fi
    if [[ -n "${generation_filter}" && "$(field "${data}" generation)" != "${generation_filter}" ]]; then
      continue
    fi
    descriptor=$(save_descriptor "${path}") || continue
    paths[${index}]=${path}
    choices+=("${index}" "${descriptor} | ${path##*/}")
  done <"${list}"
  if (( ${#choices[@]} == 0 )); then
    if (( gen3_only )); then
      message "NO COMPATIBLE SAVES FOUND\n\nThis workflow currently needs two readable Gen III .srm or .sav files. Add compatible saves to the OS card or Game Card, then try again."
    else
      message "NO SAVE FILES FOUND\n\nAdd a legally obtained .srm or .sav file to the OS card or Game Card, then try again."
    fi
    return 1
  fi
  choice=$(menu "Choose a save. Trainer, game, card, and boxed count are shown." \
    "${choices[@]}") || return 1
  printf '%s\n' "${paths[$choice]}"
}

select_generation() {
  local choice
  choice=$(menu "Choose a generation." \
    gen1 "Generation 1  •  Red / Blue / Yellow" \
    gen2 "Generation 2  •  Gold / Silver / Crystal" \
    gen3 "Generation 3  •  Ruby / Sapphire / Emerald / FRLG") || return 1
  printf '%s\n' "${choice}"
}

select_transfer_mode() {
  local choice
  choice=$(menu "Choose how to move the Pokemon." \
    swap "Trade / Swap  •  exchange two Pokemon" \
    copy "Copy  •  leave the source unchanged") || return 1
  printf '%s\n' "${choice}"
}

remote_workflow() {
  message "ANOTHER BUTTERFLYOS DEVICE\n\nThis screen is reserved for two-device trading. The connection and transfer layer is still being hardened, so no network session will be started from this build.\n\nFor a safe test today, choose LOCAL SAVE TRADE and work with protected copies on this device.\n\nNothing was changed."
}

local_trade_workflow() {
  local generation mode
  generation=$(select_generation) || return
  case "${generation}" in
    gen3)
      mode=$(select_transfer_mode) || return
      case "${mode}" in
        swap) prepare_workflow ;;
        copy) copy_workflow ;;
      esac
      ;;
    gen1|gen2)
      mode=$(select_transfer_mode) || return
      case "${mode}" in
        swap) prepare_gen12_workflow "${generation#gen}" ;;
        copy) copy_gen12_workflow "${generation#gen}" ;;
      esac
      ;;
  esac
}

rom_list_file() {
  local generation=$1 list="$STATE_ROOT/gen${1}-rom-list"
  local extension directory path canonical index=0
  local -A seen=()
  case "${generation}" in
    1) directory=gb; extension='*.gb' ;;
    2) directory=gbc; extension='*.gbc' ;;
    3) directory=gba; extension='*.gba' ;;
    *) return 1 ;;
  esac
  mkdir -p "${STATE_ROOT}"
  : >"${list}"
  while IFS= read -r -d '' path; do
    canonical=$(readlink -f -- "$path" 2>/dev/null || true)
    [[ -n "${canonical}" && -f "${canonical}" ]] || continue
    [[ -z "${seen[$canonical]:-}" ]] || continue
    seen[$canonical]=1
    index=$((index + 1))
    printf '%s\t%s\n' "${index}" "${canonical}" >>"${list}"
  done < <(find "/storage/roms/${directory}" "/storage/games-external/roms/${directory}" \
    -type f -iname "${extension}" -print0 2>/dev/null)
  printf '%s\n' "${list}"
}

select_rom() {
  local generation=$1 list path index choice label
  local -a choices=()
  declare -A paths=()
  list=$(rom_list_file "${generation}")
  while IFS=$'\t' read -r index path; do
    [[ -n "${index}" && -f "${path}" ]] || continue
    paths[${index}]=${path}
    choices+=("${index}" "$(card_label "${path}") | ${path##*/}")
  done <"${list}"
  if (( ${#choices[@]} == 0 )); then
    case "${generation}" in
      1) label="Gen I .gb" ;;
      2) label="Gen II .gbc" ;;
      3) label="Gen III .gba" ;;
    esac
    message "NO COMPATIBLE ROMS FOUND\n\nAdd a legally obtained ${label} ROM to the OS Card or Game Card, then try again."
    return 1
  fi
  choice=$(menu "Choose the Generation ${generation} ROM whose sprites should be cached locally." \
    "${choices[@]}") || return 1
  printf '%s\n' "${paths[$choice]}"
}

sprite_cache_workflow() {
  local generation rom output tool
  generation=$(select_generation) || return
  rom=$(select_rom "${generation#gen}") || return
  if [[ "${generation}" == gen3 ]]; then
    tool=${SPRITE_CACHE_TOOL}
  else
    tool=${GB_SPRITE_CACHE_TOOL}
  fi
  message "SPRITE CACHE\n\nThe first run extracts front sprites from this ROM and stores them locally. Generation II and III also cache shiny palettes. This can take a little while and does not modify the ROM or save file.\n\nPress A to begin."
  if ! output=$(python3 "${tool}" "${rom}" \
      --cache-root "${STATE_ROOT}/sprite-cache" 2>&1); then
    message "SPRITE CACHE FAILED\n\n${output}\n\nThe ROM and save files were not changed."
    return
  fi
  message "SPRITE CACHE READY\n\n${output}\n\nFuture Butterfly Link screens will reuse this cache. It is regenerated automatically if the ROM changes."
}

box_count() {
  local data=$1 box=$2
  awk -F'\t' -v box="${box}" \
    '$1 == "box_record" && $2 == box { count++ } END { print count + 0 }' <<<"${data}"
}

save_summary() {
  local path=$1 data party_count trainer gender type occupied
  local party_lines='' box_lines='' record slot species personality nickname box count
  data=$(inspect_raw "${path}") || {
    printf 'Unable to inspect %s' "${path##*/}"
    return 1
  }
  trainer=$(field "${data}" trainer_name)
  gender=$(field "${data}" trainer_gender)
  type=$(field "${data}" save_type)
  party_count=$(field "${data}" party_count)
  occupied=$(field "${data}" box_occupied)
  while IFS=$'\t' read -r record slot species personality nickname shiny; do
    [[ "${record}" == party_record ]] || continue
    [[ "${shiny:-no}" == yes ]] && shiny=" [SHINY]" || shiny=""
    party_lines+="  - $(pokemon_name "${nickname}" "${species}")${shiny} (Species #${species})"$'\n'
  done <<<"${data}"
  [[ -n "${party_lines}" ]] || party_lines=$'  - None\n'
  for ((box=0; box<14; box++)); do
    count=$(box_count "${data}" "${box}")
    (( count > 0 )) && box_lines+="  Box $((box + 1)): ${count} Pokemon"$'\n'
  done
  [[ -n "${box_lines}" ]] || box_lines=$'  No boxed Pokemon\n'
  printf 'File: %s\nCard: %s\nTrainer: %s (%s)\nSave type: %s\nParty: %s\n%s\nPC total: %s\n%s' \
    "${path##*/}" "$(card_label "${path}")" "${trainer:-Unknown}" \
    "${gender:-unknown}" "${type:-unknown}" "${party_count:-0}" \
    "${party_lines}" "${occupied:-0}" "${box_lines}"
}

save_card() {
  local path=$1 data trainer type party_count occupied party_names='' box_lines='' \
    record slot species personality nickname shiny box count
  data=$(inspect_raw "${path}") || return 1
  trainer=$(field "${data}" trainer_name)
  type=$(field "${data}" save_type)
  party_count=$(field "${data}" party_count)
  occupied=$(field "${data}" box_occupied)
  while IFS=$'\t' read -r record slot species personality nickname shiny; do
    [[ "${record}" == party_record ]] || continue
    [[ -n "${party_names}" ]] && party_names+=", "
    party_names+="$(pokemon_name "${nickname}" "${species}")"
  done <<<"${data}"
  [[ -n "${party_names}" ]] || party_names="None"
  for ((box=0; box<14; box++)); do
    count=$(box_count "${data}" "${box}")
    (( count > 0 )) && box_lines+="B$((box + 1)):${count}  "
  done
  [[ -n "${box_lines}" ]] || box_lines="No boxed Pokemon"
  printf 'File: %s\nCard: %s\nGame: %s\nTrainer: %s\nParty: %s\nPC: %s Pokemon\nBoxes: %s' \
    "${path##*/}" "$(card_label "${path}")" "${type:-unknown}" \
    "${trainer:-Unknown}" "${party_names}" "${occupied:-0}" "${box_lines}"
}

select_box() {
  local path=$1 label=$2 generation=${3:-3} data box count choice boxes=14
  local -a choices=()
  [[ "${generation}" == 1 ]] && boxes=12
  data=$(inspect_raw "${path}") || return 1
  for ((box=0; box<boxes; box++)); do
    count=$(box_count "${data}" "${box}")
    if (( count > 0 )); then
      choices+=("${box}" "Box $((box + 1)) - ${count} Pokemon")
    else
      choices+=("${box}" "Box $((box + 1)) - empty")
    fi
  done
  while true; do
    choice=$(menu "${label}: choose a PC box." "${choices[@]}") || return 1
    count=$(box_count "${data}" "${choice}")
    if (( count > 0 )); then
      printf '%s\n' "${choice}"
      return 0
    fi
    message "EMPTY BOX\n\nBox $((choice + 1)) has no Pokemon. Choose a box with a Pokemon to trade."
  done
}

select_slot() {
  local path box label data record record_box slot species personality nickname choice
  local -a choices=()
  path=$1; box=$2; label=$3
  data=$(inspect_raw "${path}") || return 1
  while IFS=$'\t' read -r record record_box slot species personality nickname shiny; do
    [[ "${record}" == box_record && "${record_box}" == "${box}" ]] || continue
    [[ "${shiny:-no}" == yes ]] && shiny=" [SHINY]" || shiny=""
    choices+=("${slot}" "Slot $((slot + 1)) - $(pokemon_name "${nickname}" "${species}")${shiny} (Species #${species})")
  done <<<"${data}"
  [[ ${#choices[@]} -gt 0 ]] || {
    message "EMPTY BOX\n\nThis box no longer contains a Pokemon. Choose another box."
    return 1
  }
  choice=$(menu "${label}: choose a Pokemon. A protected copy is used." \
    "${choices[@]}") || return 1
  printf '%s\n' "${choice}"
}

select_destination_box() {
  local path=$1 label=$2 generation=${3:-3} data box count choice boxes=14
  local -a choices=()
  [[ "${generation}" == 1 ]] && boxes=12
  data=$(inspect_raw "${path}") || return 1
  for ((box=0; box<boxes; box++)); do
    count=$(box_count "${data}" "${box}")
    choices+=("${box}" "Box $((box + 1))  •  ${count} Pokemon")
  done
  choice=$(menu "${label}: choose a destination PC box." "${choices[@]}") || return 1
  printf '%s\n' "${choice}"
}

# Gen I/II box records are contiguous: a copied Pokemon must be appended at
# the current count, rather than dropped into an arbitrary empty hole.
select_append_slot() {
  local path=$1 box=$2 label=$3 data count
  data=$(inspect_raw "${path}") || return 1
  count=$(box_count "${data}" "${box}")
  if (( count >= 20 )); then
    message "BOX FULL\n\nBox $((box + 1)) already contains 20 Pokemon. Choose another destination box."
    return 1
  fi
  confirm "${label}: add the copied Pokemon to Box $((box + 1)), Slot $((count + 1))?\n\nGeneration I and II PC boxes are kept in their original contiguous order." || return 1
  printf '%s\n' "${count}"
}

select_empty_slot() {
  local path=$1 box=$2 label=$3 data record record_box record_slot occupied choice
  local -a choices=()
  data=$(inspect_raw "${path}") || return 1
  for ((slot=0; slot<30; slot++)); do
    occupied=0
    while IFS=$'\t' read -r record record_box record_slot _species _personality _nickname _shiny; do
      [[ "${record}" == box_record && "${record_box}" == "${box}" && "${record_slot}" == "${slot}" ]] && occupied=1
    done <<<"${data}"
    (( occupied )) || choices+=("${slot}" "Slot $((slot + 1))  •  empty")
  done
  if (( ${#choices[@]} == 0 )); then
    message "BOX FULL\n\nChoose another destination box with an empty slot."
    return 1
  fi
  choice=$(menu "${label}: choose an empty slot." "${choices[@]}") || return 1
  printf '%s\n' "${choice}"
}

slot_description() {
  local path=$1 box=$2 slot=$3 data record record_box record_slot species personality nickname
  data=$(inspect_raw "${path}") || return 1
  while IFS=$'\t' read -r record record_box record_slot species personality nickname shiny; do
    [[ "${record}" == box_record && "${record_box}" == "${box}" && \
       "${record_slot}" == "${slot}" ]] || continue
    if [[ "${shiny:-no}" == yes ]]; then
      printf '%s [SHINY] (Species #%s)' "$(pokemon_name "${nickname}" "${species}")" "${species}"
    else
      printf '%s (Species #%s)' "$(pokemon_name "${nickname}" "${species}")" "${species}"
    fi
    return 0
  done <<<"${data}"
  printf 'Empty slot'
}

copy_gen12_workflow() {
  local generation=$1 source destination source_box source_slot destination_box destination_slot
  local id dir output source_name destination_name
  message "LOCAL COPY  •  GENERATION ${generation}\n\nChoose a source save and boxed Pokemon. The source save remains unchanged.\n\nOnly same-generation saves are supported."
  source=$(select_save 0 "${generation}") || return
  message "SOURCE SAVE\n\n$(save_card "${source}")\n\nChoose a boxed Pokemon to copy."
  source_box=$(select_box "${source}" "Source PC" "${generation}") || return
  source_slot=$(select_slot "${source}" "${source_box}" "Source PC") || return
  destination=$(select_save 0 "${generation}") || return
  [[ "${source}" != "${destination}" ]] || {
    message "CHOOSE TWO FILES\n\nThe source and destination saves must be different files."
    return
  }
  message "DESTINATION SAVE\n\n$(save_card "${destination}")\n\nChoose a destination PC box."
  destination_box=$(select_destination_box "${destination}" "Destination PC" "${generation}") || return
  destination_slot=$(select_append_slot "${destination}" "${destination_box}" "Destination PC") || return
  source_name=$(slot_description "${source}" "${source_box}" "${source_slot}")
  destination_name=$(save_card "${destination}")
  confirm "PREPARE A SAFE COPY?\n\nCopy: ${source_name}\nFrom: ${source##*/}, Box $((source_box + 1)), Slot $((source_slot + 1))\nTo: ${destination##*/}, Box $((destination_box + 1)), Slot $((destination_slot + 1))\n\nThe source stays unchanged. A protected destination copy will be created first." || return

  id="$(date -u '+%Y%m%dT%H%M%SZ')-$$-${RANDOM}"
  dir="${STATE_ROOT}/sessions/${id}"
  mkdir -p "${dir}"
  output="${dir}/destination-${destination##*/}"
  if ! output=$(${SAVE_TOOL} "copy-gen${generation}" \
      --source "${source}" --source-box "${source_box}" --source-slot "${source_slot}" \
      --destination "${destination}" --destination-box "${destination_box}" \
      --destination-slot "${destination_slot}" --output-destination "${output}" 2>&1); then
    rm -rf "${dir}"
    message "COPY COULD NOT BE PREPARED\n\n${output}\n\nNo original save was changed."
    return
  fi
  printf '%s\n' COPY >"${dir}/mode"
  printf '%s\n' "${source}" >"${dir}/source-original"
  printf '%s\n' "${destination}" >"${dir}/destination-original"
  printf '%s\n' READY >"${dir}/state"
  message "COPY READY\n\n${source_name} is ready to be added to the destination save.\n\nThe source is untouched. Use Commit Latest Transfer only when you are ready to write the protected destination copy."
}

prepare_gen12_workflow() {
  local generation=$1 left right left_box left_slot right_box right_slot id dir output
  local left_name right_name left_out right_out
  message "LOCAL TRADE  •  GENERATION ${generation}\n\nChoose two same-generation save files and one boxed Pokemon from each.\n\nOriginal saves are never edited during selection."
  left=$(select_save 0 "${generation}") || return
  right=$(select_save 0 "${generation}") || return
  [[ "${left}" != "${right}" ]] || {
    message "CHOOSE TWO FILES\n\nThe two saves must be different files."
    return
  }
  message "TRADE SETUP\n\nPLAYER 1\n$(save_card "${left}")\n\nPLAYER 2\n$(save_card "${right}")\n\nNext: choose one boxed Pokemon from each save."
  left_box=$(select_box "${left}" "Left player's PC" "${generation}") || return
  left_slot=$(select_slot "${left}" "${left_box}" "Left player's PC") || return
  left_name=$(slot_description "${left}" "${left_box}" "${left_slot}")
  right_box=$(select_box "${right}" "Right player's PC" "${generation}") || return
  right_slot=$(select_slot "${right}" "${right_box}" "Right player's PC") || return
  right_name=$(slot_description "${right}" "${right_box}" "${right_slot}")
  confirm "PREPARE A SAFE BOX SWAP?\n\nLeft: ${left_name}\n${left##*/}, Box $((left_box + 1)), Slot $((left_slot + 1))\n\nRight: ${right_name}\n${right##*/}, Box $((right_box + 1)), Slot $((right_slot + 1))\n\nBoth originals remain untouched. A protected working copy will be created." || return

  id="$(date -u '+%Y%m%dT%H%M%SZ')-$$-${RANDOM}"
  dir="${STATE_ROOT}/sessions/${id}"
  mkdir -p "${dir}"
  left_out="${dir}/left-${left##*/}"
  right_out="${dir}/right-${right##*/}"
  if ! output=$(${SAVE_TOOL} "swap-gen${generation}" \
      --left "${left}" --left-box "${left_box}" --left-slot "${left_slot}" \
      --right "${right}" --right-box "${right_box}" --right-slot "${right_slot}" \
      --output-left "${left_out}" --output-right "${right_out}" 2>&1); then
    rm -rf "${dir}"
    message "SWAP COULD NOT BE PREPARED\n\n${output}\n\nNo original save was changed."
    return
  fi
  printf '%s\n' "${left}" >"${dir}/left-original"
  printf '%s\n' "${right}" >"${dir}/right-original"
  printf '%s\n' READY >"${dir}/state"
  message "SAFE SWAP READY\n\n${output}\n\nThe originals are untouched. Review the result, then use Commit Latest Swap if you want to install both copies."
}

copy_workflow() {
  local source destination source_box source_slot destination_box destination_slot
  local id dir output destination_name source_name
  message "LOCAL COPY  •  GENERATION 3\n\nChoose the source save and Pokemon first. The source save will remain unchanged."
  source=$(select_save 1) || return
  source_name=$(save_card "${source}")
  message "SOURCE SAVE\n\n${source_name}\n\nChoose a boxed Pokemon to copy."
  source_box=$(select_box "${source}" "Source PC") || return
  source_slot=$(select_slot "${source}" "${source_box}" "Source PC") || return
  destination=$(select_save 1) || return
  [[ "${source}" != "${destination}" ]] || {
    message "CHOOSE TWO FILES\n\nThe source and destination saves must be different files."
    return
  }
  destination_name=$(save_card "${destination}")
  message "DESTINATION SAVE\n\n${destination_name}\n\nChoose an empty PC slot for the copied Pokemon."
  destination_box=$(select_destination_box "${destination}" "Destination PC") || return
  destination_slot=$(select_empty_slot "${destination}" "${destination_box}" "Destination PC") || return
  source_name=$(slot_description "${source}" "${source_box}" "${source_slot}")
  confirm "PREPARE A SAFE COPY?\n\nCopy: ${source_name}\nFrom: ${source##*/}, Box $((source_box + 1)), Slot $((source_slot + 1))\nTo: ${destination##*/}, Box $((destination_box + 1)), Slot $((destination_slot + 1))\n\nThe source stays unchanged. A protected destination copy will be created first." || return

  id="$(date -u '+%Y%m%dT%H%M%SZ')-$$-${RANDOM}"
  dir="${STATE_ROOT}/sessions/${id}"
  mkdir -p "${dir}"
  output="${dir}/destination-${destination##*/}"
  if ! output=$(${SAVE_TOOL} copy-gen3 \
      --source "${source}" --source-box "${source_box}" --source-slot "${source_slot}" \
      --destination "${destination}" --destination-box "${destination_box}" \
      --destination-slot "${destination_slot}" --output-destination "${output}" 2>&1); then
    rm -rf "${dir}"
    message "COPY COULD NOT BE PREPARED\n\n${output}\n\nNo original save was changed."
    return
  fi
  printf '%s\n' COPY >"${dir}/mode"
  printf '%s\n' "${source}" >"${dir}/source-original"
  printf '%s\n' "${destination}" >"${dir}/destination-original"
  printf '%s\n' READY >"${dir}/state"
  message "COPY READY\n\n${source_name} is ready to be added to the destination save.\n\nThe source is untouched. Use Commit Latest Transfer only when you are ready to write the protected destination copy."
}

inspect_workflow() {
  local save output
  save=$(select_save) || return
  output=$(save_summary "${save}")
  message "SAVE INSPECTION - READ ONLY\n\n${output}\n\nUse the directional buttons and A to choose. B returns to the previous screen."
}

prepare_workflow() {
  local left right left_box left_slot right_box right_slot id dir output
  local left_name right_name
  local left_out right_out
  message "LOCAL TRADE  •  GENERATION 3\n\nChoose the first save file. Butterfly Link will show the trainer, party, and PC contents before you choose a Pokemon.\n\nOriginal saves are never edited during selection."
  left=$(select_save 1) || return
  message "PLAYER 1 SAVE\n\n$(save_card "${left}")\n\nNext: choose the second save file."
  right=$(select_save 1) || return
  [[ "${left}" != "${right}" ]] || {
    message "CHOOSE TWO FILES\n\nThe left and right saves must be different files."
    return
  }
  message "TRADE SETUP\n\nPLAYER 1\n$(save_card "${left}")\n\nPLAYER 2\n$(save_card "${right}")\n\nNext: choose one boxed Pokemon from each save."
  left_box=$(select_box "${left}" "Left player's PC") || return
  left_slot=$(select_slot "${left}" "${left_box}" "Left player's PC") || return
  left_name=$(slot_description "${left}" "${left_box}" "${left_slot}")
  message "RIGHT PLAYER SAVE\n\n$(save_summary "${right}")\n\nNext, choose the Pokemon this player will trade."
  right_box=$(select_box "${right}" "Right player's PC") || return
  right_slot=$(select_slot "${right}" "${right_box}" "Right player's PC") || return
  right_name=$(slot_description "${right}" "${right_box}" "${right_slot}")
  confirm "PREPARE A SAFE BOX SWAP?\n\nLeft: ${left_name}\n${left##*/}, Box $((left_box + 1)), Slot $((left_slot + 1))\n\nRight: ${right_name}\n${right##*/}, Box $((right_box + 1)), Slot $((right_slot + 1))\n\nBoth originals remain untouched. A new protected working copy will be created." || return

  id="$(date -u '+%Y%m%dT%H%M%SZ')-$$-${RANDOM}"
  dir="${STATE_ROOT}/sessions/${id}"
  mkdir -p "${dir}"
  left_out="${dir}/left-${left##*/}"
  right_out="${dir}/right-${right##*/}"
  if ! output=$(${SAVE_TOOL} swap-gen3 \
      --left "${left}" --left-box "${left_box}" --left-slot "${left_slot}" \
      --right "${right}" --right-box "${right_box}" --right-slot "${right_slot}" \
      --output-left "${left_out}" --output-right "${right_out}" 2>&1); then
    rm -rf "${dir}"
    message "SWAP COULD NOT BE PREPARED\n\n${output}\n\nNo original save was changed."
    return
  fi
  printf '%s\n' "${left}" >"${dir}/left-original"
  printf '%s\n' "${right}" >"${dir}/right-original"
  printf '%s\n' READY >"${dir}/state"
  message "SAFE SWAP READY\n\n${output}\n\nThe originals are untouched. Review the result, then use Commit Latest Swap if you want to install both copies."
}

latest_session() {
  local dir latest=
  for dir in "${STATE_ROOT}"/sessions/*; do
    [[ -d "${dir}" && -f "${dir}/state" ]] || continue
    [[ "$(cat "${dir}/state" 2>/dev/null)" == READY ]] || continue
    if [[ -z "${latest}" || "${dir}" > "${latest}" ]]; then latest=${dir}; fi
  done
  [[ -n "${latest}" ]] || return 1
  printf '%s\n' "${latest}"
}

commit_latest() {
  local dir mode left right left_out right_out left_backup right_backup
  local left_tmp right_tmp output
  dir=$(latest_session) || {
    message "NO READY TRANSFER\n\nPrepare a trade or copy first."
    return
  }
  mode=$(cat "${dir}/mode" 2>/dev/null || printf 'SWAP')
  if [[ "${mode}" == COPY ]]; then
    commit_copy_session "${dir}"
    return
  fi
  left=$(cat "${dir}/left-original")
  right=$(cat "${dir}/right-original")
  left_out=$(find "${dir}" -maxdepth 1 -name 'left-*' -type f | head -n 1)
  right_out=$(find "${dir}" -maxdepth 1 -name 'right-*' -type f | head -n 1)
  [[ -f "${left_out}" && -f "${right_out}" ]] || {
    message "SWAP OUTPUT MISSING\n\nThe protected working copy is incomplete. Originals were not changed."
    return
  }
  output=$(save_card "${left_out}")$'\n\n'$(save_card "${right_out}")
  confirm "COMMIT THE LATEST SWAP?\n\n${output}\n\nVerified backups will be created first. If either write fails, the first file is restored from its backup." || return
  left_backup="${dir}/original-left-backup"
  right_backup="${dir}/original-right-backup"
  cp -p -- "${left}" "${left_backup}" && cp -p -- "${right}" "${right_backup}" || {
    message "BACKUP FAILED\n\nNo save was changed. Check available storage and try again."
    return
  }
  left_tmp="${left}.butterfly-save-trade.$$"
  right_tmp="${right}.butterfly-save-trade.$$"
  if ! cp -p -- "${left_out}" "${left_tmp}" || ! cp -p -- "${right_out}" "${right_tmp}"; then
    rm -f -- "${left_tmp}" "${right_tmp}"
    message "WRITE PREPARATION FAILED\n\nThe originals and backups remain unchanged."
    return
  fi
  sync -f "${left_tmp}" 2>/dev/null || sync
  sync -f "${right_tmp}" 2>/dev/null || sync
  if ! mv -f -- "${left_tmp}" "${left}" || ! mv -f -- "${right_tmp}" "${right}"; then
    rm -f -- "${left_tmp}" "${right_tmp}"
    cp -p -- "${left_backup}" "${left}" 2>/dev/null || true
    cp -p -- "${right_backup}" "${right}" 2>/dev/null || true
    sync
    message "COMMIT FAILED SAFELY\n\nThe verified backups were used to restore the originals."
    return
  fi
  sync
  printf '%s\n' COMMITTED >"${dir}/state"
  message "SWAP COMMITTED\n\nBoth saves were replaced only after verified backups were created.\n\nBackup session: ${dir}"
}

commit_copy_session() {
  local dir=$1 source destination destination_out destination_backup destination_tmp output
  source=$(cat "${dir}/source-original" 2>/dev/null || true)
  destination=$(cat "${dir}/destination-original" 2>/dev/null || true)
  destination_out=$(find "${dir}" -maxdepth 1 -name 'destination-*' -type f | head -n 1)
  [[ -f "${source}" && -f "${destination}" && -f "${destination_out}" ]] || {
    message "COPY OUTPUT MISSING\n\nThe protected working copy is incomplete. The source and destination were not changed."
    return
  }
  output=$(save_card "${destination_out}")
  confirm "COMMIT THE LATEST COPY?\n\n${output}\n\nThe source save remains unchanged. A verified destination backup will be created first." || return
  destination_backup="${dir}/original-destination-backup"
  cp -p -- "${destination}" "${destination_backup}" || {
    message "BACKUP FAILED\n\nNo save was changed. Check available storage and try again."
    return
  }
  destination_tmp="${destination}.butterfly-save-trade.$$"
  if ! cp -p -- "${destination_out}" "${destination_tmp}"; then
    rm -f -- "${destination_tmp}"
    message "WRITE PREPARATION FAILED\n\nThe destination and backup remain unchanged."
    return
  fi
  sync -f "${destination_tmp}" 2>/dev/null || sync
  if ! mv -f -- "${destination_tmp}" "${destination}"; then
    rm -f -- "${destination_tmp}"
    cp -p -- "${destination_backup}" "${destination}" 2>/dev/null || true
    sync
    message "COPY FAILED SAFELY\n\nThe verified destination backup was used to restore the original."
    return
  fi
  sync
  printf '%s\n' COMMITTED >"${dir}/state"
  message "COPY COMMITTED\n\nThe source save was left untouched. The destination now contains the copied Pokemon.\n\nBackup session: ${dir}"
}

discard_latest() {
  local dir
  dir=$(latest_session) || {
    message "NO READY SWAP\n\nThere is no uncommitted swap to discard."
    return
  }
  confirm "DISCARD THE LATEST SWAP?\n\nOnly the protected working copies will be removed. Originals are untouched." || return
  rm -rf "${dir}"
  message "SWAP DISCARDED\n\nThe original save files were never changed."
}

about() {
  message "BUTTERFLY LINK\n\nChoose Local transfer to work with protected save copies. Trade / Swap exchanges two boxed Pokemon. Copy leaves the source unchanged and appends a duplicate to a destination PC box.\n\nOriginal saves are never changed during selection. Commit creates a verified backup first.\n\nSame-generation PC transfers are supported for Gen I, Gen II, and Gen III. Party transfers, Gen I-to-II conversion, trade evolution, and network transfer are intentionally not available yet.\n\nNormal and shiny Gen III sprites are cached from the user's own ROM and reused by the transfer preview."
}

run_requested_action() {
  case "${1:-}" in
    local) local_trade_workflow ;;
    remote) remote_workflow ;;
    inspect) inspect_workflow ;;
    sprites) sprite_cache_workflow ;;
    prepare) prepare_workflow ;;
    commit) commit_latest ;;
    discard) discard_latest ;;
    about) about ;;
  esac
}

trap stop_controller_input EXIT INT TERM
mkdir -p "${STATE_ROOT}/sessions"
start_controller_input

if [[ $# -gt 0 ]]; then
  run_requested_action "$1"
  clear
  exit 0
fi

while true; do
  choice=$(menu "Choose an action. A Select  •  B Back" \
    local "Local transfer" \
    remote "Another ButterflyOS device" \
    inspect "Inspect a save  •  read-only" \
    prepare "Resume prepared transfer" \
    commit "Commit prepared transfer" \
    discard "Discard prepared transfer" \
    about "How Butterfly Link works" \
    close "Back to Tools") || break
  case "${choice}" in
    local) local_trade_workflow ;;
    remote) remote_workflow ;;
    inspect) inspect_workflow ;;
    sprites) sprite_cache_workflow ;;
    prepare) prepare_workflow ;;
    commit) commit_latest ;;
    discard) discard_latest ;;
    about) about ;;
    close) break ;;
  esac
done

clear
