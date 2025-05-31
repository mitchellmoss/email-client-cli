"""
Settings endpoint tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
import json


class TestSettingsEndpoints:
    """Test settings management endpoints"""
    
    def test_get_email_settings(self, client: TestClient, superuser_auth_headers: dict):
        """Test getting email settings (admin only)"""
        with patch('api.email_config.get_email_settings') as mock_get_settings:
            mock_get_settings.return_value = {
                "imap": {
                    "server": "imap.gmail.com",
                    "port": 993,
                    "email": "monitor@example.com",
                    "use_ssl": True
                },
                "smtp": {
                    "server": "smtp.gmail.com",
                    "port": 587,
                    "email": "sender@example.com",
                    "use_tls": True
                },
                "processing": {
                    "check_interval_minutes": 5,
                    "cs_email": "cs@example.com",
                    "laticrete_cs_email": "lat-cs@example.com"
                }
            }
            
            response = client.get("/api/settings/email", headers=superuser_auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["imap"]["server"] == "imap.gmail.com"
            assert data["smtp"]["port"] == 587
            assert data["processing"]["check_interval_minutes"] == 5
    
    def test_get_email_settings_non_admin(self, client: TestClient, auth_headers: dict):
        """Test that non-admin cannot get email settings"""
        response = client.get("/api/settings/email", headers=auth_headers)
        assert response.status_code == 403
        assert response.json()["detail"] == "Not enough permissions"
    
    def test_update_email_settings(self, client: TestClient, superuser_auth_headers: dict):
        """Test updating email settings"""
        update_data = {
            "imap": {
                "server": "imap.newserver.com",
                "port": 993
            },
            "processing": {
                "check_interval_minutes": 10
            }
        }
        
        with patch('api.email_config.update_email_settings') as mock_update:
            mock_update.return_value = True
            
            response = client.put(
                "/api/settings/email",
                json=update_data,
                headers=superuser_auth_headers
            )
            assert response.status_code == 200
            assert response.json()["message"] == "Email settings updated successfully"
    
    def test_test_email_connection(self, client: TestClient, superuser_auth_headers: dict):
        """Test email connection testing"""
        with patch('api.email_config.test_email_connection') as mock_test:
            mock_test.return_value = {
                "imap": {"success": True, "message": "IMAP connection successful"},
                "smtp": {"success": True, "message": "SMTP connection successful"}
            }
            
            response = client.post(
                "/api/settings/email/test",
                headers=superuser_auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["imap"]["success"] == True
            assert data["smtp"]["success"] == True
    
    def test_test_email_connection_failure(self, client: TestClient, superuser_auth_headers: dict):
        """Test email connection testing with failures"""
        with patch('api.email_config.test_email_connection') as mock_test:
            mock_test.return_value = {
                "imap": {"success": False, "message": "Authentication failed"},
                "smtp": {"success": True, "message": "SMTP connection successful"}
            }
            
            response = client.post(
                "/api/settings/email/test",
                headers=superuser_auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["imap"]["success"] == False
            assert "Authentication failed" in data["imap"]["message"]
    
    def test_get_api_settings(self, client: TestClient, superuser_auth_headers: dict):
        """Test getting API settings"""
        with patch('api.system.get_api_settings') as mock_get_api:
            mock_get_api.return_value = {
                "anthropic": {
                    "api_key_set": True,
                    "model": "claude-3-haiku-20240307",
                    "temperature": 0.1,
                    "max_tokens": 1000
                },
                "rate_limits": {
                    "requests_per_minute": 60,
                    "tokens_per_minute": 100000
                }
            }
            
            response = client.get("/api/settings/api", headers=superuser_auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["anthropic"]["api_key_set"] == True
            assert data["anthropic"]["model"] == "claude-3-haiku-20240307"
    
    def test_update_api_settings(self, client: TestClient, superuser_auth_headers: dict):
        """Test updating API settings"""
        update_data = {
            "anthropic": {
                "api_key": "sk-ant-api03-new-key",
                "temperature": 0.2,
                "max_tokens": 1500
            }
        }
        
        with patch('api.system.update_api_settings') as mock_update:
            mock_update.return_value = True
            
            response = client.put(
                "/api/settings/api",
                json=update_data,
                headers=superuser_auth_headers
            )
            assert response.status_code == 200
            assert response.json()["message"] == "API settings updated successfully"
    
    def test_get_system_info(self, client: TestClient, auth_headers: dict):
        """Test getting system information"""
        with patch('api.system.get_system_info') as mock_info:
            mock_info.return_value = {
                "version": "1.0.0",
                "python_version": "3.9.0",
                "platform": "Linux",
                "uptime": "2 days, 3:45:00",
                "database": {
                    "type": "SQLite",
                    "size": "15.2 MB",
                    "order_count": 1523
                },
                "disk_usage": {
                    "total": "500 GB",
                    "used": "245 GB",
                    "free": "255 GB",
                    "percent": 49
                }
            }
            
            response = client.get("/api/settings/system/info", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["version"] == "1.0.0"
            assert data["database"]["order_count"] == 1523
    
    def test_get_logs(self, client: TestClient, superuser_auth_headers: dict):
        """Test getting system logs (admin only)"""
        with patch('api.system.get_logs') as mock_logs:
            mock_logs.return_value = {
                "logs": [
                    {
                        "timestamp": "2024-01-15T10:00:00",
                        "level": "INFO",
                        "message": "Email processing started"
                    },
                    {
                        "timestamp": "2024-01-15T10:05:00",
                        "level": "WARNING",
                        "message": "API rate limit approaching"
                    }
                ],
                "total": 150,
                "filtered": 2
            }
            
            response = client.get(
                "/api/settings/system/logs?level=INFO&limit=50",
                headers=superuser_auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["logs"]) == 2
            assert data["total"] == 150
    
    def test_clear_logs(self, client: TestClient, superuser_auth_headers: dict):
        """Test clearing system logs"""
        with patch('api.system.clear_logs') as mock_clear:
            mock_clear.return_value = {"deleted": 500}
            
            response = client.delete(
                "/api/settings/system/logs",
                headers=superuser_auth_headers
            )
            assert response.status_code == 200
            assert response.json()["message"] == "500 log entries cleared"
    
    def test_get_backup_settings(self, client: TestClient, superuser_auth_headers: dict):
        """Test getting backup settings"""
        with patch('api.system.get_backup_settings') as mock_backup:
            mock_backup.return_value = {
                "enabled": True,
                "schedule": "daily",
                "time": "02:00",
                "retention_days": 30,
                "last_backup": "2024-01-14T02:00:00",
                "backup_location": "/backups/"
            }
            
            response = client.get("/api/settings/backup", headers=superuser_auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["enabled"] == True
            assert data["schedule"] == "daily"
    
    def test_create_backup(self, client: TestClient, superuser_auth_headers: dict):
        """Test creating a manual backup"""
        with patch('api.system.create_backup') as mock_create:
            mock_create.return_value = {
                "backup_id": "backup_20240115_103000",
                "size": "15.2 MB",
                "location": "/backups/backup_20240115_103000.tar.gz"
            }
            
            response = client.post(
                "/api/settings/backup/create",
                headers=superuser_auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert "backup_id" in data
            assert data["size"] == "15.2 MB"
    
    def test_restore_backup(self, client: TestClient, superuser_auth_headers: dict):
        """Test restoring from backup"""
        with patch('api.system.restore_backup') as mock_restore:
            mock_restore.return_value = {
                "success": True,
                "restored_items": {
                    "orders": 1500,
                    "product_mappings": 200,
                    "settings": 15
                }
            }
            
            response = client.post(
                "/api/settings/backup/restore",
                json={"backup_id": "backup_20240114_020000"},
                headers=superuser_auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["restored_items"]["orders"] == 1500
    
    def test_get_notification_settings(self, client: TestClient, auth_headers: dict):
        """Test getting notification settings"""
        with patch('api.system.get_notification_settings') as mock_notif:
            mock_notif.return_value = {
                "email_notifications": {
                    "enabled": True,
                    "recipients": ["admin@example.com"],
                    "events": ["order_failed", "system_error", "daily_summary"]
                },
                "webhook_notifications": {
                    "enabled": False,
                    "url": None,
                    "events": []
                }
            }
            
            response = client.get("/api/settings/notifications", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["email_notifications"]["enabled"] == True
            assert len(data["email_notifications"]["events"]) == 3
    
    def test_update_notification_settings(self, client: TestClient, superuser_auth_headers: dict):
        """Test updating notification settings"""
        update_data = {
            "email_notifications": {
                "enabled": True,
                "recipients": ["admin@example.com", "backup@example.com"],
                "events": ["order_failed", "system_error"]
            }
        }
        
        with patch('api.system.update_notification_settings') as mock_update:
            mock_update.return_value = True
            
            response = client.put(
                "/api/settings/notifications",
                json=update_data,
                headers=superuser_auth_headers
            )
            assert response.status_code == 200
            assert response.json()["message"] == "Notification settings updated successfully"
    
    def test_export_all_settings(self, client: TestClient, superuser_auth_headers: dict):
        """Test exporting all settings"""
        with patch('api.system.export_all_settings') as mock_export:
            mock_export.return_value = {
                "email": {"imap": {}, "smtp": {}},
                "api": {"anthropic": {}},
                "notifications": {},
                "backup": {},
                "export_date": "2024-01-15T10:30:00"
            }
            
            response = client.get(
                "/api/settings/export",
                headers=superuser_auth_headers
            )
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"
            assert "attachment; filename=" in response.headers["content-disposition"]
    
    def test_import_settings(self, client: TestClient, superuser_auth_headers: dict):
        """Test importing settings"""
        settings_data = {
            "email": {"imap": {"server": "imap.gmail.com"}},
            "api": {"anthropic": {"temperature": 0.1}}
        }
        
        files = {
            "file": ("settings.json", json.dumps(settings_data), "application/json")
        }
        
        with patch('api.system.import_settings') as mock_import:
            mock_import.return_value = {
                "imported": ["email", "api"],
                "skipped": [],
                "errors": []
            }
            
            response = client.post(
                "/api/settings/import",
                files=files,
                headers=superuser_auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["imported"]) == 2
            assert "email" in data["imported"]