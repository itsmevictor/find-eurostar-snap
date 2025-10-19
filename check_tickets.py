import os
import requests
import smtplib
from email.mime.text import MIMEText
import json

# --- Configuration ---
# Base URL for the Eurostar Snap API. The destination code will be inserted into this.
BASE_URL = "https://snap.eurostar.com/_next/data/bmR4ZJH0w6ti5FN6-tty8/uk-en/search.json?adult=1&origin=7015400&outbound=2025-10-22&outslot=13%3A00&destination={destination_code}"

DESTINATIONS = {
    "Lille": "8722326",
    "Brussels": "8814001",
    "Amsterdam": "8400058"
}

# Email configuration from environment variables
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
MY_EMAIL = os.environ.get("EMAIL_ADDRESS")
RECIPIENT_EMAILS = [MY_EMAIL] # Add more recipients here if needed

# --- Email Sending Function ---
def send_notification_email(subject, body, sender_email=MY_EMAIL, receiver_emails=RECIPIENT_EMAILS, sender_password=GMAIL_APP_PASSWORD):
    """Sends an email using Gmail's SMTP server."""
    if not sender_email or not sender_password:
        print("Error: Email credentials (EMAIL_ADDRESS, GMAIL_APP_PASSWORD) are not set as environment variables.")
        # In a real scenario, you might want to handle this more gracefully than exiting,
        # but for a simple script, this is clear.
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
def check_all_destinations():
    """Checks all configured destinations for available tickets and sends one summary email."""
    print("Starting Eurostar Snap ticket check for all destinations...")
    all_available_tickets_info = []

    for city, code in DESTINATIONS.items():
        print(f"-- Checking for tickets to {city}...")
        url = BASE_URL.format(destination_code=code)
        
        try:
            response = requests.get(url)
            response.raise_for_status()  # Check for HTTP errors
            data = response.json()
            time_slots = data.get("pageProps", {}).get("outboundTimeSlots", [])

            if not time_slots:
                print(f"   No time slots found in the response for {city}.")
                continue

            # Find slots that have a fare
            available_slots = [slot for slot in time_slots if slot.get("fare") is not None]

            if available_slots:
                info_line = f"Found {len(available_slots)} available slot(s) for London to {city}:"
                print(f"   {info_line}")
                all_available_tickets_info.append(info_line)
                for slot in available_slots:
                    window = slot.get("departureWindow", {})
                    earliest = window.get('earliest', 'N/A').split(' ')[1]
                    latest = window.get('latest', 'N/A').split(' ')[1]
                    price = slot.get("fare", {}).get("prices", {}).get("displayPrice", "N/A")
                    slot_info = f"  - Window: {earliest} - {latest}, Price: £{price}"
                    print(f"     {slot_info}")
                    all_available_tickets_info.append(slot_info)
            else:
                print(f"   No available tickets found for {city}.")

        except requests.exceptions.RequestException as e:
            print(f"   Error fetching data for {city}: {e}")
        except (json.JSONDecodeError, AttributeError):
            print(f"   Error parsing data for {city}.")

    # After checking all destinations, send one email if any tickets were found
    if all_available_tickets_info:
        print("\nTickets found! Preparing summary email...")
        email_subject = "Eurostar Snap Tickets Available!"
        email_body = "\n".join(all_available_tickets_info)
        send_notification_email(email_subject, email_body)
    else:
        print("\nFinished check. No available tickets found for any destination.")

if __name__ == "__main__":
    check_all_destinations()