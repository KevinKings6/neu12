#!/usr/bin/env python3
"""
Comprehensive Backend API Tests for Fixed CRUD Problems
Tests the recently fixed issues mentioned in the German review request:

1. User Management (FIXED): PUT /api/admin/users/{user_id}/role, POST /api/admin/users/{user_id}/toggle-status
2. SOS Alert Management (FIXED): PUT /api/admin/sos/{sos_id}/activate, GET /api/admin/sos-alerts
3. Radio Channel Management: POST/PUT/DELETE /api/admin/chat/groups
4. Chat Message Management: PUT/DELETE /api/admin/chat/{message_id}
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Use external URL from frontend environment
EXTERNAL_URL = "https://emergency-sos-3.preview.emergentagent.com/api"
INTERNAL_URL = "http://localhost:8001/api"

class FixedCRUDTester:
    def __init__(self):
        self.external_url = EXTERNAL_URL
        self.internal_url = INTERNAL_URL
        self.session = requests.Session()
        self.test_results = []
        self.admin_token = None
        self.test_user_ids = []
        self.test_sos_ids = []
        self.test_group_ids = []
        self.test_message_ids = []
        
    def log_test(self, test_name: str, success: bool, message: str, details: Dict = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")

    def get_auth_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """Get authorization headers with Bearer token"""
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def setup_admin_login(self):
        """Setup admin login for testing"""
        print("\n=== Setting up Admin Authentication ===")
        
        # Create admin if not exists
        try:
            response = self.session.post(f"{self.external_url}/create-admin")
            print(f"Admin creation response: {response.status_code}")
        except Exception as e:
            print(f"Admin creation error: {e}")
        
        # Login as admin
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        try:
            response = self.session.post(
                f"{self.external_url}/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.admin_token = token_data.get("access_token")
                admin_user = token_data.get("user", {})
                
                self.log_test(
                    "Admin Login Setup",
                    True,
                    f"Admin login successful, role: {admin_user.get('role', 'unknown')}",
                    {"token_length": len(self.admin_token) if self.admin_token else 0}
                )
                return True
            else:
                self.log_test(
                    "Admin Login Setup",
                    False,
                    f"Failed to login admin with status {response.status_code}",
                    {"response_text": response.text}
                )
                return False
        except Exception as e:
            self.log_test(
                "Admin Login Setup",
                False,
                f"Error logging in admin: {str(e)}"
            )
            return False

    def create_test_users(self):
        """Create test users for role management testing"""
        print("\n=== Creating Test Users ===")
        
        if not self.admin_token:
            self.log_test("Create Test Users", False, "No admin token available")
            return
        
        # Create test users with different roles
        test_users = [
            {
                "username": "testuser_role1",
                "email": "roletest1@emergency.com",
                "full_name": "Test User Role 1",
                "password": "test123",
                "role": "user"
            },
            {
                "username": "testuser_role2", 
                "email": "roletest2@emergency.com",
                "full_name": "Test User Role 2",
                "password": "test123",
                "role": "user"
            },
            {
                "username": "testuser_role3",
                "email": "roletest3@emergency.com", 
                "full_name": "Test User Role 3",
                "password": "test123",
                "role": "user"
            }
        ]
        
        for i, user_data in enumerate(test_users):
            try:
                response = self.session.post(
                    f"{self.external_url}/register",
                    json=user_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    created_user = response.json()
                    user_id = created_user.get("id")
                    if user_id:
                        self.test_user_ids.append(user_id)
                    
                    self.log_test(
                        f"Create Test User {i+1}",
                        True,
                        f"User '{user_data['username']}' created successfully",
                        {"user_id": user_id}
                    )
                elif response.status_code == 400 and "already registered" in response.text:
                    # User exists, try to get ID from admin users list
                    try:
                        users_response = self.session.get(
                            f"{self.external_url}/admin/users",
                            headers=self.get_auth_headers(self.admin_token)
                        )
                        if users_response.status_code == 200:
                            users = users_response.json()
                            for user in users:
                                if user.get("username") == user_data["username"]:
                                    user_id = user.get("id")
                                    if user_id and user_id not in self.test_user_ids:
                                        self.test_user_ids.append(user_id)
                                    break
                    except Exception:
                        pass
                    
                    self.log_test(
                        f"Create Test User {i+1}",
                        True,
                        f"User '{user_data['username']}' already exists (expected in testing)"
                    )
                else:
                    self.log_test(
                        f"Create Test User {i+1}",
                        False,
                        f"Failed to create user with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    f"Create Test User {i+1}",
                    False,
                    f"Error creating user: {str(e)}"
                )

    def create_test_sos_alerts(self):
        """Create test SOS alerts for activation testing"""
        print("\n=== Creating Test SOS Alerts ===")
        
        if not self.admin_token:
            self.log_test("Create Test SOS Alerts", False, "No admin token available")
            return
        
        # Create test SOS alerts
        test_alerts = [
            {
                "location_lat": 52.52,
                "location_lng": 13.405,
                "location_address": "Berlin Hauptbahnhof, Deutschland",
                "alert_type": "emergency",
                "message": "Test Notfall - Verkehrsunfall"
            },
            {
                "location_lat": 48.1351,
                "location_lng": 11.5820,
                "location_address": "München Marienplatz, Deutschland", 
                "alert_type": "medical",
                "message": "Test Medizinischer Notfall"
            },
            {
                "location_lat": 50.1109,
                "location_lng": 8.6821,
                "location_address": "Frankfurt am Main, Deutschland",
                "alert_type": "fire",
                "message": "Test Feuer-Notfall"
            }
        ]
        
        for i, alert_data in enumerate(test_alerts):
            try:
                response = self.session.post(
                    f"{self.external_url}/sos-alert",
                    json=alert_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    created_alert = response.json()
                    alert_id = created_alert.get("id")
                    if alert_id:
                        self.test_sos_ids.append(alert_id)
                    
                    self.log_test(
                        f"Create Test SOS Alert {i+1}",
                        True,
                        f"SOS alert '{alert_data['alert_type']}' created successfully",
                        {"alert_id": alert_id, "location": alert_data["location_address"]}
                    )
                else:
                    self.log_test(
                        f"Create Test SOS Alert {i+1}",
                        False,
                        f"Failed to create SOS alert with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    f"Create Test SOS Alert {i+1}",
                    False,
                    f"Error creating SOS alert: {str(e)}"
                )

    def test_user_role_management_fixed(self):
        """Test FIXED User Role Management - PUT /api/admin/users/{user_id}/role"""
        print("\n=== Testing FIXED User Role Management ===")
        
        if not self.admin_token:
            self.log_test("User Role Management", False, "No admin token available")
            return
        
        # Get user IDs from admin users list if we don't have them
        if not self.test_user_ids:
            try:
                users_response = self.session.get(
                    f"{self.external_url}/admin/users",
                    headers=self.get_auth_headers(self.admin_token)
                )
                if users_response.status_code == 200:
                    users = users_response.json()
                    # Get non-admin users for testing
                    for user in users:
                        if user.get("role") != "admin" and user.get("username") != "admin":
                            user_id = user.get("id")
                            if user_id and user_id not in self.test_user_ids:
                                self.test_user_ids.append(user_id)
                                if len(self.test_user_ids) >= 3:
                                    break
            except Exception as e:
                self.log_test("Get Users for Role Testing", False, f"Error getting users: {str(e)}")
        
        if not self.test_user_ids:
            self.log_test("User Role Management", False, "No test users available for role testing")
            return
        
        # Test all supported roles
        test_roles = ["user", "team", "admin", "emergency"]
        
        for i, user_id in enumerate(self.test_user_ids[:3]):  # Test first 3 users
            for role in test_roles:
                try:
                    role_data = {"role": role}
                    response = self.session.put(
                        f"{self.external_url}/admin/users/{user_id}/role",
                        json=role_data,
                        headers=self.get_auth_headers(self.admin_token)
                    )
                    
                    if response.status_code == 200:
                        self.log_test(
                            f"Change User {i+1} Role to {role.upper()}",
                            True,
                            f"User role successfully changed to {role}",
                            {"user_id": user_id, "new_role": role}
                        )
                    else:
                        self.log_test(
                            f"Change User {i+1} Role to {role.upper()}",
                            False,
                            f"Failed to change role with status {response.status_code}",
                            {"response_text": response.text, "user_id": user_id}
                        )
                except Exception as e:
                    self.log_test(
                        f"Change User {i+1} Role to {role.upper()}",
                        False,
                        f"Error changing user role: {str(e)}"
                    )
        
        # Test invalid role rejection
        if self.test_user_ids:
            invalid_roles = ["superuser", "moderator", "invalid", ""]
            for invalid_role in invalid_roles:
                try:
                    role_data = {"role": invalid_role}
                    response = self.session.put(
                        f"{self.external_url}/admin/users/{self.test_user_ids[0]}/role",
                        json=role_data,
                        headers=self.get_auth_headers(self.admin_token)
                    )
                    
                    if response.status_code == 400:
                        self.log_test(
                            f"Reject Invalid Role '{invalid_role}'",
                            True,
                            f"Invalid role '{invalid_role}' correctly rejected with 400"
                        )
                    else:
                        self.log_test(
                            f"Reject Invalid Role '{invalid_role}'",
                            False,
                            f"Expected 400 for invalid role but got {response.status_code}"
                        )
                except Exception as e:
                    self.log_test(
                        f"Reject Invalid Role '{invalid_role}'",
                        False,
                        f"Error testing invalid role: {str(e)}"
                    )
        
        # Test admin self-role change prevention
        try:
            # Get admin user ID
            admin_response = self.session.get(
                f"{self.external_url}/me",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if admin_response.status_code == 200:
                admin_user = admin_response.json()
                admin_id = admin_user.get("id")
                
                if admin_id:
                    role_data = {"role": "user"}
                    response = self.session.put(
                        f"{self.external_url}/admin/users/{admin_id}/role",
                        json=role_data,
                        headers=self.get_auth_headers(self.admin_token)
                    )
                    
                    if response.status_code == 400:
                        self.log_test(
                            "Prevent Admin Self-Role Change",
                            True,
                            "Admin correctly prevented from changing own role"
                        )
                    else:
                        self.log_test(
                            "Prevent Admin Self-Role Change",
                            False,
                            f"Expected 400 for admin self-role change but got {response.status_code}"
                        )
        except Exception as e:
            self.log_test(
                "Prevent Admin Self-Role Change",
                False,
                f"Error testing admin self-role change: {str(e)}"
            )

    def test_user_status_toggle_fixed(self):
        """Test FIXED User Status Toggle - POST /api/admin/users/{user_id}/toggle-status"""
        print("\n=== Testing FIXED User Status Toggle ===")
        
        if not self.admin_token:
            self.log_test("User Status Toggle", False, "No admin token available")
            return
        
        # Get user IDs from admin users list if we don't have them
        if not self.test_user_ids:
            try:
                users_response = self.session.get(
                    f"{self.external_url}/admin/users",
                    headers=self.get_auth_headers(self.admin_token)
                )
                if users_response.status_code == 200:
                    users = users_response.json()
                    # Get non-admin users for testing
                    for user in users:
                        if user.get("role") != "admin" and user.get("username") != "admin":
                            user_id = user.get("id")
                            if user_id and user_id not in self.test_user_ids:
                                self.test_user_ids.append(user_id)
                                if len(self.test_user_ids) >= 2:
                                    break
            except Exception as e:
                self.log_test("Get Users for Status Testing", False, f"Error getting users: {str(e)}")
        
        if not self.test_user_ids:
            self.log_test("User Status Toggle", False, "No test users available for status testing")
            return
        
        # Test toggling user status for each test user
        for i, user_id in enumerate(self.test_user_ids[:2]):  # Test first 2 users
            try:
                # Toggle status (should deactivate if active, activate if inactive)
                response = self.session.post(
                    f"{self.external_url}/admin/users/{user_id}/toggle-status",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    new_status = response_data.get("is_active")
                    status_text = "aktiviert" if new_status else "gesperrt"
                    
                    self.log_test(
                        f"Toggle User {i+1} Status (First Toggle)",
                        True,
                        f"User status toggled successfully - User {status_text}",
                        {"user_id": user_id, "new_status": new_status}
                    )
                    
                    # Toggle back to original state
                    response2 = self.session.post(
                        f"{self.external_url}/admin/users/{user_id}/toggle-status",
                        headers=self.get_auth_headers(self.admin_token)
                    )
                    
                    if response2.status_code == 200:
                        response_data2 = response2.json()
                        final_status = response_data2.get("is_active")
                        status_text2 = "aktiviert" if final_status else "gesperrt"
                        
                        self.log_test(
                            f"Toggle User {i+1} Status (Second Toggle)",
                            True,
                            f"User status toggled back successfully - User {status_text2}",
                            {"user_id": user_id, "final_status": final_status}
                        )
                    else:
                        self.log_test(
                            f"Toggle User {i+1} Status (Second Toggle)",
                            False,
                            f"Failed to toggle back with status {response2.status_code}",
                            {"response_text": response2.text}
                        )
                else:
                    self.log_test(
                        f"Toggle User {i+1} Status (First Toggle)",
                        False,
                        f"Failed to toggle user status with status {response.status_code}",
                        {"response_text": response.text, "user_id": user_id}
                    )
            except Exception as e:
                self.log_test(
                    f"Toggle User {i+1} Status",
                    False,
                    f"Error toggling user status: {str(e)}"
                )
        
        # Test invalid user ID
        try:
            response = self.session.post(
                f"{self.external_url}/admin/users/invalid_user_id/toggle-status",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 400:
                self.log_test(
                    "Toggle Invalid User ID",
                    True,
                    "Invalid user ID correctly rejected with 400"
                )
            else:
                self.log_test(
                    "Toggle Invalid User ID",
                    False,
                    f"Expected 400 for invalid user ID but got {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "Toggle Invalid User ID",
                False,
                f"Error testing invalid user ID: {str(e)}"
            )

    def test_sos_activation_fixed(self):
        """Test FIXED SOS Activation - PUT /api/admin/sos/{sos_id}/activate"""
        print("\n=== Testing FIXED SOS Activation ===")
        
        if not self.admin_token or not self.test_sos_ids:
            self.log_test("SOS Activation", False, "No admin token or test SOS alerts available")
            return
        
        # Test activating SOS alerts
        for i, sos_id in enumerate(self.test_sos_ids):
            try:
                response = self.session.put(
                    f"{self.external_url}/admin/sos/{sos_id}/activate",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    status = response_data.get("status", "unknown")
                    
                    self.log_test(
                        f"Activate SOS Alert {i+1}",
                        True,
                        f"SOS alert activated successfully (status: {status})",
                        {"sos_id": sos_id, "status": status}
                    )
                else:
                    self.log_test(
                        f"Activate SOS Alert {i+1}",
                        False,
                        f"Failed to activate SOS with status {response.status_code}",
                        {"response_text": response.text, "sos_id": sos_id}
                    )
            except Exception as e:
                self.log_test(
                    f"Activate SOS Alert {i+1}",
                    False,
                    f"Error activating SOS alert: {str(e)}"
                )
        
        # Test invalid SOS ID
        try:
            response = self.session.put(
                f"{self.external_url}/admin/sos/invalid_sos_id/activate",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 400:
                self.log_test(
                    "Activate Invalid SOS ID",
                    True,
                    "Invalid SOS ID correctly rejected with 400"
                )
            else:
                self.log_test(
                    "Activate Invalid SOS ID",
                    False,
                    f"Expected 400 for invalid SOS ID but got {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "Activate Invalid SOS ID",
                False,
                f"Error testing invalid SOS ID: {str(e)}"
            )

    def test_sos_list_filtering_fixed(self):
        """Test FIXED SOS List Filtering - GET /api/admin/sos-alerts (should only show pending, not active)"""
        print("\n=== Testing FIXED SOS List Filtering ===")
        
        if not self.admin_token:
            self.log_test("SOS List Filtering", False, "No admin token available")
            return
        
        try:
            # Get SOS alerts list (should only show pending/new, not active ones)
            response = self.session.get(
                f"{self.external_url}/admin/sos-alerts",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                sos_alerts = response.json()
                
                # Check that no active SOS alerts are in the list
                active_alerts = [alert for alert in sos_alerts if alert.get("status") == "active"]
                pending_alerts = [alert for alert in sos_alerts if alert.get("status") in ["pending", "new"]]
                
                if len(active_alerts) == 0:
                    self.log_test(
                        "SOS List Filters Out Active Alerts",
                        True,
                        f"SOS list correctly filters out active alerts. Found {len(pending_alerts)} pending alerts, 0 active alerts",
                        {"total_alerts": len(sos_alerts), "pending_alerts": len(pending_alerts), "active_alerts": len(active_alerts)}
                    )
                else:
                    self.log_test(
                        "SOS List Filters Out Active Alerts",
                        False,
                        f"SOS list contains {len(active_alerts)} active alerts (should be 0)",
                        {"total_alerts": len(sos_alerts), "pending_alerts": len(pending_alerts), "active_alerts": len(active_alerts)}
                    )
                
                # Verify all returned alerts have correct status
                all_valid_status = all(alert.get("status") in ["pending", "new"] for alert in sos_alerts)
                if all_valid_status or len(sos_alerts) == 0:
                    self.log_test(
                        "SOS List Status Validation",
                        True,
                        "All SOS alerts in list have valid pending/new status"
                    )
                else:
                    self.log_test(
                        "SOS List Status Validation",
                        False,
                        "Some SOS alerts have invalid status for pending list"
                    )
            else:
                self.log_test(
                    "Get SOS Alerts List",
                    False,
                    f"Failed to get SOS alerts with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "SOS List Filtering",
                False,
                f"Error testing SOS list filtering: {str(e)}"
            )

    def test_radio_channel_crud(self):
        """Test Radio Channel CRUD Operations"""
        print("\n=== Testing Radio Channel CRUD Operations ===")
        
        if not self.admin_token:
            self.log_test("Radio Channel CRUD", False, "No admin token available")
            return
        
        # Test data for German emergency channels
        test_channels = [
            {
                "name": "Einsatzleitung",
                "description": "Hauptkommunikation für Einsatzleitung",
                "members": []
            },
            {
                "name": "Rettungsdienst", 
                "description": "Kommunikation für Rettungskräfte",
                "members": []
            },
            {
                "name": "Feuerwehr",
                "description": "Feuerwehr-Kommunikationsgruppe", 
                "members": []
            },
            {
                "name": "Polizei",
                "description": "Polizei-Kommunikationsgruppe",
                "members": []
            }
        ]
        
        # Test CREATE channels (POST /api/admin/chat/groups)
        print("\n--- Testing Channel Creation ---")
        for i, channel_data in enumerate(test_channels):
            # Try external URL first, then internal URL if needed
            for url_type, base_url in [("External", self.external_url), ("Internal", self.internal_url)]:
                try:
                    response = self.session.post(
                        f"{base_url}/admin/chat/groups",
                        json=channel_data,
                        headers=self.get_auth_headers(self.admin_token)
                    )
                    
                    if response.status_code == 200:
                        created_channel = response.json()
                        channel_id = created_channel.get("id") or created_channel.get("_id")
                        if channel_id:
                            self.test_group_ids.append(channel_id)
                        
                        self.log_test(
                            f"Create Channel {i+1} ({url_type} URL)",
                            True,
                            f"Channel '{channel_data['name']}' created successfully",
                            {"channel_id": channel_id, "url_type": url_type}
                        )
                        break  # Success, no need to try other URL
                    elif response.status_code == 405 and url_type == "External":
                        # Expected for external URL due to Kubernetes ingress, try internal
                        continue
                    else:
                        self.log_test(
                            f"Create Channel {i+1} ({url_type} URL)",
                            False,
                            f"Failed to create channel with status {response.status_code}",
                            {"response_text": response.text, "url_type": url_type}
                        )
                        if url_type == "External":
                            continue  # Try internal URL
                        break
                except Exception as e:
                    self.log_test(
                        f"Create Channel {i+1} ({url_type} URL)",
                        False,
                        f"Error creating channel: {str(e)}"
                    )
                    if url_type == "External":
                        continue  # Try internal URL
                    break
        
        # Test READ channels (GET /api/admin/chat/groups)
        print("\n--- Testing Channel Reading ---")
        for url_type, base_url in [("External", self.external_url), ("Internal", self.internal_url)]:
            try:
                response = self.session.get(
                    f"{base_url}/admin/chat/groups",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    channels = response.json()
                    self.log_test(
                        f"Read All Channels ({url_type} URL)",
                        True,
                        f"Retrieved {len(channels)} channels successfully",
                        {"channels_count": len(channels), "url_type": url_type}
                    )
                    break  # Success, no need to try other URL
                elif response.status_code == 405 and url_type == "External":
                    # Expected for external URL, try internal
                    continue
                else:
                    self.log_test(
                        f"Read All Channels ({url_type} URL)",
                        False,
                        f"Failed to read channels with status {response.status_code}",
                        {"response_text": response.text, "url_type": url_type}
                    )
                    if url_type == "External":
                        continue  # Try internal URL
                    break
            except Exception as e:
                self.log_test(
                    f"Read All Channels ({url_type} URL)",
                    False,
                    f"Error reading channels: {str(e)}"
                )
                if url_type == "External":
                    continue  # Try internal URL
                break
        
        # Test UPDATE channels (PUT /api/admin/chat/groups/{id})
        print("\n--- Testing Channel Updates ---")
        if self.test_group_ids:
            channel_id = self.test_group_ids[0]
            update_data = {
                "name": "Einsatzleitung (Aktualisiert)",
                "description": "Aktualisierte Hauptkommunikation für Einsatzleitung",
                "is_active": True
            }
            
            for url_type, base_url in [("External", self.external_url), ("Internal", self.internal_url)]:
                try:
                    response = self.session.put(
                        f"{base_url}/admin/chat/groups/{channel_id}",
                        json=update_data,
                        headers=self.get_auth_headers(self.admin_token)
                    )
                    
                    if response.status_code == 200:
                        updated_channel = response.json()
                        self.log_test(
                            f"Update Channel ({url_type} URL)",
                            True,
                            f"Channel updated successfully: '{updated_channel.get('name', '')}'",
                            {"channel_id": channel_id, "url_type": url_type}
                        )
                        break  # Success, no need to try other URL
                    elif response.status_code == 405 and url_type == "External":
                        # Expected for external URL, try internal
                        continue
                    else:
                        self.log_test(
                            f"Update Channel ({url_type} URL)",
                            False,
                            f"Failed to update channel with status {response.status_code}",
                            {"response_text": response.text, "url_type": url_type}
                        )
                        if url_type == "External":
                            continue  # Try internal URL
                        break
                except Exception as e:
                    self.log_test(
                        f"Update Channel ({url_type} URL)",
                        False,
                        f"Error updating channel: {str(e)}"
                    )
                    if url_type == "External":
                        continue  # Try internal URL
                    break
        
        # Test DELETE channels (DELETE /api/admin/chat/groups/{id})
        print("\n--- Testing Channel Deletion ---")
        if len(self.test_group_ids) > 1:
            channel_id = self.test_group_ids[-1]  # Delete last created channel
            
            for url_type, base_url in [("External", self.external_url), ("Internal", self.internal_url)]:
                try:
                    response = self.session.delete(
                        f"{base_url}/admin/chat/groups/{channel_id}",
                        headers=self.get_auth_headers(self.admin_token)
                    )
                    
                    if response.status_code == 200:
                        self.log_test(
                            f"Delete Channel ({url_type} URL)",
                            True,
                            "Channel deleted successfully",
                            {"channel_id": channel_id, "url_type": url_type}
                        )
                        self.test_group_ids.remove(channel_id)  # Remove from our list
                        break  # Success, no need to try other URL
                    elif response.status_code == 405 and url_type == "External":
                        # Expected for external URL, try internal
                        continue
                    else:
                        self.log_test(
                            f"Delete Channel ({url_type} URL)",
                            False,
                            f"Failed to delete channel with status {response.status_code}",
                            {"response_text": response.text, "url_type": url_type}
                        )
                        if url_type == "External":
                            continue  # Try internal URL
                        break
                except Exception as e:
                    self.log_test(
                        f"Delete Channel ({url_type} URL)",
                        False,
                        f"Error deleting channel: {str(e)}"
                    )
                    if url_type == "External":
                        continue  # Try internal URL
                    break

    def test_chat_message_crud(self):
        """Test Chat Message CRUD Operations"""
        print("\n=== Testing Chat Message CRUD Operations ===")
        
        if not self.admin_token:
            self.log_test("Chat Message CRUD", False, "No admin token available")
            return
        
        # Test CREATE messages (POST /api/admin/chat)
        print("\n--- Testing Message Creation ---")
        test_messages = [
            {
                "message": "Test Nachricht 1 - Einsatz in der Hauptstraße",
                "chat_type": "admin",
                "group_id": self.test_group_ids[0] if self.test_group_ids else None,
                "is_voice_message": False
            },
            {
                "message": "Test Nachricht 2 - Rettungswagen unterwegs",
                "chat_type": "admin",
                "group_id": self.test_group_ids[1] if len(self.test_group_ids) > 1 else None,
                "is_voice_message": False
            },
            {
                "message": "Test Nachricht 3 - Status Update",
                "chat_type": "admin",
                "group_id": None,  # General message
                "is_voice_message": False
            }
        ]
        
        for i, message_data in enumerate(test_messages):
            try:
                response = self.session.post(
                    f"{self.external_url}/admin/chat",
                    json=message_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    created_message = response.json()
                    message_id = created_message.get("id") or created_message.get("_id")
                    if message_id:
                        self.test_message_ids.append(message_id)
                    
                    self.log_test(
                        f"Create Message {i+1}",
                        True,
                        f"Message created successfully: '{message_data['message'][:30]}...'",
                        {"message_id": message_id}
                    )
                else:
                    self.log_test(
                        f"Create Message {i+1}",
                        False,
                        f"Failed to create message with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    f"Create Message {i+1}",
                    False,
                    f"Error creating message: {str(e)}"
                )
        
        # Test UPDATE messages (PUT /api/admin/chat/{message_id})
        print("\n--- Testing Message Updates ---")
        if self.test_message_ids:
            message_id = self.test_message_ids[0]
            update_data = {
                "message": "AKTUALISIERT: Test Nachricht 1 - Einsatz in der Hauptstraße (Bearbeitet)"
            }
            
            # Try both URLs since this might have infrastructure limitations
            for url_type, base_url in [("External", self.external_url), ("Internal", self.internal_url)]:
                try:
                    response = self.session.put(
                        f"{base_url}/admin/chat/{message_id}",
                        json=update_data,
                        headers=self.get_auth_headers(self.admin_token)
                    )
                    
                    if response.status_code == 200:
                        self.log_test(
                            f"Update Message ({url_type} URL)",
                            True,
                            "Message updated successfully",
                            {"message_id": message_id, "url_type": url_type}
                        )
                        break  # Success, no need to try other URL
                    elif response.status_code == 500:
                        self.log_test(
                            f"Update Message ({url_type} URL)",
                            False,
                            f"Message update failed with 500 Internal Server Error (known issue)",
                            {"message_id": message_id, "url_type": url_type, "response_text": response.text}
                        )
                        if url_type == "External":
                            continue  # Try internal URL
                        break
                    else:
                        self.log_test(
                            f"Update Message ({url_type} URL)",
                            False,
                            f"Failed to update message with status {response.status_code}",
                            {"response_text": response.text, "url_type": url_type}
                        )
                        if url_type == "External":
                            continue  # Try internal URL
                        break
                except Exception as e:
                    self.log_test(
                        f"Update Message ({url_type} URL)",
                        False,
                        f"Error updating message: {str(e)}"
                    )
                    if url_type == "External":
                        continue  # Try internal URL
                    break
        
        # Test DELETE messages (DELETE /api/admin/chat/{message_id})
        print("\n--- Testing Message Deletion ---")
        if len(self.test_message_ids) > 1:
            message_id = self.test_message_ids[-1]  # Delete last created message
            
            try:
                response = self.session.delete(
                    f"{self.external_url}/admin/chat/{message_id}",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "Delete Message",
                        True,
                        "Message deleted successfully",
                        {"message_id": message_id}
                    )
                    self.test_message_ids.remove(message_id)  # Remove from our list
                else:
                    self.log_test(
                        "Delete Message",
                        False,
                        f"Failed to delete message with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    "Delete Message",
                    False,
                    f"Error deleting message: {str(e)}"
                )

    def run_comprehensive_test(self):
        """Run all comprehensive tests for fixed CRUD problems"""
        print("🚨 COMPREHENSIVE TESTING OF FIXED CRUD PROBLEMS 🚨")
        print("=" * 80)
        
        # Setup
        if not self.setup_admin_login():
            print("❌ Cannot proceed without admin authentication")
            return
        
        self.create_test_users()
        self.create_test_sos_alerts()
        
        # Test the fixed issues
        self.test_user_role_management_fixed()
        self.test_user_status_toggle_fixed()
        self.test_sos_activation_fixed()
        self.test_sos_list_filtering_fixed()
        self.test_radio_channel_crud()
        self.test_chat_message_crud()
        
        # Summary
        self.print_test_summary()

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("🎯 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 OVERALL STATISTICS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Group results by category
        categories = {
            "User Role Management": [],
            "User Status Toggle": [],
            "SOS Activation": [],
            "SOS List Filtering": [],
            "Radio Channel CRUD": [],
            "Chat Message CRUD": [],
            "Setup": []
        }
        
        for result in self.test_results:
            test_name = result["test"]
            if "Role" in test_name:
                categories["User Role Management"].append(result)
            elif "Toggle" in test_name or "Status" in test_name:
                categories["User Status Toggle"].append(result)
            elif "SOS" in test_name and ("Activate" in test_name or "activate" in test_name.lower()):
                categories["SOS Activation"].append(result)
            elif "SOS" in test_name and ("List" in test_name or "Filter" in test_name):
                categories["SOS List Filtering"].append(result)
            elif "Channel" in test_name or "Group" in test_name:
                categories["Radio Channel CRUD"].append(result)
            elif "Message" in test_name:
                categories["Chat Message CRUD"].append(result)
            else:
                categories["Setup"].append(result)
        
        print(f"\n📋 DETAILED RESULTS BY CATEGORY:")
        
        for category, results in categories.items():
            if results:
                passed = sum(1 for r in results if r["success"])
                total = len(results)
                rate = (passed / total * 100) if total > 0 else 0
                
                print(f"\n🔸 {category}: {passed}/{total} ({rate:.1f}%)")
                
                # Show failed tests
                failed_results = [r for r in results if not r["success"]]
                if failed_results:
                    print("   ❌ FAILED TESTS:")
                    for result in failed_results:
                        print(f"      - {result['test']}: {result['message']}")
                
                # Show successful tests (brief)
                successful_results = [r for r in results if r["success"]]
                if successful_results:
                    print(f"   ✅ PASSED: {len(successful_results)} tests")
        
        print(f"\n🎯 ERWARTUNG vs REALITÄT:")
        print(f"   User Management: {self.get_category_success_rate('User Role Management') + self.get_category_success_rate('User Status Toggle'):.1f}% (Erwartung: 100%)")
        print(f"   SOS Management: {self.get_category_success_rate('SOS Activation') + self.get_category_success_rate('SOS List Filtering'):.1f}% (Erwartung: SOS verschwindet nach Aktivierung)")
        print(f"   Funkgerät CRUD: {self.get_category_success_rate('Radio Channel CRUD'):.1f}% (Erwartung: Alle CRUD-Operationen funktional)")
        print(f"   Chat Message CRUD: {self.get_category_success_rate('Chat Message CRUD'):.1f}% (Erwartung: Keine 500-Fehler)")
        
        print(f"\n🚀 FAZIT:")
        if success_rate >= 90:
            print("   ✅ EXCELLENT: Alle kritischen CRUD-Probleme wurden erfolgreich behoben!")
        elif success_rate >= 75:
            print("   ✅ GOOD: Die meisten CRUD-Probleme wurden behoben, einige kleinere Probleme verbleiben.")
        elif success_rate >= 50:
            print("   ⚠️  PARTIAL: Einige CRUD-Probleme wurden behoben, aber wichtige Probleme verbleiben.")
        else:
            print("   ❌ CRITICAL: Viele CRUD-Probleme sind noch nicht behoben.")

    def get_category_success_rate(self, category):
        """Get success rate for a specific category"""
        category_results = []
        for result in self.test_results:
            test_name = result["test"]
            if category == "User Role Management" and "Role" in test_name:
                category_results.append(result)
            elif category == "User Status Toggle" and ("Toggle" in test_name or "Status" in test_name):
                category_results.append(result)
            elif category == "SOS Activation" and "SOS" in test_name and ("Activate" in test_name or "activate" in test_name.lower()):
                category_results.append(result)
            elif category == "SOS List Filtering" and "SOS" in test_name and ("List" in test_name or "Filter" in test_name):
                category_results.append(result)
            elif category == "Radio Channel CRUD" and ("Channel" in test_name or "Group" in test_name):
                category_results.append(result)
            elif category == "Chat Message CRUD" and "Message" in test_name:
                category_results.append(result)
        
        if not category_results:
            return 0
        
        passed = sum(1 for r in category_results if r["success"])
        return (passed / len(category_results) * 100)

if __name__ == "__main__":
    tester = FixedCRUDTester()
    tester.run_comprehensive_test()