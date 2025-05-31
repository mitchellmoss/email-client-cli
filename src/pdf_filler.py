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
            # Read the PDF template
            reader = PdfReader(self.template_path)
            writer = PdfWriter()
            
            # Get the first page (assuming single-page form)
            page = reader.pages[0]
            
            # Try to fill form fields if they exist
            if '/AcroForm' in reader.trailer['/Root']:
                self._fill_acroform_fields(reader, writer, order_data)
            else:
                # If no form fields, overlay text
                self._overlay_text_on_pdf(order_data, output_path)
                return True
            
            # Write the filled PDF
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            logger.info(f"Successfully filled order form: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error filling PDF form: {e}")
            return False
    
    def _fill_acroform_fields(self, reader, writer, order_data):
        """Fill AcroForm fields in PDF."""
        # Clone all pages
        for page in reader.pages:
            writer.add_page(page)
        
        # Get form fields
        if '/AcroForm' in reader.trailer['/Root']:
            writer._root_object.update({
                NameObject("/AcroForm"): reader.trailer["/Root"]["/AcroForm"]
            })
            
            # Map order data to common form field names
            field_mappings = {
                'Date': datetime.now().strftime('%m/%d/%Y'),
                'OrderDate': datetime.now().strftime('%m/%d/%Y'),
                'CustomerName': order_data.get('customer_name', ''),
                'Customer': order_data.get('customer_name', ''),
                'ShipTo': order_data.get('customer_name', ''),
                'ShipToName': order_data.get('customer_name', ''),
                'Address': order_data.get('shipping_address', {}).get('street', ''),
                'ShipAddress': order_data.get('shipping_address', {}).get('street', ''),
                'City': order_data.get('shipping_address', {}).get('city', ''),
                'ShipCity': order_data.get('shipping_address', {}).get('city', ''),
                'State': order_data.get('shipping_address', {}).get('state', ''),
                'ShipState': order_data.get('shipping_address', {}).get('state', ''),
                'Zip': order_data.get('shipping_address', {}).get('zip', ''),
                'ShipZip': order_data.get('shipping_address', {}).get('zip', ''),
                'PONumber': order_data.get('order_id', ''),
                'PO': order_data.get('order_id', ''),
                'OrderNumber': order_data.get('order_id', ''),
            }
            
            # Fill product lines
            products = order_data.get('laticrete_products', [])
            for i, product in enumerate(products[:10]):  # Assume max 10 product lines
                field_mappings.update({
                    f'Item{i+1}': product.get('sku', ''),
                    f'SKU{i+1}': product.get('sku', ''),
                    f'Description{i+1}': product.get('name', ''),
                    f'Qty{i+1}': str(product.get('quantity', '')),
                    f'Quantity{i+1}': str(product.get('quantity', '')),
                    f'Price{i+1}': product.get('price', ''),
                    f'UnitPrice{i+1}': product.get('price', ''),
                })
            
            # Update form fields
            if '/Fields' in reader.trailer['/Root']['/AcroForm']:
                fields = reader.trailer['/Root']['/AcroForm']['/Fields']
                for field in fields:
                    field_obj = field.get_object()
                    if '/T' in field_obj:
                        field_name = field_obj['/T']
                        if field_name in field_mappings:
                            field_obj.update({
                                NameObject("/V"): TextStringObject(field_mappings[field_name])
                            })
    
    def _overlay_text_on_pdf(self, order_data: Dict, output_path: str):
        """Overlay text on PDF when form fields aren't available."""
        # Create a temporary PDF with the text
        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_pdf.close()
        
        # Create canvas for overlay
        c = canvas.Canvas(temp_pdf.name, pagesize=letter)
        
        # Set font
        c.setFont("Helvetica", 10)
        
        # Add order information at approximate positions
        # These positions would need to be adjusted based on the actual form
        y_start = 700
        line_height = 20
        
        # Header info
        c.drawString(450, y_start, datetime.now().strftime('%m/%d/%Y'))
        c.drawString(100, y_start - line_height, f"Order #: {order_data.get('order_id', '')}")
        
        # Customer info
        c.drawString(100, y_start - 3*line_height, order_data.get('customer_name', ''))
        
        # Shipping address
        address = order_data.get('shipping_address', {})
        c.drawString(100, y_start - 4*line_height, address.get('street', ''))
        c.drawString(100, y_start - 5*line_height, 
                    f"{address.get('city', '')}, {address.get('state', '')} {address.get('zip', '')}")
        
        # Product details
        y_products = 450
        products = order_data.get('laticrete_products', [])
        
        c.setFont("Helvetica", 9)
        for i, product in enumerate(products):
            y_pos = y_products - (i * 25)
            c.drawString(50, y_pos, product.get('sku', ''))
            
            # Add verification indicator if needed
            name = product.get('name', '')[:50]  # Truncate long names
            if product.get('needs_verification'):
                name += ' *'
            c.drawString(150, y_pos, name)
            
            c.drawString(400, y_pos, str(product.get('quantity', '')))
            c.drawString(450, y_pos, product.get('price', ''))
        
        # Add verification note if any products need it
        if any(p.get('needs_verification') for p in products):
            c.setFont("Helvetica", 8)
            c.drawString(50, y_products - (len(products) * 25) - 20, 
                        "* Product requires manual price verification")
        
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
        'shipping_address': {
            'street': '123 Test Street',
            'city': 'Test City',
            'state': 'CA',
            'zip': '12345'
        },
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