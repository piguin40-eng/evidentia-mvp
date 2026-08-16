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
