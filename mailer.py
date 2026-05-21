# =============================================================================
# mailer.py — All email sending logic lives here
# =============================================================================
# This file handles:
#   1. Replacing {{placeholders}} in subject and body with real data from CSV
#   2. Building a MIME email message (the format email servers understand)
#   3. Attaching files (both per-person and static attachments)
#   4. Connecting to an SMTP server and sending the email
#
# "MIME" stands for Multipurpose Internet Mail Extensions — it's the standard
# format for email messages that can contain text, HTML, and file attachments.
# =============================================================================

import re
import smtplib
from email.mime.multipart import MIMEMultipart   # For messages with multiple parts (HTML + attachments)
from email.mime.text import MIMEText             # For the HTML body
from email.mime.base import MIMEBase             # For file attachments
from email import encoders                       # To encode attachments in base64
import os


def replace_placeholders(template_string, row_data):
    """
    Replaces all {{column_name}} placeholders in a string with actual values
    from a CSV row.

    Example:
        template_string = "Hell
        row_data = {"name": "Alice", "team": "Engineering"}
        Result: "Hello Alice, welcome to Engineering!"

    If a placeholder doesn't exist in row_data, it's left as-is.
    For example, if the template has {{phone}} but the CSV has no "phone" column,
    the output will still contain {{phone}}.

    Args:
        template_string (str): The text containing {{placeholder}} patterns
        row_data (dict): A dictionary mapping column names to values

    Returns:
        str: The string with placeholders replaced by real values
    """
    # re.sub replaces text using a pattern (regex).
    # r'\{\{(\w+)\}\}' matches {{word}} and captures "word" inside group 1.
    # \w+ means "one or more word characters (letters, digits, underscore)".
    def replacer(match):
        # match.group(1) gets the text captured by (\w+), e.g., "name"
        key = match.group(1)
        # Return the value from row_data if it exists, otherwise keep the original {{key}}
        if key in row_data and row_data[key] is not None:
            return str(row_data[key])
        # If the key isn't in the row data, return the placeholder as-is
        return match.group(0)  # match.group(0) is the full match, e.g., "{{name}}"

    return re.sub(r'\{\{(\w+)\}\}', replacer, template_string)


def build_email_message(sender_name, sender_email, recipient_email,
                        subject, html_body, static_attachments, row_data,
                        uploads_folder):
    """
    Builds a complete MIME email message with HTML body and file attachments.

    A MIME message is like an envelope that can contain:
      - A text part (the HTML email body)
      - Zero or more file attachments (PDFs, images, etc.)

    Args:
        sender_name (str): Display name for the "From" field
        sender_email (str): The email address sending the mail
        recipient_email (str): The email address receiving the mail
        subject (str): Email subject (may contain {{placeholders}})
        html_body (str): Email body in HTML (may contain {{placeholders}})
        static_attachments (list): List of filenames to attach to every email
        row_data (dict): The CSV row data for this recipient (for placeholders)
        uploads_folder (str): Path to the uploads directory

    Returns:
        MIMEMultipart: The complete email message ready to send
    """

    # --- Step 1: Replace placeholders in subject and body ---
    personalized_subject = replace_placeholders(subject, row_data)
    personalized_body = replace_placeholders(html_body, row_data)

    # --- Step 2: Create the MIME message ---
    # MIMEMultipart() creates a message that can hold multiple parts.
    # "alternative" means the parts are different versions of the same content.
    message = MIMEMultipart()

    # Set email headers (the metadata that email clients display)
    message["From"] = f"{sender_name} <{sender_email}>"   # Who sent it
    message["To"] = recipient_email                         # Who receives it
    message["Subject"] = personalized_subject               # Email subject line

    # --- Step 3: Attach the HTML body ---
    # MIMEText creates a text part. We specify "html" so the email client
    # renders it as a web page instead of plain text.
    html_part = MIMEText(personalized_body, "html")
    message.attach(html_part)

    # --- Step 4: Attach static files (same for every recipient) ---
    for filename in static_attachments:
        filepath = os.path.join(uploads_folder, filename)
        if os.path.isfile(filepath):
            _attach_file(message, filepath)

    # --- Step 5: Attach per-person file (e.g., a QR code specific to this person) ---
    # If the CSV has a "qr_file" column, attach that file for this recipient.
    if "qr_file" in row_data and row_data["qr_file"]:
        qr_filename = row_data["qr_file"]
        qr_path = os.path.join(uploads_folder, "qr", qr_filename)
        if os.path.isfile(qr_path):
            _attach_file(message, qr_path)

    return message


def _attach_file(message, filepath):
    """
    Helper function: Attaches a file to a MIME message.

    This reads the file from disk, encodes it, and adds it as an attachment.
    "base64" encoding is a way to represent binary data (like PDFs or images)
    as text so it can travel through email protocols.

    Args:
        message (MIMEMultipart): The email message to add the attachment to
        filepath (str): Full path to the file on disk
    """
    # Open the file in binary mode ("rb") — binary because it could be
    # a PDF, image, or any non-text file.
    with open(filepath, "rb") as file_handle:
        # MIMEBase creates a generic attachment part.
        # "application" and "octet-stream" is a catch-all MIME type for
        # any binary file (it tells the email client "this is a file, figure out the type").
        attachment_part = MIMEBase("application", "octet-stream")
        attachment_part.set_payload(file_handle.read())

    # Encode the file data in base64 so it can be sent over email safely.
    encoders.encode_base64(attachment_part)

    # Get just the filename (not the full path) for the attachment header.
    filename = os.path.basename(filepath)

    # Add a header that tells the email client: "this is a file attachment
    # called 'filename'". Without this, the email client won't know to
    # show a download link for the file.
    attachment_part.add_header(
        "Content-Disposition",
        f"attachment; filename={filename}"
    )

    # Add the attachment to the message
    message.attach(attachment_part)


def send_single_email(smtp_config, message, recipient_email):
    """
    Connects to the SMTP server and sends one email.

    SMTP (Simple Mail Transfer Protocol) is the standard protocol for
    sending emails. Think of it as the "language" that email servers speak.

    STARTTLS is a command that upgrades an existing plain-text connection
    to an encrypted one — like putting a lock on a conversation that
    already started.

    Args:
        smtp_config (dict): SMTP connection settings from config.py
        message (MIMEMultipart): The email message to send
        recipient_email (str): The recipient's email address

    Returns:
        tuple: (success: bool, error_message: str or None)
    """

    try:
        # --- Step 1: Connect to the SMTP server ---
        # smtplib.SMTP() creates a connection to the mail server.
        # It's like opening a phone line to the post office.
        smtp_connection = smtplib.SMTP(smtp_config["host"], smtp_config["port"])

        # Enable debug output (optional — shows the SMTP conversation in terminal)
        # smtp_connection.set_debuglevel(1)

        # --- Step 2: Start TLS encryption if needed ---
        # starttls() upgrades the connection from plain text to encrypted.
        # This is required for Gmail and any server that cares about security.
        if smtp_config["use_tls"]:
            smtp_connection.starttls()

        # --- Step 3: Log in (if credentials are provided) ---
        # Mailpit doesn't need login, but Gmail does.
        if smtp_config["username"] and smtp_config["password"]:
            smtp_connection.login(smtp_config["username"], smtp_config["password"])

        # --- Step 4: Send the email ---
        # sendmail() takes the sender, recipient, and the full message as a string.
        # message.as_string() converts our MIME object into the raw email format.
        smtp_connection.sendmail(
            smtp_config["username"] or "noreply@localhost",  # Sender address
            recipient_email,                                  # Recipient address
            message.as_string()                               # The full email content
        )

        # --- Step 5: Close the connection ---
        # Always quit when done — it's polite and frees up resources.
        smtp_connection.quit()

        return (True, None)  # Success, no error

    except Exception as error:
        # If anything goes wrong (wrong password, network issue, etc.),
        # we catch the error and return it as a string.
        return (False, str(error))
