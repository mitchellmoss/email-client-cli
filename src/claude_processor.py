"""Claude API integration for intelligent email processing."""

import json
import time
from typing import Dict, Optional, Any
from anthropic import Anthropic
import logging

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ClaudeProcessor:
    """Process emails using Claude API for intelligent data extraction."""
    
    def __init__(self, api_key: str):
        """
        Initialize Claude processor.
        
        Args:
            api_key: Anthropic API key
        """
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-haiku-20240307"  # Cost-effective for parsing
        
    def extract_order_details(self, html_content: str, product_type: str = "tileware") -> Optional[Dict[str, Any]]:
        """
        Extract detailed order information using Claude.
        
        Args:
            html_content: HTML content of the email
            product_type: Type of products to extract ("tileware" or "laticrete")
            
        Returns:
            Dictionary with extracted order details or None if extraction fails
        """
        prompt = self._create_extraction_prompt(html_content, product_type)
        
        try:
            start_time = time.time()
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.1,  # Low temperature for consistent parsing
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    },
                    {
                        "role": "assistant",
                        "content": "{"  # Start JSON response
                    }
                ]
            )
            
            # Complete the JSON response
            json_response = "{" + response.content[0].text
            
            # Parse the JSON response
            order_details = json.loads(json_response)
            
            processing_time = time.time() - start_time
            logger.info(f"Claude processed order in {processing_time:.2f} seconds")
            
            return order_details
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            return None
    
    def _create_extraction_prompt(self, html_content: str, product_type: str = "tileware") -> str:
        """Create a structured prompt for Claude to extract order details."""
        if product_type == "laticrete":
            return self._create_laticrete_prompt(html_content)
        else:
            return self._create_tileware_prompt(html_content)
    
    def _create_tileware_prompt(self, html_content: str) -> str:
        """Create prompt for TileWare product extraction."""
        return f"""Extract order details from this Tile Pro Depot email. Focus on TileWare products only.

<email_content>
{html_content}
</email_content>

Extract the following information and return as JSON:

1. Order ID (from subject or content)
2. Customer name
3. Customer phone number (if available)
4. All TileWare products with:
   - Product name (full description)
   - Product code/SKU (if available, usually in parentheses)
   - Quantity
   - Price (if available)
5. Billing address (full address) - if available
6. Shipping address (full address) - if not found, will use billing address
7. Shipping method (e.g., UPS Ground, FedEx, etc.)
8. Order total (if available)

IMPORTANT: Only include products that contain "TileWare" in the name.

Return the data in this exact JSON format:
{{
    "order_id": "order number",
    "customer_name": "full name",
    "phone": "phone number",
    "tileware_products": [
        {{
            "name": "product full name",
            "sku": "product code",
            "quantity": number,
            "price": "price as string"
        }}
    ],
    "billing_address": {{
        "name": "recipient name",
        "street": "street address",
        "city": "city",
        "state": "state",
        "zip": "zip code"
    }},
    "shipping_address": {{
        "name": "recipient name",
        "street": "street address",
        "city": "city",
        "state": "state",
        "zip": "zip code"
    }},
    "shipping_method": "shipping method",
    "total": "total amount"
}}

If any field is not found, use null for that field. If shipping address is not found but billing address is available, use null for shipping_address."""
    
    def _create_laticrete_prompt(self, html_content: str) -> str:
        """Create prompt for Laticrete product extraction."""
        return f"""Extract order details from this Tile Pro Depot email. Focus on LATICRETE products only.

<email_content>
{html_content}
</email_content>

Extract the following information and return as JSON:

1. Order ID (from subject or content)
2. Customer name
3. Customer phone number (if available)
4. All LATICRETE products with:
   - Product name (full description)
   - Product code/SKU (if available)
   - Quantity
   - Price (if available)
5. Billing address (full address) - if available
6. Shipping address (full address) - if not found, will use billing address
7. Shipping method (e.g., UPS Ground, FedEx, etc.)
8. Order total (if available)

IMPORTANT: Only include products that contain "LATICRETE" or "Laticrete" in the name.

Return the data in this exact JSON format:
{{
    "order_id": "order number",
    "customer_name": "full name",
    "phone": "phone number",
    "laticrete_products": [
        {{
            "name": "product full name",
            "sku": "product code",
            "quantity": number,
            "price": "price as string"
        }}
    ],
    "billing_address": {{
        "name": "recipient name",
        "street": "street address",
        "city": "city",
        "state": "state",
        "zip": "zip code"
    }},
    "shipping_address": {{
        "name": "recipient name",
        "street": "street address",
        "city": "city",
        "state": "state",
        "zip": "zip code"
    }},
    "shipping_method": "shipping method",
    "total": "total amount"
}}

If any field is not found, use null for that field. If shipping address is not found but billing address is available, use null for shipping_address."""
    
    def format_for_cs_team(self, order_details: Dict[str, Any]) -> Optional[str]:
        """
        Use Claude to format order details for CS team.
        
        Args:
            order_details: Extracted order details
            
        Returns:
            Formatted order text or None if formatting fails
        """
        prompt = f"""Format this order information for the customer service team.

Order Details:
{json.dumps(order_details, indent=2)}

Format the output EXACTLY as follows:
- Start with: "Hi CS - Please place this order::::"
- Then: "Hi CS, please place this order -"
- List each TileWare product with name, SKU in parentheses, and quantity (e.g., "Product Name (#SKU) x3")
- Add blank line
- Add "SHIP TO:"
- Add shipping method in caps
- Add blank line
- Add customer name and full address
- End with "::::"

Example format:
Hi CS - Please place this order::::
Hi CS, please place this order -
TileWare Promessa™ Series Tee Hook - Contemporary - Polished Chrome (#T101-211-PC) x3

SHIP TO:
UPS GROUND

John Doe
123 Main St
Anytown, IL 60000
::::

Return only the formatted text, nothing else."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            formatted_text = response.content[0].text.strip()
            return formatted_text
            
        except Exception as e:
            logger.error(f"Error formatting order with Claude: {e}")
            return None
    
    def validate_extraction(self, order_details: Dict[str, Any], product_type: str = "tileware") -> bool:
        """
        Validate that extracted order details contain required information.
        
        Args:
            order_details: Extracted order details
            product_type: Type of products ("tileware" or "laticrete")
            
        Returns:
            True if valid, False otherwise
        """
        if not order_details:
            return False
            
        # Check for required fields
        product_field = f"{product_type}_products"
        required_fields = ['customer_name', product_field, 'shipping_address']
        
        for field in required_fields:
            if field not in order_details or not order_details[field]:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Check that we have at least one product
        if not isinstance(order_details[product_field], list) or \
           len(order_details[product_field]) == 0:
            logger.warning(f"No {product_type} products found")
            return False
            
        # Validate shipping address
        shipping = order_details.get('shipping_address', {})
        if not shipping.get('name') or not shipping.get('street'):
            logger.warning("Incomplete shipping address")
            return False
            
        return True