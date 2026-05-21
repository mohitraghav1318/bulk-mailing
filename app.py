# =============================================================================
# app.py — Flask web application (routes and request handling)
# =============================================================================
# This is the main entry point of the app. It defines:
#   - GET  "/"        → Show the dashboard page
#   - POST "/upload"  → Upload a CSV file and return its column headers
#   - POST "/send"    → Send personalized emails to everyone in the CSV
#
# Flask is a lightweight web framework. Routes are like doors — when a user
# visits a URL, Flask looks for a matching route and runs the function.
# =============================================================================

import os
import csv
import uuid
from flask import (
    Flask,          # The main Flask class — creates the web app
    render_template,# Renders an HTML file using Jinja2 templates
    request,        # Lets us access form data, files, etc. from the user
    jsonify,        # Converts Python dicts/lists to JSON for API responses
)

from config import get_smtp_config
from mailer import build_email_message, send_single_email


# --- Create the Flask app ---
# __name__ tells Flask where to look for templates and static files.
app = Flask(__name__)

# --- Define folder paths ---
# BASE_DIR is the folder where app.py lives.
BASE_DIR = os.path.dirname(os.path.abspath(__file__

# UPLOAD_FOLDER is where we store uploaded CSV files and attachments temporarily.
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)       # Create if it doesn't exist
os.makedirs(os.path.join(UPLOAD_FOLDER, "qr"), exist_ok=True)  # For per-person QR files


# =============================================================================
# ROUTE: Home page
# =============================================================================
# When someone visits http://localhost:5000/, this function runs.
# It renders the index.html template and sends it to the browser.
# =============================================================================
@app.route("/")
def index():
    """
    Renders the main dashboard page.
    This is a GET request — the browser just wants to see the page.
    """
    return render_template("index.html")


# =============================================================================
# ROUTE: Upload CSV and detect columns
# =============================================================================
# When the user selects a CSV file and clicks "Upload", the browser sends
# a POST request here with the file attached.
# We read the CSV headers and return them as JSON so the frontend can
# display them as clickable placeholder chips.
# =============================================================================
@app.route("/upload", methods=["POST"])
def upload_csv():
    """
    Handles CSV file upload.

    Steps:
    1. Get the uploaded file from the request
    2. Save it to the uploads folder
    3. Read the first row (headers) using Python's csv module
    4. Return the column names as JSON

    Returns:
        JSON: {"columns": ["name", "email", "team", ...]} or an error message
    """

    # Check if a file was actually uploaded
    # request.files is a dictionary of all uploaded files in this request.
    if "csv_file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    csv_file = request.files["csv_file"]

    # Check if the user selected a file (filename is empty if they didn't)
    if csv_file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # --- Save the uploaded file ---
    # We generate a unique filename using uuid (a random unique ID) to avoid
    # conflicts if two people upload files with the same name.
    unique_filename = f"{uuid.uuid4().hex}_{csv_file.filename}"
    saved_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    csv_file.save(saved_path)

    # --- Read the CSV headers ---
    # csv.DictReader reads a CSV file and treats the first row as column names.
    # Each subsequent row becomes a dictionary where keys = column names.
    with open(saved_path, "r", newline="", encoding="utf-8") as file_handle:
        # DictReader automatically uses the first row as headers
        csv_reader = csv.DictReader(file_handle)

        # fieldnames is a list of column names from the header row
        # e.g., ["name", "email", "team", "qr_file"]
        columns = csv_reader.fieldnames or []

    # Return the column names and saved filename to the frontend
    # jsonify() converts a Python dict to a JSON response the browser can read.
    return jsonify({
        "columns": columns,
        "filename": unique_filename,  # We need this later to re-read the file when sending
    })


# =============================================================================
# ROUTE: Upload static attachments
# =============================================================================
# The user can upload PDFs, images, or documents that get attached to
# every email (same file for all recipients).
# =============================================================================
@app.route("/upload-attachments", methods=["POST"])
def upload_attachments():
    """
    Handles uploading static attachment files.
    These files will be attached to every outgoing email.

    Returns:
        JSON: {"attachments": ["file1.pdf", "file2.png"]} or an error
    """

    # request.files.getlist() gets all files uploaded under the same field name.
    # This allows the user to select multiple files at once.
    files = request.files.getlist("attachments")

    if not files or all(f.filename == "" for f in files):
        return jsonify({"error": "No files selected"}), 400

    saved_filenames = []

    for file in files:
        if file.filename and file.filename != "":
            # Save each file with a unique prefix to avoid name conflicts
            unique_name = f"{uuid.uuid4().hex}_{file.filename}"
            file.save(os.path.join(UPLOAD_FOLDER, unique_name))
            saved_filenames.append(unique_name)

    return jsonify({"attachments": saved_filenames})


# =============================================================================
# ROUTE: Send bulk emails
# =============================================================================
# This is the main route — it reads the CSV, personalizes each email,
# and sends them one by one. It returns a results table showing which
# emails succeeded and which failed.
# =============================================================================
@app.route("/send", methods=["POST"])
def send_emails():
    """
    Sends personalized bulk emails to every person in the uploaded CSV.

    Steps:
    1. Get form data (subject, body, CSV filename, attachment filenames)
    2. Re-read the CSV file and iterate over each row
    3. For each row: replace placeholders, build the email, send it
    4. Collect results (success/failure for each recipient)
    5. Return results as JSON

    Returns:
        JSON: {"results": [{"email": "...", "status": "sent"}, ...]}
    """

    # --- Step 1: Get form data ---
    # request.form is a dictionary of text fields submitted in the form.
    subject = request.form.get("subject", "")
    body = request.form.get("body", "")
    csv_filename = request.form.get("csv_filename", "")

    # request.form.getlist() gets all values for a field that has multiple values
    # (like a list of attachment filenames).
    attachment_filenames = request.form.getlist("attachments")

    # Validate: we need at least a subject and a CSV file
    if not csv_filename:
        return jsonify({"error": "No CSV file uploaded yet"}), 400

    csv_path = os.path.join(UPLOAD_FOLDER, csv_filename)
    if not os.path.isfile(csv_path):
        return jsonify({"error": "CSV file not found"}), 400

    # --- Step 2: Get SMTP configuration ---
    smtp_config = get_smtp_config()

    # The sender's email address depends on which provider we're using.
    # For Mailpit, any address works since it's local testing.
    # For Gmail, it must match the authenticated Gmail account.
    sender_email = smtp_config["username"] or "noreply@localhost"

    # --- Step 3: Read CSV and send emails ---
    results = []

    # Open the CSV and read it row by row
    with open(csv_path, "r", newline="", encoding="utf-8") as file_handle:
        csv_reader = csv.DictReader(file_handle)

        for row in csv_reader:
            # Each 'row' is a dictionary like {"name": "Alice", "email": "alice@example.com"}

            # Get the recipient's email address from the row
            # We look for a column named "email" (case-insensitive).
            recipient_email = None
            for key, value in row.items():
                if key.lower() == "email" and value:
                    recipient_email = value.strip()
                    break

            # If there's no email in this row, skip it and record the failure
            if not recipient_email:
                results.append({
                    "email": "(no email found)",
                    "status": "failed",
                    "reason": "No 'email' column or empty email in this row",
                })
                continue

            # --- Build the personalized email ---
            email_message = build_email_message(
                sender_name=smtp_config["sender_name"],
                sender_email=sender_email,
                recipient_email=recipient_email,
                subject=subject,
                html_body=body,
                static_attachments=attachment_filenames,
                row_data=row,
                uploads_folder=UPLOAD_FOLDER,
            )

            # --- Send the email ---
            success, error_message = send_single_email(
                smtp_config, email_message, recipient_email
            )

            # --- Record the result ---
            if success:
                results.append({
                    "email": recipient_email,
                    "status": "sent",
                    "reason": None,
                })
            else:
                results.append({
                    "email": recipient_email,
                    "status": "failed",
                    "reason": error_message,
                })

    # Return all results as JSON so the frontend can display them in a table
    return jsonify({"results": results})


# =============================================================================
# START THE APP
# =============================================================================
# This block runs only when you execute "python app.py" directly.
# It starts the Flask development server on http://localhost:5000.
# =============================================================================
if __name__ == "__main__":
    # debug=True means the server auto-reloads when you save code changes,
    # and shows detailed error pages in the browser.
    # host="0.0.0.0" makes the server accessible from other devices on your network.
    app.run(debug=True, host="0.0.0.0", port=5000)
