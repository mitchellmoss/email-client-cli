"""
Order management endpoint tests
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock


class TestOrderEndpoints:
    """Test order management endpoints"""
    
    def test_get_orders_empty(self, client: TestClient, auth_headers: dict):
        """Test getting orders when none exist"""
        response = client.get("/api/orders", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["orders"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["per_page"] == 20
    
    @patch('api.orders.get_processed_orders')
    def test_get_orders_with_data(self, mock_get_orders, client: TestClient, auth_headers: dict, sample_order_data: dict):
        """Test getting orders with data"""
        mock_get_orders.return_value = [sample_order_data]
        
        response = client.get("/api/orders", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["orders"]) == 1
        assert data["total"] == 1
        assert data["orders"][0]["order_id"] == "12345"
        assert data["orders"][0]["customer_name"] == "John Doe"
    
    @patch('api.orders.get_processed_orders')
    def test_get_orders_pagination(self, mock_get_orders, client: TestClient, auth_headers: dict):
        """Test orders pagination"""
        # Create 25 mock orders
        mock_orders = []
        for i in range(25):
            order = {
                "order_id": f"order_{i}",
                "customer_name": f"Customer {i}",
                "order_date": datetime.now().isoformat(),
                "status": "processed",
                "total_amount": 100.0 + i
            }
            mock_orders.append(order)
        
        mock_get_orders.return_value = mock_orders
        
        # Test first page
        response = client.get("/api/orders?page=1&per_page=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["orders"]) == 10
        assert data["total"] == 25
        assert data["page"] == 1
        assert data["orders"][0]["order_id"] == "order_0"
        
        # Test second page
        response = client.get("/api/orders?page=2&per_page=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["orders"]) == 10
        assert data["page"] == 2
        assert data["orders"][0]["order_id"] == "order_10"
    
    @patch('api.orders.get_processed_orders')
    def test_get_orders_filtering(self, mock_get_orders, client: TestClient, auth_headers: dict):
        """Test orders filtering"""
        mock_orders = [
            {
                "order_id": "12345",
                "customer_name": "John Doe",
                "status": "processed",
                "order_date": "2024-01-15T10:00:00",
                "total_amount": 299.99
            },
            {
                "order_id": "12346",
                "customer_name": "Jane Smith",
                "status": "pending",
                "order_date": "2024-01-16T11:00:00",
                "total_amount": 199.99
            },
            {
                "order_id": "12347",
                "customer_name": "John Doe",
                "status": "failed",
                "order_date": "2024-01-17T12:00:00",
                "total_amount": 399.99
            }
        ]
        mock_get_orders.return_value = mock_orders
        
        # Filter by status
        response = client.get("/api/orders?status=processed", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["orders"]) == 1
        assert data["orders"][0]["status"] == "processed"
        
        # Filter by date range
        response = client.get(
            "/api/orders?start_date=2024-01-16&end_date=2024-01-16",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["orders"]) == 1
        assert data["orders"][0]["order_id"] == "12346"
        
        # Search by customer name
        response = client.get("/api/orders?search=john", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["orders"]) == 2
        assert all("John" in order["customer_name"] for order in data["orders"])
    
    def test_get_single_order(self, client: TestClient, auth_headers: dict, sample_order_data: dict):
        """Test getting a single order"""
        with patch('api.orders.get_order_by_id') as mock_get_order:
            mock_get_order.return_value = sample_order_data
            
            response = client.get("/api/orders/12345", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["order_id"] == "12345"
            assert data["customer_name"] == "John Doe"
            assert len(data["products"]) == 1
            assert data["shipping_address"]["city"] == "Anytown"
    
    def test_get_nonexistent_order(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent order"""
        with patch('api.orders.get_order_by_id') as mock_get_order:
            mock_get_order.return_value = None
            
            response = client.get("/api/orders/99999", headers=auth_headers)
            assert response.status_code == 404
            assert response.json()["detail"] == "Order not found"
    
    def test_update_order_status(self, client: TestClient, auth_headers: dict):
        """Test updating order status"""
        with patch('api.orders.update_order_status') as mock_update:
            mock_update.return_value = True
            
            response = client.patch(
                "/api/orders/12345/status",
                json={"status": "shipped", "tracking_number": "TRACK123"},
                headers=auth_headers
            )
            assert response.status_code == 200
            assert response.json()["message"] == "Order status updated successfully"
            
            mock_update.assert_called_once_with("12345", "shipped", "TRACK123")
    
    def test_update_order_invalid_status(self, client: TestClient, auth_headers: dict):
        """Test updating order with invalid status"""
        response = client.patch(
            "/api/orders/12345/status",
            json={"status": "invalid_status"},
            headers=auth_headers
        )
        assert response.status_code == 422
    
    def test_resend_order_email(self, client: TestClient, auth_headers: dict):
        """Test resending order email"""
        with patch('api.orders.resend_order_email') as mock_resend:
            mock_resend.return_value = {"success": True, "message": "Email sent"}
            
            response = client.post(
                "/api/orders/12345/resend",
                headers=auth_headers
            )
            assert response.status_code == 200
            assert response.json()["message"] == "Order email resent successfully"
    
    def test_export_orders_csv(self, client: TestClient, auth_headers: dict):
        """Test exporting orders as CSV"""
        with patch('api.orders.export_orders_csv') as mock_export:
            mock_export.return_value = "order_id,customer_name,total\n12345,John Doe,299.99\n"
            
            response = client.get(
                "/api/orders/export?format=csv",
                headers=auth_headers
            )
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/csv; charset=utf-8"
            assert "attachment; filename=" in response.headers["content-disposition"]
            assert response.text.startswith("order_id,customer_name,total")
    
    def test_export_orders_excel(self, client: TestClient, auth_headers: dict):
        """Test exporting orders as Excel"""
        with patch('api.orders.export_orders_excel') as mock_export:
            mock_export.return_value = b"fake_excel_data"
            
            response = client.get(
                "/api/orders/export?format=excel",
                headers=auth_headers
            )
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            assert "attachment; filename=" in response.headers["content-disposition"]
    
    def test_get_order_stats(self, client: TestClient, auth_headers: dict):
        """Test getting order statistics"""
        with patch('api.orders.get_order_statistics') as mock_stats:
            mock_stats.return_value = {
                "total_orders": 150,
                "total_revenue": 45678.90,
                "average_order_value": 304.53,
                "orders_by_status": {
                    "processed": 120,
                    "pending": 20,
                    "failed": 10
                },
                "orders_by_day": [
                    {"date": "2024-01-15", "count": 5, "revenue": 1499.95},
                    {"date": "2024-01-16", "count": 8, "revenue": 2399.92}
                ]
            }
            
            response = client.get("/api/orders/stats", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["total_orders"] == 150
            assert data["total_revenue"] == 45678.90
            assert data["average_order_value"] == 304.53
            assert data["orders_by_status"]["processed"] == 120
            assert len(data["orders_by_day"]) == 2
    
    def test_bulk_update_orders(self, client: TestClient, superuser_auth_headers: dict):
        """Test bulk updating orders (admin only)"""
        with patch('api.orders.bulk_update_orders') as mock_bulk_update:
            mock_bulk_update.return_value = {"updated": 3, "failed": 0}
            
            update_data = {
                "order_ids": ["12345", "12346", "12347"],
                "status": "shipped",
                "tracking_prefix": "SHIP"
            }
            
            response = client.post(
                "/api/orders/bulk-update",
                json=update_data,
                headers=superuser_auth_headers
            )
            assert response.status_code == 200
            assert response.json()["updated"] == 3
            assert response.json()["message"] == "3 orders updated successfully"
    
    def test_bulk_update_non_admin(self, client: TestClient, auth_headers: dict):
        """Test that non-admin cannot bulk update orders"""
        update_data = {
            "order_ids": ["12345", "12346"],
            "status": "shipped"
        }
        
        response = client.post(
            "/api/orders/bulk-update",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "Not enough permissions"
    
    def test_no_auth_access(self, client: TestClient):
        """Test accessing orders without authentication"""
        response = client.get("/api/orders")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"