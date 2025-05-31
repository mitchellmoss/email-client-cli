"""
PDF form filler for Laticrete order forms.
Fills out PDF order forms with order data using multiple methods for maximum compatibility.
"""

import os
from typing import Dict, List, Optional
from pathlib import Path
import logging
from datetime import datetime
import tempfile

# Try to import all available PDF libraries
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pdfrw
    PDFRW_AVAILABLE = True
except ImportError:
    PDFRW_AVAILABLE = False

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    NameObject, TextStringObject, BooleanObject,
    DictionaryObject, ArrayObject, NumberObject
)
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class PDFOrderFormFiller:
    """Fills out Laticrete PDF order forms with order data using multiple methods."""
    
    def __init__(self, template_path: str = None):
        """Initialize with path to blank order form template."""
        if template_path is None:
            # Use absolute path based on project structure
            from pathlib import Path
            # Try to find the project root by looking for the main.py file
            current = Path(__file__).parent
            while current != current.parent:
                if (current / "main.py").exists() and (current / "resources" / "laticrete").exists():
                    template_path = str(current / "resources" / "laticrete" / "lat_blank_orderform.pdf")
                    break
                current = current.parent
            else:
                # Fallback to relative path
                template_path = "resources/laticrete/lat_blank_orderform.pdf"
        
        self.template_path = Path(template_path)
        if not self.template_path.exists():
            raise FileNotFoundError(f"PDF template not found at {self.template_path}")
    
    def fill_order_form(self, order_data: Dict, output_path: str, method: str = "auto") -> bool:
        """
        Fill out PDF order form with order data using the best available method.
        
        Args:
            order_data: Dictionary containing order information
            output_path: Path to save filled PDF
            method: Method to use - "auto", "pymupdf", "pdfrw", "pypdf", or "overlay"
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if method == "auto":
                # Try methods in order of reliability
                methods = []
                if PYMUPDF_AVAILABLE:
                    methods.append(("pymupdf", self._fill_with_pymupdf))
                if PDFRW_AVAILABLE:
                    methods.append(("pdfrw", self._fill_with_pdfrw))
                methods.extend([
                    ("pypdf", self._fill_with_pypdf_improved),
                    ("overlay", self._overlay_text_on_pdf)
                ])
                
                for method_name, method_func in methods:
                    logger.info(f"Trying {method_name} method for PDF filling")
                    try:
                        if method_func(order_data, output_path):
                            logger.info(f"Successfully filled PDF with {method_name} method")
                            return True
                    except Exception as e:
                        logger.debug(f"{method_name} method failed: {e}")
                
                logger.error("All PDF filling methods failed")
                return False
            
            else:
                # Use specific method
                method_map = {
                    "pymupdf": self._fill_with_pymupdf,
                    "pdfrw": self._fill_with_pdfrw,
                    "pypdf": self._fill_with_pypdf_improved,
                    "overlay": self._overlay_text_on_pdf
                }
                
                if method not in method_map:
                    logger.error(f"Unknown method: {method}")
                    return False
                
                return method_map[method](order_data, output_path)
            
        except Exception as e:
            logger.error(f"Error filling PDF form: {e}")
            return False
    
    def _fill_with_pymupdf(self, order_data: Dict, output_path: str) -> bool:
        """Fill PDF using PyMuPDF which has excellent form field support."""
        if not PYMUPDF_AVAILABLE:
            return False
        
        try:
            # Open the PDF
            doc = fitz.open(str(self.template_path))
            
            # Get the first page
            page = doc[0]
            
            # Get form fields
            widgets = page.widgets()
            if not widgets:
                logger.debug("No form fields found with PyMuPDF")
                doc.close()
                return False
            
            # Prepare field mappings
            field_mappings = self._prepare_field_mappings(order_data)
            
            # Fill the fields
            filled_count = 0
            for widget in widgets:
                field_name = widget.field_name
                if field_name in field_mappings:
                    value = field_mappings[field_name]
                    widget.field_value = value
                    widget.update()
                    filled_count += 1
                    logger.debug(f"Filled field: {field_name} = {value}")
            
            if filled_count == 0:
                logger.debug("No fields were filled")
                doc.close()
                return False
            
            logger.info(f"Filled {filled_count} form fields with PyMuPDF")
            
            # Save the document
            doc.save(output_path)
            doc.close()
            
            # Verify file was created
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"Successfully created PDF with PyMuPDF: {output_path}")
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"PyMuPDF method failed: {e}")
            return False
    
    def _fill_with_pdfrw(self, order_data: Dict, output_path: str) -> bool:
        """Fill PDF using pdfrw library."""
        if not PDFRW_AVAILABLE:
            return False
            
        try:
            # Load the PDF
            pdf = pdfrw.PdfReader(str(self.template_path))
            
            # Get the form fields
            if not pdf.Root.AcroForm or not pdf.Root.AcroForm.Fields:
                logger.debug("No form fields found in PDF")
                return False
            
            fields = pdf.Root.AcroForm.Fields
            
            # Prepare field mappings
            field_mappings = self._prepare_field_mappings(order_data)
            
            # Fill the fields
            filled_count = 0
            for field in fields:
                field_name = field.T
                if field_name and field_name[1:-1] in field_mappings:
                    clean_name = field_name[1:-1]
                    value = field_mappings[clean_name]
                    
                    # Set the field value
                    field.V = pdfrw.objects.pdfstring.PdfString.encode(value)
                    
                    # Clear existing appearance to force regeneration
                    field.AP = None
                    filled_count += 1
                    logger.debug(f"Filled field: {clean_name} = {value}")
            
            if filled_count == 0:
                logger.debug("No fields were filled")
                return False
            
            logger.info(f"Filled {filled_count} form fields with pdfrw")
            
            # Set NeedAppearances to ensure fields are rendered
            pdf.Root.AcroForm.NeedAppearances = pdfrw.PdfObject('true')
            
            # Write the output
            pdfrw.PdfWriter().write(output_path, pdf)
            
            # Verify file was created
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"Successfully created PDF with pdfrw: {output_path}")
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"pdfrw method failed: {e}")
            return False
    
    def _fill_with_pypdf_improved(self, order_data: Dict, output_path: str) -> bool:
        """Fill PDF using improved pypdf approach."""
        try:
            reader = PdfReader(self.template_path)
            writer = PdfWriter()
            
            # Clone the entire document
            writer.clone_reader_document_root(reader)
            
            # Check for AcroForm
            if '/AcroForm' not in writer._root_object:
                logger.debug("No AcroForm found in PDF")
                return False
            
            # Set NeedAppearances to true
            writer._root_object['/AcroForm'][NameObject('/NeedAppearances')] = BooleanObject(True)
            
            # Prepare field mappings
            field_mappings = self._prepare_field_mappings(order_data)
            
            # Get all fields
            fields = writer._root_object['/AcroForm'].get('/Fields', [])
            filled_count = 0
            
            for field_ref in fields:
                try:
                    field_obj = field_ref.get_object()
                    
                    if '/T' in field_obj:
                        field_name = str(field_obj['/T'])
                        
                        if field_name in field_mappings:
                            value = field_mappings[field_name]
                            
                            # Update the field value
                            field_obj.update({
                                NameObject("/V"): TextStringObject(value)
                            })
                            
                            # Remove existing appearance
                            if '/AP' in field_obj:
                                del field_obj['/AP']
                            
                            # Clear read-only flag if present
                            if '/Ff' in field_obj:
                                flags = field_obj['/Ff']
                                field_obj[NameObject('/Ff')] = NumberObject(flags & ~1)
                            
                            filled_count += 1
                            logger.debug(f"Filled field: {field_name} = {value}")
                            
                except Exception as e:
                    logger.debug(f"Error filling field: {e}")
            
            if filled_count == 0:
                logger.debug("No fields were filled")
                return False
            
            logger.info(f"Filled {filled_count} form fields with pypdf")
            
            # Write the output
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            # Verify file was created
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"Successfully created PDF with pypdf: {output_path}")
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"pypdf method failed: {e}")
            return False
    
    def _prepare_field_mappings(self, order_data: Dict) -> Dict[str, str]:
        """Prepare the field mappings from order data."""
        # Basic field mappings
        field_mappings = {
            'DATE': datetime.now().strftime('%m/%d/%Y'),
            'O': order_data.get('order_id', ''),
            'S 1': order_data.get('customer_name', ''),
            'S 2': order_data.get('shipping_address', {}).get('street', ''),
            'S 3': f"{order_data.get('shipping_address', {}).get('city', '')}, {order_data.get('shipping_address', {}).get('state', '')} {order_data.get('shipping_address', {}).get('zip', '')}",
            'S 4': '',
            'Contact name': order_data.get('customer_name', ''),
            'Phone': order_data.get('phone', ''),
            'Special Instructions 1': f"Tile Pro Depot Order #{order_data.get('order_id', '')}",
            'Special Instructions 2': f"Ship via: {order_data.get('shipping_method', 'Standard')}",
        }
        
        # Add product lines
        products = order_data.get('laticrete_products', [])
        for i, product in enumerate(products[:13]):  # Form has 13 product rows
            row_num = i + 1
            field_mappings.update({
                f'Quantity OrderedRow{row_num}': str(product.get('quantity', '')),
                f'DescriptionRow{row_num}': product.get('name', ''),
                f'Item NumberRow{row_num}': product.get('sku', ''),
                f'Unit PriceRow{row_num}': product.get('list_price', product.get('price', '')),
                f'AmountRow{row_num}': self._calculate_amount(product.get('quantity', 0), product.get('list_price', product.get('price', '0')))
            })
        
        return field_mappings
    
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
    
    def _overlay_text_on_pdf(self, order_data: Dict, output_path: str) -> bool:
        """Overlay text on PDF as a fallback method."""
        try:
            # Create a temporary PDF with the text
            temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_pdf.close()
            
            # Create canvas for overlay
            c = canvas.Canvas(temp_pdf.name, pagesize=letter)
            
            # Set font
            c.setFont("Helvetica", 10)
            
            # Based on the screenshot, adjust positions:
            # Date (top right area - after "DATE" label)
            c.drawString(520, 645, datetime.now().strftime('%m/%d/%Y'))
            
            # Order number (left side - after "Order #:")
            c.drawString(180, 625, order_data.get('order_id', ''))
            
            # Bill To section (left side)
            c.drawString(140, 585, order_data.get('customer_name', ''))
            c.drawString(100, 565, order_data.get('customer_name', ''))  # Company name
            c.drawString(100, 550, order_data.get('shipping_address', {}).get('street', ''))
            c.drawString(100, 535, f"{order_data.get('shipping_address', {}).get('city', '')}, {order_data.get('shipping_address', {}).get('state', '')} {order_data.get('shipping_address', {}).get('zip', '')}")
            
            # Phone number (left side - after "Tel. No.")
            c.drawString(150, 510, order_data.get('phone', ''))
            
            # Ship To section (right side)
            c.drawString(365, 585, order_data.get('customer_name', ''))
            c.drawString(365, 565, order_data.get('shipping_address', {}).get('street', ''))
            c.drawString(365, 550, f"{order_data.get('shipping_address', {}).get('city', '')}, {order_data.get('shipping_address', {}).get('state', '')} {order_data.get('shipping_address', {}).get('zip', '')}")
            
            # Contact name and phone (right bottom section)
            c.drawString(450, 510, order_data.get('customer_name', ''))
            c.drawString(470, 495, order_data.get('phone', ''))
            
            # Product details table
            y_start = 425  # First product row
            row_height = 26.5  # Space between rows based on form
            
            products = order_data.get('laticrete_products', [])
            
            c.setFont("Helvetica", 9)
            for i, product in enumerate(products[:13]):  # Max 13 rows on form
                y_pos = y_start - (i * row_height)
                
                # Quantity (left column)
                c.drawString(65, y_pos, str(product.get('quantity', '')))
                
                # Description (wide column)
                name = product.get('name', '')[:45]  # Truncate long names
                if product.get('needs_verification'):
                    name += ' *'
                c.drawString(170, y_pos, name)
                
                # Item Number/SKU (middle column)
                c.drawString(450, y_pos, product.get('sku', ''))
                
                # Unit Price (right columns)
                c.drawString(520, y_pos, product.get('list_price', product.get('price', '')))
                
                # Amount (far right - removed as it exceeds page width)
                # amount = self._calculate_amount(product.get('quantity', 0), product.get('price', '0'))
                # c.drawString(550, y_pos, amount)
            
            # Special instructions (lower on page)
            c.setFont("Helvetica", 8)
            c.drawString(100, 90, f"Tile Pro Depot Order #{order_data.get('order_id', '')}")
            c.drawString(100, 75, f"Ship via: {order_data.get('shipping_method', 'Standard')}")
            
            # Add verification note if any products need it
            if any(p.get('needs_verification') for p in products):
                c.drawString(100, 60, "* Product requires manual price verification")
            
            # Requested by / Email fields at bottom
            c.drawString(210, 30, "Tile Pro Depot")
            c.drawString(510, 30, "orders@tileprodepot.com")
            
            # Save overlay
            c.save()
            
            # Merge with original PDF
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
            
            logger.info(f"Successfully created PDF with overlay method: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Overlay method failed: {e}")
            return False
        finally:
            # Clean up temp file
            if 'temp_pdf' in locals():
                try:
                    os.unlink(temp_pdf.name)
                except:
                    pass


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