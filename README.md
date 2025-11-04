Minimal Flask on EC2 (dev server) for quick demo.

Quick start (single EC2, Nginx reverse proxy):

1) Install runtime deps

   sudo apt update && sudo apt install -y nginx
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-streamlit.txt

2) Run Flask

   source venv/bin/activate
   python app.py  # binds 0.0.0.0:8000

3) Run Streamlit

   source venv/bin/activate
   streamlit run nba_scatter_live_app.py \
     --server.port 8501 \
     --server.baseUrlPath /nba \
     --server.headless true

4) Nginx config

   sudo cp nginx.conf /etc/nginx/sites-available/flask_streamlit
   sudo ln -sf /etc/nginx/sites-available/flask_streamlit /etc/nginx/sites-enabled/flask_streamlit
   sudo nginx -t && sudo systemctl reload nginx

5) Open in browser

   http://<your-ec2-host>/explorer

Notes
- Do not expose port 8501 publicly; Nginx proxies /nba/ to it.
- If you use HTTPS, install a cert (Let's Encrypt) and update the server block.

Data file (parquet) usage
- Flask `/shots` attempts to load a parquet at `sample_data/nba_pbp_combined.parquet`.
- You may override the location with the env var `NBA_PBP_PARQUET_PATH`.
- Example on EC2 (repo path `/home/ubuntu/209_nba_data_viz`):

  ```bash
  export NBA_PBP_PARQUET_PATH="/home/ubuntu/209_nba_data_viz/sample_data/nba_pbp_combined.parquet"
  nohup ./venv/bin/python app.py > flask.out 2>&1 &
  ```

Recommended: keep large data outside git and symlink into `sample_data/`:

```bash
sudo mkdir -p /srv/nbadata && sudo chown "$USER":"$USER" /srv/nbadata
mv sample_data/nba_pbp_combined.parquet /srv/nbadata/   # if present
ln -sfn /srv/nbadata/nba_pbp_combined.parquet sample_data/nba_pbp_combined.parquet
```

The repository `.gitignore` excludes parquet files in `sample_data/` so you won't accidentally commit them.
