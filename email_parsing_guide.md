# Email Parsing Guide: Libraries and Best Practices

## Overview
This guide covers the best libraries and techniques for parsing HTML emails, extracting structured data, and handling attachments in both Python and Node.js.

## Python Libraries

### 1. **Core Email Parsing Libraries**

#### email (Built-in)
The standard Python library for parsing email messages.
```python
import email
from email import policy
from email.parser import BytesParser

# Parse raw email
msg = BytesParser(policy=policy.default).parsebytes(raw_email_bytes)

# Access email parts
subject = msg['subject']
from_addr = msg['from']
body = msg.get_body(preferencelist=('html', 'plain'))
```

#### mail-parser
A more advanced email parser with better attachment handling.
```python
# Install: pip install mail-parser
import mailparser

# Parse email
mail = mailparser.parse_from_bytes(raw_email_bytes)
# or
mail = mailparser.parse_from_file(email_file_path)

# Access parsed data
print(mail.subject)
print(mail.from_)
print(mail.to)
print(mail.attachments)
print(mail.body)
```

### 2. **HTML Parsing Libraries**

#### BeautifulSoup4
The most popular HTML parsing library for Python.
```python
# Install: pip install beautifulsoup4 lxml
from bs4 import BeautifulSoup
import re

# Parse HTML content
soup = BeautifulSoup(html_content, 'lxml')

# Extract tables
tables = soup.find_all('table')
for table in tables:
    rows = table.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        data = [cell.get_text(strip=True) for cell in cells]
        print(data)

# Find specific patterns
order_number_pattern = re.compile(r'Order #(\d+)')
order_match = soup.find(text=order_number_pattern)
if order_match:
    order_number = order_number_pattern.search(order_match).group(1)
```

#### pandas.read_html()
Excellent for extracting tables directly into DataFrames.
```python
# Install: pip install pandas lxml
import pandas as pd

# Extract all tables from HTML
tables = pd.read_html(html_content)

# Access specific table
if tables:
    order_table = tables[0]  # First table
    print(order_table)
```

### 3. **Pattern Matching and Text Extraction**

```python
import re
from bs4 import BeautifulSoup

def extract_order_details(html_content):
    soup = BeautifulSoup(html_content, 'lxml')
    
    # Common patterns for order confirmation emails
    patterns = {
        'order_number': r'Order\s*#?\s*[:]\s*(\w+)',
        'total_amount': r'\$\s*(\d+\.?\d*)',
        'tracking_number': r'Tracking\s*#?\s*[:]\s*(\w+)',
        'email': r'[\w\.-]+@[\w\.-]+\.\w+',
        'date': r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
    }
    
    extracted_data = {}
    
    # Search in text
    text = soup.get_text()
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted_data[key] = match.group(1) if match.groups() else match.group(0)
    
    return extracted_data
```

## Node.js Libraries

### 1. **Email Parsing Libraries**

#### mailparser
The Node.js version of the mail parsing library.
```javascript
// Install: npm install mailparser
const { simpleParser } = require('mailparser');

async function parseEmail(rawEmail) {
    const parsed = await simpleParser(rawEmail);
    
    console.log(parsed.subject);
    console.log(parsed.from.text);
    console.log(parsed.text); // Plain text
    console.log(parsed.html); // HTML content
    console.log(parsed.attachments); // Array of attachments
    
    return parsed;
}
```

### 2. **HTML Parsing Libraries**

#### Cheerio
jQuery-like server-side DOM manipulation.
```javascript
// Install: npm install cheerio
const cheerio = require('cheerio');

function parseOrderEmail(html) {
    const $ = cheerio.load(html);
    
    // Extract tables
    const tables = [];
    $('table').each((i, table) => {
        const rows = [];
        $(table).find('tr').each((j, row) => {
            const cells = [];
            $(row).find('td, th').each((k, cell) => {
                cells.push($(cell).text().trim());
            });
            rows.push(cells);
        });
        tables.push(rows);
    });
    
    // Find specific elements
    const orderNumber = $('*:contains("Order #")').text().match(/Order #(\w+)/)?.[1];
    const totalAmount = $('*:contains("Total")').next().text();
    
    return { tables, orderNumber, totalAmount };
}
```

#### node-html-parser
Fast HTML parser with CSS selector support.
```javascript
// Install: npm install node-html-parser
const { parse } = require('node-html-parser');

function extractData(html) {
    const root = parse(html);
    
    // Find elements by CSS selector
    const orderInfo = root.querySelector('.order-info');
    const itemsTable = root.querySelector('table.items');
    
    // Extract text with regex
    const text = root.text;
    const patterns = {
        orderNumber: /Order\s*#\s*(\w+)/i,
        tracking: /Tracking:\s*(\w+)/i
    };
    
    const data = {};
    for (const [key, pattern] of Object.entries(patterns)) {
        const match = text.match(pattern);
        if (match) data[key] = match[1];
    }
    
    return data;
}
```

## Handling Email Attachments

### Python Example
```python
import email
import os
from email.mime.multipart import MIMEMultipart

def extract_attachments(msg, output_dir):
    """Extract attachments from email message"""
    attachments = []
    
    for part in msg.walk():
        if part.get_content_disposition() == 'attachment':
            filename = part.get_filename()
            if filename:
                # Save attachment
                filepath = os.path.join(output_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(part.get_payload(decode=True))
                
                attachments.append({
                    'filename': filename,
                    'path': filepath,
                    'content_type': part.get_content_type()
                })
    
    return attachments

# For CSV/Excel attachments
import pandas as pd

def parse_csv_attachment(filepath):
    """Parse CSV attachment data"""
    df = pd.read_csv(filepath)
    return df.to_dict('records')
```

### Node.js Example
```javascript
const fs = require('fs').promises;
const path = require('path');
const csv = require('csv-parse/sync');

async function handleAttachments(parsed, outputDir) {
    const attachments = [];
    
    for (const attachment of parsed.attachments) {
        const filepath = path.join(outputDir, attachment.filename);
        
        // Save attachment
        await fs.writeFile(filepath, attachment.content);
        
        // Parse CSV if applicable
        if (attachment.filename.endsWith('.csv')) {
            const records = csv.parse(attachment.content, {
                columns: true,
                skip_empty_lines: true
            });
            attachment.parsedData = records;
        }
        
        attachments.push(attachment);
    }
    
    return attachments;
}
```

## Best Practices for Order Confirmation Emails

### 1. **Structure Your Parser**
```python
class OrderConfirmationParser:
    def __init__(self):
        self.patterns = {
            'amazon': {
                'order_id': r'Order #\s*(\d{3}-\d{7}-\d{7})',
                'total': r'Order Total:\s*\$([0-9,]+\.\d{2})',
                'items_selector': 'table.shipment'
            },
            'shopify': {
                'order_id': r'Order #(\d+)',
                'total': r'Total\s*\$([0-9,]+\.\d{2})',
                'items_selector': '.order-list__item'
            }
        }
    
    def detect_vendor(self, html):
        """Detect which vendor sent the email"""
        if 'amazon.com' in html.lower():
            return 'amazon'
        elif 'shopify' in html.lower():
            return 'shopify'
        return 'generic'
    
    def parse(self, html):
        vendor = self.detect_vendor(html)
        patterns = self.patterns.get(vendor, self.patterns['generic'])
        
        soup = BeautifulSoup(html, 'lxml')
        data = {'vendor': vendor}
        
        # Extract using vendor-specific patterns
        for field, pattern in patterns.items():
            if field.endswith('_selector'):
                # CSS selector
                elements = soup.select(pattern)
                data[field.replace('_selector', '')] = [elem.text for elem in elements]
            else:
                # Regex pattern
                match = re.search(pattern, html)
                if match:
                    data[field] = match.group(1)
        
        return data
```

### 2. **Error Handling**
```python
def safe_parse_email(raw_email):
    try:
        # Parse email
        msg = email.message_from_bytes(raw_email)
        
        # Get HTML body
        html_body = None
        for part in msg.walk():
            if part.get_content_type() == 'text/html':
                html_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                break
        
        if not html_body:
            return {'error': 'No HTML content found'}
        
        # Parse HTML
        return parse_order_details(html_body)
        
    except Exception as e:
        return {'error': str(e), 'status': 'failed'}
```

### 3. **Data Validation**
```python
def validate_order_data(data):
    """Validate extracted order data"""
    required_fields = ['order_number', 'total_amount', 'date']
    
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Missing required field: {field}"
    
    # Validate formats
    if not re.match(r'^\d+$', str(data.get('order_number', ''))):
        return False, "Invalid order number format"
    
    try:
        float(data.get('total_amount', '0').replace('$', '').replace(',', ''))
    except ValueError:
        return False, "Invalid total amount format"
    
    return True, "Valid"
```

### 4. **Performance Tips**
- Use streaming parsers for large emails
- Cache compiled regex patterns
- Process attachments asynchronously
- Use connection pooling for database operations
- Implement rate limiting for API calls

### 5. **Common Gotchas**
- Email encoding issues (use proper charset detection)
- Multi-part emails with duplicate content
- Inline CSS and JavaScript in HTML emails
- Dynamic content loaded via images
- Different HTML structures across email clients

## Example: Complete Order Parser
```python
import re
from bs4 import BeautifulSoup
import pandas as pd
from typing import Dict, List, Any

class EmailOrderParser:
    def __init__(self):
        self.vendor_patterns = self._load_vendor_patterns()
    
    def _load_vendor_patterns(self):
        return {
            'amazon': {
                'order_id': r'Order #\s*(\d{3}-\d{7}-\d{7})',
                'total': r'Order Total:\s*\$([0-9,]+\.\d{2})',
                'shipping_address': r'Ship to:(.*?)(?=\n\n|\Z)',
                'items_table': 'table[class*="shipment"]'
            },
            'generic': {
                'order_id': r'Order\s*#?\s*[:]\s*(\w+)',
                'total': r'Total:?\s*\$([0-9,]+\.\d{2})',
                'email': r'[\w\.-]+@[\w\.-]+\.\w+',
                'items_table': 'table'
            }
        }
    
    def parse_email(self, html_content: str) -> Dict[str, Any]:
        """Main parsing method"""
        soup = BeautifulSoup(html_content, 'lxml')
        vendor = self._detect_vendor(html_content)
        patterns = self.vendor_patterns.get(vendor, self.vendor_patterns['generic'])
        
        result = {
            'vendor': vendor,
            'raw_text': soup.get_text(),
            'items': [],
            'metadata': {}
        }
        
        # Extract fields using patterns
        for field, pattern in patterns.items():
            if '_table' in field:
                # Parse table
                tables = soup.select(pattern) if pattern else soup.find_all('table')
                if tables:
                    result['items'] = self._parse_table(tables[0])
            else:
                # Extract using regex
                match = re.search(pattern, result['raw_text'], re.IGNORECASE | re.DOTALL)
                if match:
                    result['metadata'][field] = match.group(1).strip()
        
        return result
    
    def _detect_vendor(self, html: str) -> str:
        """Detect email vendor based on content"""
        html_lower = html.lower()
        if 'amazon.com' in html_lower:
            return 'amazon'
        elif 'shopify' in html_lower:
            return 'shopify'
        elif 'ebay' in html_lower:
            return 'ebay'
        return 'generic'
    
    def _parse_table(self, table) -> List[Dict[str, str]]:
        """Parse HTML table into list of dictionaries"""
        headers = []
        rows = []
        
        # Get headers
        header_row = table.find('tr')
        if header_row:
            headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
        
        # Get data rows
        for row in table.find_all('tr')[1:]:
            cells = [td.get_text(strip=True) for td in row.find_all('td')]
            if cells:
                if headers:
                    rows.append(dict(zip(headers, cells)))
                else:
                    rows.append(cells)
        
        return rows

# Usage example
parser = EmailOrderParser()
result = parser.parse_email(email_html_content)
print(f"Order ID: {result['metadata'].get('order_id')}")
print(f"Total: {result['metadata'].get('total')}")
print(f"Items: {result['items']}")
```

## Summary

### Python Recommendations:
1. **Email Parsing**: Use `mail-parser` for robust email handling
2. **HTML Parsing**: Use `BeautifulSoup4` with `lxml` parser
3. **Table Extraction**: Use `pandas.read_html()` for quick table extraction
4. **Pattern Matching**: Combine regex with BeautifulSoup selectors

### Node.js Recommendations:
1. **Email Parsing**: Use `mailparser` package
2. **HTML Parsing**: Use `cheerio` for jQuery-like syntax
3. **Performance**: Consider `node-html-parser` for faster parsing
4. **CSV Processing**: Use `csv-parse` for attachment handling

### Key Best Practices:
1. Always handle encoding issues gracefully
2. Use vendor-specific patterns when possible
3. Validate extracted data before processing
4. Handle attachments asynchronously
5. Implement proper error handling and logging
6. Cache parsed results when appropriate
7. Use streaming for large emails
8. Test with various email clients and formats