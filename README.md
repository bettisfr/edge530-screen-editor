# Edge 530 Screen Editor

A small local web app for previewing and editing Garmin Edge 530 activity-profile data screens. It reads a `.FIT` profile, lets you choose the fields and screen layout, then exports a modified `.FIT` file. It does not write to the Garmin automatically.

## Run locally

Python 3.9 or newer is required. Run the commands below inside the Python environment you want to use (for example, an already activated virtual environment).

```bash
python -m pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5050>. To use a different port, set `PORT` before starting the app.

Choose **Open Road from Garmin** when the Edge is mounted under `/run/media/<username>/GARMIN`, or use **Open FIT file** to load a profile from any location. For a different mount point, set `GARMIN_ROOT` to the Garmin volume's root directory before starting the app. Select a page with the arrows, set its field count from 1 to 10, choose layout A/B where available, then click a cell and select a field. **Prepare changes** updates the in-memory working copy; **Export FIT** downloads it using the original profile filename. Copy the exported file to `Garmin/NewFiles` yourself and eject the device safely.

The preview uses the two-column Edge 530 layout geometry recorded in the upstream Activity Profile Editor code. Garmin-defined pages are read-only. FIT files, backups, and temporary files are ignored by Git.

## Project files

- `app.py` — local Flask API and FIT read/patch workflow.
- `templates/` and `static/` — minimal visual editor and device preview.
- `edge530-campi-road.csv` — field catalog and Edge 530 ID validation status.
- `edge530-fit-mappings.csv` — observed field mapping for the Road profile.
- `vendor/activity-profile-editor/` — the four upstream FIT parsing/patching modules used by the app, with their MIT license.

The vendored modules come from [Activity Profile Editor for Garmin Edge](https://github.com/fullcarbonbike/Activity-Profile-Editor). FIT decoding uses Garmin's `garmin-fit-sdk` Python package, installed from `requirements.txt`.
