#!/usr/bin/env node

/**
 * Email Parser Example - Node.js Implementation
 * Demonstrates parsing HTML emails and extracting structured data
 */

const { simpleParser } = require('mailparser');
const cheerio = require('cheerio');
const fs = require('fs').promises;
const path = require('path');
const csv = require('csv-parse/sync');
const xlsx = require('xlsx');

class EmailParser {
    constructor() {
        this.vendorConfigs = {
            amazon: {
                identifiers: ['amazon.com', 'Your order has been dispatched'],
                patterns: {
                    orderId: /Order #\s*(\d{3}-\d{7}-\d{7})/i,
                    total: /Order Total:\s*\$([0-9,]+\.\d{2})/i,
                    deliveryDate: /Arriving:\s*([A-Za-z]+\s+\d+)/i,
                    tracking: /Tracking ID:\s*(\w+)/i
                },
                selectors: {
                    items: 'table.shipment tr',
                    address: 'div.ship-to-address'
                }
            },
            shopify: {
                identifiers: ['Order confirmation', 'Thank you for your purchase'],
                patterns: {
                    orderId: /Order\s*#(\d+)/i,
                    total: /Total\s*\$([0-9,]+\.\d{2})/i,
                    customerName: /Hi\s+([^,]+),/i,
                    email: /[\w\.-]+@[\w\.-]+\.\w+/
                },
                selectors: {
                    items: '.order-list__item',
                    shipping: '.shipping-address'
                }
            },
            generic: {
                identifiers: [],
                patterns: {
                    orderId: /Order\s*(?:#|Number|ID)?\s*[:]\s*(\w+)/i,
                    total: /(?:Total|Amount|Grand Total):?\s*\$([0-9,]+\.\d{2})/i,
                    date: /(?:Date|Order Date):?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})/i,
                    email: /[\w\.-]+@[\w\.-]+\.\w+/,
                    phone: /(?:Phone|Tel):?\s*\+?(\d[\d\s\-\(\)]+)/i
                },
                selectors: {
                    items: 'table',
                    anyTable: 'table'
                }
            }
        };
    }

    async parseRawEmail(rawEmail) {
        try {
            const parsed = await simpleParser(rawEmail);
            
            const result = {
                headers: {
                    subject: parsed.subject || '',
                    from: parsed.from ? parsed.from.text : '',
                    to: parsed.to ? parsed.to.text : '',
                    date: parsed.date || ''
                },
                body: {
                    html: parsed.html || null,
                    text: parsed.text || null
                },
                attachments: []
            };

            // Process attachments
            if (parsed.attachments && parsed.attachments.length > 0) {
                for (const attachment of parsed.attachments) {
                    result.attachments.push({
                        filename: attachment.filename,
                        contentType: attachment.contentType,
                        size: attachment.size,
                        content: attachment.content
                    });
                }
            }

            return result;
        } catch (error) {
            throw new Error(`Failed to parse email: ${error.message}`);
        }
    }

    detectVendor(content) {
        const contentLower = content.toLowerCase();
        
        for (const [vendor, config] of Object.entries(this.vendorConfigs)) {
            if (vendor === 'generic') continue;
            
            for (const identifier of config.identifiers) {
                if (contentLower.includes(identifier.toLowerCase())) {
                    return vendor;
                }
            }
        }
        
        return 'generic';
    }

    extractData(htmlContent) {
        const $ = cheerio.load(htmlContent);
        const vendor = this.detectVendor(htmlContent);
        const config = this.vendorConfigs[vendor];
        
        const result = {
            vendor: vendor,
            extractedData: {},
            items: [],
            tables: [],
            rawText: $.text()
        };

        // Extract using patterns
        for (const [field, pattern] of Object.entries(config.patterns)) {
            const match = result.rawText.match(pattern);
            if (match) {
                result.extractedData[field] = match[1].trim();
            }
        }

        // Extract using selectors
        for (const [field, selector] of Object.entries(config.selectors)) {
            const elements = $(selector);
            if (elements.length > 0) {
                if (field === 'items') {
                    result.items = this._parseItems($, elements);
                } else {
                    result.extractedData[field] = elements.map((i, el) => $(el).text().trim()).get();
                }
            }
        }

        // Extract all tables
        result.tables = this._extractTables($);

        return result;
    }

    _parseItems($, elements) {
        const items = [];
        
        elements.each((i, elem) => {
            const $elem = $(elem);
            const item = {};

            // Try to extract common fields
            const nameElem = $elem.find('[class*="product"], [class*="item"], [class*="name"]').first();
            if (nameElem.length) {
                item.name = nameElem.text().trim();
            }

            const priceElem = $elem.find('[class*="price"], [class*="cost"], [class*="amount"]').first();
            if (priceElem.length) {
                item.price = priceElem.text().trim();
            }

            const qtyElem = $elem.find('[class*="qty"], [class*="quantity"], [class*="count"]').first();
            if (qtyElem.length) {
                item.quantity = qtyElem.text().trim();
            }

            // If no specific fields found, just get all text
            if (Object.keys(item).length === 0) {
                item.text = $elem.text().trim();
            }

            if (Object.keys(item).length > 0) {
                items.push(item);
            }
        });

        return items;
    }

    _extractTables($) {
        const tables = [];
        
        $('table').each((i, table) => {
            const tableData = this._parseTable($, table);
            if (tableData && tableData.length > 0) {
                tables.push(tableData);
            }
        });

        return tables;
    }

    _parseTable($, table) {
        const rows = [];
        const $table = $(table);
        
        $table.find('tr').each((i, row) => {
            const cells = [];
            $(row).find('td, th').each((j, cell) => {
                cells.push($(cell).text().trim());
            });
            if (cells.length > 0) {
                rows.push(cells);
            }
        });

        return rows;
    }

    async parseAttachment(content, filename) {
        if (filename.endsWith('.csv')) {
            return csv.parse(content, {
                columns: true,
                skip_empty_lines: true
            });
        } else if (filename.endsWith('.xlsx') || filename.endsWith('.xls')) {
            const workbook = xlsx.read(content, { type: 'buffer' });
            const sheetName = workbook.SheetNames[0];
            return xlsx.utils.sheet_to_json(workbook.Sheets[sheetName]);
        } else if (filename.endsWith('.json')) {
            return JSON.parse(content.toString());
        } else {
            return content;
        }
    }
}

class OrderDataExtractor {
    static normalizePrice(priceStr) {
        if (!priceStr) return 0.0;
        
        // Remove currency symbols and commas
        const cleanPrice = priceStr.replace(/[^\d.]/g, '');
        
        try {
            return parseFloat(cleanPrice);
        } catch (error) {
            return 0.0;
        }
    }

    static parseDate(dateStr) {
        const dateFormats = [
            { regex: /(\d{1,2})\/(\d{1,2})\/(\d{4})/, format: 'MM/DD/YYYY' },
            { regex: /(\d{1,2})-(\d{1,2})-(\d{4})/, format: 'MM-DD-YYYY' },
            { regex: /(\d{4})-(\d{1,2})-(\d{1,2})/, format: 'YYYY-MM-DD' },
            { regex: /([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})/, format: 'Month DD, YYYY' }
        ];

        for (const { regex } of dateFormats) {
            const match = dateStr.match(regex);
            if (match) {
                return new Date(dateStr);
            }
        }

        return null;
    }

    static extractAddress(text) {
        const address = {};
        
        // ZIP code pattern
        const zipMatch = text.match(/\b\d{5}(?:-\d{4})?\b/);
        if (zipMatch) {
            address.zip = zipMatch[0];
        }
        
        // State pattern (US)
        const stateMatch = text.match(/\b[A-Z]{2}\b/);
        if (stateMatch) {
            address.state = stateMatch[0];
        }
        
        // City (word before state)
        if (address.state) {
            const cityMatch = text.match(new RegExp(`(\\w+)\\s+${address.state}`));
            if (cityMatch) {
                address.city = cityMatch[1];
            }
        }
        
        return address;
    }
}

// Utility functions
async function parseEmailFile(filePath) {
    const parser = new EmailParser();
    
    try {
        // Read email file
        const rawEmail = await fs.readFile(filePath);
        
        // Parse email
        const emailData = await parser.parseRawEmail(rawEmail);
        
        // Extract order data from HTML body
        if (emailData.body.html) {
            const orderData = parser.extractData(emailData.body.html);
            
            console.log(`Vendor: ${orderData.vendor}`);
            console.log(`Order ID: ${orderData.extractedData.orderId || 'Not found'}`);
            console.log(`Total: ${orderData.extractedData.total || 'Not found'}`);
            console.log(`Items found: ${orderData.items.length}`);
            
            // Process tables
            orderData.tables.forEach((table, index) => {
                console.log(`\nTable ${index + 1}:`);
                console.table(table.slice(0, 5)); // Show first 5 rows
            });

            // Process attachments
            if (emailData.attachments.length > 0) {
                console.log(`\nAttachments: ${emailData.attachments.length}`);
                for (const attachment of emailData.attachments) {
                    console.log(`- ${attachment.filename} (${attachment.size} bytes)`);
                    
                    // Parse attachment if supported
                    try {
                        const parsedData = await parser.parseAttachment(
                            attachment.content,
                            attachment.filename
                        );
                        console.log(`  Parsed ${attachment.filename}:`, parsedData);
                    } catch (err) {
                        console.log(`  Could not parse ${attachment.filename}: ${err.message}`);
                    }
                }
            }
        }
        
        return emailData;
    } catch (error) {
        console.error('Error parsing email:', error);
        throw error;
    }
}

// Export modules
module.exports = {
    EmailParser,
    OrderDataExtractor,
    parseEmailFile
};

// Example usage
if (require.main === module) {
    // Example: Parse an email file
    const emailPath = process.argv[2] || 'sample_order_email.eml';
    
    parseEmailFile(emailPath)
        .then(() => console.log('\nEmail parsing complete!'))
        .catch(err => console.error('Failed to parse email:', err));
}