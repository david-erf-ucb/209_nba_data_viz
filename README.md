NBA Data Visualizations — Local Run Guide (Mac & Windows)

What you get
- Flask server (homepage + /shots) on http://localhost:8001
- Streamlit Explorer on http://localhost:8501/nba (opens in a separate tab)
- Sample parquet for the shot chart: sample_data/nba_shots_min.parquet

Prerequisites
- Git
- Python 3.9 or newer

Option A: One‑command startup (recommended)
Mac/Linux
1) Open Terminal and run:
   bash scripts/start.sh
2) Open:
   - Flask: http://localhost:8001
   - Explorer: http://localhost:8501/nba

Windows (PowerShell)
1) Open PowerShell and run:
   powershell -ExecutionPolicy Bypass -File scripts\\start.ps1
2) Open:
   - Flask: http://localhost:8001
   - Explorer: http://localhost:8501/nba

Option B: Manual steps
Mac/Linux
1) Clone
   git clone <your-repo-url> && cd flask-hello-ec2
2) Create and activate venv
   python3 -m venv .venv && source .venv/bin/activate
3) Install dependencies
   pip install -U pip
   pip install -r requirements.txt -r requirements-streamlit.txt
4) Start Flask (port 8001)
   python app.py
   (keep this terminal open)
5) In a second terminal (same venv), start Streamlit (port 8501)
   source .venv/bin/activate
   streamlit run nba_scatter_live_app.py --server.port 8501 --server.baseUrlPath /nba --server.headless true
6) Open:
   - http://localhost:8001
   - http://localhost:8501/nba

Windows (PowerShell)
1) Clone
   git clone <your-repo-url>
   cd flask-hello-ec2
2) Create and activate venv
   python -m venv .venv
   .\\.venv\\Scripts\\Activate.ps1
3) Install dependencies
   pip install -U pip
   pip install -r requirements.txt -r requirements-streamlit.txt
4) Start Flask (port 8001)
   python app.py
   (keep this window open)
5) New PowerShell, start Streamlit (port 8501)
   .\\.venv\\Scripts\\Activate.ps1
   streamlit run \"nba_scatter_live_app.py\" --server.port 8501 --server.baseUrlPath /nba --server.headless true
6) Open:
   - http://localhost:8001
   - http://localhost:8501/nba

Stopping the servers
- Mac/Linux:
  pkill -f \"python app.py\" || true
  pkill -f \"streamlit run\" || true
- Windows:
  Close the terminal windows or end Python processes from Task Manager.

Troubleshooting
- Port already in use:
  - Mac/Linux:
    lsof -tiTCP:8001 -sTCP:LISTEN | xargs kill -9\n    lsof -tiTCP:8501 -sTCP:LISTEN | xargs kill -9
  - Windows (PowerShell):
    netstat -ano | findstr \":8001\"\n    netstat -ano | findstr \":8501\"\n    taskkill /PID <pid> /F
- Virtual environment missing:
  - Recreate: python -m venv .venv (activate and pip install)
- Explorer embedded page:
  - Expected to open in a separate tab at http://localhost:8501/nba

Data used by /shots
- Flask reads from sample_data/nba_shots_min.parquet
- If the file is missing, a tiny demo dataframe is used as fallback
