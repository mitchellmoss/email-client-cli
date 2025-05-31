"""
PDF form filler for Laticrete order forms.
Fills out PDF order forms with order data.
"""

import os
from typing import Dict, List
from pathlib import Path
import logging
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import tempfile
from datetime import datetime
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class PDFOrderFormFiller:
    """Fills out Laticrete PDF order forms with order data."""
    
    def __init__(self, template_path: str = "resources/laticrete/lat_blank_orderform.pdf"):
        """Initialize with path to blank order form template."""
        self.template_path = Path(template_path)
        if not self.template_path.exists():
            raise FileNotFoundError(f"PDF template not found at {self.template_path}")
    
    def fill_order_form(self, order_data: Dict, output_path: str) -> bool:
        """
        Fill out PDF order form with order data.
        
        Args:
            order_data: Dictionary containing order information
            output_path: Path to save filled PDF
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Try to fill form fields first (preferred method)
            if self._fill_form_fields(order_data, output_path):
                logger.info(f"Successfully filled order form using form fields: {output_path}")
                return True
            else:
                # Fall back to overlay method if form fields don't work
                logger.info("Form field filling failed, using overlay method")
                self._overlay_text_on_pdf(order_data, output_path)
                
                # Verify the file was created and has content
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    logger.info(f"Successfully filled order form using overlay: {output_path} (size: {os.path.getsize(output_path)} bytes)")
                    return True
                else:
                    logger.error(f"Failed to create filled PDF at {output_path}")
                    return False
            
        except Exception as e:
            logger.error(f"Error filling PDF form: {e}")
            return False
    
    def _fill_form_fields(self, order_data: Dict, output_path: str) -> bool:
        """
        Fill PDF form using AcroForm fields.
        
        Returns:
            True if successful, False if should fall back to overlay method
        """
        try:
            reader = PdfReader(self.template_path)
            writer = PdfWriter()
            
            # Clone all pages
            for page in reader.pages:
                writer.add_page(page)
            
            # Check for AcroForm
            if '/AcroForm' not in reader.trailer.get('/Root', {}):
                logger.debug("No AcroForm found in PDF")
                return False
            
            # Copy the AcroForm
            writer._root_object.update({
                NameObject("/AcroForm"): reader.trailer["/Root"]["/AcroForm"]
            })
            
            # Prepare field data based on actual field names from the PDF
            field_data = {
                # Date
                'DATE': datetime.now().strftime('%m/%d/%Y'),
                
                # Ship to address (S 1-4 fields)
                'S 1': order_data.get('customer_name', ''),
                'S 2': order_data.get('shipping_address', {}).get('street', ''),
                'S 3': f"{order_data.get('shipping_address', {}).get('city', '')}, {order_data.get('shipping_address', {}).get('state', '')} {order_data.get('shipping_address', {}).get('zip', '')}",
                'S 4': '',  # Additional address line if needed
                
                # Contact info
                'Contact name': order_data.get('customer_name', ''),
                'Phone': order_data.get('phone', ''),
                
                # Special instructions
                'Special Instructions 1': f"Tile Pro Depot Order #{order_data.get('order_id', '')}",
                'Special Instructions 2': f"Ship via: {order_data.get('shipping_method', 'Standard')}",
            }
            
            # Add product lines
            products = order_data.get('laticrete_products', [])
            for i, product in enumerate(products[:13]):  # Form has 13 product rows
                row_num = i + 1
                field_data.update({
                    f'Quantity OrderedRow{row_num}': str(product.get('quantity', '')),
                    f'DescriptionRow{row_num}': product.get('name', ''),
                    f'Item NumberRow{row_num}': product.get('sku', ''),
                    f'Unit PriceRow{row_num}': product.get('price', ''),
                    f'AmountRow{row_num}': self._calculate_amount(product.get('quantity', 0), product.get('price', '0'))
                })
            
            # Update form fields
            if '/Fields' not in reader.trailer['/Root']['/AcroForm']:
                logger.debug("No fields found in AcroForm")
                return False
            
            fields = reader.trailer['/Root']['/AcroForm']['/Fields']
            filled_count = 0
            
            for field_ref in fields:
                try:
                    field = field_ref.get_object()
                    if '/T' in field:
                        field_name = str(field['/T'])
                        if field_name in field_data:
                            # Update the field value
                            field.update({
                                NameObject("/V"): TextStringObject(field_data[field_name])
                            })
                            filled_count += 1
                            logger.debug(f"Filled field: {field_name}")
                except Exception as e:
                    logger.debug(f"Error filling field: {e}")
            
            if filled_count == 0:
                logger.debug("No fields were filled")
                return False
            
            logger.info(f"Filled {filled_count} form fields")
            
            # Write the output
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            return True
            
        except Exception as e:
            logger.debug(f"Form field filling failed: {e}")
            return False
    
    def _calculate_amount(self, quantity, unit_price):
        """Calculate total amount from quantity and unit price."""
        try:
            # Remove $ and commas from price
            price_str = str(unit_price).replace('$', '').replace(',', '')
            price = float(price_str)
            total = quantity * price
            return f"${total:,.2f}"
        except:
            return ""
    
    def _overlay_text_on_pdf(self, order_data: Dict, output_path: str):
        """Overlay text on PDF when form fields aren't available."""
        # Create a temporary PDF with the text
        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_pdf.close()
        
        # Create canvas for overlay
        c = canvas.Canvas(temp_pdf.name, pagesize=letter)
        
        # Set font
        c.setFont("Helvetica", 10)
        
        # Add order information at specific positions based on the form layout
        # Date (top right)
        c.drawString(450, 675, datetime.now().strftime('%m/%d/%Y'))
        
        # Ship to address (right side, under "SHIP" section)
        c.drawString(350, 625, order_data.get('customer_name', ''))
        c.drawString(350, 610, order_data.get('shipping_address', {}).get('street', ''))
        c.drawString(350, 595, f"{order_data.get('shipping_address', {}).get('city', '')}, {order_data.get('shipping_address', {}).get('state', '')} {order_data.get('shipping_address', {}).get('zip', '')}")
        
        # Contact info
        c.drawString(420, 545, order_data.get('customer_name', ''))
        c.drawString(420, 530, order_data.get('phone', ''))
        
        # Product details - starting positions based on form
        y_start = 420  # First product row
        row_height = 15.5  # Space between rows
        
        products = order_data.get('laticrete_products', [])
        
        c.setFont("Helvetica", 9)
        for i, product in enumerate(products[:13]):  # Max 13 rows on form
            y_pos = y_start - (i * row_height)
            
            # Quantity
            c.drawString(45, y_pos, str(product.get('quantity', '')))
            
            # Description
            name = product.get('name', '')[:40]  # Truncate long names
            if product.get('needs_verification'):
                name += ' *'
            c.drawString(90, y_pos, name)
            
            # Item Number (SKU)
            c.drawString(330, y_pos, product.get('sku', ''))
            
            # Unit Price
            c.drawString(420, y_pos, product.get('price', ''))
            
            # Amount
            amount = self._calculate_amount(product.get('quantity', 0), product.get('price', '0'))
            c.drawString(490, y_pos, amount)
        
        # Special instructions
        c.setFont("Helvetica", 8)
        c.drawString(170, 195, f"Tile Pro Depot Order #{order_data.get('order_id', '')}")
        c.drawString(170, 180, f"Ship via: {order_data.get('shipping_method', 'Standard')}")
        
        # Add verification note if any products need it
        if any(p.get('needs_verification') for p in products):
            c.drawString(170, 165, "* Product requires manual price verification")
        
        # Save overlay
        c.save()
        
        # Merge with original PDF
        try:
            # Read both PDFs
            original = PdfReader(self.template_path)
            overlay = PdfReader(temp_pdf.name)
            writer = PdfWriter()
            
            # Merge first page
            page = original.pages[0]
            page.merge_page(overlay.pages[0])
            writer.add_page(page)
            
            # Add remaining pages if any
            for i in range(1, len(original.pages)):
                writer.add_page(original.pages[i])
            
            # Write output
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
                
        finally:
            # Clean up temp file
            os.unlink(temp_pdf.name)


if __name__ == "__main__":
    # Test the PDF filler
    filler = PDFOrderFormFiller()
    
    # Test data
    test_order = {
        'order_id': 'TEST123',
        'customer_name': 'Test Customer',
        'phone': '555-123-4567',
        'shipping_address': {
            'street': '123 Test Street',
            'city': 'Test City',
            'state': 'CA',
            'zip': '12345'
        },
        'shipping_method': 'UPS Ground',
        'laticrete_products': [
            {
                'name': 'HYDRO BAN Sheet Membrane',
                'sku': 'HB-SHEET-5',
                'quantity': 2,
                'price': '$125.00'
            },
            {
                'name': '254 Platinum Adhesive',
                'sku': '254-50',
                'quantity': 5,
                'price': '$45.00'
            }
        ]
    }
    
    output_path = "test_filled_order.pdf"
    if filler.fill_order_form(test_order, output_path):
        print(f"Test order form created: {output_path}")
    else:
        print("Failed to create test order form")