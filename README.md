# Bulk Mailer

A localhost web app for sending personalized bulk emails. Upload a CSV with recipients, compose an HTML email with `{{placeholders}}`, attach files, and send to everyone at once.

## Project Structure

```
bulk-mailer/
├── app.py               # Flask routes (web server)
├── mailer.py            # Email sending logic (MIME, SMTP)
├── config.py            # SMTP config loaded from .env
├── templates/
│   └── index.html       # Full UI (HTML + CSS + JavaScript)
├── uploads/             # Temp folder for CSVs and attachments
├── uploads/qr/          # Per-person QR/file attachments
├── .env                 # Your credentials (not committed)
├── .env.example         # Template for .env
├── .gitignore
├── requirements.txt
├── start.bat            # One-click start for Windows
├── start.sh             # One-click start for macOS/Linux
└── README.md            # This file
```

## Quick Start (with start scripts)

**Windows:** Double-click `start.bat` — it creates venv, installs deps, and runs the app.

**macOS/Linux:** Run `chmod +x start.sh && ./start.sh`

Then open **http://localhost:5000** in your browser.

> **Prerequisite:** Python 3.8+ must be installed. Download from https://python.org

## Step-by-Step Setup

### 1. Create and Activate Virtual Environment

A virtual environment (venv) is an isolated Python environment so your project's packages don't conflict with other projects.

**Windows (PowerShell):**

```powershell
# Navigate to the project folder
cd bulk-mailer

# Create the virtual environment (only once)
python -m venv venv

# Activate it (every time you work on the project)
.\venv\Scripts\Activate.ps1

# If you get an execution policy error, run this first:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Windows (CMD):**

```cmd
cd bulk-mailer
python -m venv venv
.\venv\Scripts\activate.bat
```

**macOS / Linux:**

```bash
cd bulk-mailer
python3 -m venv venv
source venv/bin/activate
```

You'll see `(venv)` in your terminal prompt when the virtual environment is active.

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# Copy the example file to create your .env
cp .env.example .env      # macOS/Linux
copy .env.example .env    # Windows
```

Open `.env` in a text editor and configure your SMTP provider.

### 4. Choose Your SMTP Provider

#### Option A: Mailpit (Local Testing — Recommended to Start)

Mailpit is a fake email server that runs on your machine. It catches all outgoing emails so you can test without sending real emails.

**Install Mailpit:**

- **Windows:** Download from [mailpit releases](https://github.com/axllent/mailpit/releases), extract `mailpit.exe` to a folder, and run it.
- **macOS:** `brew install mailpit`
- **Linux:** `docker run -d -p 1025:1025 -p 8025:8025 axllent/mailpit`

**Run Mailpit:**

```bash
mailpit
```

Mailpit will start two servers:
- `localhost:1025` — SMTP server (where your app sends emails)
- `localhost:8025` — Web UI (view sent emails in your browser)

**Set in .env:**

```
SMTP_PROVIDER=mailpit
```

#### Option B: Gmail (Real Emails)

Gmail requires an "App Password" instead of your regular password.

**Steps to get a Gmail App Password:**

1. Go to your Google Account: https://myaccount.google.com
2. Click **Security** in the left sidebar
3. Enable **2-Step Verification** (if not already enabled)
4. Go to **App Passwords**: https://myaccount.google.com/apppasswords
5. Select app: **Mail**, select device: **Other** (type "Bulk Mailer")
6. Click **Generate** — you'll get a 16-character password like `abcd efgh ijkl mnop`
7. Copy this password (remove spaces) and put it in `.env`

**Set in .env:**

```
SMTP_PROVIDER=gmail
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=abcdefghijklmnop
```

### 5. Run the App

```bash
python app.py
```

Open your browser and go to: **http://localhost:5000**

### 6. Deactivate Virtual Environment (When Done)

```bash
deactivate
```

## How to Use

1. **Compose your email** — Write a subject and HTML body using `{{column_name}}` placeholders
2. **Upload a CSV** — The app reads the headers and shows clickable chips for each column
3. **Click chips** to insert placeholders at the cursor position in the body
4. **Upload attachments** (optional) — Files that get attached to every email
5. **Per-person attachments** — If your CSV has a `qr_file` column, put the files in `uploads/qr/` and the app attaches each person's file automatically
6. **Click Send** — Watch the results table update in real time

## CSV Format Example

```csv
name,email,team,qr_file
Alice,alice@example.com,Engineering,alice_qr.png
Bob,bob@example.com,Marketing,bob_qr.png
Charlie,charlie@example.com,Design,
```

- The `email` column is required (used as recipient address)
- All other columns are optional and become `{{placeholders}}`
- The `qr_file` column is special — it auto-attaches a file from `uploads/qr/`

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'flask'` | Run `pip install -r requirements.txt` with venv activated |
| Mailpit emails not appearing | Make sure Mailpit is running and check `http://localhost:8025` |
| Gmail "Authentication failed" | You need an App Password, not your regular password. See Step 4B |
| `python` command not found | Try `python3` instead, or add Python to your PATH |
| Port 5000 already in use | Change the port in `app.py` at the bottom: `app.run(port=5001)` |
