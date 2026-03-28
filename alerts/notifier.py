import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def send_drift_alert(anomaly_score: float, anomaly_count: int, total_records: int):
    """
    Sends email alert when data drift is detected.
    Uses Gmail SMTP - requires App Password.
    """
    sender = os.environ.get('ALERT_EMAIL')
    password = os.environ.get('ALERT_EMAIL_PASSWORD')
    recipient = os.environ.get('ALERT_EMAIL')

    if not sender or not password:
        print(f"[ALERT] DATA DRIFT DETECTED at {datetime.now()}")
        print(f"[ALERT] Anomaly Score: {anomaly_score:.4f}")
        print(f"[ALERT] Anomalies: {anomaly_count}/{total_records} records")
        return

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = f"🚨 FRAUD PIPELINE ALERT: Data Drift Detected"

    body = f"""
    Data Drift Detected in Self-Healing Fraud Pipeline
    
    Timestamp: {datetime.now()}
    Anomaly Score: {anomaly_score:.4f}
    Anomalous Records: {anomaly_count} / {total_records}
    
    ACTION: Pipeline has been automatically halted.
    Please investigate the incoming data source.
    """

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())
        server.quit()
        print(f"[ALERT] Email sent successfully")
    except Exception as e:
        print(f"[ALERT] Email failed, logging alert: {e}")
        print(f"[ALERT] DATA DRIFT DETECTED - Score: {anomaly_score:.4f}, Anomalies: {anomaly_count}/{total_records}")