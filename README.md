## Nifty Options ROC Dashboard (Flask)

NIFTY options monitoring tool that logs into Sensibull via Zerodha, scrapes the option chain, and serves **rate‑of‑change (ROC)** analytics over a Flask dashboard with a headless Chrome/Selenium backend.

The app is designed for intraday use during Indian market hours and keeps state in memory for fast, streaming‑style updates.

---

## Architecture

High‑level structure:

```text
npc/
├── app.py                 # Main Flask app + scraping orchestration
├── config.py              # Trading hours, strike config, driver path, env lookups
├── services/
│   ├── __init__.py
│   ├── scraper.py         # Selenium login + Sensibull table scraper
│   ├── data_processor.py  # DataFrame construction + ROC calculations
│   └── data_store.py      # In‑memory AppState (data, logs, state machine)
├── templates/
│   └── dashboard.html     # Main dashboard UI
├── static/
│   ├── css/style.css      # Dark‑theme styling
│   └── js/main.js         # Frontend polling + table rendering
├── frontend/
│   └── app.py             # Legacy/simple OTP Flask app (not required for main flow)
├── requirements.txt       # Python dependencies
├── README_FLASK_APP.md    # Older, implementation‑heavy README
└── DEPLOYMENT_CHECKLIST.md
```

Core flow:

- **Flask API** in `app.py` exposes `/api/start`, `/api/stop`, `/api/submit_otp`, `/api/status`, `/api/roc`, `/api/reference`, `/api/highest_oi`.
- **Background scraping loop** runs in a daemon thread, managed by `AppState` in `data_store.py`.
- **Selenium + ChromeDriver** in `scraper.py` logs into Sensibull via Zerodha and scrapes the option chain.
- **Pandas processing** in `data_processor.py` converts raw table text into structured frames, slices around ATM strikes, and computes ROC + remarks.
- **Frontend** polls JSON endpoints and updates the dashboard without page reloads.

---

## Prerequisites

- Python 3.9+ (tested on macOS / Linux).
- Google Chrome installed.
- Matching ChromeDriver binary.
- Ability to run a virtual X display on headless Linux (uses `pyvirtualdisplay`).

---

## Setup

### 1. Clone and create a virtualenv

```bash
git clone <this-repo-url>
cd npc
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. ChromeDriver

- Place the `chromedriver` binary in the project root **or** update `CHROMEDRIVER_PATH` in `config.py`:

```python
CHROMEDRIVER_PATH = "./chromedriver"
```

Make sure the ChromeDriver version matches your installed Chrome major version.

### 4. Environment variables / `.env`

Credentials and some flags are pulled via environment variables (loaded with `python-dotenv`):

- `ZERODHA_USER_ID` – Zerodha login user ID.
- `ZERODHA_PASSWORD` – Zerodha password.
- `FLASK_DEBUG` – `"true"` or `"false"` (string, case‑insensitive).

You can either export them in your shell:

```bash
export ZERODHA_USER_ID="your_user_id"
export ZERODHA_PASSWORD="your_password"
export FLASK_DEBUG="true"
```

Or create a `.env` file in the project root:

```env
ZERODHA_USER_ID=your_user_id
ZERODHA_PASSWORD=your_password
FLASK_DEBUG=true
```

Never commit real credentials.

---

## Running the app (local)

From the project root:

```bash
source .venv/bin/activate  # if not already active
python app.py
```

By default `app.py` runs:

- Host: `0.0.0.0`
- Port: `8501`
- Debug: controlled by `FLASK_DEBUG` env var (defaults to `False`)

Open the dashboard in your browser:

```text
http://localhost:8501
```

---

## Usage flow

1. **Open the dashboard**
   - Go to `http://localhost:8501`.

2. **Configure and start**
   - On the UI, select:
     - Ticker (e.g. `NIFTY`).
     - Expiry date (required, `YYYY-MM-DD`).
   - Click **Start**.
   - The backend:
     - Creates a virtual display (`pyvirtualdisplay`).
     - Opens Sensibull in headless Chrome.
     - Clicks through to login with Zerodha.
     - Fills in user ID and password from env.

3. **Submit OTP**
   - Once Zerodha sends an OTP, the app moves into `WAITING_FOR_OTP`.
   - Enter the OTP in the dashboard and submit.
   - Backend calls `submit_otp(...)` in `scraper.py` to complete login and transitions to scraping.

4. **Live ROC updates**
   - App waits until Indian market open (`09:15–15:30` IST, configured in `config.py`).
   - It fetches initial data from Sensibull, builds a reference frame (`t0`), and then:
     - Polls the option chain at `SCRAPING_INTERVAL_SECONDS`.
     - Computes ROC vs reference using `calculate_roc(...)`.
     - Pushes:
       - Reference data via `/api/reference`.
       - Incremental ROC rows via `/api/roc`.
   - Frontend updates tables and stats without full page refresh.

5. **Stop / reset**
   - **Stop** button calls `/api/stop`, sets `should_stop = True`, joins the thread, cleans up the browser and virtual display, and resets state.
   - **Force reset** (via `/api/reset`) is available if things get stuck.

---

## Key configuration

All in `config.py`:

- **Trading hours** (IST):
  - `TRADING_START_HOUR`, `TRADING_START_MINUTE`
  - `TRADING_END_HOUR`, `TRADING_END_MINUTE`
- **Scraping cadence**:
  - `INITIAL_WAIT_SECONDS` – delay after initial fetch before first ROC.
  - `SCRAPING_INTERVAL_SECONDS` – seconds between scrapes.
- **Strike selection**:
  - `STRIKE_RANGE` – number of strikes up/down around ATM.
  - `STRIKE_INTERVAL` – strike step (e.g. 100).
- **Market / symbol**:
  - `SENSIBULL_URL`
  - `NIFTY_TICKER` (used with `yfinance` to get futures).
- **ChromeDriver**:
  - `CHROMEDRIVER_PATH`

---

## API surface

The dashboard uses these endpoints; they’re also usable programmatically:

- `GET /`
  - Renders `dashboard.html`.

- `POST /api/start`
  - Body: JSON with:
    - `ticker` (default `"NIFTY"`).
    - `expiry_date` (`YYYY-MM-DD`, required).
  - Starts background scraping if state is `IDLE`, `ERROR`, or `STOPPED`.

- `POST /api/stop`
  - Stops scraping when state is `LOGGING_IN`, `WAITING_FOR_OTP`, `OTP_SUBMITTED`, or `SCRAPING`.

- `POST /api/reset`
  - Hard reset: stops thread (if any), forces cleanup, resets `AppState`.

- `POST /api/submit_otp`
  - Body: JSON with `otp` (required).
  - Only valid while state is `WAITING_FOR_OTP`.

- `GET /api/status`
  - Returns current state, last update, last logs, and any error message.

- `GET /api/roc`
  - Returns list of ROC rows as JSON, newest-first.

- `GET /api/reference`
  - Returns initial snapshot (t0) with renamed columns.

- `GET /api/highest_oi`
  - Returns `{ strike, type, oi_value }` for the highest OI among calls/puts using the latest frame.

---

## Deployment notes (Linux / server)

For production you typically:

- Run under a process manager (e.g. `supervisord`, `systemd`) with:
  - The virtualenv Python.
  - `DISPLAY=":99"` (or similar) for `pyvirtualdisplay`.
- Front it with Nginx or another reverse proxy.
