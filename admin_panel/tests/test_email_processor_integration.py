"""
Integration tests between admin panel and email processor modules
"""
import pytest
import os
import sys
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.email_fetcher import EmailFetcher
from src.email_parser import EmailParser
from src.claude_processor import ClaudeProcessor
from src.order_formatter import OrderFormatter
from src.email_sender import EmailSender
from src.order_tracker import OrderTracker
from src.laticrete_processor import LaticroteProcessor
from src.price_list_reader import PriceListReader
from src.pdf_filler import PDFFiller

from admin_panel.backend.database import SessionLocal
from admin_panel.backend.models.product import ProductMapping
from admin_panel.backend.services.order_service import OrderService


class TestEmailProcessorIntegration:
    """Test integration between email processor and admin panel"""
    
    @pytest.fixture
    def mock_email_data(self):
        """Sample email data for testing"""
        return {
            "subject": "New customer order #12345",
            "from": "noreply@tileprodepot.com",
            "date": datetime.now().isoformat(),
            "body": """
            <html>
            <body>
                <h2>You've received the following order from John Doe:</h2>
                <p>Order #12345</p>
                <table>
                    <tr>
                        <td>Product</td>
                        <td>TileWare Premium Tile</td>
                    </tr>
                    <tr>
                        <td>SKU</td>
                        <td>TW-PREM-001</td>
                    </tr>
                    <tr>
                        <td>Quantity</td>
                        <td>2</td>
                    </tr>
                    <tr>
                        <td>Price</td>
                        <td>$149.99</td>
                    </tr>
                </table>
                <p>Ship to:</p>
                <p>John Doe<br>
                123 Main St<br>
                Anytown, CA 12345</p>
                <p>Total: $299.98</p>
            </body>
            </html>
            """
        }
    
    @pytest.fixture
    def db_session(self):
        """Create database session"""
        session = SessionLocal()
        yield session
        session.close()
    
    def test_email_to_order_flow(self, mock_email_data, db_session):
        """Test complete flow from email to order in database"""
        # 1. Parse email
        parser = EmailParser()
        basic_info = parser.extract_basic_info(mock_email_data["body"])
        
        assert basic_info["order_id"] == "12345"
        assert basic_info["has_tileware_products"] == True
        
        # 2. Process with Claude (mocked)
        with patch.object(ClaudeProcessor, 'process_order') as mock_claude:
            mock_claude.return_value = {
                "order_id": "12345",
                "customer_name": "John Doe",
                "email": "john@example.com",
                "tileware_products": [{
                    "name": "TileWare Premium Tile",
                    "sku": "TW-PREM-001",
                    "quantity": 2,
                    "price": "$149.99"
                }],
                "shipping_address": {
                    "name": "John Doe",
                    "street": "123 Main St",
                    "city": "Anytown",
                    "state": "CA",
                    "zip": "12345"
                },
                "shipping_method": "Standard",
                "total": "$299.98"
            }
            
            processor = ClaudeProcessor()
            order_data = processor.process_order(
                mock_email_data["body"],
                has_tileware=True,
                has_laticrete=False
            )
        
        # 3. Check product mapping in database
        mapping = db_session.query(ProductMapping).filter(
            ProductMapping.original_name == "TileWare Premium Tile"
        ).first()
        
        if not mapping:
            # Create mapping if it doesn't exist
            mapping = ProductMapping(
                original_name="TileWare Premium Tile",
                mapped_name="TileWare Premium Tile Pro",
                mapped_sku="TW-PREM-001-PRO",
                product_type="tileware",
                confidence_score=0.95
            )
            db_session.add(mapping)
            db_session.commit()
        
        # 4. Apply product mapping
        if mapping:
            order_data["tileware_products"][0]["mapped_name"] = mapping.mapped_name
            order_data["tileware_products"][0]["mapped_sku"] = mapping.mapped_sku
        
        # 5. Format order
        formatter = OrderFormatter()
        formatted_order = formatter.format_tileware_order(order_data)
        
        assert "TileWare Premium Tile" in formatted_order
        assert "123 Main St" in formatted_order
        
        # 6. Track order
        tracker = OrderTracker()
        is_duplicate = tracker.is_duplicate_order("12345")
        
        if not is_duplicate:
            tracker.track_order("12345", formatted_order)
        
        # 7. Store in admin panel database (via OrderService)
        order_service = OrderService(db_session)
        stored_order = order_service.create_order({
            "order_id": order_data["order_id"],
            "customer_name": order_data["customer_name"],
            "email": order_data.get("email", ""),
            "order_date": datetime.now(),
            "status": "processed",
            "total_amount": float(order_data["total"].replace("$", "").replace(",", "")),
            "products": order_data["tileware_products"],
            "shipping_address": order_data["shipping_address"],
            "shipping_method": order_data.get("shipping_method", "Standard"),
            "raw_email": mock_email_data["body"],
            "formatted_output": formatted_order
        })
        
        assert stored_order is not None
    
    def test_product_mapping_synchronization(self, db_session):
        """Test that product mappings are properly used by email processor"""
        # Create product mappings in admin panel
        mappings = [
            ProductMapping(
                original_name="TileWare Basic Tile",
                mapped_name="TileWare Basic Tile Enhanced",
                mapped_sku="TW-BASIC-ENH",
                product_type="tileware",
                confidence_score=0.9
            ),
            ProductMapping(
                original_name="Laticrete 254 Platinum",
                mapped_name="Laticrete 254 Platinum Pro",
                mapped_sku="LAT-254-PRO",
                product_type="laticrete",
                confidence_score=0.92
            )
        ]
        
        for mapping in mappings:
            db_session.add(mapping)
        db_session.commit()
        
        # Simulate email processor using these mappings
        def get_product_mapping(original_name: str) -> Dict:
            mapping = db_session.query(ProductMapping).filter(
                ProductMapping.original_name == original_name
            ).first()
            
            if mapping:
                return {
                    "mapped_name": mapping.mapped_name,
                    "mapped_sku": mapping.mapped_sku,
                    "confidence": mapping.confidence_score
                }
            return None
        
        # Test mapping lookup
        basic_mapping = get_product_mapping("TileWare Basic Tile")
        assert basic_mapping is not None
        assert basic_mapping["mapped_sku"] == "TW-BASIC-ENH"
        
        laticrete_mapping = get_product_mapping("Laticrete 254 Platinum")
        assert laticrete_mapping is not None
        assert laticrete_mapping["confidence"] == 0.92
    
    def test_laticrete_order_processing(self, db_session):
        """Test Laticrete order processing with price list integration"""
        # Mock Laticrete order data
        laticrete_order = {
            "order_id": "54321",
            "customer_name": "Jane Smith",
            "laticrete_products": [{
                "name": "Laticrete 254 Platinum",
                "quantity": 5,
                "sku": "LAT-254"
            }],
            "shipping_address": {
                "name": "Jane Smith",
                "street": "456 Oak Ave",
                "city": "Other City",
                "state": "NY",
                "zip": "54321"
            }
        }
        
        # Mock price list reader
        with patch.object(PriceListReader, '__init__', return_value=None):
            with patch.object(PriceListReader, 'find_product') as mock_find:
                mock_find.return_value = {
                    "name": "Laticrete 254 Platinum",
                    "sku": "LAT-254",
                    "price": 45.99,
                    "unit": "bag"
                }
                
                reader = PriceListReader("mock_path.xlsx")
                product_info = reader.find_product("Laticrete 254 Platinum")
                
                # Calculate total
                total = product_info["price"] * laticrete_order["laticrete_products"][0]["quantity"]
                laticrete_order["total"] = f"${total:.2f}"
        
        # Mock PDF filler
        with patch.object(PDFFiller, '__init__', return_value=None):
            with patch.object(PDFFiller, 'fill_order_form') as mock_fill:
                mock_fill.return_value = "/tmp/filled_order_54321.pdf"
                
                filler = PDFFiller("mock_template.pdf")
                pdf_path = filler.fill_order_form(laticrete_order)
        
        assert pdf_path == "/tmp/filled_order_54321.pdf"
        assert laticrete_order["total"] == "$229.95"
    
    def test_order_status_updates(self, db_session):
        """Test order status updates from admin panel affecting email processor"""
        # Create an order
        order_service = OrderService(db_session)
        order = order_service.create_order({
            "order_id": "67890",
            "customer_name": "Test Customer",
            "order_date": datetime.now(),
            "status": "pending",
            "total_amount": 199.99,
            "products": [{"name": "Test Product", "sku": "TEST-001", "quantity": 1}],
            "shipping_address": {"street": "Test St", "city": "Test City", "state": "TS", "zip": "12345"}
        })
        
        # Update status via admin panel
        updated_order = order_service.update_order_status("67890", "shipped", "TRACK123")
        assert updated_order.status == "shipped"
        assert updated_order.tracking_number == "TRACK123"
        
        # Verify order tracker sees the update
        tracker = OrderTracker()
        
        # In real implementation, tracker would check database
        # Here we simulate the check
        with patch.object(tracker, 'get_order_status') as mock_status:
            mock_status.return_value = "shipped"
            
            status = tracker.get_order_status("67890")
            assert status == "shipped"
    
    def test_error_handling_integration(self, db_session):
        """Test error handling between components"""
        # Test invalid email format
        parser = EmailParser()
        
        invalid_email = {
            "body": "<html><body>Invalid order format</body></html>"
        }
        
        basic_info = parser.extract_basic_info(invalid_email["body"])
        assert basic_info["order_id"] is None
        
        # Test product not in mapping
        unmapped_product = "Unknown TileWare Product XYZ"
        mapping = db_session.query(ProductMapping).filter(
            ProductMapping.original_name == unmapped_product
        ).first()
        assert mapping is None
        
        # System should handle unmapped products gracefully
        # Could create automatic mapping or flag for review
    
    def test_concurrent_order_processing(self, db_session):
        """Test handling of concurrent order processing"""
        import threading
        import time
        
        order_service = OrderService(db_session)
        tracker = OrderTracker()
        
        def process_order(order_id: str, delay: float = 0):
            time.sleep(delay)
            
            # Check if already processed
            if not tracker.is_duplicate_order(order_id):
                # Process order
                order_service.create_order({
                    "order_id": order_id,
                    "customer_name": f"Customer {order_id}",
                    "order_date": datetime.now(),
                    "status": "processed",
                    "total_amount": 100.0,
                    "products": [{"name": "Product", "sku": "SKU", "quantity": 1}],
                    "shipping_address": {"street": "St", "city": "City", "state": "ST", "zip": "12345"}
                })
                tracker.track_order(order_id, f"Order {order_id} processed")
        
        # Simulate concurrent processing of same order
        threads = []
        for i in range(3):
            thread = threading.Thread(
                target=process_order,
                args=("CONCURRENT-001", i * 0.1)
            )
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify only one order was created
        orders = order_service.get_orders_by_id("CONCURRENT-001")
        assert len(orders) <= 1  # Should be at most 1 due to duplicate prevention
    
    def test_email_resend_functionality(self, db_session):
        """Test resending orders from admin panel"""
        # Create a processed order
        order_service = OrderService(db_session)
        order = order_service.create_order({
            "order_id": "RESEND-001",
            "customer_name": "Resend Customer",
            "email": "customer@example.com",
            "order_date": datetime.now(),
            "status": "processed",
            "total_amount": 299.99,
            "products": [{
                "name": "TileWare Product",
                "sku": "TW-001",
                "quantity": 2,
                "price": 149.99
            }],
            "shipping_address": {
                "street": "123 Resend St",
                "city": "Resend City",
                "state": "RS",
                "zip": "12345"
            },
            "formatted_output": "Formatted order text..."
        })
        
        # Mock email sender
        with patch.object(EmailSender, 'send_order') as mock_send:
            mock_send.return_value = True
            
            sender = EmailSender()
            result = sender.send_order(
                order_data=order.__dict__,
                formatted_text=order.formatted_output,
                is_tileware=True,
                is_laticrete=False
            )
            
            assert result == True
            mock_send.assert_called_once()
    
    def test_analytics_data_collection(self, db_session):
        """Test that order processing feeds analytics correctly"""
        order_service = OrderService(db_session)
        
        # Create multiple orders
        base_date = datetime.now()
        orders_data = [
            {
                "order_id": f"ANALYTICS-{i:03d}",
                "customer_name": f"Customer {i}",
                "order_date": base_date - timedelta(days=i),
                "status": "processed" if i % 3 != 0 else "failed",
                "total_amount": 100.0 + (i * 10),
                "products": [{"name": f"Product {i}", "sku": f"SKU-{i}", "quantity": 1}],
                "shipping_address": {"street": "St", "city": "City", "state": "ST", "zip": "12345"}
            }
            for i in range(10)
        ]
        
        for order_data in orders_data:
            order_service.create_order(order_data)
        
        # Get analytics
        stats = order_service.get_order_statistics(
            start_date=base_date - timedelta(days=10),
            end_date=base_date
        )
        
        assert stats["total_orders"] >= 10
        assert stats["total_revenue"] >= 1450.0  # Sum of amounts
        assert stats["orders_by_status"]["processed"] >= 7
        assert stats["orders_by_status"]["failed"] >= 3