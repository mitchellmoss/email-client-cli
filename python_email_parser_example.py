#!/usr/bin/env python3
"""
Email Parser Example - Python Implementation
Demonstrates parsing HTML emails and extracting structured data
"""

import re
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
import pandas as pd
from email import policy
from email.parser import BytesParser


class EmailParser:
    """Main email parser class with vendor-specific support"""
    
    def __init__(self):
        self.vendor_configs = {
            'amazon': {
                'identifiers': ['amazon.com', 'Your order has been dispatched'],
                'patterns': {
                    'order_id': r'Order #\s*(\d{3}-\d{7}-\d{7})',
                    'total': r'Order Total:\s*\$([0-9,]+\.\d{2})',
                    'delivery_date': r'Arriving:\s*([A-Za-z]+\s+\d+)',
                    'tracking': r'Tracking ID:\s*(\w+)'
                },
                'selectors': {
                    'items': 'table.shipment tr',
                    'address': 'div.ship-to-address'
                }
            },
            'shopify': {
                'identifiers': ['Order confirmation', 'Thank you for your purchase'],
                'patterns': {
                    'order_id': r'Order\s*#(\d+)',
                    'total': r'Total\s*\$([0-9,]+\.\d{2})',
                    'customer_name': r'Hi\s+([^,]+),',
                    'email': r'[\w\.-]+@[\w\.-]+\.\w+'
                },
                'selectors': {
                    'items': '.order-list__item',
                    'shipping': '.shipping-address'
                }
            },
            'generic': {
                'identifiers': [],
                'patterns': {
                    'order_id': r'Order\s*(?:#|Number|ID)?\s*[:]\s*(\w+)',
                    'total': r'(?:Total|Amount|Grand Total):?\s*\$([0-9,]+\.\d{2})',
                    'date': r'(?:Date|Order Date):?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                    'email': r'[\w\.-]+@[\w\.-]+\.\w+',
                    'phone': r'(?:Phone|Tel):?\s*\+?(\d[\d\s\-\(\)]+)'
                },
                'selectors': {
                    'items': 'table',
                    'any_table': 'table'
                }
            }
        }
    
    def parse_raw_email(self, raw_email: bytes) -> Dict[str, Any]:
        """Parse raw email bytes and extract content"""
        msg = BytesParser(policy=policy.default).parsebytes(raw_email)
        
        result = {
            'headers': {
                'subject': msg.get('subject', ''),
                'from': msg.get('from', ''),
                'to': msg.get('to', ''),
                'date': msg.get('date', '')
            },
            'body': {
                'html': None,
                'text': None
            },
            'attachments': []
        }
        
        # Extract body and attachments
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = part.get_content_disposition()
            
            if content_disposition == 'attachment':
                # Handle attachment
                filename = part.get_filename()
                if filename:
                    result['attachments'].append({
                        'filename': filename,
                        'content_type': content_type,
                        'size': len(part.get_payload(decode=True))
                    })
            elif content_type == 'text/html':
                result['body']['html'] = part.get_payload(decode=True).decode('utf-8', errors='ignore')
            elif content_type == 'text/plain':
                result['body']['text'] = part.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        return result
    
    def detect_vendor(self, content: str) -> str:
        """Detect email vendor based on content"""
        content_lower = content.lower()
        
        for vendor, config in self.vendor_configs.items():
            if vendor == 'generic':
                continue
            for identifier in config['identifiers']:
                if identifier.lower() in content_lower:
                    return vendor
        
        return 'generic'
    
    def extract_data(self, html_content: str) -> Dict[str, Any]:
        """Extract structured data from HTML email"""
        soup = BeautifulSoup(html_content, 'lxml')
        vendor = self.detect_vendor(html_content)
        config = self.vendor_configs[vendor]
        
        result = {
            'vendor': vendor,
            'extracted_data': {},
            'items': [],
            'tables': [],
            'raw_text': soup.get_text()
        }
        
        # Extract using patterns
        for field, pattern in config['patterns'].items():
            match = re.search(pattern, result['raw_text'], re.IGNORECASE | re.MULTILINE)
            if match:
                result['extracted_data'][field] = match.group(1).strip()
        
        # Extract using selectors
        for field, selector in config['selectors'].items():
            elements = soup.select(selector)
            if elements:
                if field == 'items':
                    result['items'] = self._parse_items(elements)
                else:
                    result['extracted_data'][field] = [elem.get_text(strip=True) for elem in elements]
        
        # Extract all tables
        result['tables'] = self._extract_tables(soup)
        
        return result
    
    def _parse_items(self, elements: List) -> List[Dict[str, str]]:
        """Parse order items from HTML elements"""
        items = []
        
        for elem in elements:
            item = {}
            
            # Try to extract common fields
            name_elem = elem.find(class_=re.compile('product|item|name', re.I))
            if name_elem:
                item['name'] = name_elem.get_text(strip=True)
            
            price_elem = elem.find(class_=re.compile('price|cost|amount', re.I))
            if price_elem:
                item['price'] = price_elem.get_text(strip=True)
            
            qty_elem = elem.find(class_=re.compile('qty|quantity|count', re.I))
            if qty_elem:
                item['quantity'] = qty_elem.get_text(strip=True)
            
            # If no specific fields found, just get all text
            if not item:
                item['text'] = elem.get_text(strip=True)
            
            if item:
                items.append(item)
        
        return items
    
    def _extract_tables(self, soup: BeautifulSoup) -> List[pd.DataFrame]:
        """Extract all tables as pandas DataFrames"""
        tables = []
        
        try:
            # Use pandas to read tables
            dfs = pd.read_html(str(soup))
            tables.extend(dfs)
        except:
            # Fallback to manual parsing
            for table in soup.find_all('table'):
                df = self._parse_table_manual(table)
                if df is not None:
                    tables.append(df)
        
        return tables
    
    def _parse_table_manual(self, table) -> Optional[pd.DataFrame]:
        """Manually parse HTML table to DataFrame"""
        rows = []
        headers = []
        
        # Get headers
        header_row = table.find('tr')
        if header_row:
            headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
        
        # Get data
        for row in table.find_all('tr')[1:]:
            cells = [td.get_text(strip=True) for td in row.find_all('td')]
            if cells:
                rows.append(cells)
        
        if rows:
            if headers and len(headers) == len(rows[0]):
                return pd.DataFrame(rows, columns=headers)
            else:
                return pd.DataFrame(rows)
        
        return None
    
    def parse_attachment(self, content: bytes, filename: str) -> Any:
        """Parse email attachment based on file type"""
        if filename.endswith('.csv'):
            return pd.read_csv(pd.io.common.BytesIO(content))
        elif filename.endswith(('.xlsx', '.xls')):
            return pd.read_excel(pd.io.common.BytesIO(content))
        elif filename.endswith('.json'):
            return json.loads(content.decode('utf-8'))
        else:
            return content


class OrderDataExtractor:
    """Specialized class for extracting order-specific data"""
    
    @staticmethod
    def normalize_price(price_str: str) -> float:
        """Convert price string to float"""
        if not price_str:
            return 0.0
        
        # Remove currency symbols and commas
        price_str = re.sub(r'[^\d.]', '', price_str)
        
        try:
            return float(price_str)
        except ValueError:
            return 0.0
    
    @staticmethod
    def parse_date(date_str: str) -> Optional[datetime]:
        """Parse various date formats"""
        date_formats = [
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y-%m-%d',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    @staticmethod
    def extract_address(text: str) -> Dict[str, str]:
        """Extract address components from text"""
        address = {}
        
        # ZIP code pattern
        zip_match = re.search(r'\b\d{5}(?:-\d{4})?\b', text)
        if zip_match:
            address['zip'] = zip_match.group()
        
        # State pattern (US)
        state_match = re.search(r'\b[A-Z]{2}\b', text)
        if state_match:
            address['state'] = state_match.group()
        
        # City (word before state)
        if state_match:
            city_match = re.search(r'(\w+)\s+' + address['state'], text)
            if city_match:
                address['city'] = city_match.group(1)
        
        return address


# Example usage
if __name__ == "__main__":
    # Example: Parse an email file
    parser = EmailParser()
    
    # Read raw email
    with open('sample_order_email.eml', 'rb') as f:
        raw_email = f.read()
    
    # Parse email
    email_data = parser.parse_raw_email(raw_email)
    
    # Extract order data from HTML body
    if email_data['body']['html']:
        order_data = parser.extract_data(email_data['body']['html'])
        
        print(f"Vendor: {order_data['vendor']}")
        print(f"Order ID: {order_data['extracted_data'].get('order_id')}")
        print(f"Total: {order_data['extracted_data'].get('total')}")
        print(f"Items found: {len(order_data['items'])}")
        
        # Process tables
        for i, df in enumerate(order_data['tables']):
            print(f"\nTable {i+1}:")
            print(df.head())