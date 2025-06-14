#!/usr/bin/env python3
"""Debug product extraction from new template."""

from bs4 import BeautifulSoup

test_email_html = """
<table style="width: 100%; border-collapse: collapse;">
    <tr>
        <td style="padding: 10px;">
            <img src="product-image.jpg" style="width: 60px; height: 60px;">
        </td>
        <td style="padding: 10px;">
            TileWare Promessa™ Series Tee Hook - Traditional - Brushed Nickel (#T101-212-BN)
        </td>
        <td style="padding: 10px; text-align: center;">
            ×1
        </td>
        <td style="padding: 10px; text-align: right;">
            $46.42
        </td>
    </tr>
</table>
"""

soup = BeautifulSoup(test_email_html, 'html.parser')
tables = soup.find_all('table')

print(f"Found {len(tables)} tables")

for i, table in enumerate(tables):
    print(f"\nTable {i+1}:")
    rows = table.find_all('tr')
    print(f"  Rows: {len(rows)}")
    
    for j, row in enumerate(rows):
        cells = row.find_all(['td', 'th'])
        print(f"  Row {j+1} has {len(cells)} cells:")
        for k, cell in enumerate(cells):
            text = cell.get_text().strip()
            print(f"    Cell {k+1}: {text[:50]}...")