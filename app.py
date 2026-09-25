#!/usr/bin/env python3
"""Small localhost workbench for Garmin Edge data-screen profiles."""

from __future__ import annotations

import csv
import getpass
import io
import os
import secrets
import sys
import tempfile
import uuid
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request, send_file, session


ROOT = Path(__file__).resolve().parent
TOOL_DIR = ROOT / "vendor" / "activity-profile-editor"
sys.path.insert(0, str(TOOL_DIR))

from fit_dump import (  # noqa: E402
    DATA_SCREEN_MESG_KEY,
    FIELD_ID_NAMES,
    NAMED_SCREEN_TYPES,
    active_field_ids,
    classify_screens,
    decode_file,
    field_name,
    layout_grid,
    layout_states,
    screen_type_name,
)
from fit_patch import (  # noqa: E402
    pack_field_count,
    pack_field_id_array,
    pack_layout_variant,
    patch_screen_maintaining_ciq,
)


app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

# The browser session holds only a random key. FIT bytes stay in memory and
# are never written over the source profile or directly onto the device.
PROFILES: dict[str, tuple[str, bytes]] = {}
GARMIN_ROOT = Path(os.environ.get(
    "GARMIN_ROOT",
    str(Path("/run/media") / getpass.getuser() / "GARMIN"),
))
DEVICE_ROAD_FIT = GARMIN_ROOT / "Garmin" / "Sports" / "CyclingRoadROAD.fit"


def read_catalog() -> list[dict]:
    result = []
    with (ROOT / "edge530-campi-road.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            raw_id = row["fit_id"].strip()
            if not raw_id:
                continue
            result.append({
                "category": row["category"],
                "name": row["field"],
                "id": int(raw_id),
                "status": row["id_status"],
                "notes": row["notes"],
            })
    return result


CATALOG = read_catalog()
CATALOG_IDS = {entry["id"] for entry in CATALOG}
CATALOG_NAMES: dict[int, str] = {}
for _entry in CATALOG:
    CATALOG_NAMES.setdefault(_entry["id"], _entry["name"])


def current_profile() -> tuple[str, str, bytes]:
    key = session.get("profile_key")
    if not key or key not in PROFILES:
        abort(400, description="Open a FIT profile first.")
    filename, data = PROFILES[key]
    return key, filename, data


def decode_bytes(data: bytes):
    with tempfile.NamedTemporaryFile(suffix=".fit") as temp:
        temp.write(data)
        temp.flush()
        messages = decode_file(temp.name)
    if DATA_SCREEN_MESG_KEY not in messages:
        raise ValueError("The FIT file does not contain recognizable data screens.")
    return messages


def serialize_screens(messages) -> list[dict]:
    classified = classify_screens(messages)
    screens = []
    for position, slot, message in classified["orderable"]:
        f10 = message.get(10)
        count = message.get(3, 0) or 0
        variant = message.get(8, 0) or 0
        fields = []
        for field_id in active_field_ids(message, count):
            fields.append({
                "id": field_id,
                "name": CATALOG_NAMES.get(field_id, field_name(field_id)),
            })
        options = []
        for option_count, option_variant in layout_states(f10):
            if not any(item["count"] == option_count for item in options):
                options.append({"count": option_count, "variants": []})
            grid = layout_grid(f10, option_count, option_variant)
            options[-1]["variants"].append({
                "value": option_variant,
                "label": "A" if len([v for c, v in layout_states(f10) if c == option_count]) == 1 or option_variant == layout_states(f10)[0][1] else "B",
                "grid": grid,
            })
        screens.append({
            "position": position,
            "slot": slot,
            "type": screen_type_name(f10),
            "typeCode": f10,
            "count": count,
            "variant": variant,
            "enabled": message.get(12, 0) == 0,
            "editable": f10 not in NAMED_SCREEN_TYPES,
            "fields": fields,
            "layoutOptions": options,
        })
    return screens


def activate_profile(filename: str, data: bytes) -> list[dict]:
    messages = decode_bytes(data)
    screens = serialize_screens(messages)
    key = session.get("profile_key") or uuid.uuid4().hex
    session["profile_key"] = key
    PROFILES[key] = (Path(filename).name, data)
    return screens


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/catalog")
def catalog():
    return jsonify(CATALOG)


@app.post("/api/open")
def open_profile():
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        return jsonify(error="Choose a FIT file."), 400
    data = uploaded.read()
    if not data:
        return jsonify(error="The file is empty."), 400
    try:
        screens = activate_profile(uploaded.filename, data)
    except Exception as exc:  # report malformed or unsupported FITs to the UI
        return jsonify(error=f"Could not read the FIT profile: {exc}"), 400
    return jsonify(filename=Path(uploaded.filename).name, screens=screens)


@app.post("/api/open-device")
def open_device_profile():
    if not DEVICE_ROAD_FIT.is_file():
        return jsonify(error="Could not find CyclingRoadROAD.fit in the mounted Garmin/Sports folder."), 404
    try:
        data = DEVICE_ROAD_FIT.read_bytes()
        screens = activate_profile("CyclingRoadROAD.fit", data)
    except Exception as exc:
        return jsonify(error=f"Could not read the Road profile: {exc}"), 400
    return jsonify(filename="CyclingRoadROAD.fit", screens=screens)


@app.get("/api/state")
def get_state():
    _key, filename, data = current_profile()
    try:
        screens = serialize_screens(decode_bytes(data))
    except Exception as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(filename=filename, screens=screens)


@app.post("/api/save")
def save_changes():
    key, filename, original = current_profile()
    payload = request.get_json(silent=True) or {}
    requested = payload.get("screens", [])
    if not isinstance(requested, list):
        return jsonify(error="Invalid change format."), 400
    try:
        with tempfile.TemporaryDirectory(prefix="edge530-ui-") as temp_dir:
            base = Path(temp_dir)
            current_path = base / "source.fit"
            current_path.write_bytes(original)
            messages = decode_file(str(current_path))
            data_screens = messages.get(DATA_SCREEN_MESG_KEY, [])
            by_slot = {m.get(254): m for m in data_screens}

            for edit in requested:
                slot = int(edit["slot"])
                message = by_slot.get(slot)
                if not message or message.get(9) is None:
                    raise ValueError(f"Screen slot {slot} is not editable.")
                f10 = message.get(10)
                if f10 in NAMED_SCREEN_TYPES:
                    raise ValueError(f"{screen_type_name(f10)} is a protected Garmin screen.")
                ids = edit.get("fieldIds")
                count = int(edit.get("count", -1))
                variant = int(edit.get("variant", -1))
                if not isinstance(ids, list) or count < 1 or count > 10 or len(ids) != count:
                    raise ValueError("Each screen must have between 1 and 10 selected fields.")
                ids = [int(value) for value in ids]
                old_count = message.get(3, 0) or 0
                old_variant = message.get(8, 0) or 0
                old_ids = active_field_ids(message, old_count)
                if any(field_id not in CATALOG_IDS and field_id not in old_ids for field_id in ids):
                    raise ValueError("The selection includes a field that is not in the catalog.")
                if ids == old_ids and count == old_count and variant == old_variant:
                    continue
                legal_states = layout_states(f10)
                if (count, variant) not in legal_states:
                    raise ValueError(f"That layout is not available for {count} fields on screen slot {slot}.")
                if len([i for i, fid in enumerate(old_ids) if fid == 216]) > 1:
                    raise ValueError("This screen has multiple Connect IQ fields and cannot be safely rearranged.")

                next_path = base / f"patched-{slot}.fit"
                patch_screen_maintaining_ciq(
                    str(current_path),
                    str(next_path),
                    slot,
                    {
                        3: pack_field_count(count),
                        7: pack_field_id_array(ids),
                        8: pack_layout_variant(variant),
                    },
                )
                current_path = next_path

            result = current_path.read_bytes()
    except Exception as exc:
        return jsonify(error=str(exc)), 400

    PROFILES[key] = (filename, result)
    return jsonify(filename=filename, screens=serialize_screens(decode_bytes(result)))


@app.get("/api/download")
def download_profile():
    _key, filename, data = current_profile()
    return send_file(
        io.BytesIO(data),
        mimetype="application/octet-stream",
        as_attachment=True,
        download_name=filename,
        max_age=0,
    )


@app.errorhandler(413)
def too_large(_error):
    return jsonify(error="The FIT file exceeds the 16 MB limit."), 413


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5050"))
    print(f"Garmin screen workbench: http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=False)
