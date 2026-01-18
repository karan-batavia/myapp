"""
Email Service for DataGuardian Pro
Handles payment confirmations, invoice delivery, and customer communications
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, Optional, List
from datetime import datetime
import io

logger = logging.getLogger(__name__)

class EmailService:
    """Professional email service for payment confirmations and invoices"""
    
    def __init__(self):
        # Email configuration from environment
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        
        # Support multiple env var names for flexibility
        self.email_username = os.getenv('EMAIL_USERNAME') or os.getenv('SMTP_USERNAME')
        self.email_password = os.getenv('EMAIL_PASSWORD') or os.getenv('SMTP_PASSWORD')
        
        self.from_email = os.getenv('FROM_EMAIL', 'billing@dataguardian.pro')
        self.from_name = os.getenv('FROM_NAME', 'DataGuardian Pro')
        
        # Company information for invoices
        self.company_info = {
            'name': 'DataGuardian Pro B.V.',
            'address': 'Science Park 123',
            'city': 'Amsterdam',
            'postal_code': '1098 XG',
            'country': 'Netherlands',
            'vat_number': 'NL123456789B01',
            'kvk_number': '12345678',
            'email': 'billing@dataguardian.pro',
            'phone': '+31 20 123 4567',
            'website': 'https://dataguardian.pro'
        }
        
        self.enabled = bool(self.email_username and self.email_password)
        if not self.enabled:
            logger.warning("Email service disabled - SMTP credentials not configured")
    
    def send_payment_confirmation(self, payment_record: Dict[str, Any], invoice_pdf: Optional[bytes] = None) -> bool:
        """
        Send payment confirmation email with optional invoice attachment
        
        Args:
            payment_record: Payment details from webhook
            invoice_pdf: Optional PDF invoice as bytes
            
        Returns:
            True if email sent successfully
        """
        if not self.enabled:
            logger.warning("Email service not configured - skipping payment confirmation")
            return False
        
        try:
            # Prepare email content
            subject = f"Payment Confirmation - DataGuardian Pro ({payment_record['scan_type']})"
            
            # Create email body
            email_body = self._create_payment_confirmation_html(payment_record)
            
            # Send email
            return self._send_email(
                to_email=payment_record['customer_email'],
                subject=subject,
                html_body=email_body,
                attachments=[('invoice.pdf', invoice_pdf)] if invoice_pdf else None
            )
            
        except Exception as e:
            logger.error(f"Failed to send payment confirmation: {str(e)}")
            return False
    
    def send_subscription_confirmation(self, subscription_data: Dict[str, Any]) -> bool:
        """Send subscription activation confirmation"""
        if not self.enabled:
            return False
        
        try:
            subject = f"Subscription Activated - DataGuardian Pro ({subscription_data['plan_name']})"
            email_body = self._create_subscription_confirmation_html(subscription_data)
            
            return self._send_email(
                to_email=subscription_data['customer_email'],
                subject=subject,
                html_body=email_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send subscription confirmation: {str(e)}")
            return False
    
    def send_certificate_delivery(self, customer_email: str, certificate_data: Dict[str, Any], 
                                certificate_pdf: bytes) -> bool:
        """Send compliance certificate via email"""
        if not self.enabled:
            return False
        
        try:
            subject = f"Your Compliance Certificate - DataGuardian Pro"
            email_body = self._create_certificate_delivery_html(certificate_data)
            
            return self._send_email(
                to_email=customer_email,
                subject=subject,
                html_body=email_body,
                attachments=[('compliance_certificate.pdf', certificate_pdf)]
            )
            
        except Exception as e:
            logger.error(f"Failed to send certificate: {str(e)}")
            return False
    
    def send_invoice(self, customer_email: str, invoice_data: Dict[str, Any], invoice_pdf: bytes) -> bool:
        """Send standalone invoice"""
        if not self.enabled:
            return False
        
        try:
            subject = f"Invoice {invoice_data['invoice_number']} - DataGuardian Pro"
            email_body = self._create_invoice_delivery_html(invoice_data)
            
            return self._send_email(
                to_email=customer_email,
                subject=subject,
                html_body=email_body,
                attachments=[('invoice.pdf', invoice_pdf)]
            )
            
        except Exception as e:
            logger.error(f"Failed to send invoice: {str(e)}")
            return False
    
    def send_payment_failure_notification(self, failure_data: Dict[str, Any]) -> bool:
        """Send payment failure notification email"""
        if not self.enabled:
            return False
        
        try:
            subject = f"Payment Issue - DataGuardian Pro ({failure_data['plan_name']})"
            email_body = self._create_payment_failure_html(failure_data)
            
            return self._send_email(
                to_email=failure_data['customer_email'],
                subject=subject,
                html_body=email_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send payment failure notification: {str(e)}")
            return False
    
    def _create_payment_confirmation_html(self, payment_record: Dict[str, Any]) -> str:
        """Create HTML email for payment confirmation"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2e7d32; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
                .amount {{ font-size: 24px; font-weight: bold; color: #2e7d32; }}
                .details {{ background: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .button {{ background: #2e7d32; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Payment Confirmed</h1>
                    <p>Thank you for your payment to DataGuardian Pro</p>
                </div>
                
                <div class="content">
                    <h2>Payment Details</h2>
                    <div class="details">
                        <p><strong>Service:</strong> {payment_record['scan_type']}</p>
                        <p><strong>Amount:</strong> <span class="amount">€{payment_record['amount']:.2f}</span></p>
                        <p><strong>Payment Method:</strong> {payment_record.get('payment_method', 'Card').title()}</p>
                        <p><strong>Transaction ID:</strong> {payment_record['session_id']}</p>
                        <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
                        <p><strong>Country:</strong> {payment_record.get('country_code', 'NL')}</p>
                    </div>
                    
                    <h3>What's Next?</h3>
                    <ul>
                        <li>✅ Your scan will be processed automatically</li>
                        <li>📊 Results will be available in your dashboard</li>
                        <li>📧 You'll receive a notification when complete</li>
                        <li>🏛️ EU VAT invoice attached (if applicable)</li>
                    </ul>
                    
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="https://dataguardian.pro/dashboard" class="button">View Dashboard</a>
                    </p>
                </div>
                
                <div class="footer">
                    <p><strong>{self.company_info['name']}</strong></p>
                    <p>{self.company_info['address']}, {self.company_info['postal_code']} {self.company_info['city']}</p>
                    <p>VAT: {self.company_info['vat_number']} | KvK: {self.company_info['kvk_number']}</p>
                    <p>Questions? Contact us at {self.company_info['email']}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_subscription_confirmation_html(self, subscription_data: Dict[str, Any]) -> str:
        """Create HTML email for subscription confirmation"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #1976d2; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
                .plan-name {{ font-size: 20px; font-weight: bold; color: #1976d2; }}
                .details {{ background: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .button {{ background: #1976d2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Subscription Activated</h1>
                    <p>Welcome to DataGuardian Pro!</p>
                </div>
                
                <div class="content">
                    <h2>Subscription Details</h2>
                    <div class="details">
                        <p><strong>Plan:</strong> <span class="plan-name">{subscription_data['plan_name']}</span></p>
                        <p><strong>Billing:</strong> €{subscription_data['amount']:.2f} per {subscription_data.get('interval', 'month')}</p>
                        <p><strong>Next Billing:</strong> {subscription_data.get('next_billing_date', 'N/A')}</p>
                        <p><strong>Subscription ID:</strong> {subscription_data['subscription_id']}</p>
                    </div>
                    
                    <h3>Your Benefits</h3>
                    <ul>
                        <li>🔍 Advanced PII scanning capabilities</li>
                        <li>🇳🇱 Netherlands UAVG compliance</li>
                        <li>📊 Professional compliance reports</li>
                        <li>🔌 Enterprise data connectors</li>
                        <li>💎 Priority customer support</li>
                    </ul>
                    
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="https://dataguardian.pro/dashboard" class="button">Start Scanning</a>
                    </p>
                </div>
                
                <div class="footer">
                    <p><strong>{self.company_info['name']}</strong></p>
                    <p>Questions? Contact us at {self.company_info['email']}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_certificate_delivery_html(self, certificate_data: Dict[str, Any]) -> str:
        """Create HTML email for certificate delivery"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #9c27b0; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
                .certificate-title {{ font-size: 18px; font-weight: bold; color: #9c27b0; }}
                .details {{ background: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏆 Compliance Certificate Ready</h1>
                    <p>Your professional compliance certificate is attached</p>
                </div>
                
                <div class="content">
                    <h2>Certificate Details</h2>
                    <div class="details">
                        <p><strong>Certificate Type:</strong> <span class="certificate-title">{certificate_data.get('type', 'GDPR Compliance Certificate')}</span></p>
                        <p><strong>Organization:</strong> {certificate_data.get('organization', 'N/A')}</p>
                        <p><strong>Issue Date:</strong> {certificate_data.get('issue_date', datetime.now().strftime('%B %d, %Y'))}</p>
                        <p><strong>Valid Until:</strong> {certificate_data.get('valid_until', 'N/A')}</p>
                        <p><strong>Certificate ID:</strong> {certificate_data.get('certificate_id', 'N/A')}</p>
                    </div>
                    
                    <h3>Important Notes</h3>
                    <ul>
                        <li>📎 Certificate is attached as PDF</li>
                        <li>🔒 Digitally signed and verifiable</li>
                        <li>⚖️ Meets Netherlands AP requirements</li>
                        <li>🏛️ EU GDPR Article 35 compliant</li>
                    </ul>
                </div>
                
                <div class="footer">
                    <p><strong>{self.company_info['name']}</strong></p>
                    <p>Certificate verification: {self.company_info['website']}/verify</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_invoice_delivery_html(self, invoice_data: Dict[str, Any]) -> str:
        """Create HTML email for invoice delivery"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #424242; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
                .invoice-number {{ font-size: 20px; font-weight: bold; color: #424242; }}
                .details {{ background: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .amount {{ font-size: 18px; font-weight: bold; color: #2e7d32; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📄 Invoice</h1>
                    <p>EU VAT Compliant Invoice</p>
                </div>
                
                <div class="content">
                    <h2>Invoice Details</h2>
                    <div class="details">
                        <p><strong>Invoice Number:</strong> <span class="invoice-number">{invoice_data['invoice_number']}</span></p>
                        <p><strong>Date:</strong> {invoice_data.get('date', datetime.now().strftime('%B %d, %Y'))}</p>
                        <p><strong>Due Date:</strong> {invoice_data.get('due_date', 'Paid')}</p>
                        <p><strong>Total Amount:</strong> <span class="amount">€{invoice_data['total_amount']:.2f}</span></p>
                        <p><strong>VAT Included:</strong> €{invoice_data.get('vat_amount', 0):.2f}</p>
                    </div>
                    
                    <h3>Payment Information</h3>
                    <p>This invoice has been automatically generated following your payment. No further action is required.</p>
                    
                    <p><strong>VAT Number:</strong> {self.company_info['vat_number']}</p>
                </div>
                
                <div class="footer">
                    <p><strong>{self.company_info['name']}</strong></p>
                    <p>{self.company_info['address']}, {self.company_info['postal_code']} {self.company_info['city']}</p>
                    <p>VAT: {self.company_info['vat_number']} | KvK: {self.company_info['kvk_number']}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_payment_failure_html(self, failure_data: Dict[str, Any]) -> str:
        """Create HTML email for payment failure notification"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #d32f2f; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
                .alert {{ background: #ffebee; border-left: 4px solid #d32f2f; padding: 15px; margin: 15px 0; }}
                .button {{ background: #d32f2f; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; }}
                .details {{ background: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚠️ Payment Issue</h1>
                    <p>Action Required for Your DataGuardian Pro Subscription</p>
                </div>
                
                <div class="content">
                    <div class="alert">
                        <strong>Payment Failed:</strong> We couldn't process your payment for the {failure_data['plan_name']} subscription.
                    </div>
                    
                    <h2>Subscription Details</h2>
                    <div class="details">
                        <p><strong>Subscription:</strong> {failure_data['plan_name']}</p>
                        <p><strong>Subscription ID:</strong> {failure_data['subscription_id']}</p>
                        <p><strong>Failed Invoice:</strong> {failure_data['invoice_id']}</p>
                        <p><strong>Customer Email:</strong> {failure_data['customer_email']}</p>
                    </div>
                    
                    <h3>What You Can Do</h3>
                    <ul>
                        <li>🔄 <strong>Update Payment Method:</strong> Check if your card has expired or needs updating</li>
                        <li>💳 <strong>Verify Billing Info:</strong> Ensure sufficient funds and correct billing address</li>
                        <li>📞 <strong>Contact Your Bank:</strong> Some payments may be blocked by your financial institution</li>
                        <li>🔔 <strong>Update Automatically:</strong> We'll retry the payment in 24 hours</li>
                    </ul>
                    
                    <div class="alert">
                        <strong>Important:</strong> Your subscription remains active for a grace period. Please update your payment method to avoid service interruption.
                    </div>
                    
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="https://dataguardian.pro/billing" class="button">Update Payment Method</a>
                    </p>
                </div>
                
                <div class="footer">
                    <p><strong>{self.company_info['name']}</strong></p>
                    <p>{self.company_info['address']}, {self.company_info['postal_code']} {self.company_info['city']}</p>
                    <p>VAT: {self.company_info['vat_number']} | KvK: {self.company_info['kvk_number']}</p>
                    <p>Questions? Contact us at {self.company_info['email']}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _send_email(self, to_email: str, subject: str, html_body: str, 
                   attachments: Optional[List[tuple]] = None) -> bool:
        """
        Send email with optional attachments
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            attachments: List of (filename, content) tuples
            
        Returns:
            True if email sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add HTML body
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for filename, content in attachments:
                    if content:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(content)
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {filename}'
                        )
                        msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.email_username and self.email_password:
                    server.login(self.email_username, self.email_password)
                else:
                    raise ValueError("Email credentials not configured")
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_welcome_email(self, user_data: Dict[str, Any]) -> bool:
        """
        Send welcome email after user registration
        
        Args:
            user_data: User details (username, email, role)
            
        Returns:
            True if email sent successfully
        """
        if not self.enabled:
            logger.warning("Email service not configured - skipping welcome email")
            return False
        
        try:
            subject = "Welcome to DataGuardian Pro - Registration Confirmed"
            email_body = self._create_welcome_email_html(user_data)
            
            return self._send_email(
                to_email=user_data['email'],
                subject=subject,
                html_body=email_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send welcome email: {str(e)}")
            return False
    
    def _create_welcome_email_html(self, user_data: Dict[str, Any]) -> str:
        """Create HTML email for welcome/registration confirmation"""
        username = user_data.get('username', 'User')
        role = user_data.get('role', 'user').title()
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #1976d2; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
                .details {{ background: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .button {{ background: #1976d2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; }}
                .feature-list {{ list-style: none; padding: 0; }}
                .feature-list li {{ padding: 8px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to DataGuardian Pro</h1>
                    <p>Your Registration is Complete</p>
                </div>
                
                <div class="content">
                    <h2>Hello {username}!</h2>
                    <p>Thank you for registering with DataGuardian Pro - Europe's leading privacy compliance platform.</p>
                    
                    <div class="details">
                        <p><strong>Username:</strong> {username}</p>
                        <p><strong>Account Type:</strong> {role}</p>
                        <p><strong>Registration Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
                    </div>
                    
                    <h3>What You Can Do Now</h3>
                    <ul class="feature-list">
                        <li>🔍 <strong>PII Scanning:</strong> Detect personal data across documents, databases, and code</li>
                        <li>🇳🇱 <strong>Netherlands Compliance:</strong> 100% GDPR + UAVG coverage</li>
                        <li>🤖 <strong>EU AI Act:</strong> Complete 113-article compliance checking</li>
                        <li>📊 <strong>Professional Reports:</strong> Generate audit-ready compliance reports</li>
                        <li>🛡️ <strong>Deepfake Detection:</strong> Audio/video authenticity verification</li>
                    </ul>
                    
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="https://dataguardianpro.nl" class="button">Start Using DataGuardian Pro</a>
                    </p>
                    
                    <h3>Need Help?</h3>
                    <p>Our team is here to support you. Contact us at {self.company_info['email']} for any questions.</p>
                </div>
                
                <div class="footer">
                    <p><strong>{self.company_info['name']}</strong></p>
                    <p>{self.company_info['address']}, {self.company_info['postal_code']} {self.company_info['city']}</p>
                    <p>VAT: {self.company_info['vat_number']} | KvK: {self.company_info['kvk_number']}</p>
                    <p>This email was sent because you registered at DataGuardian Pro</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def test_email_configuration(self) -> Dict[str, Any]:
        """Test email configuration and return status"""
        if not self.enabled:
            return {
                'status': 'disabled',
                'message': 'Email service not configured',
                'missing_vars': [
                    var for var in ['EMAIL_USERNAME', 'EMAIL_PASSWORD'] 
                    if not os.getenv(var)
                ]
            }
        
        try:
            # Test SMTP connection
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.email_username and self.email_password:
                    server.login(self.email_username, self.email_password)
                else:
                    raise ValueError("Email credentials not configured")
            
            return {
                'status': 'configured',
                'message': 'Email service ready',
                'smtp_server': self.smtp_server,
                'from_email': self.from_email
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'SMTP connection failed: {str(e)}',
                'smtp_server': self.smtp_server
            }

# Global email service instance
email_service = EmailService()