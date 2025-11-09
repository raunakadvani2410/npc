# Deployment Checklist for Flask App

## Pre-Deployment (Local)

- [x] Create modular structure (services/, static/, templates/)
- [x] Extract Selenium functions into services/scraper.py
- [x] Extract data processing into services/data_processor.py
- [x] Create AppState for state management
- [x] Build Flask app with all API endpoints
- [x] Create dashboard HTML with UI components
- [x] Add CSS styling (Streamlit-inspired dark theme)
- [x] Add JavaScript for AJAX polling and table rendering
- [x] Update requirements.txt (Flask instead of Streamlit)

## Server Deployment Steps

### 1. Pull Latest Code
```bash
cd /opt/npc
git pull origin <branch-name>
```

### 2. Activate Virtual Environment and Install Dependencies
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Verify File Structure
```bash
ls -R services/ static/ templates/
# Should show:
# - services/__init__.py, scraper.py, data_processor.py, data_store.py
# - static/css/style.css, static/js/main.js
# - templates/dashboard.html
```

### 4. Test Imports (Optional)
```bash
python -c "from services.data_store import app_state; print('OK')"
python -c "from services.scraper import enter_webpage; print('OK')"
python -c "from services.data_processor import build_dataframe; print('OK')"
```

### 5. Update Supervisor Configuration

Create new config: `/etc/supervisor/conf.d/npc_flask.conf`

```ini
[program:npc_flask]
directory=/opt/npc
command=/opt/npc/venv/bin/python app.py
autostart=true
autorestart=true
stderr_logfile=/var/log/npc_flask.err.log
stdout_logfile=/var/log/npc_flask.out.log
user=root
environment=DISPLAY=":99"
```

### 6. Reload Supervisor
```bash
supervisorctl reread
supervisorctl update
supervisorctl start npc_flask
supervisorctl status
```

### 7. Check Logs
```bash
tail -f /var/log/npc_flask.out.log
tail -f /var/log/npc_flask.err.log
```

### 8. Access the App
Open browser to: `http://<server-ip>:5000`

### 9. Test the Flow
1. Click "Start Scraping"
2. Wait for "Waiting for OTP" status
3. Enter OTP when prompted
4. Verify data appears in tabs
5. Click "Stop" to test stopping

## Port Configuration

If port 5000 is already in use, edit `app.py`:
```python
app.run(debug=False, host='0.0.0.0', port=5001, threaded=True)
```

## Nginx Reverse Proxy (Optional)

If you want to access via domain/subdomain:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## Troubleshooting

### App won't start
- Check Python path: `which python` in venv
- Check dependencies: `pip list | grep Flask`
- Check logs: `supervisorctl tail npc_flask stderr`

### Browser errors
- Check if port is open: `netstat -tuln | grep 5000`
- Check firewall: `ufw status`
- Try accessing locally first: `curl http://localhost:5000`

### Selenium errors
- Verify ChromeDriver: `./chromedriver --version`
- Check Display: `echo $DISPLAY`
- Install xvfb if needed: `apt-get install xvfb`

## Monitoring

Check app status:
```bash
supervisorctl status npc_flask
```

Restart app:
```bash
supervisorctl restart npc_flask
```

Stop app:
```bash
supervisorctl stop npc_flask
```

## Git Workflow

Don't forget to commit your changes:
```bash
git add .
git commit -m "Migrate from Streamlit to Flask"
git push origin <branch-name>
```

## Rollback Plan

If the Flask app has issues, you can rollback to Streamlit:
```bash
git checkout <previous-commit>
supervisorctl restart npc_streamlit  # or whatever your old supervisor program was
```

