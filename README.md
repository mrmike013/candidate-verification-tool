# Candidate Verification Tool (v2)

Lightweight Flask backend that sends 5‑minute assessments to job applicants so companies can filter out mass‑appliers.

## Quick start (local)
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=backend.wsgi:application
flask --app backend.wsgi run --debug
