# =============================================================================
# config.py — Loads SMTP configuration from the .env file
# =============================================================================
# This file reads the .env file and provides SMTP settings to the rest of the
# app. It decides which SMTP provider to use (Mailpit or Gmail) based on the
# SMTP_PROVIDER variable in .env.
# =============================================================================

import os

# python-dotenv lets us load variables from a .env file into os.environ.
# Think of it as a way to keep secrets out of your code.
from dotenv import load_dotenv

# Load all variables from the .env file into the environment.
# This must be called before we try to read any env vars.
load_dotenv()


def get_smtp_config():
    """
    Reads SMTP settings from environment variables and returns a dictionary
    with everything the mailer needs to connect to an SMTP server.

    Returns:
        dict: A dictionary with keys:
            - host       (str): The SMTP server hostname
            - port       (int): The SMTP server port
            - use_tls    (bool): Whether to use STARTTLS encryption
            - username   (str or None): Login username (None if no auth)
            - password   (str or None): Login password (None if no auth)
            - sender_name (str): The display name for the "From" field
    """

    # Read which provider the user wants to use (default: mailpit)
    provider = os.getenv("SMTP_PROVIDER", "mailpit").lower()

    # Common setting: the sender's display name
    sender_name = os.getenv("SENDER_NAME", "Bulk Mailer")

    if provider == "gmail":
        # --- Gmail SMTP settings ---
        # Gmail requires authentication and TLS encryption.
        return {
            "host": os.getenv("GMAIL_HOST", "smtp.gmail.com"),
            "port": int(os.getenv("GMAIL_PORT", 587)),
            "use_tls": True,           # Gmail requires STARTTLS
            "username": os.getenv("GMAIL_USER"),
            "password": os.getenv("GMAIL_APP_PASSWORD"),  # App Password, not regular password
            "sender_name": sender_name,
        }
    else:
        # --- Mailpit settings (default for local testing) ---
        # Mailpit runs locally with no authentication needed.
        return {
            "host": os.getenv("MAILPIT_HOST", "localhost"),
            "port": int(os.getenv("MAILPIT_PORT", 1025)),
            "use_tls": False,          # Mailpit doesn't need TLS
            "username": None,          # No login required
            "password": None,          # No password required
            "sender_name": sender_name,
        }
