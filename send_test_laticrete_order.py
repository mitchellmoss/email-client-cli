#!/usr/bin/env python3
"""Send a test Laticrete order with filled PDF attachment."""

import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from src.price_list_reader import PriceListReader
from src.pdf_filler import PDFOrderFormFiller
from src.email_sender import EmailSender
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def send_test_laticrete_order():
    """Send a test Laticrete order email with filled PDF."""
    
    # Test order data
    test_order = {
        'order_id': 'TEST-12345',
        'customer_name': 'John Smith',
        'phone': '555-123-4567',
        'shipping_address': {
            'street': '123 Test Street',
            'city': 'Boston',
            'state': 'MA',
            'zip': '02101'
        },
        'shipping_method': 'UPS GROUND',
        'laticrete_products': [
            {
                'name': 'LATICRETE 254 Platinum Multipurpose Thinset - Gray 50lb',
                'sku': '0254-0050-2',
                'quantity': 5,
                'price': '$45.99'
            },
            {
                'name': 'LATICRETE HYDRO BAN Sheet Membrane 5\' x 100\'',
                'sku': '9235-0500-1',
                'quantity': 2,
                'price': '$385.00'
            },
            {
                'name': 'LATICRETE PERMACOLOR Select Grout - Bright White 25lb',
                'sku': '2600-0025-2',
                'quantity': 10,
                'price': '$28.50'
            }
        ]
    }
    
    # Initialize components
    logger.info("Initializing components...")
    
    # Price list reader (optional - for enrichment)
    try:
        price_reader = PriceListReader()
        logger.info("Price list loaded successfully")
    except Exception as e:
        logger.warning(f"Could not load price list: {e}")
        price_reader = None
    
    # PDF Filler
    pdf_filler = PDFOrderFormFiller()
    
    # Email Sender
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    if not all([smtp_server, smtp_username, smtp_password]):
        logger.error("SMTP configuration missing in .env file")
        return False
    
    email_sender = EmailSender(smtp_server, smtp_port, smtp_username, smtp_password)
    
    # Generate PDF
    logger.info("Generating PDF order form...")
    pdf_path = f"/tmp/test_laticrete_order_{test_order['order_id']}.pdf"
    
    if not pdf_filler.fill_order_form(test_order, pdf_path):
        logger.error("Failed to generate PDF")
        return False
    
    logger.info(f"PDF generated: {pdf_path} (size: {os.path.getsize(pdf_path)} bytes)")
    
    # Prepare email content
    subject = f"TEST - Laticrete Order #{test_order['order_id']} - {test_order['customer_name']}"
    
    # HTML content
    html_content = f"""
    <html>
    <body>
        <h2>TEST - New Laticrete Order</h2>
        <p><strong>This is a TEST order for demonstration purposes.</strong></p>
        <p>Please process the attached Laticrete order form.</p>
        
        <h3>Order Summary:</h3>
        <ul>
            <li><strong>Order ID:</strong> {test_order['order_id']}</li>
            <li><strong>Customer:</strong> {test_order['customer_name']}</li>
            <li><strong>Phone:</strong> {test_order['phone']}</li>
            <li><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}</li>
            <li><strong>Total Items:</strong> {len(test_order['laticrete_products'])}</li>
        </ul>
        
        <h3>Products:</h3>
        <table border="1" cellpadding="5" cellspacing="0">
            <tr>
                <th>SKU</th>
                <th>Product</th>
                <th>Quantity</th>
                <th>Unit Price</th>
            </tr>
    """
    
    for product in test_order['laticrete_products']:
        html_content += f"""
            <tr>
                <td>{product['sku']}</td>
                <td>{product['name']}</td>
                <td>{product['quantity']}</td>
                <td>{product['price']}</td>
            </tr>
        """
    
    html_content += f"""
        </table>
        
        <h3>Shipping Address:</h3>
        <p>
        {test_order['customer_name']}<br>
        {test_order['shipping_address']['street']}<br>
        {test_order['shipping_address']['city']}, {test_order['shipping_address']['state']} {test_order['shipping_address']['zip']}<br>
        </p>
        
        <p><em>This is a TEST order sent from the Email Client CLI system.</em></p>
    </body>
    </html>
    """
    
    # Plain text content
    text_content = f"""
TEST - New Laticrete Order

This is a TEST order for demonstration purposes.

Please process the attached Laticrete order form.

Order Summary:
- Order ID: {test_order['order_id']}
- Customer: {test_order['customer_name']}
- Phone: {test_order['phone']}
- Date: {datetime.now().strftime('%B %d, %Y')}
- Total Items: {len(test_order['laticrete_products'])}

Products:
"""
    
    for product in test_order['laticrete_products']:
        text_content += f"- {product['sku']} | {product['name']} | Qty: {product['quantity']} | {product['price']}\n"
    
    text_content += f"""
Shipping Address:
{test_order['customer_name']}
{test_order['shipping_address']['street']}
{test_order['shipping_address']['city']}, {test_order['shipping_address']['state']} {test_order['shipping_address']['zip']}

This is a TEST order sent from the Email Client CLI system.
"""
    
    # Get recipient email
    laticrete_cs_email = os.getenv('LATICRETE_CS_EMAIL')
    if not laticrete_cs_email:
        logger.error("LATICRETE_CS_EMAIL not configured in .env file")
        return False
    
    # Send email with attachment
    logger.info(f"Sending test email to {laticrete_cs_email}...")
    
    success = email_sender.send_email_with_attachment(
        to_email=laticrete_cs_email,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
        attachment_path=pdf_path,
        attachment_name=f"TEST_Laticrete_Order_{test_order['order_id']}.pdf"
    )
    
    if success:
        logger.info("Test email sent successfully!")
        logger.info(f"Check {laticrete_cs_email} for the test order with PDF attachment")
    else:
        logger.error("Failed to send test email")
    
    # Clean up temporary PDF
    try:
        os.unlink(pdf_path)
        logger.info("Temporary PDF cleaned up")
    except:
        pass
    
    return success


if __name__ == "__main__":
    print("\n" + "="*60)
    print("LATICRETE TEST ORDER SENDER")
    print("="*60)
    print("\nThis will send a TEST Laticrete order with a filled PDF attachment")
    print(f"to the email configured in LATICRETE_CS_EMAIL")
    print("\n" + "="*60 + "\n")
    
    if send_test_laticrete_order():
        print("\n✅ Test order sent successfully!")
    else:
        print("\n❌ Failed to send test order")