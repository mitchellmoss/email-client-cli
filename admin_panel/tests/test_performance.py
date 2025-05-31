"""
Performance and load tests using locust
"""
from locust import HttpUser, task, between
import random
import string
import json
from datetime import datetime, timedelta


class AdminPanelUser(HttpUser):
    """Simulated admin panel user for load testing"""
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Login before running tasks"""
        # Create test user or use existing
        self.username = "loadtest@example.com"
        self.password = "loadtest123"
        
        # Try to login
        response = self.client.post(
            "/api/auth/login",
            data={
                "username": self.username,
                "password": self.password
            }
        )
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            # If login fails, we might need to create the user first
            # In real test, this would be pre-configured
            self.headers = {}
    
    @task(3)
    def view_dashboard(self):
        """View dashboard - most common operation"""
        self.client.get("/api/analytics/dashboard", headers=self.headers)
    
    @task(2)
    def view_orders(self):
        """View orders list with pagination"""
        page = random.randint(1, 5)
        self.client.get(f"/api/orders?page={page}&per_page=20", headers=self.headers)
    
    @task(2)
    def search_orders(self):
        """Search for orders"""
        search_terms = ["john", "smith", "tile", "12345", "pending"]
        search = random.choice(search_terms)
        self.client.get(f"/api/orders?search={search}", headers=self.headers)
    
    @task(1)
    def view_order_details(self):
        """View individual order details"""
        order_id = f"ORDER-{random.randint(1000, 9999)}"
        self.client.get(f"/api/orders/{order_id}", headers=self.headers)
    
    @task(2)
    def view_product_mappings(self):
        """View product mappings"""
        self.client.get("/api/products/mappings", headers=self.headers)
    
    @task(1)
    def create_product_mapping(self):
        """Create a new product mapping"""
        mapping_data = {
            "original_name": f"Load Test Product {random.randint(1000, 9999)}",
            "mapped_name": f"Mapped Load Test Product",
            "mapped_sku": f"LT-{random.randint(1000, 9999)}",
            "product_type": random.choice(["tileware", "laticrete"]),
            "confidence_score": round(random.uniform(0.7, 1.0), 2)
        }
        
        self.client.post(
            "/api/products/mappings",
            json=mapping_data,
            headers=self.headers
        )
    
    @task(1)
    def update_order_status(self):
        """Update order status"""
        order_id = f"ORDER-{random.randint(1000, 9999)}"
        status_data = {
            "status": random.choice(["processed", "shipped", "failed"]),
            "tracking_number": f"TRACK{random.randint(100000, 999999)}" if random.random() > 0.5 else None
        }
        
        self.client.patch(
            f"/api/orders/{order_id}/status",
            json=status_data,
            headers=self.headers
        )
    
    @task(1)
    def get_statistics(self):
        """Get various statistics"""
        endpoints = [
            "/api/orders/stats",
            "/api/products/stats",
            "/api/settings/system/info"
        ]
        
        endpoint = random.choice(endpoints)
        self.client.get(endpoint, headers=self.headers)


class AdminPanelPowerUser(HttpUser):
    """Simulated power user performing admin operations"""
    wait_time = between(0.5, 2)
    
    def on_start(self):
        """Login as admin"""
        self.username = "admin@example.com"
        self.password = "admin123"
        
        response = self.client.post(
            "/api/auth/login",
            data={
                "username": self.username,
                "password": self.password
            }
        )
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}
    
    @task(2)
    def bulk_update_orders(self):
        """Perform bulk order updates"""
        order_ids = [f"ORDER-{random.randint(1000, 9999)}" for _ in range(random.randint(5, 20))]
        
        update_data = {
            "order_ids": order_ids,
            "status": "shipped",
            "tracking_prefix": "BULK"
        }
        
        self.client.post(
            "/api/orders/bulk-update",
            json=update_data,
            headers=self.headers
        )
    
    @task(1)
    def export_data(self):
        """Export orders or mappings"""
        export_types = [
            ("/api/orders/export?format=csv", "orders"),
            ("/api/orders/export?format=excel", "orders"),
            ("/api/products/mappings/export?format=csv", "mappings")
        ]
        
        endpoint, _ = random.choice(export_types)
        self.client.get(endpoint, headers=self.headers)
    
    @task(1)
    def manage_settings(self):
        """Update various settings"""
        setting_updates = [
            {
                "endpoint": "/api/settings/email",
                "data": {
                    "processing": {
                        "check_interval_minutes": random.randint(5, 30)
                    }
                }
            },
            {
                "endpoint": "/api/settings/notifications",
                "data": {
                    "email_notifications": {
                        "enabled": True,
                        "events": ["order_failed", "system_error"]
                    }
                }
            }
        ]
        
        update = random.choice(setting_updates)
        self.client.put(
            update["endpoint"],
            json=update["data"],
            headers=self.headers
        )
    
    @task(1)
    def view_logs(self):
        """View system logs with filtering"""
        levels = ["INFO", "WARNING", "ERROR", None]
        level = random.choice(levels)
        
        url = "/api/settings/system/logs"
        if level:
            url += f"?level={level}"
        
        self.client.get(url, headers=self.headers)


class EmailProcessorSimulation(HttpUser):
    """Simulate email processor creating orders"""
    wait_time = between(5, 15)  # Simulate email arrival patterns
    
    def on_start(self):
        """Setup for email processor simulation"""
        # In real scenario, this would use service account
        self.api_key = "email-processor-api-key"
        self.headers = {"X-API-Key": self.api_key}
    
    @task
    def process_email_order(self):
        """Simulate email processor creating an order"""
        order_types = ["tileware", "laticrete", "mixed"]
        order_type = random.choice(order_types)
        
        order_data = self._generate_order_data(order_type)
        
        # Simulate order creation through internal API
        # In real system, this would be done by email processor
        self.client.post(
            "/api/internal/orders/create",
            json=order_data,
            headers=self.headers
        )
    
    def _generate_order_data(self, order_type):
        """Generate realistic order data"""
        order_id = f"{random.randint(10000, 99999)}"
        
        base_order = {
            "order_id": order_id,
            "customer_name": self._random_name(),
            "email": f"customer{order_id}@example.com",
            "phone": f"555-{random.randint(1000, 9999)}",
            "order_date": datetime.now().isoformat(),
            "shipping_address": {
                "name": self._random_name(),
                "street": f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Elm', 'First'])} St",
                "city": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
                "state": random.choice(["NY", "CA", "IL", "TX", "AZ"]),
                "zip": f"{random.randint(10000, 99999)}"
            },
            "shipping_method": random.choice(["Standard", "Express", "Overnight"])
        }
        
        if order_type == "tileware":
            base_order["tileware_products"] = self._generate_tileware_products()
        elif order_type == "laticrete":
            base_order["laticrete_products"] = self._generate_laticrete_products()
        else:  # mixed
            base_order["tileware_products"] = self._generate_tileware_products()
            base_order["laticrete_products"] = self._generate_laticrete_products()
        
        # Calculate total
        total = 0
        for products in [base_order.get("tileware_products", []), 
                        base_order.get("laticrete_products", [])]:
            for product in products:
                price = float(product["price"].replace("$", ""))
                total += price * product["quantity"]
        
        base_order["total"] = f"${total:.2f}"
        
        return base_order
    
    def _generate_tileware_products(self):
        """Generate TileWare products"""
        products = [
            ("TileWare Premium Tile", "TW-PREM-001", 149.99),
            ("TileWare Standard Tile", "TW-STD-001", 99.99),
            ("TileWare Economy Tile", "TW-ECO-001", 79.99),
            ("TileWare Luxury Collection", "TW-LUX-001", 199.99),
            ("TileWare Outdoor Series", "TW-OUT-001", 129.99)
        ]
        
        selected = random.sample(products, random.randint(1, 3))
        return [
            {
                "name": name,
                "sku": sku,
                "quantity": random.randint(1, 10),
                "price": f"${price}"
            }
            for name, sku, price in selected
        ]
    
    def _generate_laticrete_products(self):
        """Generate Laticrete products"""
        products = [
            ("Laticrete 254 Platinum", "LAT-254", 45.99),
            ("Laticrete 317 Adhesive", "LAT-317", 35.99),
            ("Laticrete SpectraLOCK Grout", "LAT-SLG", 55.99),
            ("Laticrete Hydro Ban", "LAT-HB", 65.99),
            ("Laticrete Glass Tile Adhesive", "LAT-GTA", 39.99)
        ]
        
        selected = random.sample(products, random.randint(1, 2))
        return [
            {
                "name": name,
                "sku": sku,
                "quantity": random.randint(1, 5),
                "price": f"${price}"
            }
            for name, sku, price in selected
        ]
    
    def _random_name(self):
        """Generate random customer name"""
        first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emma", 
                      "Robert", "Lisa", "James", "Mary", "William", "Jennifer"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
                     "Miller", "Davis", "Martinez", "Anderson", "Taylor", "Wilson"]
        
        return f"{random.choice(first_names)} {random.choice(last_names)}"


class StressTestUser(HttpUser):
    """User for stress testing specific endpoints"""
    wait_time = between(0.1, 0.5)  # Very aggressive timing
    
    def on_start(self):
        """Quick setup"""
        self.headers = {"X-Stress-Test": "true"}
    
    @task
    def hammer_search(self):
        """Stress test search functionality"""
        # Generate random search strings
        chars = string.ascii_letters + string.digits
        search_term = ''.join(random.choice(chars) for _ in range(random.randint(3, 20)))
        
        self.client.get(
            f"/api/orders?search={search_term}",
            headers=self.headers,
            name="/api/orders?search=[random]"
        )
    
    @task
    def concurrent_updates(self):
        """Test concurrent update handling"""
        order_id = f"STRESS-{random.randint(1, 100)}"  # Limited set for conflicts
        
        self.client.patch(
            f"/api/orders/{order_id}/status",
            json={"status": random.choice(["pending", "processed", "shipped"])},
            headers=self.headers,
            name="/api/orders/[id]/status"
        )
    
    @task
    def large_data_requests(self):
        """Request large datasets"""
        self.client.get(
            "/api/orders?per_page=100",
            headers=self.headers,
            name="/api/orders?per_page=100"
        )


# Custom test scenarios for specific performance testing
class PerformanceScenarios:
    """Specific performance test scenarios"""
    
    @staticmethod
    def test_dashboard_under_load():
        """Test dashboard performance with many concurrent users"""
        # This would be run with: locust -f test_performance.py --users 100 --spawn-rate 10
        pass
    
    @staticmethod
    def test_order_creation_throughput():
        """Test maximum order creation rate"""
        # Focus on EmailProcessorSimulation user class
        pass
    
    @staticmethod
    def test_search_performance():
        """Test search performance with various query complexities"""
        # Focus on search-heavy operations
        pass
    
    @staticmethod
    def test_export_performance():
        """Test export performance with large datasets"""
        # Test CSV/Excel export with thousands of records
        pass


if __name__ == "__main__":
    # Run with: locust -f test_performance.py
    print("Run with: locust -f test_performance.py --host http://localhost:8000")
    print("Then open http://localhost:8089 to configure and run tests")