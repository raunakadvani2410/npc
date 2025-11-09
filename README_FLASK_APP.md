# Option Chain ROC Flask Application

This is a Flask-based web application that scrapes Nifty options data from Sensibull and displays rate-of-change (ROC) analysis in real-time without page refreshes.

## Architecture

```
npc/
├── app.py                      # Main Flask application
├── config.py                   # Configuration & constants
├── services/
│   ├── __init__.py
│   ├── scraper.py              # Selenium scraping logic
│   ├── data_processor.py       # DataFrame processing
│   └── data_store.py           # In-memory state management
├── static/
│   ├── css/
│   │   └── style.css           # Styling (Streamlit-inspired)
│   └── js/
│       └── main.js             # Frontend logic (AJAX polling, table rendering)
├── templates/
│   └── dashboard.html          # Main dashboard view
└── requirements.txt            # Python dependencies
```

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure ChromeDriver is present:**
   - The `chromedriver` binary should be in the project root
   - Or update `CHROMEDRIVER_PATH` in `config.py`

3. **Configure credentials (optional):**
   - Set environment variables:
     ```bash
     export ZERODHA_USER_ID="your_user_id"
     export ZERODHA_PASSWORD="your_password"
     ```
   - Or edit `config.py` directly (not recommended for production)

## Running the App

### Local Development
```bash
python app.py
```
Then open http://localhost:5000 in your browser.

### Production (Ubuntu Server)
Use Supervisor to manage the Flask app:

1. **Update supervisor config:**
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

2. **Reload supervisor:**
   ```bash
   supervisorctl reread
   supervisorctl update
   supervisorctl start npc_flask
   ```

3. **Check status:**
   ```bash
   supervisorctl status npc_flask
   ```

## Usage Flow

1. **Click "Start Scraping"**
   - App opens Sensibull in headless browser
   - Enters credentials automatically
   - Sends OTP to your phone

2. **Enter OTP**
   - OTP input field appears
   - Enter the 6-digit OTP from your phone
   - Click "Submit OTP"

3. **View Data**
   - App fetches initial data
   - Waits 30 seconds, then starts polling every 30 seconds
   - Tables update automatically without page refresh
   - Most recent data appears at the top

4. **Click "Stop"**
   - Stops scraping
   - Closes browser
   - Resets app to IDLE state

## API Endpoints

- `GET /` - Main dashboard
- `POST /api/start` - Start scraping process
- `POST /api/stop` - Stop scraping and reset
- `POST /api/submit_otp` - Submit OTP during login
- `GET /api/status` - Get current state and logs
- `GET /api/roc` - Get rate-of-change data
- `GET /api/reference` - Get reference data (t0)

## Features

- **No page refreshes** - AJAX polling updates data in place
- **State management** - Proper state machine (IDLE → LOGGING_IN → WAITING_FOR_OTP → SCRAPING)
- **Error handling** - Shows errors in UI, requires manual restart
- **Logs display** - Real-time logs visible in dashboard
- **Tab-based UI** - Separate tabs for each strike price
- **Streamlit-inspired styling** - Dark theme matching original app

## Differences from Streamlit Version

| Feature | Streamlit | Flask |
|---------|-----------|-------|
| Page refresh | Full reload on every update | No refresh, AJAX updates only |
| State persistence | Limited | Full control with AppState |
| UI updates | Entire page | Only changed data |
| Start/Stop | Auto-start on load | Manual start/stop buttons |
| OTP entry | External Flask app | Integrated in UI |
| Scroll position | Resets on update | Preserved |
| Tab selection | Resets on update | Preserved |

## Configuration

Edit `config.py` to change:
- Trading hours
- Scraping intervals
- Strike price range
- Chrome driver path

## Troubleshooting

**Browser not opening:**
- Check ChromeDriver path in `config.py`
- Ensure PyVirtualDisplay is installed

**OTP not working:**
- Verify you're entering the OTP from your phone
- Check logs for Selenium errors

**Data not updating:**
- Check browser console for JavaScript errors
- Verify `/api/status` returns `"state": "SCRAPING"`
- Check Flask logs for Python errors

**Port already in use:**
- Change port in `app.py`: `app.run(port=5001)`

## Development Notes

- Background scraping runs in a separate thread
- Thread-safe operations use locks in AppState
- Frontend polls status every 2 seconds
- Frontend polls data every 5 seconds (only when SCRAPING)
- Most recent ROC data is stacked at the top

