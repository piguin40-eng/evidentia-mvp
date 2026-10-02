# BigColor PREP 2 Render Package

Technical QA viewer for preoperative/wax-up STL thickness mapping.

## Local Run

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python prep_app_server.py 8787 --host 127.0.0.1
```

Open:

```text
http://127.0.0.1:8787/BigColor_PREP_2_APP.html
```

## Render

This package is intentionally stripped down for deployment:

- App HTML
- Python analysis server
- Prep engine
- Demo STL assets
- Material rules

Historical QA images, logs, backups and generated outputs are excluded.

Clinical caveat: technical QA viewer only. Do not use as validated clinical precision until registration, units, segmentation and repeatability are validated.

## Python measurement map

`POST /api/analyze` with `include_viewer=1` returns optional
`analysis.measurement_viewer` (`prep.vertex-distance.v1`). Its indexed positions
are the engine's measured, unit-scaled wax-up in mm; distances, teeth and zones
share exactly that vertex order. The viewer does not recompute a browser field.
Colors encode geometric distance, not material compliance or instructions to
prepare a tooth. Registration/clinical gates and estimated segmentation remain.
Point readings interpolate the engine distances on the hit triangle.

Fast-vertex and exact-surface vertex outputs support the map. Normal-ray sample
outputs return an explicit unavailable reason rather than inventing a continuous
field. Production may restrict heavy methods; inspect executed method in the
response. Oversized/nonfinite transports leave the table available.

Regression: `python -m unittest test_measurement_viewer -v` covers a known 0.5 mm
separation, unit conversion and the opt-in contract. Browser checks cover actual
STL upload, Python analysis, color rendering and touch/click readings.
