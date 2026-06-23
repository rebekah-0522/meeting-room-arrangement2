# Debug Session: backend-unstable

## Status: [OPEN]

## Bug Description
- Backend service (Flask) keeps crashing/exiting unexpectedly
- Frontend shows "API request failed: TypeError: Failed to fetch"
- Terminal output is empty or service exits immediately

## Hypotheses
1. **H1**: Flask debug mode causes auto-reload issues when files change
2. **H2**: SQLite database file permission issues cause crashes
3. **H3**: Python environment has missing/incompatible dependencies
4. **H4**: Port 5000 is already in use by another process
5. **H5**: Flask app has unhandled exceptions during initialization

## Environment
- OS: Windows
- Python: 3.14.6
- Flask: 3.1.3
- SQLite: Built-in

## Reproduction Steps
1. Run `python server/app.py`
2. Service starts but exits shortly after
3. Frontend cannot connect to backend API

## Evidence Collection
- TBD

## Fix Applied
- TBD

## Verification
- TBD