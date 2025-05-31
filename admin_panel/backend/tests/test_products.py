"""
Product mapping endpoint tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models.product import ProductMapping
from unittest.mock import patch, MagicMock


class TestProductEndpoints:
    """Test product mapping endpoints"""
    
    def test_get_product_mappings_empty(self, client: TestClient, auth_headers: dict):
        """Test getting product mappings when none exist"""
        response = client.get("/api/products/mappings", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["mappings"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["per_page"] == 20
    
    def test_get_product_mappings_with_data(
        self, 
        client: TestClient, 
        auth_headers: dict, 
        sample_product_mapping: ProductMapping
    ):
        """Test getting product mappings with data"""
        response = client.get("/api/products/mappings", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["mappings"]) == 1
        assert data["total"] == 1
        assert data["mappings"][0]["original_name"] == "TileWare Original Product"
        assert data["mappings"][0]["mapped_sku"] == "TW-001"
    
    def test_get_product_mappings_pagination(
        self, 
        client: TestClient, 
        auth_headers: dict,
        test_db_session: Session
    ):
        """Test product mappings pagination"""
        # Create 25 product mappings
        for i in range(25):
            mapping = ProductMapping(
                original_name=f"Original Product {i}",
                mapped_name=f"Mapped Product {i}",
                mapped_sku=f"SKU-{i:03d}",
                product_type="tileware" if i % 2 == 0 else "laticrete",
                confidence_score=0.8 + (i % 10) / 50
            )
            test_db_session.add(mapping)
        test_db_session.commit()
        
        # Test first page
        response = client.get("/api/products/mappings?page=1&per_page=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["mappings"]) == 10
        assert data["total"] == 26  # 25 + 1 from fixture
        assert data["page"] == 1
        
        # Test second page
        response = client.get("/api/products/mappings?page=2&per_page=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["mappings"]) == 10
        assert data["page"] == 2
    
    def test_get_product_mappings_filter_by_type(
        self, 
        client: TestClient, 
        auth_headers: dict,
        test_db_session: Session
    ):
        """Test filtering product mappings by type"""
        # Add some laticrete mappings
        laticrete_mapping = ProductMapping(
            original_name="Laticrete Original",
            mapped_name="Laticrete Mapped",
            mapped_sku="LAT-001",
            product_type="laticrete",
            confidence_score=0.9
        )
        test_db_session.add(laticrete_mapping)
        test_db_session.commit()
        
        # Filter by tileware
        response = client.get("/api/products/mappings?product_type=tileware", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(m["product_type"] == "tileware" for m in data["mappings"])
        
        # Filter by laticrete
        response = client.get("/api/products/mappings?product_type=laticrete", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(m["product_type"] == "laticrete" for m in data["mappings"])
    
    def test_search_product_mappings(
        self, 
        client: TestClient, 
        auth_headers: dict,
        sample_product_mapping: ProductMapping
    ):
        """Test searching product mappings"""
        response = client.get("/api/products/mappings?search=original", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["mappings"]) == 1
        assert "Original" in data["mappings"][0]["original_name"]
    
    def test_create_product_mapping(self, client: TestClient, auth_headers: dict):
        """Test creating a new product mapping"""
        new_mapping = {
            "original_name": "New TileWare Product",
            "mapped_name": "Mapped TileWare Product",
            "mapped_sku": "TW-NEW-001",
            "product_type": "tileware",
            "confidence_score": 0.95
        }
        
        response = client.post(
            "/api/products/mappings",
            json=new_mapping,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["original_name"] == new_mapping["original_name"]
        assert data["mapped_sku"] == new_mapping["mapped_sku"]
        assert "id" in data
        assert "created_at" in data
    
    def test_create_duplicate_mapping(
        self, 
        client: TestClient, 
        auth_headers: dict,
        sample_product_mapping: ProductMapping
    ):
        """Test creating duplicate product mapping"""
        duplicate_mapping = {
            "original_name": sample_product_mapping.original_name,
            "mapped_name": "Different Mapped Name",
            "mapped_sku": "TW-002",
            "product_type": "tileware",
            "confidence_score": 0.8
        }
        
        response = client.post(
            "/api/products/mappings",
            json=duplicate_mapping,
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_update_product_mapping(
        self, 
        client: TestClient, 
        auth_headers: dict,
        sample_product_mapping: ProductMapping
    ):
        """Test updating a product mapping"""
        update_data = {
            "mapped_name": "Updated Mapped Name",
            "mapped_sku": "TW-001-UPDATED",
            "confidence_score": 0.98
        }
        
        response = client.put(
            f"/api/products/mappings/{sample_product_mapping.id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["mapped_name"] == update_data["mapped_name"]
        assert data["mapped_sku"] == update_data["mapped_sku"]
        assert data["confidence_score"] == update_data["confidence_score"]
        assert data["original_name"] == sample_product_mapping.original_name
    
    def test_update_nonexistent_mapping(self, client: TestClient, auth_headers: dict):
        """Test updating non-existent product mapping"""
        update_data = {
            "mapped_name": "Updated Name",
            "mapped_sku": "UPDATED-SKU"
        }
        
        response = client.put(
            "/api/products/mappings/99999",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Product mapping not found"
    
    def test_delete_product_mapping(
        self, 
        client: TestClient, 
        superuser_auth_headers: dict,
        sample_product_mapping: ProductMapping
    ):
        """Test deleting a product mapping (admin only)"""
        response = client.delete(
            f"/api/products/mappings/{sample_product_mapping.id}",
            headers=superuser_auth_headers
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Product mapping deleted successfully"
        
        # Verify it's deleted
        response = client.get(
            f"/api/products/mappings/{sample_product_mapping.id}",
            headers=superuser_auth_headers
        )
        assert response.status_code == 404
    
    def test_delete_mapping_non_admin(
        self, 
        client: TestClient, 
        auth_headers: dict,
        sample_product_mapping: ProductMapping
    ):
        """Test that non-admin cannot delete mappings"""
        response = client.delete(
            f"/api/products/mappings/{sample_product_mapping.id}",
            headers=auth_headers
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "Not enough permissions"
    
    def test_bulk_create_mappings(self, client: TestClient, auth_headers: dict):
        """Test bulk creating product mappings"""
        mappings_data = [
            {
                "original_name": f"Bulk Product {i}",
                "mapped_name": f"Bulk Mapped {i}",
                "mapped_sku": f"BULK-{i:03d}",
                "product_type": "tileware",
                "confidence_score": 0.85
            }
            for i in range(5)
        ]
        
        response = client.post(
            "/api/products/mappings/bulk",
            json={"mappings": mappings_data},
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["created"] == 5
        assert data["failed"] == 0
        assert len(data["mappings"]) == 5
    
    def test_import_mappings_csv(self, client: TestClient, superuser_auth_headers: dict):
        """Test importing mappings from CSV (admin only)"""
        csv_content = """original_name,mapped_name,mapped_sku,product_type,confidence_score
Import Product 1,Import Mapped 1,IMP-001,tileware,0.9
Import Product 2,Import Mapped 2,IMP-002,laticrete,0.85
"""
        
        files = {"file": ("mappings.csv", csv_content, "text/csv")}
        response = client.post(
            "/api/products/mappings/import",
            files=files,
            headers=superuser_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["imported"] == 2
        assert "Import successful" in data["message"]
    
    def test_export_mappings_csv(self, client: TestClient, auth_headers: dict):
        """Test exporting mappings as CSV"""
        response = client.get(
            "/api/products/mappings/export?format=csv",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment; filename=" in response.headers["content-disposition"]
    
    def test_get_unmapped_products(self, client: TestClient, auth_headers: dict):
        """Test getting unmapped products from recent orders"""
        with patch('api.products.get_unmapped_products') as mock_unmapped:
            mock_unmapped.return_value = [
                {
                    "product_name": "Unknown Product 1",
                    "occurrences": 5,
                    "last_seen": "2024-01-15T10:00:00",
                    "example_order_id": "12345"
                },
                {
                    "product_name": "Unknown Product 2",
                    "occurrences": 3,
                    "last_seen": "2024-01-14T15:00:00",
                    "example_order_id": "12344"
                }
            ]
            
            response = client.get("/api/products/unmapped", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert len(data["unmapped_products"]) == 2
            assert data["unmapped_products"][0]["occurrences"] == 5
    
    def test_suggest_mapping(self, client: TestClient, auth_headers: dict):
        """Test getting mapping suggestions using AI"""
        with patch('api.products.get_mapping_suggestions') as mock_suggest:
            mock_suggest.return_value = {
                "suggestions": [
                    {
                        "mapped_name": "TileWare Premium Tile Pro",
                        "mapped_sku": "TW-PREM-001",
                        "confidence": 0.92,
                        "reason": "Name similarity and product features match"
                    }
                ]
            }
            
            response = client.post(
                "/api/products/suggest-mapping",
                json={"product_name": "TileWare Premium Tile Professional"},
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["suggestions"]) == 1
            assert data["suggestions"][0]["confidence"] == 0.92
    
    def test_validate_sku(self, client: TestClient, auth_headers: dict):
        """Test SKU validation"""
        # Valid SKU
        response = client.post(
            "/api/products/validate-sku",
            json={"sku": "TW-001-PC", "product_type": "tileware"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["valid"] == True
        
        # Invalid SKU format
        response = client.post(
            "/api/products/validate-sku",
            json={"sku": "invalid sku!", "product_type": "tileware"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == False
        assert "Invalid SKU format" in data["message"]
    
    def test_get_mapping_stats(self, client: TestClient, auth_headers: dict):
        """Test getting product mapping statistics"""
        with patch('api.products.get_mapping_statistics') as mock_stats:
            mock_stats.return_value = {
                "total_mappings": 150,
                "mappings_by_type": {
                    "tileware": 95,
                    "laticrete": 55
                },
                "average_confidence": 0.87,
                "low_confidence_count": 12,
                "recent_mappings": 25,
                "unmapped_products": 8
            }
            
            response = client.get("/api/products/stats", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["total_mappings"] == 150
            assert data["mappings_by_type"]["tileware"] == 95
            assert data["average_confidence"] == 0.87