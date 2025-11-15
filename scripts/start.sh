#!/usr/bin/env bash
set -euo pipefail

# Start Flask (8001) and Streamlit (8501) locally.
# No app code is modified; this just automates venv + installs + run.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_DIR}"

if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt -r requirements-streamlit.txt

# Kill any previous instances
pkill -f "python app.py" || true
pkill -f "streamlit run" || true

# Start Flask (8001)
nohup python app.py >/tmp/flask_8001.out 2>&1 &
sleep 1

# Start Streamlit (8501)
nohup streamlit run "nba_scatter_live_app.py" --server.port 8501 --server.baseUrlPath /nba --server.headless true >/tmp/streamlit_8501.out 2>&1 &
sleep 2

echo
echo "Flask:     http://localhost:8001"
echo "Explorer:  http://localhost:8501/nba"
echo
echo "Logs:"
echo "  tail -f /tmp/flask_8001.out"
echo "  tail -f /tmp/streamlit_8501.out"


