
import os
import requests
import smtplib
from email.mime.text import MIMEText
import json

# --- Configuration ---
# The URL to fetch the JSON data from
EUROSTAR_URL = "https://snap.eurostar.com/_next/data/bmR4ZJH0w6ti5FN6-tty8/uk-en/search.json?adult=1&origin=7015400&destination=8722326&outbound=2025-10-22&outslot=13%3A00"

# Email configuration from environment variables
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
MY_EMAIL = os.environ.get("EMAIL_ADDRESS")
RECIPIENT_EMAILS = [MY_EMAIL] # Add more recipients here if needed

# --- Email Sending Function (adapted from your example) ---
def send_notification_email(subject, body, sender_email=MY_EMAIL, receiver_emails=RECIPIENT_EMAILS, sender_password=GMAIL_APP_PASSWORD):
    """Sends an email using Gmail's SMTP server."""
    if not sender_email or not sender_password:
        print("Error: Email credentials (EMAIL_ADDRESS, GMAIL_APP_PASSWORD) are not set as environment variables.")
        exit(1)

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = ', '.join(receiver_emails)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(sender_email, sender_password)
            smtp_server.sendmail(sender_email, receiver_emails, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")
        exit(1)

# --- Main Logic ---
def check_for_tickets():
    """Fetches Eurostar data, checks for available tickets, and sends an email if any are found."""
    print("Checking for available Eurostar Snap tickets...")
    try:
        response = requests.get(EUROSTAR_URL)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Eurostar URL: {e}")
        exit(1)

    try:
        data = response.json()
        time_slots = data.get("pageProps", {}).get("outboundTimeSlots", [])
    except (json.JSONDecodeError, AttributeError):
        print("Error: Could not parse JSON data or find the expected structure.")
        exit(1)

    if not time_slots:
        print("No time slots found in the response.")
        return

    available_slots = [slot for slot in time_slots if slot.get("fare") is not None]

    if available_slots:
        print(f"Success! Found {len(available_slots)} available time slot(s).")
        
        # Format email body
        body_lines = ["Available Eurostar Snap tickets found for London to Lille on 2025-10-22:"]
        for slot in available_slots:
            window = slot.get("departureWindow", {})
            earliest = window.get('earliest', 'N/A').split(' ')[1] # Get time part
            latest = window.get('latest', 'N/A').split(' ')[1]
            
            fare_info = slot.get("fare", {})
            price = fare_info.get("prices", {}).get("displayPrice", "N/A")
            
            body_lines.append(f"  - Window: {earliest} - {latest}, Price: £{price}")

        email_body = "\n".join(body_lines)
        email_subject = f"Eurostar Snap Tickets Available for 22/10!"
        
        send_notification_email(email_subject, email_body)
    else:
        print("No available tickets found at this time.")

if __name__ == "__main__":
    check_for_tickets()
