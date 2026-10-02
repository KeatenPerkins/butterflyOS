#!/usr/bin/env python3
"""Butterfly Link's on-device SDL front end.

The save-transfer and backup logic remains in ``save-trade-ui.sh``.  This
program owns the presentation of the top-level Butterfly Link screen so the
device uses the same large, high-contrast layout as the design preview.  A
selected action is handed to the existing shell workflow; if SDL2/SDL_ttf is
not available, the launcher falls back to that workflow directly.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import hashlib
import json
import os
import select
import shutil
import signal
import socket
import struct
import subprocess
import sys
import time
import uuid
import zlib
from typing import Optional


WIDTH, HEIGHT = 640, 480
SDL_INIT_VIDEO = 0x00000020
SDL_WINDOW_FULLSCREEN_DESKTOP = 0x00001001
SDL_WINDOW_BORDERLESS = 0x00000010
SDL_RENDERER_ACCELERATED = 0x00000002
SDL_RENDERER_PRESENTVSYNC = 0x00000004
SDL_QUIT = 0x100
SDL_KEYDOWN = 0x300
SDL_JOYBUTTONDOWN = 0x603
SDL_JOYHATMOTION = 0x602
SDL_CONTROLLERBUTTONDOWN = 0x651
SDL_INIT_GAMECONTROLLER = 0x00002000
KEY_RETURN = 13
KEY_ESCAPE = 27
KEY_UP = 1073741906
KEY_DOWN = 1073741905
KEY_LEFT = 1073741904
KEY_RIGHT = 1073741903
KEY_A = ord("a")
KEY_B = ord("b")
KEY_Q = ord("q")
# The Flip's keyboard bridge reports its face buttons as the familiar
# retro-emulator Z/X pair: Z is physical A, X is physical B/Menu.
KEY_CONFIRM = ord("z")
KEY_CANCEL = ord("x")

# SDL_GameController button identifiers. These make the Flip's built-in pad
# and standard Bluetooth pads work directly, without relying on a separate
# keyboard-emulation helper.
CONTROLLER_A = 0
CONTROLLER_B = 1
CONTROLLER_BACK = 4
CONTROLLER_START = 6
CONTROLLER_DPAD_UP = 11
CONTROLLER_DPAD_DOWN = 12
CONTROLLER_DPAD_LEFT = 13
CONTROLLER_DPAD_RIGHT = 14
HAT_UP = 0x01
HAT_RIGHT = 0x02
HAT_DOWN = 0x04
HAT_LEFT = 0x08


class SDL_Rect(ctypes.Structure):
    _fields_ = [("x", ctypes.c_int), ("y", ctypes.c_int),
                ("w", ctypes.c_int), ("h", ctypes.c_int)]


class SDL_Color(ctypes.Structure):
    _fields_ = [("r", ctypes.c_uint8), ("g", ctypes.c_uint8),
                ("b", ctypes.c_uint8), ("a", ctypes.c_uint8)]


PAGES = {
    "main": (
        "BUTTERFLY LINK",
        "Choose an action.  A Select   B Back",
        [
            ("local", "Local transfer"),
            ("remote", "Another ButterflyOS device"),
            ("about", "How Butterfly Link works"),
            ("close", "Back to Tools"),
        ],
    )
}

# Butterfly Link never opens a router port or contacts an Internet service.
# Discovery and the short-lived pairing socket are intentionally limited to
# devices already on the same local network.
LAN_DISCOVERY_PORT = 42676
LAN_SESSION_PORT = 42677
LAN_PROTOCOL_VERSION = 1
LAN_MAX_MESSAGE = 8192
# TCP is a byte stream: a recv can contain one message, part of one, or more
# than one.  Keep any bytes after the first newline for the next protocol
# read rather than silently dropping a coalesced selection/offer message.
_WIRE_BUFFERS: dict[int, bytearray] = {}
REMOTE_MODES = [
    ("GEN 1", "Red / Blue / Yellow trade or copy", "gen1"),
    ("GEN 2", "Gold / Silver / Crystal trade or copy", "gen2"),
    ("GEN 3", "Ruby / Sapphire / Emerald / FRLG trade or copy", "gen3"),
    ("GEN 1 → 2", "Time Capsule-compatible copy", "gen1-to-gen2"),
    ("GEN 2 → 3", "One-way converted copy", "gen2-to-gen3"),
]


class LinkNetworkError(RuntimeError):
    """A local Butterfly Link network session could not be established."""


def _device_name() -> str:
    # Butterfly Link is a user-facing ButterflyOS feature.  Do not expose an
    # upstream hostname such as "rocknix" during pairing, even if a base image
    # has not yet updated /etc/hostname.
    try:
        with open("/etc/hostname", encoding="utf-8") as handle:
            hostname = handle.read().strip()
        if hostname and hostname.lower() not in ("rocknix", "rk3566", "batocera"):
            return hostname
    except OSError:
        pass
    return "ButterflyOS"


def _local_ip() -> str:
    """Find the active LAN address without sending application data."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("192.0.2.1", 9))
        return probe.getsockname()[0]
    except OSError:
        return "0.0.0.0"
    finally:
        probe.close()


def _wire_send(connection: socket.socket, document: dict) -> None:
    payload = json.dumps(document, separators=(",", ":")).encode("utf-8") + b"\n"
    if len(payload) > LAN_MAX_MESSAGE:
        raise LinkNetworkError("Butterfly Link message was unexpectedly large.")
    connection.sendall(payload)


def _wire_receive(connection: socket.socket, timeout: float) -> dict:
    deadline = time.monotonic() + timeout
    data = _WIRE_BUFFERS.pop(connection.fileno(), bytearray())
    while time.monotonic() < deadline:
        if b"\n" in data:
            line, remainder = bytes(data).split(b"\n", 1)
            if remainder:
                _WIRE_BUFFERS[connection.fileno()] = bytearray(remainder)
            try:
                document = json.loads(line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise LinkNetworkError("Butterfly Link received an invalid local message.") from error
            if not isinstance(document, dict):
                raise LinkNetworkError("Butterfly Link received an invalid local message.")
            return document
        remaining = max(0.01, deadline - time.monotonic())
        ready, _write, _error = select.select([connection], [], [], remaining)
        if not ready:
            continue
        chunk = connection.recv(1024)
        if not chunk:
            raise LinkNetworkError("The other ButterflyOS device disconnected.")
        data.extend(chunk)
        if len(data) > LAN_MAX_MESSAGE:
            raise LinkNetworkError("Butterfly Link rejected an oversized message.")
    raise LinkNetworkError("The other ButterflyOS device did not respond.")


def _file_digest(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(128 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _send_save_copy(connection: socket.socket, path: str, label: str) -> None:
    """Send a working-save copy only after the peer explicitly accepts it."""
    size = os.path.getsize(path)
    if size <= 0 or size > 1024 * 1024:
        raise LinkNetworkError("Butterfly Link rejected an unexpected save-file size.")
    digest = _file_digest(path)
    _wire_send(connection, {"type": "butterfly-link-save-offer", "label": label,
                            "size": size, "sha256": digest})
    response = _wire_receive(connection, 15.0)
    if response.get("type") != "butterfly-link-save-ready":
        raise LinkNetworkError("The other ButterflyOS device did not accept the prepared save.")
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(128 * 1024), b""):
            connection.sendall(chunk)
    response = _wire_receive(connection, 20.0)
    if response.get("type") != "butterfly-link-save-verified" or response.get("sha256") != digest:
        raise LinkNetworkError("The other ButterflyOS device could not verify the prepared save.")


def _receive_save_copy(connection: socket.socket, destination: str) -> tuple[str, str]:
    """Receive and hash-verify a save into a caller-owned session directory."""
    offer = _wire_receive(connection, 20.0)
    if offer.get("type") != "butterfly-link-save-offer":
        raise LinkNetworkError("The other ButterflyOS device sent an unexpected transfer request.")
    try:
        size = int(offer["size"])
        expected = str(offer["sha256"])
    except (KeyError, TypeError, ValueError) as error:
        raise LinkNetworkError("The other ButterflyOS device sent invalid save details.") from error
    if size <= 0 or size > 1024 * 1024 or len(expected) != 64:
        raise LinkNetworkError("Butterfly Link rejected an unexpected save-file size.")
    _wire_send(connection, {"type": "butterfly-link-save-ready"})
    temporary = destination + ".receiving"
    digest, remaining = hashlib.sha256(), size
    try:
        with open(temporary, "wb") as handle:
            while remaining:
                chunk = connection.recv(min(128 * 1024, remaining))
                if not chunk:
                    raise LinkNetworkError("The other ButterflyOS device disconnected during save transfer.")
                handle.write(chunk)
                digest.update(chunk)
                remaining -= len(chunk)
            handle.flush()
            os.fsync(handle.fileno())
        actual = digest.hexdigest()
        if actual != expected:
            raise LinkNetworkError("The received save did not pass hash verification.")
        os.replace(temporary, destination)
        _wire_send(connection, {"type": "butterfly-link-save-verified", "sha256": actual})
        return str(offer.get("label", "remote save")), actual
    except (OSError, LinkNetworkError):
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _public_record(record: dict) -> dict:
    """Return only the fields the other local device needs to choose safely."""
    return {key: record.get(key) for key in ("box", "slot", "species", "name", "level")}


def _matching_record(save_path: str, expected: dict) -> Optional[dict]:
    """Verify that a peer's advertised PC slot still describes its received save."""
    _generation, _trainer, _save_type, records = save_metadata(save_path)
    try:
        box, slot, species = int(expected["box"]), int(expected["slot"]), int(expected["species"])
    except (KeyError, TypeError, ValueError):
        return None
    for record in records:
        if (record.get("box") == box and record.get("slot") == slot and
                record.get("species") == species):
            return record
    return None


def commit_remote_output(session: str, original: str, output: str) -> tuple[bool, str]:
    """Atomically replace one locally-owned save after preserving its original.

    A remote peer never supplies a destination path: this function is called
    only with a path selected on the local device.  A disconnect therefore can
    at worst leave a prepared session and a backup, never an unverified write.
    """
    try:
        backup = os.path.join(session, "original-local-backup")
        copy_with_sync(original, backup)
        replace_save_with_verified_output(original, output, backup)
        write_session_value(session, "state", "COMMITTED")
        return True, "Local save committed. Its original remains in this Butterfly Link session."
    except OSError as error:
        return False, "Commit failed safely: %s" % error


def _announcement(session_id: str, mode: str) -> dict:
    return {"type": "butterfly-link-announce", "version": LAN_PROTOCOL_VERSION,
            "session": session_id, "host": _device_name(), "ip": _local_ip(),
            "port": LAN_SESSION_PORT, "mode": mode}


def _announce(sock: socket.socket, session_id: str, mode: str) -> None:
    try:
        sock.sendto(json.dumps(_announcement(session_id, mode)).encode("utf-8"),
                    ("255.255.255.255", LAN_DISCOVERY_PORT))
    except OSError:
        # The listener can still be reached on networks that suppress broadcast;
        # a future manual-address fallback will use the same TCP handshake.
        pass


def _discover_hosts(frontend: 'SDLFrontEnd') -> list[dict]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", LAN_DISCOVERY_PORT))
        sock.setblocking(False)
        hosts, deadline = {}, time.monotonic() + 7.0
        while time.monotonic() < deadline:
            frontend.draw_list("FINDING BUTTERFLY LINK HOSTS",
                               "Looking on your current Wi-Fi network. B cancels.",
                               [("SEARCHING", "Waiting for a host session…")], 0,
                               "B / MENU Cancel")
            while True:
                try:
                    payload, address = sock.recvfrom(LAN_MAX_MESSAGE)
                except BlockingIOError:
                    break
                try:
                    item = json.loads(payload.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
                if (not isinstance(item, dict) or item.get("type") != "butterfly-link-announce" or
                        item.get("version") != LAN_PROTOCOL_VERSION or not item.get("session") or
                        not item.get("mode")):
                    continue
                item["ip"] = address[0]
                hosts[str(item["session"])] = item
            key = frontend.next_key()
            if key in (KEY_ESCAPE, KEY_B, ord("B"), KEY_CANCEL, ord("X")):
                return []
            time.sleep(0.02)
        return list(hosts.values())
    finally:
        sock.close()


def _remote_generation(mode: str) -> Optional[int]:
    return {"gen1": 1, "gen2": 2, "gen3": 3,
            "gen1-to-gen2": 1, "gen2-to-gen3": 2}.get(mode)


def _remote_destination_generation(mode: str) -> Optional[int]:
    return {"gen1": 1, "gen2": 2, "gen3": 3,
            "gen1-to-gen2": 2, "gen2-to-gen3": 3}.get(mode)


def _remote_abort(connection: socket.socket, message: str) -> None:
    """Best-effort cancellation notice; never let a network error hide locally."""
    try:
        _wire_send(connection, {"type": "butterfly-link-abort", "message": message[:240]})
    except (OSError, LinkNetworkError):
        pass


def remote_host_transfer(frontend: 'SDLFrontEnd', connection: socket.socket,
                         mode: str, peer: str) -> None:
    """Run a protected remote trade, copy, or generation conversion.

    Only working copies cross the network.  The native helper prepares both
    outputs on the host; each device then commits only the output for the save
    it owns, after both players explicitly approve the review screen.
    """
    generation = _remote_generation(mode)
    destination_generation = _remote_destination_generation(mode)
    debug("remote host transfer started: mode=%s peer=%s" % (mode, peer))
    if generation is None:
        notice(frontend, "REMOTE MODE NOT READY",
               "This generation conversion is not supported.")
        _remote_abort(connection, "This remote transfer type is not ready yet.")
        return
    source_save = choose_save(frontend, generation, "HOST SOURCE SAVE")
    if not source_save:
        _remote_abort(connection, "Host cancelled before choosing a save.")
        return
    source_cache = ensure_sprite_cache(frontend, generation, source_save[0])
    if not source_cache:
        _remote_abort(connection, "Host could not prepare its local sprite cache.")
        return
    source_record = choose_record(frontend, "HOST POKEMON", source_save, source_cache)
    if not source_record:
        _remote_abort(connection, "Host cancelled before choosing a Pokémon.")
        return
    cross_generation = generation != destination_generation
    national_species = None
    if cross_generation:
        national_species = national_species_for(source_record, generation, source_cache)
        maximum = 151 if generation == 1 else 251
        if not isinstance(national_species, int) or not 1 <= national_species <= maximum:
            _remote_abort(connection, "The source ROM could not identify this Pokémon safely.")
            notice(frontend, "MIGRATION BLOCKED", "The matching source ROM could not identify this Pokémon safely.")
            return
    actions = ([("COPY", "Copy into a Gen %d PC; source stays unchanged" % destination_generation)]
               if cross_generation else
               [("TRADE", "Swap with one boxed Pokémon from %s" % peer),
                ("COPY", "Copy into an empty PC slot on %s" % peer)])
    action_choice = choose_list(frontend, "REMOTE ACTION",
                                "Choose what to do with %s." % source_record["name"],
                                actions)
    if action_choice is None:
        _remote_abort(connection, "Host cancelled the transfer.")
        return
    action = "copy" if cross_generation else ("trade" if action_choice == 0 else "copy")
    debug("remote host proposal: generation=%d action=%s" % (generation, action))
    _wire_send(connection, {"type": "butterfly-link-proposal", "generation": generation,
                            "destination_generation": destination_generation, "mode": mode,
                            "action": action, "record": _public_record(source_record),
                            "source": os.path.basename(source_save[0])})
    frontend.draw_list("WAITING FOR %s" % peer.upper(),
                       "The other Flip is choosing its compatible save.",
                       [("WAITING", "No original save has changed")], 0, "Please wait…")
    selection = _wire_receive(connection, 120.0)
    if selection.get("type") == "butterfly-link-abort":
        notice(frontend, "REMOTE TRANSFER CANCELLED", str(selection.get("message", "The other Flip cancelled.")))
        return
    if selection.get("type") != "butterfly-link-selection":
        raise LinkNetworkError("The other Flip returned an invalid transfer selection.")
    if selection.get("action") != action:
        raise LinkNetworkError("The other Flip returned a mismatched transfer action.")
    session = new_session()
    try:
        remote_original = os.path.join(session, "peer-original.srm")
        _receive_save_copy(connection, remote_original)
        debug("remote host received verified peer save")
        received_generation, _trainer, _kind, _records = save_metadata(remote_original)
        if received_generation != destination_generation:
            raise LinkNetworkError("The other Flip sent a save from a different generation.")
        if action == "trade":
            peer_record = _matching_record(remote_original, selection.get("record", {}))
            if not peer_record:
                raise LinkNetworkError("The other Flip's selected Pokémon did not match its verified save.")
            prepared, message = prepare_swap(generation, (source_save[0], source_record),
                                              (remote_original, peer_record))
            if not prepared:
                raise LinkNetworkError(message)
            # prepare_swap owns a new session. Keep the received original with
            # it for a complete recovery record, then discard the outer shell.
            copy_with_sync(remote_original, os.path.join(prepared, "peer-original.srm"))
            shutil.rmtree(session, ignore_errors=True)
            session = prepared
            local_output, peer_output = session_output(session, "left-"), session_output(session, "right-")
            review_right = peer_record
        else:
            try:
                destination_box = int(selection["box"])
                destination_slot = int(selection["slot"])
            except (KeyError, TypeError, ValueError):
                raise LinkNetworkError("The other Flip returned an invalid PC destination.")
            destination = (remote_original, destination_box, destination_slot)
            if mode == "gen1-to-gen2":
                prepared, message = prepare_gen1_to_gen2(
                    (source_save[0], source_record), national_species, destination)
            elif mode == "gen2-to-gen3":
                prepared, message = prepare_gen2_to_gen3(
                    (source_save[0], source_record), national_species, destination)
            else:
                prepared, message = prepare_copy(generation, (source_save[0], source_record), destination)
            if not prepared:
                raise LinkNetworkError(message)
            copy_with_sync(remote_original, os.path.join(prepared, "peer-original.srm"))
            shutil.rmtree(session, ignore_errors=True)
            session = prepared
            local_output, peer_output = None, session_output(session, "destination-")
            review_right = {"name": "Empty PC slot", "box": destination_box, "slot": destination_slot}
        if not peer_output or (action == "trade" and not local_output):
            raise LinkNetworkError("Butterfly Link could not find its protected working copies.")
        _wire_send(connection, {"type": "butterfly-link-prepared", "action": action,
                                "record": _public_record(source_record)})
        _send_save_copy(connection, peer_output, "prepared-by-%s" % _device_name())
        debug("remote host sent verified prepared peer copy")
        _wire_send(connection, {"type": "butterfly-link-review", "action": action})
        peer_review = _wire_receive(connection, 120.0)
        if peer_review.get("type") != "butterfly-link-review" or not peer_review.get("approved"):
            _remote_abort(connection, "The other Flip declined the final review. Original saves are unchanged.")
            notice(frontend, "REMOTE TRANSFER CANCELLED", "The other Flip declined the final review. Original saves are unchanged.")
            return
        host_left = (source_save[0], source_record)
        host_right = ("%s's save" % peer, review_right)
        if not confirm_transfer(frontend, "REMOTE COPIES READY - COMMIT?", host_left, host_right, action=action):
            _remote_abort(connection, "Host declined the final review. Original saves are unchanged.")
            return
        if local_output:
            success, message = commit_remote_output(session, source_save[0], local_output)
            if not success:
                _remote_abort(connection, message)
                notice(frontend, "HOST COMMIT FAILED", message)
                return
            debug("remote host committed local output")
        _wire_send(connection, {"type": "butterfly-link-host-committed", "action": action})
        final = _wire_receive(connection, 45.0)
        if final.get("type") != "butterfly-link-peer-committed":
            notice(frontend, "REMOTE COMMIT INCOMPLETE",
                   "This Flip's original backup is preserved. The other Flip did not confirm its commit.")
            return
        write_session_value(session, "remote-peer-confirmed", "COMMITTED")
        notice(frontend, "REMOTE %s COMPLETE" % action.upper(),
               completion_message(action), completion=True)
    except (OSError, LinkNetworkError, KeyError, ValueError) as error:
        _remote_abort(connection, str(error))
        notice(frontend, "REMOTE TRANSFER FAILED", str(error))
    finally:
        # Prepared sessions are intentionally retained for recovery/audit.
        pass


def remote_join_transfer(frontend: 'SDLFrontEnd', connection: socket.socket, host: str) -> None:
    """Choose the joined Flip's save, receive its working copy, and commit it."""
    proposal = _wire_receive(connection, 180.0)
    debug("remote join received proposal from %s" % host)
    if proposal.get("type") == "butterfly-link-abort":
        notice(frontend, "REMOTE TRANSFER CANCELLED", str(proposal.get("message", "The host cancelled.")))
        return
    if proposal.get("type") != "butterfly-link-proposal":
        raise LinkNetworkError("The host did not send a valid transfer proposal.")
    try:
        generation, action = int(proposal["generation"]), str(proposal["action"])
        destination_generation = int(proposal.get("destination_generation", generation))
    except (KeyError, TypeError, ValueError) as error:
        raise LinkNetworkError("The host sent an invalid transfer proposal.") from error
    if generation not in (1, 2, 3) or action not in ("trade", "copy"):
        raise LinkNetworkError("This host requested an unsupported transfer.")
    mode = proposal.get("mode", "gen%d" % generation)
    if (_remote_generation(mode) != generation or
            _remote_destination_generation(mode) != destination_generation or
            (generation != destination_generation and action != "copy")):
        raise LinkNetworkError("This host requested an unsupported generation conversion.")
    local_save = choose_save(frontend, destination_generation, "JOINED FLIP SAVE")
    if not local_save:
        _remote_abort(connection, "Joined Flip cancelled before choosing a save.")
        return
    local_cache = ensure_sprite_cache(frontend, destination_generation, local_save[0])
    if not local_cache:
        _remote_abort(connection, "Joined Flip could not prepare its local sprite cache.")
        return
    if action == "trade":
        local_record = choose_record(frontend, "YOUR POKEMON", local_save, local_cache)
        if not local_record:
            _remote_abort(connection, "Joined Flip cancelled before choosing a Pokémon.")
            return
        selection = {"type": "butterfly-link-selection", "action": action,
                     "record": _public_record(local_record)}
        right_record = local_record
    else:
        destination = choose_copy_destination(frontend, destination_generation, local_save)
        if not destination:
            _remote_abort(connection, "Joined Flip cancelled before choosing a PC destination.")
            return
        box, slot = destination
        selection = {"type": "butterfly-link-selection", "action": action, "box": box, "slot": slot}
        right_record = {"name": "Empty PC slot", "box": box, "slot": slot}
    _wire_send(connection, selection)
    session = new_session()
    try:
        local_original = local_save[0]
        _send_save_copy(connection, local_original, "original-from-%s" % _device_name())
        debug("remote join sent verified local save")
        prepared = _wire_receive(connection, 60.0)
        if prepared.get("type") == "butterfly-link-abort":
            notice(frontend, "REMOTE TRANSFER CANCELLED", str(prepared.get("message", "The host cancelled.")))
            return
        if prepared.get("type") != "butterfly-link-prepared" or prepared.get("action") != action:
            raise LinkNetworkError("The host did not prepare a compatible working save.")
        output = os.path.join(session, "prepared-from-host.srm")
        _receive_save_copy(connection, output)
        if save_metadata(output)[0] != destination_generation:
            raise LinkNetworkError("The prepared save failed destination-generation validation.")
        debug("remote join received verified prepared output")
        review = _wire_receive(connection, 30.0)
        if review.get("type") != "butterfly-link-review" or review.get("action") != action:
            raise LinkNetworkError("The host did not request the expected final review.")
        host_record = proposal.get("record", {"name": "Host Pokémon"})
        if not confirm_transfer(frontend, "REMOTE COPIES READY - COMMIT?",
                                ("%s's save" % host, host_record), (local_original, right_record), action=action):
            _wire_send(connection, {"type": "butterfly-link-review", "approved": False})
            return
        _wire_send(connection, {"type": "butterfly-link-review", "approved": True})
        decision = _wire_receive(connection, 90.0)
        if decision.get("type") == "butterfly-link-abort":
            notice(frontend, "REMOTE TRANSFER CANCELLED", str(decision.get("message", "The host cancelled.")))
            return
        if decision.get("type") != "butterfly-link-host-committed":
            raise LinkNetworkError("The host did not confirm its local commit.")
        success, message = commit_remote_output(session, local_original, output)
        if not success:
            _remote_abort(connection, message)
            notice(frontend, "JOINED COMMIT FAILED", message)
            return
        debug("remote join committed local output")
        _wire_send(connection, {"type": "butterfly-link-peer-committed"})
        notice(frontend, "REMOTE %s COMPLETE" % action.upper(),
               completion_message(action), completion=True)
    except (OSError, LinkNetworkError, KeyError, ValueError) as error:
        _remote_abort(connection, str(error))
        notice(frontend, "REMOTE TRANSFER FAILED", str(error))


def remote_session_workflow(frontend: 'SDLFrontEnd') -> None:
    """Pair two devices and run a protected save transfer."""
    role = choose_list(frontend, "REMOTE TRANSFER",
                       "Both Flips must be on the same Wi-Fi network.",
                       [("HOST", "Create a Butterfly Link session"),
                        ("JOIN", "Join a session created by another Flip")])
    if role is None:
        return
    if role == 0:
        # Generation conversions reuse the tested local copy-only helpers.
        remote_options = REMOTE_MODES
        mode_index = choose_list(frontend, "HOST: CHOOSE TRANSFER TYPE",
                                 "The joined Flip will be limited to compatible saves.",
                                 [(tag, detail) for tag, detail, _mode in remote_options])
        if mode_index is None:
            return
        mode = remote_options[mode_index][2]
        session_id = uuid.uuid4().hex
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        announcer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        connection = None
        try:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind(("", LAN_SESSION_PORT))
            listener.listen(1)
            listener.setblocking(False)
            announcer.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            last_announce = 0.0
            while True:
                if time.monotonic() - last_announce > 0.6:
                    _announce(announcer, session_id, mode)
                    last_announce = time.monotonic()
                frontend.draw_list("HOSTING BUTTERFLY LINK",
                                   "Mode: %s. Waiting for another Flip to join." % remote_options[mode_index][0],
                                   [("WI-FI", "Session visible to nearby ButterflyOS devices")], 0,
                                   "B / MENU Cancel host session")
                key = frontend.next_key()
                if key in (KEY_ESCAPE, KEY_B, ord("B"), KEY_CANCEL, ord("X")):
                    return
                ready, _write, _error = select.select([listener], [], [], 0)
                if ready:
                    connection, address = listener.accept()
                    hello = _wire_receive(connection, 3.0)
                    if (hello.get("type") != "butterfly-link-join" or
                            hello.get("version") != LAN_PROTOCOL_VERSION or
                            hello.get("session") != session_id):
                        connection.close(); connection = None; continue
                    choice = choose_list(frontend, "JOIN REQUEST",
                                         "%s at %s wants to join." % (hello.get("device", "ButterflyOS"), address[0]),
                                         [("ACCEPT", "Pair for %s" % remote_options[mode_index][0]),
                                          ("DECLINE", "Keep waiting for another device")])
                    if choice != 0:
                        _wire_send(connection, {"type": "butterfly-link-declined"})
                        connection.close(); connection = None; continue
                    _wire_send(connection, {"type": "butterfly-link-paired", "mode": mode,
                                            "host": _device_name()})
                    remote_host_transfer(frontend, connection, mode,
                                         str(hello.get("device", "the other Flip")))
                    return
                time.sleep(0.02)
        except (OSError, LinkNetworkError) as error:
            notice(frontend, "HOST SESSION FAILED", str(error))
        finally:
            if connection:
                connection.close()
            listener.close(); announcer.close()
    else:
        hosts = _discover_hosts(frontend)
        if not hosts:
            notice(frontend, "NO HOST FOUND", "Start Host Session on the other Flip, then try Join again.")
            return
        items = []
        for host in hosts:
            label = "%s  •  %s" % (host.get("host", "ButterflyOS"), host.get("ip", "local network"))
            items.append((str(host.get("mode", "LINK")).upper()[:12], label[:58]))
        selected = choose_list(frontend, "JOIN BUTTERFLY LINK",
                               "Choose the Flip hosting the session.", items)
        if selected is None:
            return
        host = hosts[selected]
        try:
            connection = socket.create_connection((host["ip"], int(host.get("port", LAN_SESSION_PORT))), 5.0)
            _wire_send(connection, {"type": "butterfly-link-join", "version": LAN_PROTOCOL_VERSION,
                                    "session": host["session"], "device": _device_name()})
            frontend.draw_list("JOINING BUTTERFLY LINK", "Waiting for the host to approve this device.",
                               [("WAITING", "The host must select Accept")], 0, "B / MENU Cancel")
            answer = _wire_receive(connection, 10.0)
            if answer.get("type") == "butterfly-link-paired":
                remote_join_transfer(frontend, connection, str(answer.get("host", "the host")))
            elif answer.get("type") == "butterfly-link-declined":
                notice(frontend, "JOIN DECLINED", "The host declined this pairing request.")
            else:
                notice(frontend, "JOIN FAILED", "The host returned an invalid pairing response.")
        except (OSError, KeyError, ValueError, LinkNetworkError) as error:
            notice(frontend, "JOIN FAILED", str(error))
        finally:
            try:
                connection.close()
            except UnboundLocalError:
                pass


class SDLFrontEnd:
    def __init__(self, keyboard_bridge: bool = False) -> None:
        lib_name = ctypes.util.find_library("SDL2") or "libSDL2-2.0.so.0"
        ttf_name = ctypes.util.find_library("SDL2_ttf") or "libSDL2_ttf-2.0.so.0"
        self.sdl = ctypes.CDLL(lib_name)
        self.ttf = ctypes.CDLL(ttf_name)
        self._configure_api()
        self.controllers = []
        self.keyboard_bridge = keyboard_bridge
        self.closed = False
        init_flags = SDL_INIT_VIDEO if keyboard_bridge else (SDL_INIT_VIDEO | SDL_INIT_GAMECONTROLLER)
        if self.sdl.SDL_Init(init_flags) != 0:
            raise RuntimeError(self.sdl.SDL_GetError().decode("utf-8", "replace"))
        if self.ttf.TTF_Init() != 0:
            self.sdl.SDL_Quit()
            # SDL_ttf exposes its errors through SDL_GetError on the target;
            # TTF_GetError is a C header macro, not an exported library symbol.
            raise RuntimeError(self.sdl.SDL_GetError().decode("utf-8", "replace"))
        flags = SDL_WINDOW_FULLSCREEN_DESKTOP | SDL_WINDOW_BORDERLESS
        self.window = self.sdl.SDL_CreateWindow(
            b"Butterfly Link", 0x2FFF0000, 0x2FFF0000, 0, 0, flags
        )
        if not self.window:
            self.close()
            raise RuntimeError(self.sdl.SDL_GetError().decode("utf-8", "replace"))
        self.renderer = self.sdl.SDL_CreateRenderer(
            self.window, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC
        )
        if not self.renderer:
            self.close()
            raise RuntimeError(self.sdl.SDL_GetError().decode("utf-8", "replace"))
        self.sdl.SDL_RenderSetLogicalSize(self.renderer, WIDTH, HEIGHT)
        if not keyboard_bridge:
            self._open_input_devices()
        self.font_path = self._find_font()
        self.fonts = {}
        self.textures = {}

    def _configure_api(self) -> None:
        s = self.sdl
        s.SDL_Init.argtypes = [ctypes.c_uint32]
        s.SDL_Init.restype = ctypes.c_int
        s.SDL_Quit.argtypes = []
        s.SDL_GetError.argtypes = []
        s.SDL_GetError.restype = ctypes.c_char_p
        s.SDL_CreateWindow.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int,
                                       ctypes.c_int, ctypes.c_int, ctypes.c_uint32]
        s.SDL_CreateWindow.restype = ctypes.c_void_p
        s.SDL_DestroyWindow.argtypes = [ctypes.c_void_p]
        s.SDL_CreateRenderer.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_uint32]
        s.SDL_CreateRenderer.restype = ctypes.c_void_p
        s.SDL_DestroyRenderer.argtypes = [ctypes.c_void_p]
        s.SDL_RenderSetLogicalSize.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
        s.SDL_SetRenderDrawColor.argtypes = [ctypes.c_void_p, ctypes.c_uint8,
                                              ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8]
        s.SDL_RenderClear.argtypes = [ctypes.c_void_p]
        s.SDL_RenderPresent.argtypes = [ctypes.c_void_p]
        s.SDL_RenderFillRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(SDL_Rect)]
        s.SDL_RenderDrawRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(SDL_Rect)]
        s.SDL_RenderDrawLine.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                                         ctypes.c_int, ctypes.c_int]
        s.SDL_PollEvent.argtypes = [ctypes.c_void_p]
        s.SDL_PollEvent.restype = ctypes.c_int
        s.SDL_RenderCopy.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                     ctypes.POINTER(SDL_Rect), ctypes.POINTER(SDL_Rect)]
        s.SDL_CreateTextureFromSurface.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        s.SDL_CreateTextureFromSurface.restype = ctypes.c_void_p
        s.SDL_DestroyTexture.argtypes = [ctypes.c_void_p]
        s.SDL_QueryTexture.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32),
                                       ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
                                       ctypes.POINTER(ctypes.c_int)]
        s.SDL_FreeSurface.argtypes = [ctypes.c_void_p]
        s.SDL_NumJoysticks.argtypes = []
        s.SDL_NumJoysticks.restype = ctypes.c_int
        s.SDL_IsGameController.argtypes = [ctypes.c_int]
        s.SDL_IsGameController.restype = ctypes.c_int
        s.SDL_GameControllerOpen.argtypes = [ctypes.c_int]
        s.SDL_GameControllerOpen.restype = ctypes.c_void_p
        s.SDL_GameControllerClose.argtypes = [ctypes.c_void_p]
        s.SDL_JoystickOpen.argtypes = [ctypes.c_int]
        s.SDL_JoystickOpen.restype = ctypes.c_void_p
        s.SDL_JoystickClose.argtypes = [ctypes.c_void_p]

        t = self.ttf
        t.TTF_Init.argtypes = []
        t.TTF_Init.restype = ctypes.c_int
        t.TTF_Quit.argtypes = []
        t.TTF_OpenFont.argtypes = [ctypes.c_char_p, ctypes.c_int]
        t.TTF_OpenFont.restype = ctypes.c_void_p
        t.TTF_CloseFont.argtypes = [ctypes.c_void_p]
        t.TTF_RenderUTF8_Blended.argtypes = [ctypes.c_void_p, ctypes.c_char_p, SDL_Color]
        t.TTF_RenderUTF8_Blended.restype = ctypes.c_void_p

    def _open_input_devices(self) -> None:
        for index in range(self.sdl.SDL_NumJoysticks()):
            if self.sdl.SDL_IsGameController(index):
                opened = self.sdl.SDL_GameControllerOpen(index)
                if opened:
                    self.controllers.append(("controller", opened))
            else:
                opened = self.sdl.SDL_JoystickOpen(index)
                if opened:
                    self.controllers.append(("joystick", opened))

    @staticmethod
    def _find_font() -> str:
        for path in (
            "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",
            "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
        ):
            if os.path.exists(path):
                return path
        raise RuntimeError("Butterfly Link font was not installed")

    def font(self, size: int, bold: bool = False) -> ctypes.c_void_p:
        # The target dejavu package currently ships the condensed regular face.
        # Opening it at a larger size keeps the device UI readable without
        # adding another font package to the image.
        key = (size, bold)
        if key not in self.fonts:
            opened = self.ttf.TTF_OpenFont(self.font_path.encode(), size)
            if not opened:
                raise RuntimeError(self.sdl.SDL_GetError().decode("utf-8", "replace"))
            self.fonts[key] = opened
        return self.fonts[key]

    def text_texture(self, value: str, size: int, color: tuple[int, int, int], bold: bool = False):
        key = (value, size, color, bold)
        if key in self.textures:
            return self.textures[key]
        rgba = SDL_Color(color[0], color[1], color[2], 255)
        surface = self.ttf.TTF_RenderUTF8_Blended(
            self.font(size, bold), value.encode("utf-8"), rgba
        )
        if not surface:
            raise RuntimeError(self.sdl.SDL_GetError().decode("utf-8", "replace"))
        texture = self.sdl.SDL_CreateTextureFromSurface(self.renderer, surface)
        width, height = ctypes.c_int(), ctypes.c_int()
        self.sdl.SDL_QueryTexture(texture, None, None, ctypes.byref(width), ctypes.byref(height))
        self.sdl.SDL_FreeSurface(surface)
        if not texture:
            raise RuntimeError(self.sdl.SDL_GetError().decode("utf-8", "replace"))
        self.textures[key] = (texture, width.value, height.value)
        return self.textures[key]

    def draw_text(self, value: str, x: int, y: int, size: int,
                  color: tuple[int, int, int], *, bold: bool = False,
                  center: bool = False) -> None:
        texture, width, height = self.text_texture(value, size, color, bold)
        if center:
            x -= width // 2
        destination = SDL_Rect(x, y, width, height)
        self.sdl.SDL_RenderCopy(self.renderer, texture, None, ctypes.byref(destination))

    def wrap_text(self, value: str, size: int, width: int) -> list[str]:
        """Wrap by rendered pixel width, including long ROM/save filenames."""
        lines = []
        for paragraph in value.splitlines() or [""]:
            line = ""
            for word in paragraph.split():
                candidate = (line + " " + word).strip()
                if self.text_texture(candidate, size, (255, 255, 255))[1] <= width:
                    line = candidate
                    continue
                if line:
                    lines.append(line)
                    line = ""
                for character in word:
                    candidate = line + character
                    if line and self.text_texture(candidate, size, (255, 255, 255))[1] > width:
                        lines.append(line)
                        line = character
                    else:
                        line = candidate
            lines.append(line)
        return lines

    def draw_message(self, title: str, message: str, footer: str,
                     offset: int = 0) -> int:
        """Full-width, wrapped notice; return its maximum scroll offset."""
        self.sdl.SDL_SetRenderDrawColor(self.renderer, 6, 9, 22, 255)
        self.sdl.SDL_RenderClear(self.renderer)
        self.outline(10, 10, 620, 460, (38, 129, 190), 3)
        y = 28
        for line in self.wrap_text(title, 24, 568):
            self.draw_text(line, WIDTH // 2, y, 24, (36, 226, 224), center=True)
            y += 28
        self.line(24, y + 8, 616, y + 8, (38, 80, 140))
        top = y + 24
        self.fill(22, top, 596, 414 - top, (5, 8, 18))
        self.outline(22, top, 596, 414 - top, (35, 88, 160), 2)
        lines = self.wrap_text(message, 20, 552)
        capacity = max(1, (402 - top - 12) // 28)
        maximum = max(0, len(lines) - capacity)
        offset = min(maximum, max(0, offset))
        for index, line in enumerate(lines[offset:offset + capacity]):
            if line:
                self.draw_text(line, 42, top + 12 + index * 28, 20, (222, 231, 242))
        if maximum:
            footer = "UP/DOWN Scroll    " + footer
        for index, line in enumerate(self.wrap_text(footer, 13, 568)):
            self.draw_text(line, WIDTH // 2, 428 + index * 17, 13,
                           (150, 176, 202), center=True)
        self.sdl.SDL_RenderPresent(self.renderer)
        return maximum

    def fill(self, x: int, y: int, w: int, h: int, color: tuple[int, int, int]) -> None:
        self.sdl.SDL_SetRenderDrawColor(self.renderer, *color, 255)
        rectangle = SDL_Rect(x, y, w, h)
        self.sdl.SDL_RenderFillRect(self.renderer, ctypes.byref(rectangle))

    def outline(self, x: int, y: int, w: int, h: int, color: tuple[int, int, int], width: int = 2) -> None:
        self.sdl.SDL_SetRenderDrawColor(self.renderer, *color, 255)
        for offset in range(width):
            rectangle = SDL_Rect(x + offset, y + offset, w - offset * 2, h - offset * 2)
            self.sdl.SDL_RenderDrawRect(self.renderer, ctypes.byref(rectangle))

    def line(self, x1: int, y1: int, x2: int, y2: int, color: tuple[int, int, int]) -> None:
        self.sdl.SDL_SetRenderDrawColor(self.renderer, *color, 255)
        self.sdl.SDL_RenderDrawLine(self.renderer, x1, y1, x2, y2)

    def draw_list(self, title: str, prompt: str, items: list[tuple[str, str]],
                  selected: int, footer: str = "UP/DOWN Navigate    A / START Select    B / MENU Back") -> None:
        self.sdl.SDL_SetRenderDrawColor(self.renderer, 6, 9, 22, 255)
        self.sdl.SDL_RenderClear(self.renderer)
        self.outline(10, 10, 620, 460, (38, 129, 190), 3)
        self.outline(16, 16, 608, 448, (14, 30, 67), 1)
        y = 28
        for line in self.wrap_text(title, 24, 568):
            self.draw_text(line, WIDTH // 2, y, 24, (36, 226, 224), bold=True, center=True)
            y += 28
        y += 12
        for line in self.wrap_text(prompt, 16, 568):
            self.draw_text(line, 34, y, 16, (210, 222, 235))
            y += 20
        self.line(24, y + 4, 616, y + 4, (38, 80, 140))
        top = y + 14
        self.fill(22, top, 596, 414 - top, (5, 8, 18))
        self.outline(22, top, 596, 414 - top, (35, 88, 160), 2)
        rows = [(self.wrap_text(tag.upper(), 16, 122), self.wrap_text(label, 16, 420))
                for tag, label in items]
        heights = [max(30, max(len(tag), len(label)) * 21 + 9) for tag, label in rows]
        start = 0
        available = 402 - top - 10
        while start < selected and sum(heights[start:selected + 1]) > available:
            start += 1
        y = top + 10
        for index in range(start, len(rows)):
            tag_lines, label_lines = rows[index]
            row_height = heights[index]
            if y + row_height > 402:
                break
            active = index == selected
            if active:
                self.fill(30, y - 4, 580, row_height - 4, (24, 83, 153))
                self.outline(30, y - 4, 580, row_height - 4, (47, 145, 225), 1)
            for number, line in enumerate(tag_lines):
                self.draw_text(line, 42, y + number * 21, 16,
                               (255, 255, 255) if active else (36, 226, 224), bold=True)
            for number, line in enumerate(label_lines):
                self.draw_text(line, 176, y + number * 21, 16,
                               (255, 255, 255) if active else (222, 231, 242))
            y += row_height
        for index, line in enumerate(self.wrap_text(footer, 13, 568)):
            self.draw_text(line, WIDTH // 2, 428 + index * 17, 13,
                           (150, 176, 202), center=True)
        self.sdl.SDL_RenderPresent(self.renderer)

    def draw_page(self, page: str, selected: int) -> None:
        title, prompt, items = PAGES[page]
        self.draw_list(title, prompt, items, selected)

    def draw_sprite_browser(self, save_name: str, cache_name: str,
                            records: list[dict], selected: int,
                            sprite: Optional[tuple[int, int, bytes]]) -> None:
        self.sdl.SDL_SetRenderDrawColor(self.renderer, 6, 9, 22, 255)
        self.sdl.SDL_RenderClear(self.renderer)
        self.outline(10, 10, 620, 460, (38, 129, 190), 3)
        self.outline(16, 16, 608, 448, (14, 30, 67), 1)
        self.draw_text("CHOOSE A POKEMON", WIDTH // 2, 28, 22,
                       (36, 226, 224), bold=True, center=True)
        self.draw_text(save_name, 32, 66, 14, (216, 227, 240))
        self.draw_text(cache_name, 32, 86, 12, (143, 178, 208))
        self.fill(22, 112, 596, 142, (5, 8, 18))
        self.outline(22, 112, 596, 142, (35, 88, 160), 2)
        start = max(0, min(selected - 2, max(0, len(records) - 4)))
        for row, record in enumerate(records[start:start + 4]):
            index = start + row
            y = 130 + row * 34
            active = index == selected
            if active:
                self.fill(30, y - 5, 580, 29, (24, 83, 153))
                self.outline(30, y - 5, 580, 29, (47, 145, 225), 1)
            label = "%s %d  %s" % (record["where"], record["slot"] + 1,
                                      record["name"])
            self.draw_text(label[:60], 42, y, 16,
                           (255, 255, 255) if active else (222, 231, 242),
                           bold=active)
        self.fill(22, 268, 596, 144, (5, 8, 18))
        self.outline(22, 268, 596, 144, (35, 88, 160), 2)
        if records:
            record = records[selected]
            self.draw_text(record["name"][:24], 176, 290, 19,
                           (255, 255, 255), bold=True, center=True)
            identity = []
            if record.get("level") is not None:
                identity.append("Lv. %s" % record["level"])
            if record.get("nature"):
                identity.append("%s Nature" % record["nature"])
            if record.get("held"):
                identity.append("Held %s" % record.get(
                    "held_label", "item #%s" % record["held"]))
            self.draw_text("  •  ".join(identity) or "No held item", 176, 317, 13,
                           (153, 187, 220), center=True)
            moves = record.get("move_labels") or [
                "Move #%s" % move for move in record.get("moves", []) if move]
            if moves:
                self.draw_text("  •  ".join(moves[:2])[:36], 176, 340, 12,
                               (210, 225, 240), center=True)
                if len(moves) > 2:
                    self.draw_text("  •  ".join(moves[2:])[:36], 176, 358, 12,
                                   (210, 225, 240), center=True)
        if sprite:
            image_width, image_height, pixels = sprite
            scale = max(1, min(2, 110 // max(image_width, image_height)))
            left = 438 - (image_width * scale) // 2
            top = 338 - (image_height * scale) // 2
            # Game Boy-era art has a transparent background that disappears
            # into Butterfly Link's dark panel. Give Gen I/II a neutral card;
            # Gen III retains its existing sprite presentation and palette.
            if records and records[selected].get("generation") in (1, 2):
                self.fill(366, 278, 144, 126, (216, 220, 226))
                self.outline(366, 278, 144, 126, (145, 158, 174), 2)
            for y in range(image_height):
                for x in range(image_width):
                    base = (y * image_width + x) * 4
                    red, green, blue, alpha = pixels[base:base + 4]
                    if alpha:
                        self.fill(left + x * scale, top + y * scale, scale, scale,
                                  (red, green, blue))
        elif records:
            self.draw_text("No cached sprite", 438, 322, 15, (255, 173, 74), center=True)
            self.draw_text("Prepare Sprite Cache", 438, 348, 13, (176, 195, 215), center=True)
            self.draw_text("from the main screen.", 438, 366, 13, (176, 195, 215), center=True)
        footer = "UP/DOWN Pokemon    A / START Select    B / MENU Back"
        self.draw_text(footer, WIDTH // 2, 440, 13, (150, 176, 202), center=True)
        self.sdl.SDL_RenderPresent(self.renderer)

    def next_key(self) -> Optional[int]:
        event = ctypes.create_string_buffer(64)
        while self.sdl.SDL_PollEvent(event):
            event_type = int.from_bytes(event.raw[0:4], "little")
            if event_type == SDL_QUIT:
                return KEY_ESCAPE
            if event_type == SDL_KEYDOWN:
                return int.from_bytes(event.raw[20:24], "little", signed=True)
            if event_type == SDL_CONTROLLERBUTTONDOWN:
                button = event.raw[12]
                return {
                    CONTROLLER_A: KEY_RETURN,
                    CONTROLLER_B: KEY_ESCAPE,
                    CONTROLLER_BACK: KEY_ESCAPE,
                    CONTROLLER_START: KEY_RETURN,
                    CONTROLLER_DPAD_UP: KEY_UP,
                    CONTROLLER_DPAD_DOWN: KEY_DOWN,
                    CONTROLLER_DPAD_LEFT: KEY_LEFT,
                    CONTROLLER_DPAD_RIGHT: KEY_RIGHT,
                }.get(button)
            if event_type == SDL_JOYBUTTONDOWN:
                # Generic joysticks use the common first-button A/B layout.
                return {0: KEY_RETURN, 1: KEY_ESCAPE}.get(event.raw[12])
            if event_type == SDL_JOYHATMOTION:
                direction = event.raw[13]
                if direction & HAT_UP:
                    return KEY_UP
                if direction & HAT_DOWN:
                    return KEY_DOWN
                if direction & HAT_LEFT:
                    return KEY_LEFT
                if direction & HAT_RIGHT:
                    return KEY_RIGHT
        return None

    def close(self) -> None:
        if getattr(self, "closed", False):
            return
        self.closed = True
        for texture, _width, _height in getattr(self, "textures", {}).values():
            self.sdl.SDL_DestroyTexture(texture)
        if getattr(self, "textures", None) is not None:
            self.textures.clear()
        for opened in getattr(self, "fonts", {}).values():
            self.ttf.TTF_CloseFont(opened)
        if getattr(self, "fonts", None) is not None:
            self.fonts.clear()
        if getattr(self, "renderer", None):
            self.sdl.SDL_DestroyRenderer(self.renderer)
            self.renderer = None
        if getattr(self, "window", None):
            self.sdl.SDL_DestroyWindow(self.window)
            self.window = None
        for device_type, opened in getattr(self, "controllers", []):
            if device_type == "controller":
                self.sdl.SDL_GameControllerClose(opened)
            else:
                self.sdl.SDL_JoystickClose(opened)
        self.controllers = []
        self.ttf.TTF_Quit()
        self.sdl.SDL_Quit()


def start_controller() -> Optional[subprocess.Popen]:
    try:
        subprocess.run(["/usr/bin/control-gen_init.sh"], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=False)
        command = (
            ". /storage/.config/gptokeyb/control.ini 2>/dev/null || true; "
            "get_controls 2>/dev/null || true; "
            "exec /usr/bin/gptokeyb -c /usr/share/butterflyos/save-trade.gptk"
        )
        return subprocess.Popen(["/bin/sh", "-c", command],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        return None


def stop_controller(process: Optional[subprocess.Popen]) -> None:
    if process is None:
        return
    try:
        process.terminate()
        process.wait(timeout=1)
    except (OSError, subprocess.TimeoutExpired):
        try:
            process.kill()
        except OSError:
            pass


def run_action(action: str, controller: Optional[subprocess.Popen], frontend: SDLFrontEnd) -> None:
    stop_controller(controller)
    # Dialog draws on the terminal/display directly. Leaving the fullscreen SDL
    # window alive hides that dialog and makes it appear as an input lockup.
    frontend.close()
    subprocess.run(["/usr/share/butterflyos/save-trade-ui.sh", action], check=False)


def _field(output: str, name: str) -> str:
    prefix = name + "="
    for line in output.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):]
    return ""


def _record_from_columns(where: str, box: Optional[int], slot: int, species: int,
                         nickname: str, columns: list[str]) -> dict:
    """Parse optional, forward-compatible key=value fields from the helper."""
    extra = {}
    for field in columns[6:]:
        key, separator, value = field.partition("=")
        if separator:
            extra[key] = value
    moves = []
    for value in extra.get("moves", "").split(","):
        try:
            moves.append(int(value))
        except ValueError:
            continue
    try:
        held = int(extra.get("held", "0"))
    except ValueError:
        held = 0
    level = extra.get("level")
    try:
        level = int(level) if level is not None else None
    except ValueError:
        level = None
    if level == 0:
        # Some boxed Gen I records do not carry a literal level. Do not show a
        # misleading "Lv. 0"; Gen III will gain a derived level later.
        level = None
    record = {"where": where, "slot": slot, "species": species,
              "name": nickname, "shiny": len(columns) > 5 and columns[5].lower() == "yes",
              "moves": moves, "held": held, "level": level,
              "nature": extra.get("nature", "")}
    if box is not None:
        record["box"] = box
    return record


def _save_records(path: str) -> tuple[int, list[dict]]:
    """Read the helper's stable tab-delimited inspect protocol."""
    result = subprocess.run(["/usr/bin/butterflyos-save-trade", "inspect", "--save", path],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            check=False)
    if result.returncode:
        return 0, []
    generation_text = _field(result.stdout, "generation")
    try:
        generation = int(generation_text)
    except ValueError:
        return 0, []
    records = []
    for line in result.stdout.splitlines():
        columns = line.split("\t")
        if len(columns) < 6 or columns[0] != "box_record":
            continue
        try:
            box, slot, species = int(columns[1]), int(columns[2]), int(columns[3])
        except ValueError:
            continue
        nickname = columns[5] or "Species #%d" % species
        record = _record_from_columns("Box %d" % (box + 1), box, slot,
                                      species, nickname, columns)
        record["generation"] = generation
        records.append(record)
    return generation, records


def _find_saves() -> list[str]:
    found, seen = [], set()
    for root in ("/storage/roms", "/storage/games-external/roms"):
        if not os.path.isdir(root):
            continue
        for directory, _subdirs, files in os.walk(root):
            for name in files:
                if not name.lower().endswith((".srm", ".sav")):
                    continue
                path = os.path.realpath(os.path.join(directory, name))
                if path not in seen:
                    seen.add(path)
                    found.append(path)
    return sorted(found)


def _game_family(name: str) -> str:
    normalized = name.lower().replace("_", " ").replace("-", " ")
    if "fire red" in normalized:
        return "firered"
    if "leaf green" in normalized:
        return "leafgreen"
    for family in ("firered", "leafgreen", "sapphire", "emerald", "crystal",
                   "yellow", "silver", "gold", "ruby", "blue", "red"):
        if family in normalized:
            return family
    return ""


def _cache_for_generation(generation: int, save_path: str) -> tuple[Optional[str], str]:
    root = "/storage/.config/butterflyos/save-trade/sprite-cache"
    candidates = []
    expected_family = _game_family(os.path.basename(save_path))
    if not os.path.isdir(root):
        return None, "No sprite cache prepared"
    for name in os.listdir(root):
        manifest = os.path.join(root, name, "manifest.json")
        try:
            data = json.loads(open(manifest, encoding="utf-8").read())
        except (OSError, ValueError):
            continue
        cached_generation = data.get("generation")
        if cached_generation is None and data.get("format") == "butterflyos-gen3-sprite-cache":
            cached_generation = 3
        rom_name = data.get("rom_filename", "ROM")
        if cached_generation == generation and (not expected_family or
                                                _game_family(rom_name) == expected_family):
            candidates.append((os.path.getmtime(manifest), os.path.dirname(manifest), rom_name))
    if not candidates:
        if expected_family:
            return None, "No matching %s sprite cache" % expected_family.title()
        return None, "No Generation %d cache prepared" % generation
    _mtime, path, title = max(candidates)
    return path, "Cache: %s" % title


def _read_cache_png(path: str) -> Optional[tuple[int, int, bytes]]:
    """Read Butterfly Link's own filter-0 RGBA cache PNGs without SDL_image."""
    try:
        data = open(path, "rb").read()
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            return None
        cursor, width, height, raw = 8, None, None, bytearray()
        while cursor + 8 <= len(data):
            length = struct.unpack_from(">I", data, cursor)[0]
            kind = data[cursor + 4:cursor + 8]
            payload = data[cursor + 8:cursor + 8 + length]
            cursor += 12 + length
            if kind == b"IHDR":
                width, height, depth, color_type, compression, filtering, interlace = struct.unpack(
                    ">IIBBBBB", payload)
                if (depth, color_type, compression, filtering, interlace) != (8, 6, 0, 0, 0):
                    return None
            elif kind == b"IDAT":
                raw.extend(payload)
            elif kind == b"IEND":
                break
        if not width or not height:
            return None
        decoded = zlib.decompress(bytes(raw))
        stride = width * 4
        pixels, cursor = bytearray(), 0
        for _row in range(height):
            if decoded[cursor] != 0:
                return None
            pixels.extend(decoded[cursor + 1:cursor + 1 + stride])
            cursor += stride + 1
        return width, height, bytes(pixels)
    except (OSError, ValueError, struct.error, zlib.error):
        return None


def sprite_browser(frontend: SDLFrontEnd) -> None:
    saves = _find_saves()
    if not saves:
        return
    save_index, record_index, active_generation, records = 0, 0, 0, []

    def load_save() -> None:
        nonlocal active_generation, records, record_index
        active_generation, records = _save_records(saves[save_index])
        record_index = 0

    load_save()
    while True:
        path = saves[save_index]
        cache, cache_title = _cache_for_generation(active_generation, path)
        sprite = None
        if records and cache:
            sprite_path = os.path.join(cache, "front", "%03d.png" % records[record_index]["species"])
            sprite = _read_cache_png(sprite_path)
        frontend.draw_sprite_browser(os.path.basename(path), cache_title, records,
                                     record_index if records else 0, sprite)
        key = frontend.next_key()
        if key is None:
            continue
        if key in (KEY_ESCAPE, KEY_B, ord("B"), KEY_Q, ord("Q"), KEY_CANCEL, ord("X")):
            return
        if key in (KEY_LEFT, ord("h")):
            save_index = (save_index - 1) % len(saves)
            load_save()
        elif key in (KEY_RIGHT, ord("l")):
            save_index = (save_index + 1) % len(saves)
            load_save()
        elif records and key in (KEY_UP, ord("k")):
            record_index = (record_index - 1) % len(records)
        elif records and key in (KEY_DOWN, ord("j")):
            record_index = (record_index + 1) % len(records)


STATE_ROOT = "/storage/.config/butterflyos/save-trade"
DEBUG_LOG = "/storage/.config/butterflyos/logs/butterfly-link.log"


def debug(message: str) -> None:
    """Leave a tiny breadcrumb for diagnosing an on-device UI exit."""
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as handle:
            handle.write("[%s] %s\n" % (time.strftime("%FT%TZ", time.gmtime()), message))
    except OSError:
        pass


def choose_list(frontend: SDLFrontEnd, title: str, prompt: str,
                items: list[tuple[str, str]], selected: int = 0) -> Optional[int]:
    """Present a controller-native list and return its selected index."""
    if not items:
        return None
    selected = max(0, min(selected, len(items) - 1))
    debug("list opened: %s" % title)
    while True:
        frontend.draw_list(title, prompt, items, selected)
        key = frontend.next_key()
        if key is None:
            continue
        if key in (KEY_ESCAPE, KEY_B, ord("B"), KEY_Q, ord("Q"), KEY_CANCEL, ord("X")):
            debug("list cancelled: %s" % title)
            return None
        if key in (KEY_UP, ord("k")):
            selected = (selected - 1) % len(items)
        elif key in (KEY_DOWN, ord("j")):
            selected = (selected + 1) % len(items)
        elif key in (KEY_RETURN, KEY_A, ord("A"), KEY_CONFIRM, ord("Z")):
            debug("list selected: %s index=%d" % (title, selected))
            return selected


def completion_message(action: str) -> str:
    if action == "trade":
        return "Both game saves have been updated.\nOriginal saves were backed up."
    return ("The destination game save has been updated.\n"
            "The source save is unchanged.\nA backup was saved.")


def notice(frontend: SDLFrontEnd, title: str, message: str,
           completion: bool = False) -> None:
    offset = 0
    # Consume carry-over input from the confirmation screen before allowing
    # dismissal, so a fast double press cannot hide the successful result.
    ready_at = time.monotonic() + (1.5 if completion else 0.0)
    while True:
        ready = time.monotonic() >= ready_at
        prompt = ("Press A to return to Butterfly Link." if completion else
                  "A or B returns to Butterfly Link.")
        footer = ("A Return to Butterfly Link" if ready else "Transfer finished — please read the result")
        maximum = frontend.draw_message(title, message + "\n\n" + prompt,
                                        footer if completion else "A / B / MENU Return", offset)
        key = frontend.next_key()
        if key in (KEY_UP, ord("k")):
            offset = max(0, offset - 1)
        elif key in (KEY_DOWN, ord("j")):
            offset = min(maximum, offset + 1)
        if not ready:
            continue
        if key in (KEY_RETURN, KEY_A, ord("A"), KEY_CONFIRM, ord("Z"),
                   KEY_ESCAPE, KEY_B, ord("B"), KEY_CANCEL, ord("X"), KEY_Q, ord("Q")):
            return


def about_butterfly_link(frontend: SDLFrontEnd) -> None:
    """Short, readable explanation of the safety model and generation limits."""
    while True:
        choice = choose_list(frontend, "HOW BUTTERFLY LINK WORKS",
                             "Choose a topic. B returns to the main menu.",
                             [("SAFE FLOW", "How every local transfer is protected"),
                              ("GENERATION RULES", "What can move between game generations"),
                              ("CURRENT LIMITS", "Features intentionally not available yet")])
        if choice is None:
            return
        if choice == 0:
            notice(frontend, "SAFE LOCAL FLOW", """
1. Choose a source save and a boxed Pokemon.
2. Choose Copy or Trade, then choose the destination.
3. Butterfly Link creates protected working save copies.
4. Review the result and choose Commit to continue.
5. The original destination is backed up, then replaced atomically.
Cancel at any review screen: every original save stays unchanged.
""")
        elif choice == 1:
            notice(frontend, "GENERATION RULES", """
Same generation: boxed Pokemon can be copied or traded.
Gen 1 to Gen 2: Time Capsule transfer for Gen 1-compatible Pokemon only.
Gen 2 to Gen 3: one-way copy only; the Gen 2 source never changes.
Gen 2 to Gen 3 currently clears held items rather than risking a wrong item.
Moves, nickname, OT, level, experience, IVs and EVs are converted safely.
Gen 3 Pokemon cannot move backward to earlier generations.
""")
        else:
            notice(frontend, "CURRENT LIMITS", """
Only boxed Pokemon can be transferred; party Pokemon are preview-only.
Supported trade evolutions are optional and apply only to the protected copy.
Gen 2 to Gen 3 uses a documented conversion, not an official link cable.
Wi-Fi supports same-generation trades/copies, Gen 1 to 2 copies,
and Gen 2 to 3 copies. Cross-generation copies keep the source unchanged.
Gen 2 to 3 clears held items, matching the local conversion rules.
Both Flips must approve before applying a remote transfer.
Every operation requires an explicit final Commit confirmation.
""")


def save_metadata(path: str) -> tuple[int, str, str, list[dict]]:
    result = subprocess.run(["/usr/bin/butterflyos-save-trade", "inspect", "--save", path],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            check=False)
    if result.returncode:
        return 0, "", "", []
    generation = _field(result.stdout, "generation")
    try:
        parsed_generation = int(generation)
    except ValueError:
        return 0, "", "", []
    _parsed, records = _save_records(path)
    return (parsed_generation, _field(result.stdout, "trainer_name") or "Unknown",
            _field(result.stdout, "save_type") or "Unknown", records)


def party_records(path: str) -> list[dict]:
    """Read party entries for display only; transfers remain PC-box-only."""
    result = subprocess.run(["/usr/bin/butterflyos-save-trade", "inspect", "--save", path],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            check=False)
    if result.returncode:
        return []
    try:
        generation = int(_field(result.stdout, "generation"))
    except ValueError:
        generation = 0
    entries = []
    for line in result.stdout.splitlines():
        columns = line.split("\t")
        if len(columns) < 6 or columns[0] != "party_record":
            continue
        try:
            slot, species = int(columns[1]), int(columns[2])
        except ValueError:
            continue
        record = _record_from_columns("Party", None, slot, species,
                                      columns[4] or "Species #%d" % species,
                                      columns)
        record["generation"] = generation
        entries.append(record)
    return entries


def generation_saves(generation: int) -> list[tuple[str, str, str, list[dict]]]:
    matches = []
    for path in _find_saves():
        found_generation, trainer, save_type, records = save_metadata(path)
        if found_generation == generation:
            matches.append((path, trainer, save_type, records))
    return matches


def choose_save(frontend: SDLFrontEnd, generation: int, title: str,
                excluded: Optional[str] = None) -> Optional[tuple[str, str, str, list[dict]]]:
    saves = [entry for entry in generation_saves(generation) if entry[0] != excluded]
    if not saves:
        notice(frontend, "NO COMPATIBLE SAVES",
               "Add two Generation %d .srm or .sav files, then try again." % generation)
        return None
    items = []
    for path, trainer, save_type, records in saves:
        card = "Game Card" if path.startswith("/storage/games-external/") else "OS Card"
        label = "%s: %s | %s | PC %d" % (card, os.path.basename(path), trainer, len(records))
        items.append((save_type[:13].upper(), label[:58]))
    choice = choose_list(frontend, title,
                         "Choose a Generation %d save. B returns." % generation, items)
    return saves[choice] if choice is not None else None


def _rom_candidates(generation: int, save_path: str) -> list[str]:
    directory, extensions = {1: ("gb", (".gb",)), 2: ("gbc", (".gbc",)),
                             3: ("gba", (".gba",))}[generation]
    found = []
    for root in ("/storage/roms", "/storage/games-external/roms"):
        location = os.path.join(root, directory)
        if not os.path.isdir(location):
            continue
        for name in sorted(os.listdir(location)):
            path = os.path.join(location, name)
            if os.path.isfile(path) and name.lower().endswith(extensions):
                found.append(path)
    if not found:
        return []
    stem = os.path.splitext(os.path.basename(save_path))[0].lower()
    matching = [path for path in found if os.path.splitext(os.path.basename(path))[0].lower() == stem]
    if matching:
        return matching
    family = _game_family(os.path.basename(save_path))
    matching = [path for path in found if family and _game_family(os.path.basename(path)) == family]
    return matching or found


def ensure_sprite_cache(frontend: SDLFrontEnd, generation: int, save_path: str) -> Optional[str]:
    cache, _title = _cache_for_generation(generation, save_path)
    # Gen I/II caches also hold local labels extracted from the matching user
    # ROM.  Regenerate old art-only caches once; Gen III currently remains
    # art-only until its distinct pointer-table reader is implemented.
    if cache and generation == 3:
        return cache
    if cache:
        names = _load_rom_names(cache)
        if names and (generation != 1 or names.get("internal_to_national")):
            return cache
    candidates = _rom_candidates(generation, save_path)
    if not candidates:
        notice(frontend, "ROM NEEDED", "Add the matching Generation %d ROM to the OS Card or Game Card. The save was not changed." % generation)
        return None
    if len(candidates) == 1:
        rom = candidates[0]
    else:
        choices = [("ROM", os.path.basename(path)[:52]) for path in candidates]
        choice = choose_list(frontend, "CHOOSE MATCHING ROM",
                             "Used only to build local sprite art. B returns.", choices)
        if choice is None:
            return None
        rom = candidates[choice]
    frontend.draw_list("PREPARING SPRITES", "Reading your own ROM once; this never changes a ROM or save.",
                       [("PLEASE WAIT", os.path.basename(rom)[:52])], 0, "Working…")
    tool = ("/usr/bin/butterflyos-gen3-sprite-cache.py" if generation == 3
            else "/usr/bin/butterflyos-gb-sprite-cache.py")
    result = subprocess.run(["python3", tool, rom, "--cache-root", STATE_ROOT + "/sprite-cache"],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            check=False)
    if result.returncode:
        notice(frontend, "SPRITE CACHE FAILED", result.stdout[-350:] or "The cache tool stopped safely. No files were changed.")
        return None
    cache, _title = _cache_for_generation(generation, save_path)
    if not cache:
        notice(frontend, "SPRITE CACHE NOT FOUND", "The cache finished but did not match this save. No save was changed.")
    return cache


def _load_rom_names(cache: Optional[str]) -> dict:
    """Load labels extracted locally from a user-owned Gen I/II ROM."""
    if not cache:
        return {}
    try:
        with open(os.path.join(cache, "names.json"), encoding="utf-8") as handle:
            data = json.load(handle)
        if data.get("format") != "butterflyos-gb-rom-names":
            return {}
        return {"moves": data.get("moves", {}), "items": data.get("items", {}),
                "internal_to_national": data.get("internal_to_national", {})}
    except (OSError, ValueError):
        return {}


def _enrich_rom_names(records: list[dict], cache: Optional[str]) -> None:
    """Attach local ROM labels without ever embedding game text in the app."""
    names = _load_rom_names(cache)
    if not names:
        return
    moves, items = names.get("moves", {}), names.get("items", {})
    for record in records:
        record["move_labels"] = [moves.get(str(move), "Move #%s" % move)
                                 for move in record.get("moves", []) if move]
        held = record.get("held", 0)
        if held:
            record["held_label"] = items.get(str(held), "item #%s" % held)


def preview_party(frontend: SDLFrontEnd, save: tuple[str, str, str, list[dict]],
                  cache: Optional[str]) -> None:
    """Show party Pokémon with art, without offering an unsafe transfer path."""
    path, trainer, _save_type, _records = save
    party = party_records(path)
    _enrich_rom_names(party, cache)
    if not party:
        notice(frontend, "EMPTY PARTY", "%s has no party Pokémon to preview." % os.path.basename(path))
        return
    selected = 0
    while True:
        record = party[selected]
        sprite = None
        if cache:
            directory = "front-shiny" if record.get("shiny") else "front"
            sprite = _read_cache_png(os.path.join(cache, directory, "%03d.png" % record["species"]))
        frontend.draw_sprite_browser("%s — %s's party" % (os.path.basename(path), trainer),
                                     "Party is read-only", party, selected, sprite)
        key = frontend.next_key()
        if key is None:
            continue
        if key in (KEY_ESCAPE, KEY_B, ord("B"), KEY_CANCEL, ord("X"),
                   KEY_RETURN, KEY_A, ord("A"), KEY_CONFIRM, ord("Z")):
            return
        if key in (KEY_UP, ord("k")):
            selected = (selected - 1) % len(party)
        elif key in (KEY_DOWN, ord("j")):
            selected = (selected + 1) % len(party)


def choose_box(frontend: SDLFrontEnd, save: tuple[str, str, str, list[dict]],
               cache: Optional[str]) -> Optional[int]:
    path, trainer, _save_type, records = save
    party = party_records(path)
    boxes = {}
    for record in records:
        boxes.setdefault(record["box"], []).append(record)
    items = [("TRAINER", trainer[:46])]
    items.extend(("PARTY", "%d. %s  (read-only)" % (entry["slot"] + 1, entry["name"][:30])) for entry in party)
    items.extend(("BOX %d" % (box + 1), "%d Pokemon" % len(boxes[box])) for box in sorted(boxes))
    if not boxes:
        preview_party(frontend, save, cache)
        notice(frontend, "NO BOXED POKEMON",
               "%s has no Pokémon in its PC boxes. Party Pokémon are shown for reference; only PC boxes can be transferred safely." % os.path.basename(path))
        return None
    while True:
        first_box = next(index for index, (tag, _label) in enumerate(items) if tag.startswith("BOX "))
        selection = choose_list(frontend, "SELECT A BOX",
                                "Party is read-only. A opens the highlighted PC box.",
                                items, selected=first_box)
        if selection is None:
            return None
        tag, label = items[selection]
        if tag.startswith("BOX "):
            return int(tag[4:]) - 1
        preview_party(frontend, save, cache)


def choose_record(frontend: SDLFrontEnd, title: str,
                  save: tuple[str, str, str, list[dict]], cache: Optional[str]) -> Optional[dict]:
    selected_box = choose_box(frontend, save, cache)
    if selected_box is None:
        return None
    records = [record for record in save[3] if record["box"] == selected_box]
    _enrich_rom_names(records, cache)
    if not records:
        notice(frontend, "NO BOXED POKEMON", "%s has no boxed Pokemon." % os.path.basename(save[0]))
        return None
    selected = 0
    while True:
        record = records[selected]
        sprite = None
        if cache:
            directory = "front-shiny" if record.get("shiny") else "front"
            sprite = _read_cache_png(os.path.join(cache, directory, "%03d.png" % record["species"]))
        frontend.draw_sprite_browser("%s — Box %d" % (os.path.basename(save[0]), selected_box + 1),
                                     "A Select  B Back", records, selected, sprite)
        key = frontend.next_key()
        if key is None:
            continue
        if key in (KEY_ESCAPE, KEY_B, ord("B"), KEY_CANCEL, ord("X")):
            return None
        if key in (KEY_UP, ord("k")):
            selected = (selected - 1) % len(records)
        elif key in (KEY_DOWN, ord("j")):
            selected = (selected + 1) % len(records)
        elif key in (KEY_RETURN, KEY_A, ord("A"), KEY_CONFIRM, ord("Z")):
            return record


def confirm_transfer(frontend: SDLFrontEnd, mode: str, left: tuple[str, dict],
                     right: tuple[str, dict], action: str = "trade") -> bool:
    left_path, left_record = left
    right_path, right_record = right
    final_commit = mode.startswith("COPIES READY")
    action_name = action.capitalize()
    items = [
        ("FROM", "%s: %s" % (os.path.basename(left_path), left_record["name"][:32])),
        ("TO", "%s: %s" % (os.path.basename(right_path), right_record["name"][:32])),
        ("CANCEL", "Cancel %s" % action),
        ("ACTION", "%s these Pokémon" % action_name if final_commit else
                   "Review protected copies"),
    ]
    choice = choose_list(frontend, "%s REVIEW" % mode,
                         ("Apply the protected save copies now." if final_commit else
                          "Original saves are untouched until the final confirmation."),
                         items, selected=2)
    return choice == 3


def new_session() -> str:
    os.makedirs(os.path.join(STATE_ROOT, "sessions"), exist_ok=True)
    identity = "%s-%s-%s" % (time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()),
                               os.getpid(), time.monotonic_ns())
    path = os.path.join(STATE_ROOT, "sessions", identity)
    os.mkdir(path)
    return path


def write_session_value(session: str, name: str, value: str) -> None:
    with open(os.path.join(session, name), "w", encoding="utf-8") as handle:
        handle.write(value + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def helper_run(arguments: list[str]) -> tuple[bool, str]:
    result = subprocess.run(["/usr/bin/butterflyos-save-trade", *arguments], text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return result.returncode == 0, result.stdout.strip()


def prepare_swap(generation: int, left: tuple[str, dict],
                 right: tuple[str, dict]) -> tuple[Optional[str], str]:
    left_path, left_record = left
    right_path, right_record = right
    session = new_session()
    left_output = os.path.join(session, "left-" + os.path.basename(left_path))
    right_output = os.path.join(session, "right-" + os.path.basename(right_path))
    command = [
        "swap-gen%d" % generation,
        "--left", left_path, "--left-box", str(left_record["box"]),
        "--left-slot", str(left_record["slot"]),
        "--right", right_path, "--right-box", str(right_record["box"]),
        "--right-slot", str(right_record["slot"]),
        "--output-left", left_output, "--output-right", right_output,
    ]
    success, output = helper_run(command)
    if not success:
        shutil.rmtree(session, ignore_errors=True)
        return None, output or "The save helper rejected this swap."
    write_session_value(session, "left-original", left_path)
    write_session_value(session, "right-original", right_path)
    write_session_value(session, "state", "READY")
    return session, output


def choose_copy_destination(frontend: SDLFrontEnd, generation: int,
                            save: tuple[str, str, str, list[dict]]) -> Optional[tuple[int, int]]:
    """Choose an append-only PC destination; never offer occupied slots."""
    _path, _trainer, _save_type, records = save
    limits = {1: (12, 20), 2: (14, 20), 3: (14, 30)}
    box_count, box_size = limits[generation]
    occupied = {box: 0 for box in range(box_count)}
    for record in records:
        box = record.get("box")
        if box in occupied:
            occupied[box] += 1
    choices = [("BOX %d" % (box + 1), "%d free slots" % (box_size - count))
               for box, count in occupied.items() if count < box_size]
    if not choices:
        notice(frontend, "NO FREE PC SLOT",
               "Every PC box in this save is full. Move or release a Pokémon in-game, then try again.")
        return None
    choice = choose_list(frontend, "COPY DESTINATION",
                         "Choose a PC box. Butterfly Link adds the Pokémon to its next empty slot.",
                         choices)
    if choice is None:
        return None
    box = int(choices[choice][0][4:]) - 1
    return box, occupied[box]


def prepare_copy(generation: int, source: tuple[str, dict], destination: tuple[str, int, int]) -> tuple[Optional[str], str]:
    source_path, source_record = source
    destination_path, destination_box, destination_slot = destination
    session = new_session()
    output = os.path.join(session, "destination-" + os.path.basename(destination_path))
    command = [
        "copy-gen%d" % generation,
        "--source", source_path, "--source-box", str(source_record["box"]),
        "--source-slot", str(source_record["slot"]),
        "--destination", destination_path, "--destination-box", str(destination_box),
        "--destination-slot", str(destination_slot), "--output-destination", output,
    ]
    success, message = helper_run(command)
    if not success:
        shutil.rmtree(session, ignore_errors=True)
        return None, message or "The save helper rejected this copy."
    write_session_value(session, "destination-original", destination_path)
    write_session_value(session, "state", "READY")
    return session, message


def prepare_gen1_to_gen2(source: tuple[str, dict], national_species: int,
                         destination: tuple[str, int, int]) -> tuple[Optional[str], str]:
    source_path, source_record = source
    destination_path, destination_box, destination_slot = destination
    session = new_session()
    output = os.path.join(session, "destination-" + os.path.basename(destination_path))
    command = [
        "transfer-gen1-to-gen2",
        "--source", source_path, "--source-box", str(source_record["box"]),
        "--source-slot", str(source_record["slot"]),
        "--national-species", str(national_species),
        "--destination", destination_path, "--destination-box", str(destination_box),
        "--destination-slot", str(destination_slot), "--output-destination", output,
    ]
    success, message = helper_run(command)
    if not success:
        shutil.rmtree(session, ignore_errors=True)
        return None, message or "The Time Capsule converter rejected this transfer."
    write_session_value(session, "destination-original", destination_path)
    write_session_value(session, "state", "READY")
    return session, message


def prepare_gen2_to_gen3(source: tuple[str, dict], national_species: int,
                         destination: tuple[str, int, int]) -> tuple[Optional[str], str]:
    """Create a safe one-way Gen II -> Gen III migration output."""
    source_path, source_record = source
    destination_path, destination_box, destination_slot = destination
    session = new_session()
    output = os.path.join(session, "destination-" + os.path.basename(destination_path))
    command = [
        "copy-gen2-to-gen3",
        "--source", source_path, "--source-box", str(source_record["box"]),
        "--source-slot", str(source_record["slot"]),
        "--national-species", str(national_species),
        "--destination", destination_path, "--destination-box", str(destination_box),
        "--destination-slot", str(destination_slot), "--output-destination", output,
    ]
    success, message = helper_run(command)
    if not success:
        shutil.rmtree(session, ignore_errors=True)
        return None, message or "The Gen 2 to Gen 3 converter rejected this copy."
    write_session_value(session, "destination-original", destination_path)
    write_session_value(session, "state", "READY")
    return session, message


# National Dex species with a normal trade evolution. The optional item is
# checked using text read from the user's own Gen II ROM; no game text ships in
# ButterflyOS. Gen III's four original trade evolutions need no item lookup.
TRADE_EVOLUTIONS = {
    64: (65, "Kadabra", "Alakazam", None),
    67: (68, "Machoke", "Machamp", None),
    75: (76, "Graveler", "Golem", None),
    93: (94, "Haunter", "Gengar", None),
    79: (199, "Slowpoke", "Slowking", "KING'S ROCK"),
    95: (208, "Onix", "Steelix", "METAL COAT"),
    117: (230, "Seadra", "Kingdra", "DRAGON SCALE"),
    123: (212, "Scyther", "Scizor", "METAL COAT"),
    137: (233, "Porygon", "Porygon2", "UP-GRADE"),
}


def national_species_for(record: dict, generation: int, cache: Optional[str]) -> Optional[int]:
    if generation == 3:
        return record.get("species")
    try:
        species = _load_rom_names(cache).get("internal_to_national", {}).get(str(record["species"]))
        return int(species) if species else None
    except (KeyError, TypeError, ValueError):
        return None


def internal_species_for(national_species: int, generation: int, cache: Optional[str]) -> Optional[int]:
    if generation == 3:
        return national_species
    mapping = _load_rom_names(cache).get("internal_to_national", {})
    for internal, national in mapping.items():
        if national == national_species:
            try:
                return int(internal)
            except ValueError:
                return None
    return None


def trade_evolution_for(record: dict, generation: int, cache: Optional[str]) -> Optional[tuple[int, str, str]]:
    national = national_species_for(record, generation, cache)
    candidate = TRADE_EVOLUTIONS.get(national)
    if not candidate:
        return None
    target, source_name, target_name, required_item = candidate
    if required_item:
        held = str(record.get("held_label", "")).upper().replace("_", "-")
        if held != required_item:
            return None
    return target, source_name, target_name


def session_output(session: str, prefix: str = "destination-") -> Optional[str]:
    for entry in os.listdir(session):
        if entry.startswith(prefix) and not entry.endswith("-original"):
            return os.path.join(session, entry)
    return None


def offer_trade_evolution(frontend: SDLFrontEnd, session: str, output: str,
                          source_record: dict, source_generation: int,
                          source_cache: Optional[str], destination_generation: int,
                          destination_cache: Optional[str], destination_box: int,
                          destination_slot: int) -> bool:
    """Offer an explicit, working-copy-only evolution after a prepared transfer."""
    candidate = trade_evolution_for(source_record, source_generation, source_cache)
    if not candidate:
        return True
    national_target, source_name, target_name = candidate
    native_target = internal_species_for(national_target, destination_generation, destination_cache)
    if native_target is None:
        notice(frontend, "EVOLUTION SKIPPED",
               "Butterfly Link could not map %s safely in the destination game. The prepared copy is unchanged." % target_name)
        return True
    choice = choose_list(frontend, "TRADE EVOLUTION?",
                         "%s normally evolves through trading." % source_name,
                         [("KEEP", "Keep %s in its current form" % source_name),
                          ("EVOLVE", "Evolve into %s on the protected copy" % target_name)])
    if choice != 1:
        return True
    evolved = os.path.join(session, "evolved-" + os.path.basename(output))
    command = [
        "evolve-gen%d" % destination_generation,
        "--source", output, "--box", str(destination_box), "--slot", str(destination_slot),
        "--evolved-species", str(native_target), "--output", evolved,
    ]
    # The games normally rename an un-nicknamed Pokemon on evolution, but a
    # player-assigned nickname must be left alone.  The trade-evolution table
    # is deliberately the authority here: ROM name tables are only needed for
    # internal species IDs, not for shipping any game text.
    current_name = str(source_record.get("name", "")).strip()
    if current_name.casefold() == source_name.casefold():
        command.extend(["--nickname", target_name])
    success, message = helper_run(command)
    if not success:
        notice(frontend, "EVOLUTION NOT PREPARED", message or "The working copy was left unchanged.")
        return False
    os.replace(evolved, output)
    notice(frontend, "EVOLUTION PREPARED",
           "%s will evolve into %s only if you choose Commit next." % (source_name, target_name))
    return True


def copy_with_sync(source: str, destination: str, preserve_stat: bool = True) -> None:
    """Copy a file durably.

    Backups retain their original metadata. Saves that will be launched by an
    emulator need a fresh mtime so they are never treated as stale.
    """
    with open(source, "rb") as source_handle, open(destination, "wb") as destination_handle:
        shutil.copyfileobj(source_handle, destination_handle, 128 * 1024)
        destination_handle.flush()
        os.fsync(destination_handle.fileno())
    if preserve_stat:
        shutil.copystat(source, destination, follow_symlinks=True)


def replace_save_with_verified_output(original: str, output: str, backup: str) -> None:
    """Atomically replace a save and restore its backup if validation fails."""
    expected = _file_digest(output)
    temporary = original + ".butterfly-link-%d" % os.getpid()
    copy_with_sync(output, temporary, preserve_stat=False)
    os.replace(temporary, original)
    os.sync()
    if _file_digest(original) == expected:
        return
    restore = original + ".butterfly-link-restore-%d" % os.getpid()
    copy_with_sync(backup, restore, preserve_stat=False)
    os.replace(restore, original)
    os.sync()
    raise OSError("written save did not pass SHA-256 verification; original was restored")


def commit_swap(session: str) -> tuple[bool, str]:
    try:
        with open(os.path.join(session, "left-original"), encoding="utf-8") as handle:
            left = handle.read().strip()
        with open(os.path.join(session, "right-original"), encoding="utf-8") as handle:
            right = handle.read().strip()
        left_output = next(os.path.join(session, item) for item in os.listdir(session)
                           if item.startswith("left-") and item != "left-original")
        right_output = next(os.path.join(session, item) for item in os.listdir(session)
                            if item.startswith("right-") and item != "right-original")
        left_backup = os.path.join(session, "original-left-backup")
        right_backup = os.path.join(session, "original-right-backup")
        copy_with_sync(left, left_backup)
        copy_with_sync(right, right_backup)
        try:
            replace_save_with_verified_output(left, left_output, left_backup)
            replace_save_with_verified_output(right, right_output, right_backup)
        except OSError:
            restore = left + ".butterfly-link-restore-%d" % os.getpid()
            copy_with_sync(left_backup, restore, preserve_stat=False)
            os.replace(restore, left)
            os.sync()
            raise
        write_session_value(session, "state", "COMMITTED")
        return True, "Both saves were committed. Verified backups are in this Butterfly Link session."
    except (OSError, StopIteration) as error:
        return False, "Commit failed safely: %s" % error


def commit_copy(session: str) -> tuple[bool, str]:
    """Atomically replace only the destination save after making its backup."""
    try:
        with open(os.path.join(session, "destination-original"), encoding="utf-8") as handle:
            destination = handle.read().strip()
        output = next(os.path.join(session, item) for item in os.listdir(session)
                      if item.startswith("destination-") and item != "destination-original")
        backup = os.path.join(session, "original-destination-backup")
        copy_with_sync(destination, backup)
        replace_save_with_verified_output(destination, output, backup)
        write_session_value(session, "state", "COMMITTED")
        return True, "The copy was committed. A verified original is in this Butterfly Link session."
    except (OSError, StopIteration) as error:
        return False, "Copy commit failed safely: %s" % error


def time_capsule_workflow(frontend: SDLFrontEnd) -> None:
    """Append one Gen I boxed Pokémon to a Gen II save using Time Capsule rules."""
    source_save = choose_save(frontend, 1, "GEN 1 SOURCE SAVE")
    if not source_save:
        return
    source_cache = ensure_sprite_cache(frontend, 1, source_save[0])
    if not source_cache:
        return
    source_record = choose_record(frontend, "GEN 1 POKEMON", source_save, source_cache)
    if not source_record:
        return
    mapping = _load_rom_names(source_cache).get("internal_to_national", {})
    national_species = mapping.get(str(source_record["species"]))
    if not isinstance(national_species, int) or not 1 <= national_species <= 151:
        notice(frontend, "TIME CAPSULE BLOCKED",
               "The matching Gen 1 ROM could not map this Pokémon safely. No save was changed.")
        return
    destination_save = choose_save(frontend, 2, "GEN 2 DESTINATION SAVE")
    if not destination_save:
        return
    destination_cache = ensure_sprite_cache(frontend, 2, destination_save[0])
    if not destination_cache:
        return
    destination = choose_copy_destination(frontend, 2, destination_save)
    if not destination:
        return
    destination_box, destination_slot = destination
    placeholder = {"name": "Empty PC slot", "box": destination_box, "slot": destination_slot}
    if not confirm_transfer(frontend, "TIME CAPSULE", (source_save[0], source_record),
                            (destination_save[0], placeholder), action="transfer"):
        return
    session, output = prepare_gen1_to_gen2((source_save[0], source_record), national_species,
                                           (destination_save[0], destination_box, destination_slot))
    if not session:
        notice(frontend, "TRANSFER NOT PREPARED", output)
        return
    working = session_output(session)
    if not working or not offer_trade_evolution(frontend, session, working, source_record, 1,
                                                source_cache, 2, destination_cache,
                                                destination_box, destination_slot):
        shutil.rmtree(session, ignore_errors=True)
        return
    if confirm_transfer(frontend, "COPIES READY - COMMIT?", (source_save[0], source_record),
                        (destination_save[0], placeholder), action="transfer"):
        success, message = commit_copy(session)
        notice(frontend, "COPY COMPLETE" if success else "COMMIT FAILED",
               completion_message("copy") if success else message, completion=success)
    else:
        shutil.rmtree(session, ignore_errors=True)
        notice(frontend, "TRANSFER CANCELLED", "Original saves are unchanged.")


def gen2_to_gen3_workflow(frontend: SDLFrontEnd) -> None:
    """One-way, copy-only migration from a Gen II PC box into Gen III."""
    source_save = choose_save(frontend, 2, "GEN 2 SOURCE SAVE")
    if not source_save:
        return
    source_cache = ensure_sprite_cache(frontend, 2, source_save[0])
    if not source_cache:
        return
    source_record = choose_record(frontend, "GEN 2 POKEMON", source_save, source_cache)
    if not source_record:
        return
    national_species = _load_rom_names(source_cache).get("internal_to_national", {}).get(
        str(source_record["species"]))
    if not isinstance(national_species, int) or not 1 <= national_species <= 251:
        notice(frontend, "MIGRATION BLOCKED",
               "The matching Gen 2 ROM could not identify this Pokémon safely. No save was changed.")
        return
    destination_save = choose_save(frontend, 3, "GEN 3 DESTINATION SAVE")
    if not destination_save:
        return
    destination_cache = ensure_sprite_cache(frontend, 3, destination_save[0])
    if not destination_cache:
        return
    destination = choose_copy_destination(frontend, 3, destination_save)
    if not destination:
        return
    destination_box, destination_slot = destination
    placeholder = {"name": "Empty PC slot", "box": destination_box, "slot": destination_slot}
    notice(frontend, "GEN 2 TO GEN 3 COPY",
           "One-way copy only. The Gen 2 source remains unchanged. In this first safe pass, held items are cleared rather than risking a wrong Gen 3 item.")
    if not confirm_transfer(frontend, "MIGRATION PREVIEW", (source_save[0], source_record),
                            (destination_save[0], placeholder), action="copy"):
        return
    session, output = prepare_gen2_to_gen3((source_save[0], source_record), national_species,
                                           (destination_save[0], destination_box, destination_slot))
    if not session:
        notice(frontend, "MIGRATION NOT PREPARED", output)
        return
    working = session_output(session)
    if not working or not offer_trade_evolution(frontend, session, working, source_record, 2,
                                                source_cache, 3, destination_cache,
                                                destination_box, destination_slot):
        shutil.rmtree(session, ignore_errors=True)
        return
    warnings = []
    if "held_item_cleared=1" in output:
        warnings.append("Held item will be cleared.")
    if "ev_points_reduced=0" not in output:
        warnings.append("EVs were normalized to Gen 3 limits.")
    if "moves_cleared=0" not in output:
        warnings.append("An unsupported move slot was cleared.")
    notice(frontend, "MIGRATION READY",
           " ".join(warnings) or "Moves, level, nickname and OT are ready to copy.")
    if confirm_transfer(frontend, "COPIES READY - COMMIT?", (source_save[0], source_record),
                        (destination_save[0], placeholder), action="copy"):
        success, message = commit_copy(session)
        notice(frontend, "COPY COMPLETE" if success else "COMMIT FAILED",
               completion_message("copy") if success else message, completion=success)
    else:
        shutil.rmtree(session, ignore_errors=True)
        notice(frontend, "MIGRATION CANCELLED", "Original saves are unchanged.")


def local_swap_workflow(frontend: SDLFrontEnd) -> None:
    debug("local transfer entered")
    generation_choice = choose_list(frontend, "LOCAL TRANSFER",
                                    "Choose the game generation. B returns.",
                                     [("GEN 1", "Red / Blue / Yellow"),
                                     ("GEN 2", "Gold / Silver / Crystal"),
                                     ("GEN 3", "Ruby / Sapphire / Emerald / FRLG"),
                                     ("TIME CAPSULE", "Transfer a Gen 1 Pokémon into a Gen 2 save"),
                                     ("GEN 2 → GEN 3", "Copy a Gen 2 Pokémon into a Gen 3 save")])
    if generation_choice is None:
        return
    if generation_choice == 3:
        time_capsule_workflow(frontend)
        return
    if generation_choice == 4:
        gen2_to_gen3_workflow(frontend)
        return
    generation = generation_choice + 1
    debug("generation selected: %d" % generation)
    left_save = choose_save(frontend, generation, "FIRST SAVE")
    if not left_save:
        return
    left_cache = ensure_sprite_cache(frontend, generation, left_save[0])
    if not left_cache:
        return
    left_record = choose_record(frontend, "FIRST POKEMON", left_save, left_cache)
    if not left_record:
        return
    operation = choose_list(frontend, "CHOOSE ACTION",
                            "Choose what to do with %s. B returns without changing a save." % left_record["name"],
                            [("TRADE", "Swap with one Pokémon from another save"),
                             ("COPY", "Add a copy to an empty PC slot in another save")])
    if operation is None:
        return
    right_save = choose_save(frontend, generation, "SECOND SAVE", excluded=left_save[0])
    if not right_save:
        return
    right_cache = ensure_sprite_cache(frontend, generation, right_save[0])
    if not right_cache:
        return
    if operation == 1:
        destination = choose_copy_destination(frontend, generation, right_save)
        if not destination:
            return
        destination_box, destination_slot = destination
        placeholder = {"name": "Empty PC slot", "box": destination_box, "slot": destination_slot}
        if not confirm_transfer(frontend, "SAFE COPY", (left_save[0], left_record),
                                (right_save[0], placeholder), action="copy"):
            return
        session, output = prepare_copy(generation, (left_save[0], left_record),
                                       (right_save[0], destination_box, destination_slot))
        if not session:
            notice(frontend, "COPY NOT PREPARED", output)
            return
        working = session_output(session)
        if not working or not offer_trade_evolution(frontend, session, working, left_record,
                                                    generation, left_cache, generation, right_cache,
                                                    destination_box, destination_slot):
            shutil.rmtree(session, ignore_errors=True)
            return
        if confirm_transfer(frontend, "COPIES READY - COMMIT?", (left_save[0], left_record),
                            (right_save[0], placeholder), action="copy"):
            success, message = commit_copy(session)
            notice(frontend, "COPY COMPLETE" if success else "COMMIT FAILED",
                   completion_message("copy") if success else message, completion=success)
        else:
            shutil.rmtree(session, ignore_errors=True)
            notice(frontend, "COPY CANCELLED", "Original saves are unchanged.")
        return
    right_record = choose_record(frontend, "SECOND POKEMON", right_save, right_cache)
    if not right_record:
        return
    if not confirm_transfer(frontend, "SAFE SWAP", (left_save[0], left_record),
                            (right_save[0], right_record)):
        return
    session, output = prepare_swap(generation, (left_save[0], left_record),
                                   (right_save[0], right_record))
    if not session:
        notice(frontend, "SWAP NOT PREPARED", output)
        return
    left_working = session_output(session, "left-")
    right_working = session_output(session, "right-")
    # Each Pokémon is now in the other save's slot, so offer its evolution on
    # that corresponding working copy. Either can be declined independently.
    if (not left_working or not right_working or
        not offer_trade_evolution(frontend, session, left_working, right_record,
                                  generation, right_cache, generation, left_cache,
                                  left_record["box"], left_record["slot"]) or
        not offer_trade_evolution(frontend, session, right_working, left_record,
                                  generation, left_cache, generation, right_cache,
                                  right_record["box"], right_record["slot"])):
        shutil.rmtree(session, ignore_errors=True)
        return
    if confirm_transfer(frontend, "COPIES READY - COMMIT?", (left_save[0], left_record),
                        (right_save[0], right_record)):
        success, message = commit_swap(session)
        notice(frontend, "TRADE COMPLETE" if success else "COMMIT FAILED",
               completion_message("trade") if success else message, completion=success)
    else:
        shutil.rmtree(session, ignore_errors=True)
        notice(frontend, "TRADE CANCELLED", "Original saves are unchanged.")


def main() -> int:
    controller = None
    frontend = None
    try:
        # The Flip's physical pad is exposed through the established ButterflyOS
        # gptokeyb bridge.  It maps A to Enter and B/Menu to Escape consistently
        # across the built-in pad and standard Bluetooth controllers.
        controller = start_controller()
        time.sleep(0.15)
        frontend = SDLFrontEnd(keyboard_bridge=controller is not None)
        selected = 0
        while True:
            frontend.draw_page("main", selected)
            key = frontend.next_key()
            if key is None:
                continue
            debug("main key=%r selected=%d action=%s" %
                  (key, selected, PAGES["main"][2][selected][0]))
            items = PAGES["main"][2]
            if key in (KEY_UP, ord("k")):
                selected = (selected - 1) % len(items)
            elif key in (KEY_DOWN, ord("j")):
                selected = (selected + 1) % len(items)
            elif key in (KEY_Q, ord("Q"), KEY_ESCAPE, KEY_B, ord("B"), KEY_CANCEL, ord("X")):
                debug("main closed by input")
                return 0
            elif key in (KEY_RETURN, KEY_A, ord("A"), KEY_CONFIRM, ord("Z")):
                action = items[selected][0]
                if action == "close":
                    return 0
                if action == "sprites":
                    sprite_browser(frontend)
                    continue
                if action == "local":
                    debug("main selected local transfer")
                    local_swap_workflow(frontend)
                    continue
                if action == "remote":
                    remote_session_workflow(frontend)
                    continue
                if action == "inspect":
                    notice(frontend, "READ-ONLY INSPECTION",
                           "Select Sprite Preview to inspect boxed Pokemon while the full SDL inspector is completed.")
                    continue
                if action == "commit":
                    notice(frontend, "COMMIT PREPARED TRANSFER",
                           "Native resume and commit controls are the next SDL screen. New local swaps can commit immediately.")
                    continue
                if action == "discard":
                    notice(frontend, "DISCARD PREPARED TRANSFER",
                           "Prepared copies are harmless until committed. Native session cleanup is coming with the resume screen.")
                    continue
                if action == "about":
                    about_butterfly_link(frontend)
                    continue
    except (OSError, RuntimeError) as error:
        print(f"Butterfly Link SDL front end unavailable: {error}", file=sys.stderr)
        return 127
    finally:
        stop_controller(controller)
        if frontend is not None:
            frontend.close()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda _sig, _frame: sys.exit(0))
    raise SystemExit(main())
