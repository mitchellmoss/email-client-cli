"""Email sender module for forwarding processed orders."""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Optional, List, Dict
import time
import logging
import os
import imaplib
from email import message_from_string

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class EmailSender:
    """Send formatted orders via SMTP."""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str, signature_html: Optional[str] = None):
        """
        Initialize email sender.
        
        Args:
            smtp_server: SMTP server hostname
            smtp_port: SMTP server port
            username: Email username for authentication
            password: Email password or app password
            signature_html: Optional custom HTML signature
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_address = username
        self.signature_html = signature_html
        
    def send_order_to_cs(self, recipient: str, order_text: str, 
                        original_order_id: str = "Unknown") -> bool:
        """
        Send formatted order to CS team.
        
        Args:
            recipient: CS team email address
            order_text: Formatted order text
            original_order_id: Original order ID for subject line
            
        Returns:
            True if sent successfully, False otherwise
        """
        subject = f"TileWare Order #{original_order_id} - Action Required"
        
        # Create email message
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = self.from_address
        message['To'] = recipient
        message['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        
        # Add plain text part with signature
        text_with_signature = order_text + "\n\n" + self._get_text_signature()
        text_part = MIMEText(text_with_signature, 'plain')
        message.attach(text_part)
        
        # Also create HTML version for better formatting
        html_content = self._create_html_version(order_text, original_order_id)
        html_part = MIMEText(html_content, 'html')
        message.attach(html_part)
        
        # Send with retry logic
        return self._send_with_retry(recipient, message)
    
    def _get_text_signature(self) -> str:
        """Get plain text version of email signature."""
        return """
--
Mitchell Moss
Installations Plus Inc.
774-233-0210 | 508-733-5839
mitchell@installplusinc.com
installplusinc.com
131 Flanders Rd, Westborough, MA, 01581

Connect with us:
LinkedIn: https://www.linkedin.com/company/10612759
Facebook: http://www.facebook.com/installplusinc
Instagram: https://www.instagram.com/installations_plus/
"""
    
    def _create_html_version(self, order_text: str, order_id: str) -> str:
        """Create HTML version of the order for better email formatting."""
        # Escape HTML and convert line breaks
        lines = order_text.split('\n')
        html_lines = []
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .order-container {{ 
                    background-color: #f8f9fa; 
                    padding: 20px; 
                    border-radius: 8px; 
                    margin: 20px 0;
                }}
                .order-header {{ 
                    background-color: #007bff; 
                    color: white; 
                    padding: 10px 20px; 
                    border-radius: 8px 8px 0 0; 
                    margin: -20px -20px 20px -20px;
                }}
                .product {{ 
                    background-color: white; 
                    padding: 10px; 
                    margin: 10px 0; 
                    border-left: 4px solid #007bff;
                }}
                .shipping {{ 
                    background-color: #e9ecef; 
                    padding: 15px; 
                    margin: 20px 0; 
                    border-radius: 4px;
                }}
                .shipping-method {{ 
                    font-weight: bold; 
                    color: #007bff; 
                    margin: 10px 0;
                }}
                .footer {{ 
                    margin-top: 30px; 
                    padding-top: 20px; 
                    border-top: 1px solid #dee2e6; 
                    font-size: 12px; 
                    color: #6c757d;
                }}
            </style>
        </head>
        <body>
            <div class="order-container">
                <div class="order-header">
                    <h2>TileWare Order #{order_id}</h2>
                </div>
                <div class="content">
        """
        
        in_shipping = False
        for line in lines:
            if line.startswith("Hi CS"):
                html += f"<p><strong>{line}</strong></p>"
            elif line.strip() == "SHIP TO:":
                html += '<div class="shipping"><h3>Shipping Information</h3>'
                in_shipping = True
            elif line.strip() == "::::":
                if in_shipping:
                    html += '</div>'
                break
            elif line.strip() and not line.startswith("Hi CS"):
                if in_shipping:
                    if line.isupper():  # Shipping method
                        html += f'<p class="shipping-method">{line}</p>'
                    else:
                        html += f'<p>{line}</p>'
                else:
                    # Product line
                    if ' x' in line and ('TileWare' in line or '#' in line):
                        html += f'<div class="product">{line}</div>'
                    else:
                        html += f'<p>{line}</p>'
        
        html += """
                </div>
                <div class="footer">
                    <p>This order was automatically processed from Tile Pro Depot.</p>
                    <p>Please process this TileWare order as soon as possible.</p>
                </div>
            </div>
            
            <!-- Email Signature -->
            <div style="display: flex; align-items: center; padding: 10px; border-top: 2px solid #0078d4; margin-top: 30px;">
                <div style="margin-right: 20px;">
                    <img src="https://images.squarespace-cdn.com/content/v1/56ce6172c2ea51d77a671500/1533871562097-SIYDUTPEOQC3BIIQU126/Installations+Plus+logo+-+color+-+close+crop.png?format=1500w" alt="Installations Plus" width="120" height="60">
                </div>
                <div style="font-size: 14px; line-height: 1.5;">
                    <div style="font-size: 18px; font-weight: bold; color: #0078d4; margin-bottom: 4px;">Mitchell Moss</div>
                    <div style="color: #555; margin-bottom: 16px;">Installations Plus Inc.</div>
                    <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                        <a href="tel:774-233-0210" style="color: #0078d4; text-decoration: none; margin-right: 8px;">774-233-0210</a>
                        <a href="tel:508-733-5839" style="color: #0078d4; text-decoration: none; margin-right: 8px;">508-733-5839</a>
                        <a href="mailto:mitchell@installplusinc.com" style="color: #0078d4; text-decoration: none; margin-right: 8px;">mitchell@installplusinc.com</a>
                        <a href="https://installplusinc.com" style="color: #0078d4; text-decoration: none; margin-right: 8px;">installplusinc.com</a>
                        <span>131 Flanders Rd, Westborough, MA, 01581</span>
                    </div>
                    <div style="display: flex; gap: 10px; margin-top: 10px;">
                        <a href="https://www.linkedin.com/company/10612759?trk=vsrp_companies_cluster_name&trkInfo=VSRPsearchId%3A185298431468515352362%2CVSRPtargetId%3A10612759%2CVSRPcmpt%3Acompanies_cluster"><img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" alt="LinkedIn" width="20" height="20"></a>
                        <a href="http://www.facebook.com/installplusinc"><img src="https://cdn-icons-png.flaticon.com/512/174/174848.png" alt="Facebook" width="20" height="20"></a>
                        <a href="https://www.instagram.com/installations_plus/"><img src="https://cdn-icons-png.flaticon.com/512/174/174855.png" alt="Instagram" width="20" height="20"></a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _add_html_signature_to_content(self, html_content: str) -> str:
        """Add HTML signature to any HTML content."""
        # Use custom signature if provided, otherwise use default
        if self.signature_html:
            signature_html = self.signature_html
        else:
            # Default signature (fallback)
            signature_html = """
            <div style="display: flex; align-items: center; padding: 10px; border-top: 2px solid #0078d4; margin-top: 30px;">
                <div style="margin-right: 20px;">
                    <img src="https://images.squarespace-cdn.com/content/v1/56ce6172c2ea51d77a671500/1533871562097-SIYDUTPEOQC3BIIQU126/Installations+Plus+logo+-+color+-+close+crop.png?format=1500w" alt="Installations Plus" width="120" height="60">
                </div>
                <div style="font-size: 14px; line-height: 1.5;">
                    <div style="font-size: 18px; font-weight: bold; color: #0078d4; margin-bottom: 4px;">Mitchell Moss</div>
                    <div style="color: #555; margin-bottom: 16px;">Installations Plus Inc.</div>
                    <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                        <a href="tel:774-233-0210" style="color: #0078d4; text-decoration: none; margin-right: 8px;">774-233-0210</a>
                        <a href="tel:508-733-5839" style="color: #0078d4; text-decoration: none; margin-right: 8px;">508-733-5839</a>
                        <a href="mailto:mitchell@installplusinc.com" style="color: #0078d4; text-decoration: none; margin-right: 8px;">mitchell@installplusinc.com</a>
                        <a href="https://installplusinc.com" style="color: #0078d4; text-decoration: none; margin-right: 8px;">installplusinc.com</a>
                        <span>131 Flanders Rd, Westborough, MA, 01581</span>
                    </div>
                    <div style="display: flex; gap: 10px; margin-top: 10px;">
                        <a href="https://www.linkedin.com/company/10612759?trk=vsrp_companies_cluster_name&trkInfo=VSRPsearchId%3A185298431468515352362%2CVSRPtargetId%3A10612759%2CVSRPcmpt%3Acompanies_cluster"><img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" alt="LinkedIn" width="20" height="20"></a>
                        <a href="http://www.facebook.com/installplusinc"><img src="https://cdn-icons-png.flaticon.com/512/174/174848.png" alt="Facebook" width="20" height="20"></a>
                        <a href="https://www.instagram.com/installations_plus/"><img src="https://cdn-icons-png.flaticon.com/512/174/174855.png" alt="Instagram" width="20" height="20"></a>
                    </div>
                </div>
            </div>
            """
        
        # If HTML content has closing body tag, insert before it
        if '</body>' in html_content:
            return html_content.replace('</body>', signature_html + '</body>')
        else:
            # Otherwise append to end
            return html_content + signature_html
    
    def _send_with_retry(self, recipient: str, message: MIMEMultipart, 
                        max_retries: int = 3) -> bool:
        """
        Send email with retry logic.
        
        Args:
            recipient: Email recipient
            message: Email message to send
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if sent successfully, False otherwise
        """
        for attempt in range(max_retries):
            try:
                # Create SSL context
                context = ssl.create_default_context()
                
                # Connect to server based on port
                if self.smtp_port == 465:
                    # Use SMTP_SSL for port 465
                    with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                        server.login(self.username, self.password)
                        
                        # Send email
                        server.send_message(message)
                        
                        logger.info(f"Successfully sent order email to {recipient}")
                        
                        # Save to sent folder if configured
                        self._save_to_sent_folder(message)
                        
                        return True
                else:
                    # Use STARTTLS for other ports (587, 25)
                    with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                        server.starttls(context=context)
                        server.login(self.username, self.password)
                        
                        # Send email
                        server.send_message(message)
                        
                        logger.info(f"Successfully sent order email to {recipient}")
                        
                        # Save to sent folder if configured
                        self._save_to_sent_folder(message)
                        
                        return True
                    
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"SMTP authentication failed: {e}")
                return False  # Don't retry auth errors
                
            except smtplib.SMTPException as e:
                logger.error(f"SMTP error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"Unexpected error sending email: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    
        logger.error(f"Failed to send email after {max_retries} attempts")
        return False
    
    def test_connection(self) -> bool:
        """
        Test SMTP connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            context = ssl.create_default_context()
            
            if self.smtp_port == 465:
                # Use SMTP_SSL for port 465
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                    server.login(self.username, self.password)
            else:
                # Use STARTTLS for other ports
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls(context=context)
                    server.login(self.username, self.password)
                
            logger.info("SMTP connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False
    
    def send_batch_orders(self, recipient: str, orders: List[Dict[str, str]]) -> int:
        """
        Send multiple orders in a batch.
        
        Args:
            recipient: CS team email address
            orders: List of order dictionaries with 'text' and 'id' keys
            
        Returns:
            Number of successfully sent orders
        """
        sent_count = 0
        
        for order in orders:
            if self.send_order_to_cs(recipient, order['text'], order.get('id', 'Unknown')):
                sent_count += 1
                # Small delay between emails to avoid rate limiting
                time.sleep(1)
                
        logger.info(f"Sent {sent_count} out of {len(orders)} orders")
        return sent_count
    
    def send_email_with_attachment(self, to_email: str, subject: str, 
                                  html_content: str, text_content: str,
                                  attachment_path: str, attachment_name: str) -> bool:
        """
        Send email with a PDF attachment.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML version of email body
            text_content: Plain text version of email body
            attachment_path: Path to PDF file to attach
            attachment_name: Name for the attachment
            
        Returns:
            True if sent successfully, False otherwise
        """
        # Create message
        message = MIMEMultipart('mixed')
        message['Subject'] = subject
        message['From'] = self.from_address
        message['To'] = to_email
        message['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        
        # Create the alternative part
        alternative = MIMEMultipart('alternative')
        message.attach(alternative)
        
        # Add text and HTML parts with signature
        text_with_signature = text_content + "\n\n" + self._get_text_signature()
        text_part = MIMEText(text_with_signature, 'plain')
        
        # Add signature to HTML content
        html_with_signature = self._add_html_signature_to_content(html_content)
        html_part = MIMEText(html_with_signature, 'html')
        
        alternative.attach(text_part)
        alternative.attach(html_part)
        
        # Add PDF attachment
        try:
            # Verify attachment exists and has content
            if not os.path.exists(attachment_path):
                logger.error(f"Attachment file not found: {attachment_path}")
                return False
                
            file_size = os.path.getsize(attachment_path)
            logger.info(f"Attaching PDF: {attachment_path} (size: {file_size} bytes)")
            
            with open(attachment_path, 'rb') as attachment:
                # Create MIMEBase instance
                pdf_part = MIMEBase('application', 'pdf')
                pdf_content = attachment.read()
                pdf_part.set_payload(pdf_content)
                logger.info(f"Read {len(pdf_content)} bytes from PDF")
                
            # Encode file
            encoders.encode_base64(pdf_part)
            
            # Add header
            pdf_part.add_header(
                'Content-Disposition',
                f'attachment; filename= {attachment_name}'
            )
            
            # Attach to message
            message.attach(pdf_part)
            logger.info(f"Successfully attached PDF as {attachment_name}")
            
        except Exception as e:
            logger.error(f"Error attaching PDF: {e}")
            return False
        
        # Send with retry logic
        return self._send_with_retry(to_email, message)
    
    def _save_to_sent_folder(self, message: MIMEMultipart) -> None:
        """
        Save sent email to IMAP Sent folder.
        Note: This requires IMAP credentials and may not work with all providers.
        """
        try:
            # Check if we have IMAP credentials
            imap_server = os.getenv('IMAP_SERVER')
            imap_port = os.getenv('IMAP_PORT', '993')
            email_address = os.getenv('EMAIL_ADDRESS')
            email_password = os.getenv('EMAIL_PASSWORD')
            
            if not all([imap_server, email_address, email_password]):
                logger.debug("IMAP credentials not configured, skipping sent folder save")
                return
            
            # Connect to IMAP server
            imap = imaplib.IMAP4_SSL(imap_server, int(imap_port))
            imap.login(email_address, email_password)
            
            # Find sent folder name (varies by provider)
            sent_folder = None
            for folder_name in ['Sent', '[Gmail]/Sent Mail', 'Sent Items', 'INBOX.Sent']:
                try:
                    status, _ = imap.select(folder_name)
                    if status == 'OK':
                        sent_folder = folder_name
                        break
                except:
                    continue
            
            if not sent_folder:
                logger.warning("Could not find sent folder in IMAP")
                imap.logout()
                return
            
            # Convert message to string
            message_str = message.as_string()
            
            # Append to sent folder
            imap.append(sent_folder, '\\Seen', imaplib.Time2Internaldate(time.time()), 
                       message_str.encode('utf-8'))
            
            logger.info(f"Email saved to {sent_folder} folder")
            imap.logout()
            
        except Exception as e:
            logger.debug(f"Could not save to sent folder: {e}")
            # This is non-critical, so we don't raise the exception