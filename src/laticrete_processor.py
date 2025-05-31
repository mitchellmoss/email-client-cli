"""
Laticrete order processor.
Handles Laticrete product orders: extracts data, matches prices, fills PDF, and sends email.
"""

import os
from typing import Dict, List, Optional
from pathlib import Path
import tempfile
import logging
from datetime import datetime
from src.price_list_reader import PriceListReader
from src.pdf_filler import PDFOrderFormFiller
from src.email_sender import EmailSender
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class LatricreteProcessor:
    """Processes Laticrete orders end-to-end."""
    
    def __init__(self):
        """Initialize processor components."""
        self.price_reader = PriceListReader()
        self.pdf_filler = PDFOrderFormFiller()
        # Initialize email sender with SMTP credentials
        self.email_sender = EmailSender(
            smtp_server=os.getenv('SMTP_SERVER'),
            smtp_port=int(os.getenv('SMTP_PORT', 587)),
            username=os.getenv('SMTP_USERNAME'),
            password=os.getenv('SMTP_PASSWORD'),
            signature_html=os.getenv('EMAIL_SIGNATURE_TEXT')
        )
        self.laticrete_cs_email = os.getenv('LATICRETE_CS_EMAIL')
        
        if not self.laticrete_cs_email:
            logger.warning("LATICRETE_CS_EMAIL not set in environment")
    
    def process_order(self, order_data: Dict) -> bool:
        """
        Process a Laticrete order: match prices, fill PDF, send email.
        
        Args:
            order_data: Order data from Claude processor
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Enrich products with price list data
            enriched_order = self._enrich_with_prices(order_data)
            
            # Generate filled PDF
            pdf_path = self._generate_order_pdf(enriched_order)
            if not pdf_path:
                logger.error("Failed to generate PDF")
                return False
            
            # Send email with PDF attachment
            success = self._send_order_email(enriched_order, pdf_path)
            
            # Clean up temp file
            if pdf_path and os.path.exists(pdf_path):
                os.unlink(pdf_path)
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing Laticrete order: {e}")
            return False
    
    def _enrich_with_prices(self, order_data: Dict) -> Dict:
        """Add price list information to products."""
        enriched_order = order_data.copy()
        enriched_products = []
        
        for product in order_data.get('laticrete_products', []):
            enriched_product = product.copy()
            
            # Clean product name for better matching
            product_name = product.get('name', '')
            # Remove "Laticrete" prefix if present for cleaner matching
            if product_name.lower().startswith('laticrete '):
                product_name = product_name[10:]  # Remove "Laticrete " prefix
            
            # Look up product in price list
            price_info = self.price_reader.find_product(
                product_name,
                product.get('sku', '')
            )
            
            if price_info:
                # Add/update with price list data
                enriched_product['list_price'] = price_info.get('price', product.get('price', ''))
                enriched_product['unit'] = price_info.get('unit', 'EA')
                enriched_product['category'] = price_info.get('category', '')
                
                # Use price list SKU if original is missing
                if not enriched_product.get('sku') and price_info.get('sku'):
                    enriched_product['sku'] = price_info['sku']
                    
                logger.info(f"Matched product: {product.get('name')} -> {price_info.get('sku')}")
            else:
                logger.warning(f"Product not found in price list: {product_name} (original: {product.get('name')})")
                
                # Use original price/info if available
                if not enriched_product.get('sku') and product.get('sku'):
                    # Clean up SKU format
                    enriched_product['sku'] = product.get('sku', '').replace('#', '').strip()
                
                # Add note that this needs manual verification
                enriched_product['needs_verification'] = True
                enriched_product['verification_note'] = 'Product not found in price list - please verify pricing'
            
            enriched_products.append(enriched_product)
        
        enriched_order['laticrete_products'] = enriched_products
        
        # Log matching summary
        total_products = len(enriched_products)
        matched_products = sum(1 for p in enriched_products if not p.get('needs_verification', False))
        unmatched_products = total_products - matched_products
        
        logger.info(f"Price matching summary: {matched_products}/{total_products} products matched")
        if unmatched_products > 0:
            logger.warning(f"{unmatched_products} products need manual price verification")
        
        return enriched_order
    
    def _generate_order_pdf(self, order_data: Dict) -> Optional[str]:
        """Generate filled PDF order form."""
        try:
            # Create temp file for PDF
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f'_laticrete_order_{order_data.get("order_id", "unknown")}.pdf'
            )
            temp_file.close()
            
            # Fill the PDF
            if self.pdf_filler.fill_order_form(order_data, temp_file.name):
                logger.info(f"Generated PDF: {temp_file.name}")
                return temp_file.name
            else:
                os.unlink(temp_file.name)
                return None
                
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            return None
    
    def _send_order_email(self, order_data: Dict, pdf_path: str) -> bool:
        """Send order email with PDF attachment."""
        if not self.laticrete_cs_email:
            logger.error("LATICRETE_CS_EMAIL not configured")
            return False
        
        # Format email content
        subject = f"Laticrete Order #{order_data.get('order_id', 'Unknown')} - {order_data.get('customer_name', 'Unknown Customer')}"
        
        # HTML content
        html_content = f"""
        <html>
        <body>
            <h2>New Laticrete Order</h2>
            <p>Please process the attached Laticrete order form.</p>
            
            <h3>Order Summary:</h3>
            <ul>
                <li><strong>Order ID:</strong> {order_data.get('order_id', 'N/A')}</li>
                <li><strong>Customer:</strong> {order_data.get('customer_name', 'N/A')}</li>
                <li><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}</li>
                <li><strong>Total Items:</strong> {len(order_data.get('laticrete_products', []))}</li>
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
        
        for product in order_data.get('laticrete_products', []):
            needs_verification = product.get('needs_verification', False)
            html_content += f"""
                <tr>
                    <td>{product.get('sku', 'N/A')}</td>
                    <td>{product.get('name', 'N/A')}{'<span style="color: red;"> *</span>' if needs_verification else ''}</td>
                    <td>{product.get('quantity', 'N/A')}</td>
                    <td>{product.get('list_price', product.get('price', 'N/A'))}{'<span style="color: red;"> *</span>' if needs_verification else ''}</td>
                </tr>
            """
        
        html_content += """
            </table>
        """
        
        # Add verification note if needed
        if any(p.get('needs_verification') for p in order_data.get('laticrete_products', [])):
            html_content += """
            <p style="color: red; font-style: italic;">* These items were not found in the current price list. Please verify pricing before processing.</p>
            """
        
        html_content += """
            <h3>Shipping Address:</h3>
            <p>
        """
        
        address = order_data.get('shipping_address', {})
        html_content += f"""
                {order_data.get('customer_name', 'N/A')}<br>
                {address.get('street', 'N/A')}<br>
                {address.get('city', 'N/A')}, {address.get('state', 'N/A')} {address.get('zip', 'N/A')}<br>
            </p>
            
            <p><em>This order was automatically processed from Tile Pro Depot order confirmation.</em></p>
        </body>
        </html>
        """
        
        # Plain text content
        text_content = f"""
New Laticrete Order

Please process the attached Laticrete order form.

Order Summary:
- Order ID: {order_data.get('order_id', 'N/A')}
- Customer: {order_data.get('customer_name', 'N/A')}
- Date: {datetime.now().strftime('%B %d, %Y')}
- Total Items: {len(order_data.get('laticrete_products', []))}

Products:
"""
        
        for product in order_data.get('laticrete_products', []):
            verification = ' [NEEDS PRICE VERIFICATION]' if product.get('needs_verification') else ''
            text_content += f"- {product.get('sku', 'N/A')} | {product.get('name', 'N/A')}{verification} | Qty: {product.get('quantity', 'N/A')} | {product.get('list_price', product.get('price', 'N/A'))}\n"
        
        text_content += f"""
Shipping Address:
{order_data.get('customer_name', 'N/A')}
{address.get('street', 'N/A')}
{address.get('city', 'N/A')}, {address.get('state', 'N/A')} {address.get('zip', 'N/A')}

This order was automatically processed from Tile Pro Depot order confirmation.
"""
        
        # Send email with attachment
        return self.email_sender.send_email_with_attachment(
            to_email=self.laticrete_cs_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            attachment_path=pdf_path,
            attachment_name=f"Laticrete_Order_{order_data.get('order_id', 'unknown')}.pdf"
        )