"""Order formatter for converting extracted data to CS team format."""

from typing import Dict, Any, List
import logging

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class OrderFormatter:
    """Format extracted order data for the CS team."""
    
    def format_order(self, order_details: Dict[str, Any]) -> str:
        """
        Format order details into the required CS team format.
        
        Args:
            order_details: Dictionary containing extracted order information
            
        Returns:
            Formatted order string
        """
        try:
            # Start with the required header
            lines = [
                "Hi CS - Please place this order::::",
                "Hi CS, please place this order -"
            ]
            
            # Add TileWare products
            products = order_details.get('tileware_products', [])
            if not products:
                logger.warning("No TileWare products found in order details")
                return ""
                
            for product in products:
                product_line = self._format_product_line(product)
                if product_line:
                    lines.append(product_line)
            
            # Add blank line
            lines.append("")
            
            # Add shipping section
            lines.append("SHIP TO:")
            
            # Add shipping method - handle None case
            shipping_method = order_details.get('shipping_method')
            if shipping_method and shipping_method.strip():
                lines.append(shipping_method.upper())
            else:
                lines.append("STANDARD SHIPPING")
                logger.info("No shipping method found, defaulting to STANDARD SHIPPING")
            
            # Add blank line
            lines.append("")
            
            # Get shipping address, fall back to billing if not available
            shipping_address = order_details.get('shipping_address', {})
            billing_address = order_details.get('billing_address', {})
            
            # If shipping address is empty or missing key fields, try billing address
            if not shipping_address or not shipping_address.get('street'):
                if billing_address and billing_address.get('street'):
                    logger.info("No shipping address found, using billing address")
                    shipping_address = billing_address
                else:
                    # Create minimal address from customer name if nothing else available
                    shipping_address = {'name': order_details.get('customer_name', 'Unknown Customer')}
                    logger.warning("No shipping or billing address found, using customer name only")
            
            # Add customer name
            customer_name = shipping_address.get('name') or order_details.get('customer_name', 'Unknown Customer')
            lines.append(customer_name)
            
            # Add address lines
            if shipping_address.get('street'):
                lines.append(shipping_address['street'])
                
            # Add city, state, zip
            city_state_zip = self._format_city_state_zip(shipping_address)
            if city_state_zip:
                lines.append(city_state_zip)
            
            # Add blank line and closing
            lines.append("")
            lines.append("::::")
            
            formatted_order = '\n'.join(lines)
            logger.info("Successfully formatted order for CS team")
            
            return formatted_order
            
        except Exception as e:
            logger.error(f"Error formatting order: {e}")
            return ""
    
    def _format_product_line(self, product: Dict[str, Any]) -> str:
        """Format a single product line."""
        try:
            name = product.get('name', 'Unknown Product')
            quantity = product.get('quantity', 1)
            sku = product.get('sku', '')
            
            # Format: Product Name (#SKU) xQuantity
            if sku:
                product_line = f"{name} (#{sku}) x{quantity}"
            else:
                product_line = f"{name} x{quantity}"
                
            return product_line
            
        except Exception as e:
            logger.error(f"Error formatting product line: {e}")
            return ""
    
    def _format_city_state_zip(self, address: Dict[str, str]) -> str:
        """Format city, state, and zip into a single line."""
        parts = []
        
        if address.get('city'):
            parts.append(address['city'])
            
        if address.get('state'):
            if parts:
                parts.append(f", {address['state']}")
            else:
                parts.append(address['state'])
                
        if address.get('zip'):
            parts.append(f" {address['zip']}")
            
        return ''.join(parts)
    
    def format_simple_order(self, customer_name: str, products: List[Dict], 
                          shipping_address: str, shipping_method: str) -> str:
        """
        Format a simple order with basic information.
        
        Args:
            customer_name: Customer's name
            products: List of product dictionaries
            shipping_address: Full shipping address as string
            shipping_method: Shipping method
            
        Returns:
            Formatted order string
        """
        lines = [
            "Hi CS - Please place this order::::",
            "Hi CS, please place this order -"
        ]
        
        # Add products
        for product in products:
            name = product.get('name', '')
            quantity = product.get('quantity', '1')
            if name:
                lines.append(f"{name} x{quantity}")
        
        lines.extend(["", "SHIP TO:", shipping_method.upper(), "", customer_name])
        
        # Add address lines
        address_lines = [line.strip() for line in shipping_address.split('\n') if line.strip()]
        lines.extend(address_lines)
        
        lines.extend(["", "::::"])
        
        return '\n'.join(lines)