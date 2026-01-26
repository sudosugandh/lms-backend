from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import logging
from app.db.models.cms import WebsiteSettings

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending emails with per-institute SMTP configuration."""
    
    @staticmethod
    def get_email_config(db: Session, institute_id: int) -> Optional[Dict[str, Any]]:
        """Get email configuration for an institute from WebsiteSettings."""
        settings = db.query(WebsiteSettings).filter(
            WebsiteSettings.institute_id == institute_id
        ).first()
        
        if not settings:
            return None
        
        # Check if custom SMTP is configured
        smtp_config = {}
        if hasattr(settings, 'smtp_host') and settings.smtp_host:
            smtp_config = {
                'host': settings.smtp_host,
                'port': getattr(settings, 'smtp_port', 587),
                'username': getattr(settings, 'smtp_username', None),
                'password': getattr(settings, 'smtp_password', None),
                'use_tls': getattr(settings, 'smtp_use_tls', True),
                'from_email': getattr(settings, 'smtp_from_email', settings.contact_email),
                'from_name': getattr(settings, 'smtp_from_name', settings.site_name or 'LMS'),
            }
        
        return {
            'contact_email': settings.contact_email,
            'site_name': settings.site_name,
            'smtp_config': smtp_config if smtp_config else None,
        }
    
    @staticmethod
    def send_email(
        db: Session,
        institute_id: int,
        to_email: str,
        subject: str,
        body_html: Optional[str] = None,
        body_text: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> bool:
        """
        Send an email using institute-specific SMTP configuration.
        
        Args:
            db: Database session
            institute_id: Institute ID
            to_email: Recipient email address
            subject: Email subject
            body_html: HTML body (optional)
            body_text: Plain text body (optional, required if body_html not provided)
            reply_to: Reply-to email address (optional)
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            email_config = EmailService.get_email_config(db, institute_id)
            
            if not email_config or not email_config.get('contact_email'):
                logger.error(f"No email configuration found for institute {institute_id}")
                return False
            
            contact_email = email_config['contact_email']
            site_name = email_config.get('site_name', 'LMS')
            smtp_config = email_config.get('smtp_config')
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['To'] = to_email
            msg['From'] = formataddr((site_name, contact_email))
            
            if reply_to:
                msg['Reply-To'] = reply_to
            
            # Add body
            if body_html:
                msg.attach(MIMEText(body_html, 'html'))
            if body_text:
                msg.attach(MIMEText(body_text, 'plain'))
            elif not body_html:
                # If neither provided, use plain text
                msg.attach(MIMEText(body_text or '', 'plain'))
            
            # Send email
            if smtp_config:
                # Use custom SMTP configuration
                EmailService._send_via_smtp(msg, smtp_config, contact_email, to_email)
            else:
                # Use default system SMTP (if configured in environment)
                # For now, log and return False - institutes should configure SMTP
                logger.warning(f"No SMTP configuration for institute {institute_id}. Email not sent.")
                return False
            
            logger.info(f"Email sent successfully to {to_email} for institute {institute_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}", exc_info=True)
            return False
    
    @staticmethod
    def _send_via_smtp(
        msg: MIMEMultipart,
        smtp_config: Dict[str, Any],
        from_email: str,
        to_email: str
    ):
        """Send email via SMTP with the provided configuration."""
        host = smtp_config['host']
        port = smtp_config['port']
        username = smtp_config.get('username')
        password = smtp_config.get('password')
        use_tls = smtp_config.get('use_tls', True)
        
        try:
            # Create SMTP connection
            server = smtplib.SMTP(host, port)
            
            if use_tls:
                server.starttls()
            
            # Authenticate if credentials provided
            if username and password:
                server.login(username, password)
            
            # Send email
            server.send_message(msg, from_addr=from_email, to_addrs=[to_email])
            server.quit()
            
        except Exception as e:
            logger.error(f"SMTP error: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def send_contact_form_email(
        db: Session,
        institute_id: int,
        name: str,
        email: str,
        subject: str,
        message: str
    ) -> bool:
        """
        Send contact form submission email.
        
        Args:
            db: Database session
            institute_id: Institute ID
            name: Sender name
            email: Sender email
            subject: Message subject
            message: Message content
        
        Returns:
            bool: True if email sent successfully
        """
        email_config = EmailService.get_email_config(db, institute_id)
        
        if not email_config or not email_config.get('contact_email'):
            logger.error(f"No contact email configured for institute {institute_id}")
            return False
        
        contact_email = email_config['contact_email']
        site_name = email_config.get('site_name', 'LMS')
        
        # Create email content
        email_subject = f"Contact Form: {subject}"
        
        body_html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
              <h2 style="color: #3B82F6;">New Contact Form Submission</h2>
              <p>You have received a new message from your website contact form.</p>
              
              <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p><strong>Name:</strong> {name}</p>
                <p><strong>Email:</strong> <a href="mailto:{email}">{email}</a></p>
                <p><strong>Subject:</strong> {subject}</p>
              </div>
              
              <div style="margin: 20px 0;">
                <h3 style="color: #3B82F6;">Message:</h3>
                <p style="white-space: pre-wrap;">{message}</p>
              </div>
              
              <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
              <p style="color: #666; font-size: 12px;">
                This email was sent from the contact form on {site_name}.
                <br>You can reply directly to this email to respond to {name}.
              </p>
            </div>
          </body>
        </html>
        """
        
        body_text = f"""
New Contact Form Submission

You have received a new message from your website contact form.

Name: {name}
Email: {email}
Subject: {subject}

Message:
{message}

---
This email was sent from the contact form on {site_name}.
You can reply directly to this email to respond to {name}.
        """
        
        return EmailService.send_email(
            db=db,
            institute_id=institute_id,
            to_email=contact_email,
            subject=email_subject,
            body_html=body_html,
            body_text=body_text,
            reply_to=email  # Set reply-to to sender's email
        )
