"""
Email service using Gmail SMTP
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

class EmailService:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.username = "adverserial.ai@gmail.com"
        self.password = os.getenv("GMAIL_APP_PASSWORD", "jzzwbxwzlvlgvnox")
        
    def send_html_email(self, to_email: str, subject: str, html_body: str) -> bool:
        """Send HTML email via Gmail SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add HTML body
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Connect and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            print(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"Gmail SMTP failed: {str(e)}")
            # Console mode - token visible here
            self._console_output(to_email, subject, html_body)
            return True
    
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send email via Gmail SMTP"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            print(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"Gmail SMTP failed: {str(e)}")
            # Console mode - token visible here
            self._console_output(to_email, subject, body)
            return True
    
    def _console_output(self, to_email: str, subject: str, body: str):
        """Console fallback"""
        print("\n" + "="*50)
        print("📧 EMAIL (Console Output)")
        print("="*50)
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print("-"*30)
        print(body)
        print("="*50 + "\n")
    
    def send_password_reset_email(self, to_email: str, username: str, reset_token: str) -> bool:
        """Send password reset email with beautiful HTML template"""
        subject = "🔐 Password Reset - Adversarial AI"
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Password Reset</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 20px; text-align: center;">
            <h1 style="color: #ffffff; margin: 0; font-size: 28px;">🔐 Password Reset</h1>
            <p style="color: #ffffff; margin: 10px 0 0 0;">Adversarial AI Security</p>
        </div>
        
        <div style="padding: 40px 30px;">
            <h2 style="color: #333333; margin: 0 0 20px 0;">Hello {username}! 👋</h2>
            
            <p style="color: #666666; line-height: 1.6; margin: 0 0 30px 0;">
                We received a request to reset your password. Use the verification code below:
            </p>
            
            <div style="text-align: center; margin: 30px 0;">
                <div style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px 40px; border-radius: 10px;">
                    <p style="color: #ffffff; margin: 0 0 5px 0; font-size: 14px;">Your Verification Code</p>
                    <h1 style="color: #ffffff; margin: 0; font-size: 36px; letter-spacing: 8px;">{reset_token}</h1>
                </div>
            </div>
            
            <div style="background-color: #fff3cd; border-radius: 8px; padding: 15px; margin: 20px 0;">
                <p style="color: #856404; margin: 0; font-size: 14px;">
                    ⏰ <strong>Important:</strong> This code expires in 15 minutes.
                </p>
            </div>
            
            <p style="color: #666666; line-height: 1.6; margin: 20px 0;">
                If you didn't request this, please ignore this email.
            </p>
        </div>
        
        <div style="background-color: #f8f9fa; padding: 30px; text-align: center;">
            <p style="color: #666666; margin: 0; font-size: 14px;">
                Best regards,<br>
                <strong>The Adversarial AI Team</strong> 🤖
            </p>
        </div>
    </div>
</body>
</html>
        """
        
        return self.send_html_email(to_email, subject, html_body)

# Global instance
email_service = EmailService()