"""Email parser for extracting TileWare orders from Tile Pro Depot emails."""

import re
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
import logging

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class TileProDepotParser:
    """Parser for Tile Pro Depot order emails."""
    
    def __init__(self):
        """Initialize the parser."""
        self.tileware_patterns = [
            r'tileware',
            r'TileWare',
            r'Tile\s*Ware',
            r'TILEWARE'
        ]
        
        self.laticrete_patterns = [
            r'laticrete',
            r'LATICRETE',
            r'Laticrete',
            r'LATI\s*CRETE'
        ]
        
    def contains_tileware_product(self, html_content: str) -> bool:
        """
        Check if the email contains TileWare products.
        
        Args:
            html_content: HTML content of the email
            
        Returns:
            True if TileWare products are found, False otherwise
        """
        if not html_content:
            return False
            
        # Convert to lowercase for case-insensitive search
        content_lower = html_content.lower()
        
        # Quick check for TileWare mention
        if 'tileware' not in content_lower:
            return False
            
        # Parse HTML to look for TileWare in product tables
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for tables that might contain product information
            tables = soup.find_all('table')
            
            for table in tables:
                table_text = table.get_text()
                for pattern in self.tileware_patterns:
                    if re.search(pattern, table_text, re.IGNORECASE):
                        logger.info("Found TileWare product in order")
                        return True
                        
            # Also check in general content if not in tables
            body_text = soup.get_text()
            for pattern in self.tileware_patterns:
                if re.search(pattern, body_text, re.IGNORECASE):
                    # Make sure it's in a product context
                    lines = body_text.split('\n')
                    for i, line in enumerate(lines):
                        if re.search(pattern, line, re.IGNORECASE):
                            # Check surrounding lines for product indicators
                            context_lines = lines[max(0, i-2):min(len(lines), i+3)]
                            context = ' '.join(context_lines)
                            if any(indicator in context.lower() for indicator in 
                                   ['product', 'item', 'quantity', 'price', '$']):
                                logger.info("Found TileWare product in email content")
                                return True
                                
        except Exception as e:
            logger.error(f"Error parsing HTML content: {e}")
            
        return False
    
    def contains_laticrete_product(self, html_content: str) -> bool:
        """
        Check if the email contains Laticrete products.
        
        Args:
            html_content: HTML content of the email
            
        Returns:
            True if Laticrete products are found, False otherwise
        """
        if not html_content:
            return False
            
        # Convert to lowercase for case-insensitive search
        content_lower = html_content.lower()
        
        # Quick check for Laticrete mention
        if 'laticrete' not in content_lower:
            return False
            
        # Parse HTML to look for Laticrete in product tables
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for tables that might contain product information
            tables = soup.find_all('table')
            
            for table in tables:
                table_text = table.get_text()
                for pattern in self.laticrete_patterns:
                    if re.search(pattern, table_text, re.IGNORECASE):
                        logger.info("Found Laticrete product in order")
                        return True
                        
            # Also check in general content if not in tables
            body_text = soup.get_text()
            for pattern in self.laticrete_patterns:
                if re.search(pattern, body_text, re.IGNORECASE):
                    # Make sure it's in a product context
                    lines = body_text.split('\n')
                    for i, line in enumerate(lines):
                        if re.search(pattern, line, re.IGNORECASE):
                            # Check surrounding lines for product indicators
                            context_lines = lines[max(0, i-2):min(len(lines), i+3)]
                            context = ' '.join(context_lines)
                            if any(indicator in context.lower() for indicator in 
                                   ['product', 'item', 'quantity', 'price', '$']):
                                logger.info("Found Laticrete product in email content")
                                return True
                                
        except Exception as e:
            logger.error(f"Error parsing HTML content: {e}")
            
        return False
    
    def get_product_type(self, html_content: str) -> str:
        """
        Determine the type of products in the order.
        
        Args:
            html_content: HTML content of the email
            
        Returns:
            'tileware', 'laticrete', 'both', or 'none'
        """
        has_tileware = self.contains_tileware_product(html_content)
        has_laticrete = self.contains_laticrete_product(html_content)
        
        if has_tileware and has_laticrete:
            return 'both'
        elif has_tileware:
            return 'tileware'
        elif has_laticrete:
            return 'laticrete'
        else:
            return 'none'
    
    def extract_basic_order_info(self, html_content: str) -> Dict[str, Any]:
        """
        Extract basic order information from the email.
        
        Args:
            html_content: HTML content of the email
            
        Returns:
            Dictionary with extracted order information
        """
        order_info = {
            'customer_name': None,
            'order_id': None,
            'products': [],
            'shipping_address': None,
            'billing_address': None,
            'total': None,
            'shipping_method': None
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text()
            
            # Extract customer name
            customer_patterns = [
                r"You've received the following order from ([^:]+):",
                r"You've received a new order from ([^:]+):",
                r"Woo! You've received a new order from ([^:]+):"
            ]
            for pattern in customer_patterns:
                customer_match = re.search(pattern, text)
                if customer_match:
                    order_info['customer_name'] = customer_match.group(1).strip()
                    break
                
            # Extract order ID
            order_id_patterns = [
                r'\[Order #(\d+)\]',
                r'Order #(\d+)',
                r'#(\d+) \(.*\d{4}\)'  # Matches "#43333 (June 13, 2025)"
            ]
            for pattern in order_id_patterns:
                order_id_match = re.search(pattern, text)
                if order_id_match:
                    order_info['order_id'] = order_id_match.group(1)
                    break
                
            # Extract shipping method
            shipping_patterns = [
                r'Shipping:\s*([^\n]+)',
                r'Shipping method:\s*([^\n]+)',
                r'Ship via:\s*([^\n]+)'
            ]
            for pattern in shipping_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    order_info['shipping_method'] = match.group(1).strip()
                    break
                    
            # Extract total
            total_match = re.search(r'Total:\s*\$?([\d,]+\.?\d*)', text, re.IGNORECASE)
            if total_match:
                order_info['total'] = total_match.group(1).replace(',', '')
                
            # Extract addresses
            order_info['shipping_address'] = self._extract_address(text, 'shipping')
            order_info['billing_address'] = self._extract_address(text, 'billing')
            
            # Extract products (basic extraction, Claude will do detailed parsing)
            order_info['products'] = self._extract_products(soup)
            
        except Exception as e:
            logger.error(f"Error extracting basic order info: {e}")
            
        return order_info
    
    def _extract_address(self, text: str, address_type: str) -> Optional[str]:
        """Extract billing or shipping address from text."""
        patterns = [
            rf'{address_type}\s+address:?\s*([^$]+?)(?:Shipping|Billing|Payment|Email|Phone|$)',
            rf'{address_type}:?\s*([^$]+?)(?:Shipping|Billing|Payment|Email|Phone|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                address = match.group(1).strip()
                # Clean up the address
                address_lines = [line.strip() for line in address.split('\n') 
                               if line.strip() and not any(skip in line.lower() 
                                                          for skip in ['email:', 'phone:', 'method:'])]
                if address_lines:
                    return '\n'.join(address_lines[:4])  # Limit to 4 lines
                    
        return None
    
    def _extract_products(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract product information from HTML."""
        products = []
        
        # Look for product tables
        tables = soup.find_all('table')
        
        for table in tables:
            # Check if this looks like a product table
            headers = [th.get_text().strip().lower() for th in table.find_all('th')]
            
            # Also check if table contains product-like content even without headers
            table_text = table.get_text()
            has_product_content = any(pattern in table_text for pattern in ['TileWare', 'Laticrete', '$', '×'])
            
            if any(header in headers for header in ['product', 'item', 'description']) or has_product_content:
                rows = table.find_all('tr')
                # Skip header row only if headers exist
                if headers:
                    rows = rows[1:]
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:  # At least 2 cells
                        # Find the cell containing the product name
                        product_cell_idx = -1
                        product_text = ""
                        
                        for idx, cell in enumerate(cells):
                            cell_text = cell.get_text().strip()
                            # Check if this cell contains TileWare or Laticrete
                            if any(re.search(pattern, cell_text, re.IGNORECASE) 
                                   for pattern in self.tileware_patterns + self.laticrete_patterns):
                                product_cell_idx = idx
                                product_text = cell_text
                                break
                        
                        if product_cell_idx >= 0:
                            # Check if this is a TileWare or Laticrete product
                            is_tileware = any(re.search(pattern, product_text, re.IGNORECASE) 
                                            for pattern in self.tileware_patterns)
                            is_laticrete = any(re.search(pattern, product_text, re.IGNORECASE) 
                                             for pattern in self.laticrete_patterns)
                            
                            # Extract quantity and price from remaining cells
                            quantity = '1'
                            price = ''
                            
                            for idx, cell in enumerate(cells):
                                if idx != product_cell_idx:
                                    cell_text = cell.get_text().strip()
                                    # Check for quantity pattern (×N or xN)
                                    if re.match(r'[×x]\d+', cell_text):
                                        quantity = cell_text.replace('×', '').replace('x', '').strip()
                                    # Check for price pattern
                                    elif '$' in cell_text:
                                        price = cell_text
                            
                            product = {
                                'name': product_text,
                                'quantity': quantity,
                                'price': price,
                                'type': 'tileware' if is_tileware else 'laticrete'
                            }
                            products.append(product)
                            
        return products
    
    def validate_order_data(self, order_data: Dict[str, Any]) -> bool:
        """
        Validate that the extracted order data has minimum required fields.
        
        Args:
            order_data: Extracted order data
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['customer_name', 'products']
        
        for field in required_fields:
            if not order_data.get(field):
                logger.warning(f"Missing required field: {field}")
                return False
                
        # Check that we have at least one product
        if not order_data['products'] or len(order_data['products']) == 0:
            logger.warning("No products found in order")
            return False
            
        return True