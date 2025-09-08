#!/usr/bin/env python3
"""
Comprehensive CRUD Tests for Funkgerät (Radio) and SOS Management
Tests all CRUD operations that are not working as requested by user
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Backend API base URL from frontend environment
BASE_URL = "https://emergency-sos-3.preview.emergentagent.com/api"

class FunkgeraetSOSCRUDTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.test_results = []
        self.admin_token = None
        self.test_user_id = None
        self.created_group_ids = []
        self.created_message_ids = []
        self.created_sos_ids = []
        
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

    def setup_admin_authentication(self):
        """Setup admin authentication for testing"""
        print("\n=== Setting up Admin Authentication ===")
        
        # Create admin if not exists
        try:
            response = self.session.post(f"{self.base_url}/create-admin")
            if response.status_code == 200:
                print("✅ Admin user ready")
        except Exception as e:
            print(f"⚠️ Admin creation: {e}")
        
        # Login as admin
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.admin_token = token_data.get("access_token")
                admin_user = token_data.get("user", {})
                
                self.log_test(
                    "Admin Authentication Setup",
                    True,
                    f"Admin login successful, role: {admin_user.get('role', 'unknown')}",
                    {"token_length": len(self.admin_token) if self.admin_token else 0}
                )
                return True
            else:
                self.log_test(
                    "Admin Authentication Setup",
                    False,
                    f"Failed to login admin with status {response.status_code}",
                    {"response_text": response.text}
                )
                return False
        except Exception as e:
            self.log_test(
                "Admin Authentication Setup",
                False,
                f"Error logging in admin: {str(e)}"
            )
            return False

    def create_test_user(self):
        """Create a test user for user management tests"""
        print("\n=== Creating Test User ===")
        
        user_data = {
            "username": "testuser_funkgeraet",
            "email": "testuser_funkgeraet@emergency-sos.com",
            "full_name": "Test Funkgerät User",
            "password": "testpass123",
            "role": "user"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/register",
                json=user_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                created_user = response.json()
                self.test_user_id = created_user.get("id")
                self.log_test(
                    "Test User Creation",
                    True,
                    f"Test user created successfully",
                    {"user_id": self.test_user_id}
                )
                return True
            elif response.status_code == 400 and "already registered" in response.text:
                # User exists, get ID from admin users list
                try:
                    users_response = self.session.get(
                        f"{self.base_url}/admin/users",
                        headers=self.get_auth_headers(self.admin_token)
                    )
                    if users_response.status_code == 200:
                        users = users_response.json()
                        for user in users:
                            if user.get("username") == user_data["username"]:
                                self.test_user_id = user.get("id")
                                break
                        
                        self.log_test(
                            "Test User Creation",
                            True,
                            f"Test user already exists (using existing)",
                            {"user_id": self.test_user_id}
                        )
                        return True
                except Exception:
                    pass
                
                self.log_test(
                    "Test User Creation",
                    False,
                    "User exists but couldn't get ID"
                )
                return False
            else:
                self.log_test(
                    "Test User Creation",
                    False,
                    f"Failed to create test user with status {response.status_code}",
                    {"response_text": response.text}
                )
                return False
        except Exception as e:
            self.log_test(
                "Test User Creation",
                False,
                f"Error creating test user: {str(e)}"
            )
            return False

    def test_kanal_management_crud(self):
        """Test Kanal-Management APIs (Chat Groups CRUD)"""
        print("\n=== Testing Kanal-Management CRUD Operations ===")
        
        if not self.admin_token:
            self.log_test("Kanal Management CRUD", False, "No admin token available")
            return
        
        # Test data for German emergency channels
        test_channels = [
            {
                "name": "Einsatzleitung Zentral",
                "description": "Hauptkommunikation für zentrale Einsatzleitung",
                "members": []
            },
            {
                "name": "Rettungsdienst Nord",
                "description": "Rettungskräfte Sektor Nord",
                "members": []
            },
            {
                "name": "Feuerwehr Süd",
                "description": "Feuerwehr-Einheiten Sektor Süd",
                "members": []
            },
            {
                "name": "Polizei Verkehr",
                "description": "Verkehrspolizei Koordination",
                "members": []
            }
        ]
        
        # 1. CREATE - POST /api/admin/chat/groups
        print("\n--- Testing Channel Creation (POST /api/admin/chat/groups) ---")
        for i, channel_data in enumerate(test_channels):
            try:
                response = self.session.post(
                    f"{self.base_url}/admin/chat/groups",
                    json=channel_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    created_channel = response.json()
                    channel_id = created_channel.get("id") or created_channel.get("_id")
                    if channel_id:
                        self.created_group_ids.append(channel_id)
                    
                    self.log_test(
                        f"CREATE Channel {i+1}: {channel_data['name']}",
                        True,
                        f"Channel '{channel_data['name']}' created successfully",
                        {"channel_id": channel_id, "response": created_channel}
                    )
                else:
                    self.log_test(
                        f"CREATE Channel {i+1}: {channel_data['name']}",
                        False,
                        f"Failed to create channel with status {response.status_code}",
                        {"response_text": response.text, "request_data": channel_data}
                    )
            except Exception as e:
                self.log_test(
                    f"CREATE Channel {i+1}: {channel_data['name']}",
                    False,
                    f"Error creating channel: {str(e)}"
                )
        
        # 2. READ - GET /api/admin/chat/groups
        print("\n--- Testing Channel Listing (GET /api/admin/chat/groups) ---")
        try:
            response = self.session.get(
                f"{self.base_url}/admin/chat/groups",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                channels = response.json()
                self.log_test(
                    "READ All Channels",
                    True,
                    f"Retrieved {len(channels)} channels successfully",
                    {"channels_count": len(channels), "created_channels": len(self.created_group_ids)}
                )
                
                # Verify our created channels are in the list
                created_names = [ch["name"] for ch in test_channels]
                found_channels = [ch for ch in channels if ch.get("name") in created_names]
                
                if len(found_channels) > 0:
                    self.log_test(
                        "READ Verify Created Channels",
                        True,
                        f"Found {len(found_channels)} of our created channels in list",
                        {"found_channels": [ch.get("name") for ch in found_channels]}
                    )
                else:
                    self.log_test(
                        "READ Verify Created Channels",
                        False,
                        "None of our created channels found in list"
                    )
            else:
                self.log_test(
                    "READ All Channels",
                    False,
                    f"Failed to get channels with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "READ All Channels",
                False,
                f"Error getting channels: {str(e)}"
            )
        
        # 3. UPDATE - PUT /api/admin/chat/groups/{id}
        print("\n--- Testing Channel Updates (PUT /api/admin/chat/groups/{id}) ---")
        if self.created_group_ids:
            for i, channel_id in enumerate(self.created_group_ids[:2]):  # Test first 2 channels
                update_data = {
                    "name": f"{test_channels[i]['name']} (Aktualisiert)",
                    "description": f"UPDATED: {test_channels[i]['description']} - Neue Protokolle aktiv",
                    "is_active": True
                }
                
                try:
                    response = self.session.put(
                        f"{self.base_url}/admin/chat/groups/{channel_id}",
                        json=update_data,
                        headers=self.get_auth_headers(self.admin_token)
                    )
                    
                    if response.status_code == 200:
                        updated_channel = response.json()
                        self.log_test(
                            f"UPDATE Channel {i+1}",
                            True,
                            f"Channel updated successfully: '{updated_channel.get('name', '')}'",
                            {"channel_id": channel_id, "updated_data": update_data}
                        )
                    else:
                        self.log_test(
                            f"UPDATE Channel {i+1}",
                            False,
                            f"Failed to update channel with status {response.status_code}",
                            {"response_text": response.text, "channel_id": channel_id}
                        )
                except Exception as e:
                    self.log_test(
                        f"UPDATE Channel {i+1}",
                        False,
                        f"Error updating channel: {str(e)}"
                    )
        else:
            self.log_test(
                "UPDATE Channels",
                False,
                "No channel IDs available for update testing"
            )
        
        # 4. DELETE - DELETE /api/admin/chat/groups/{id}
        print("\n--- Testing Channel Deletion (DELETE /api/admin/chat/groups/{id}) ---")
        if len(self.created_group_ids) > 2:
            # Delete the last 2 channels, keep first 2 for other tests
            channels_to_delete = self.created_group_ids[-2:]
            
            for i, channel_id in enumerate(channels_to_delete):
                try:
                    response = self.session.delete(
                        f"{self.base_url}/admin/chat/groups/{channel_id}",
                        headers=self.get_auth_headers(self.admin_token)
                    )
                    
                    if response.status_code == 200:
                        self.log_test(
                            f"DELETE Channel {i+1}",
                            True,
                            f"Channel deleted successfully",
                            {"channel_id": channel_id}
                        )
                        # Remove from our list
                        self.created_group_ids.remove(channel_id)
                    else:
                        self.log_test(
                            f"DELETE Channel {i+1}",
                            False,
                            f"Failed to delete channel with status {response.status_code}",
                            {"response_text": response.text, "channel_id": channel_id}
                        )
                except Exception as e:
                    self.log_test(
                        f"DELETE Channel {i+1}",
                        False,
                        f"Error deleting channel: {str(e)}"
                    )
        else:
            self.log_test(
                "DELETE Channels",
                False,
                "Not enough channels created for deletion testing"
            )

    def test_chat_message_management(self):
        """Test Chat Message Management APIs"""
        print("\n=== Testing Chat Message Management ===")
        
        if not self.admin_token:
            self.log_test("Chat Message Management", False, "No admin token available")
            return
        
        # First create some test messages
        print("\n--- Creating Test Messages ---")
        test_messages = [
            {
                "message": "Einsatz Hauptstraße 123 - Verkehrsunfall mit Verletzten",
                "chat_type": "admin",
                "group_id": self.created_group_ids[0] if self.created_group_ids else None,
                "is_voice_message": False
            },
            {
                "message": "Rettungswagen RTW-01 ist vor Ort eingetroffen",
                "chat_type": "admin",
                "group_id": self.created_group_ids[0] if self.created_group_ids else None,
                "is_voice_message": False
            },
            {
                "message": "Feuerwehr benötigt hydraulisches Rettungsgerät",
                "chat_type": "admin",
                "group_id": self.created_group_ids[1] if len(self.created_group_ids) > 1 else None,
                "is_voice_message": False
            }
        ]
        
        # Create messages
        for i, message_data in enumerate(test_messages):
            try:
                response = self.session.post(
                    f"{self.base_url}/admin/chat",
                    json=message_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    created_message = response.json()
                    message_id = created_message.get("id") or created_message.get("_id")
                    if message_id:
                        self.created_message_ids.append(message_id)
                    
                    self.log_test(
                        f"Create Test Message {i+1}",
                        True,
                        f"Message created successfully",
                        {"message_id": message_id, "message_preview": message_data["message"][:50]}
                    )
                else:
                    self.log_test(
                        f"Create Test Message {i+1}",
                        False,
                        f"Failed to create message with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    f"Create Test Message {i+1}",
                    False,
                    f"Error creating message: {str(e)}"
                )
        
        # Test message editing - PUT /api/admin/chat/{message_id}
        print("\n--- Testing Message Editing (PUT /api/admin/chat/{message_id}) ---")
        if self.created_message_ids:
            for i, message_id in enumerate(self.created_message_ids[:2]):  # Test first 2 messages
                updated_message_data = {
                    "message": f"AKTUALISIERT: {test_messages[i]['message']} - Status: Bearbeitet um {datetime.now().strftime('%H:%M')}"
                }
                
                try:
                    response = self.session.put(
                        f"{self.base_url}/admin/chat/{message_id}",
                        json=updated_message_data,
                        headers=self.get_auth_headers(self.admin_token)
                    )
                    
                    if response.status_code == 200:
                        self.log_test(
                            f"EDIT Message {i+1}",
                            True,
                            f"Message edited successfully",
                            {"message_id": message_id, "new_content": updated_message_data["message"][:50]}
                        )
                    else:
                        self.log_test(
                            f"EDIT Message {i+1}",
                            False,
                            f"Failed to edit message with status {response.status_code}",
                            {"response_text": response.text, "message_id": message_id}
                        )
                except Exception as e:
                    self.log_test(
                        f"EDIT Message {i+1}",
                        False,
                        f"Error editing message: {str(e)}"
                    )
        else:
            self.log_test(
                "EDIT Messages",
                False,
                "No message IDs available for editing"
            )
        
        # Test message deletion - DELETE /api/admin/chat/{message_id}
        print("\n--- Testing Message Deletion (DELETE /api/admin/chat/{message_id}) ---")
        if len(self.created_message_ids) > 1:
            # Delete the last message, keep others for verification
            message_id = self.created_message_ids[-1]
            
            try:
                response = self.session.delete(
                    f"{self.base_url}/admin/chat/{message_id}",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "DELETE Message",
                        True,
                        f"Message deleted successfully",
                        {"message_id": message_id}
                    )
                    self.created_message_ids.remove(message_id)
                else:
                    self.log_test(
                        "DELETE Message",
                        False,
                        f"Failed to delete message with status {response.status_code}",
                        {"response_text": response.text, "message_id": message_id}
                    )
            except Exception as e:
                self.log_test(
                    "DELETE Message",
                    False,
                    f"Error deleting message: {str(e)}"
                )
        else:
            self.log_test(
                "DELETE Message",
                False,
                "Not enough messages for deletion testing"
            )

    def test_user_group_management(self):
        """Test User Group Management APIs"""
        print("\n=== Testing User Group Management ===")
        
        if not self.admin_token or not self.test_user_id:
            self.log_test("User Group Management", False, "No admin token or test user ID available")
            return
        
        # Test user role changes - PUT /api/admin/users/{user_id}/role
        print("\n--- Testing User Role Changes (PUT /api/admin/users/{user_id}/role) ---")
        
        roles_to_test = ["team", "admin", "emergency", "user"]  # Test different roles
        
        for i, role in enumerate(roles_to_test):
            role_data = {"role": role}
            
            try:
                response = self.session.put(
                    f"{self.base_url}/admin/users/{self.test_user_id}/role",
                    json=role_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        f"Change User Role to {role.upper()}",
                        True,
                        f"User role successfully changed to {role}",
                        {"user_id": self.test_user_id, "new_role": role}
                    )
                else:
                    self.log_test(
                        f"Change User Role to {role.upper()}",
                        False,
                        f"Failed to change role to {role} with status {response.status_code}",
                        {"response_text": response.text, "user_id": self.test_user_id}
                    )
            except Exception as e:
                self.log_test(
                    f"Change User Role to {role.upper()}",
                    False,
                    f"Error changing role to {role}: {str(e)}"
                )
        
        # Test user status toggle - POST /api/admin/users/{user_id}/toggle-status
        print("\n--- Testing User Status Toggle (POST /api/admin/users/{user_id}/toggle-status) ---")
        
        try:
            # First toggle (should deactivate)
            response = self.session.post(
                f"{self.base_url}/admin/users/{self.test_user_id}/toggle-status",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                response_data = response.json()
                new_status = response_data.get("is_active")
                self.log_test(
                    "Toggle User Status (First)",
                    True,
                    f"User status toggled successfully to: {'Active' if new_status else 'Inactive'}",
                    {"user_id": self.test_user_id, "new_status": new_status}
                )
                
                # Second toggle (should reactivate)
                response2 = self.session.post(
                    f"{self.base_url}/admin/users/{self.test_user_id}/toggle-status",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response2.status_code == 200:
                    response_data2 = response2.json()
                    new_status2 = response_data2.get("is_active")
                    self.log_test(
                        "Toggle User Status (Second)",
                        True,
                        f"User status toggled back to: {'Active' if new_status2 else 'Inactive'}",
                        {"user_id": self.test_user_id, "new_status": new_status2}
                    )
                else:
                    self.log_test(
                        "Toggle User Status (Second)",
                        False,
                        f"Failed second toggle with status {response2.status_code}",
                        {"response_text": response2.text}
                    )
            else:
                self.log_test(
                    "Toggle User Status (First)",
                    False,
                    f"Failed to toggle user status with status {response.status_code}",
                    {"response_text": response.text, "user_id": self.test_user_id}
                )
        except Exception as e:
            self.log_test(
                "Toggle User Status",
                False,
                f"Error toggling user status: {str(e)}"
            )

    def test_sos_alert_management(self):
        """Test SOS Alert Management APIs"""
        print("\n=== Testing SOS Alert Management ===")
        
        if not self.admin_token:
            self.log_test("SOS Alert Management", False, "No admin token available")
            return
        
        # First create some test SOS alerts
        print("\n--- Creating Test SOS Alerts ---")
        
        # Create a test user first to create SOS alerts
        test_sos_data = [
            {
                "location_lat": 52.5200,
                "location_lng": 13.4050,
                "location_address": "Brandenburger Tor, Berlin",
                "alert_type": "emergency",
                "message": "Notfall am Brandenburger Tor - Person benötigt medizinische Hilfe"
            },
            {
                "location_lat": 48.1351,
                "location_lng": 11.5820,
                "location_address": "Marienplatz, München",
                "alert_type": "medical",
                "message": "Medizinischer Notfall - Herzinfarkt vermutet"
            },
            {
                "location_lat": 53.5511,
                "location_lng": 9.9937,
                "location_address": "Hamburger Hafen",
                "alert_type": "fire",
                "message": "Feuer im Hafenbereich - Feuerwehr angefordert"
            }
        ]
        
        # We need a regular user token to create SOS alerts
        user_login_data = {
            "username": "testuser_funkgeraet",
            "password": "testpass123"
        }
        
        user_token = None
        try:
            response = self.session.post(
                f"{self.base_url}/login",
                json=user_login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                user_token = token_data.get("access_token")
                print("✅ User login successful for SOS creation")
            else:
                print(f"⚠️ User login failed: {response.status_code}")
        except Exception as e:
            print(f"⚠️ User login error: {e}")
        
        # Create SOS alerts as user
        if user_token:
            for i, sos_data in enumerate(test_sos_data):
                try:
                    response = self.session.post(
                        f"{self.base_url}/sos-alert",
                        json=sos_data,
                        headers=self.get_auth_headers(user_token)
                    )
                    
                    if response.status_code == 200:
                        created_sos = response.json()
                        sos_id = created_sos.get("id") or created_sos.get("_id")
                        if sos_id:
                            self.created_sos_ids.append(sos_id)
                        
                        self.log_test(
                            f"Create Test SOS Alert {i+1}",
                            True,
                            f"SOS alert created: {sos_data['alert_type']} at {sos_data['location_address']}",
                            {"sos_id": sos_id, "alert_type": sos_data["alert_type"]}
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
        
        # Test SOS activation - PUT /api/admin/sos/{sos_id}/activate
        print("\n--- Testing SOS Activation (PUT /api/admin/sos/{sos_id}/activate) ---")
        
        if self.created_sos_ids:
            for i, sos_id in enumerate(self.created_sos_ids[:2]):  # Test first 2 SOS alerts
                try:
                    response = self.session.put(
                        f"{self.base_url}/admin/sos/{sos_id}/activate",
                        headers=self.get_auth_headers(self.admin_token)
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        self.log_test(
                            f"ACTIVATE SOS Alert {i+1}",
                            True,
                            f"SOS alert activated successfully: {response_data.get('status', 'active')}",
                            {"sos_id": sos_id, "response": response_data}
                        )
                    else:
                        self.log_test(
                            f"ACTIVATE SOS Alert {i+1}",
                            False,
                            f"Failed to activate SOS alert with status {response.status_code}",
                            {"response_text": response.text, "sos_id": sos_id}
                        )
                except Exception as e:
                    self.log_test(
                        f"ACTIVATE SOS Alert {i+1}",
                        False,
                        f"Error activating SOS alert: {str(e)}"
                    )
        else:
            self.log_test(
                "ACTIVATE SOS Alerts",
                False,
                "No SOS alert IDs available for activation testing"
            )
        
        # Test getting SOS alerts list after activation - GET /api/admin/sos-alerts
        print("\n--- Testing SOS Alerts List (GET /api/admin/sos-alerts) ---")
        
        try:
            response = self.session.get(
                f"{self.base_url}/admin/sos-alerts",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                sos_alerts = response.json()
                
                # Count different status types
                active_count = len([alert for alert in sos_alerts if alert.get("status") == "active"])
                total_count = len(sos_alerts)
                
                self.log_test(
                    "GET SOS Alerts List",
                    True,
                    f"Retrieved {total_count} SOS alerts ({active_count} active)",
                    {"total_alerts": total_count, "active_alerts": active_count}
                )
                
                # Verify our created alerts are in the list
                our_alert_ids = set(self.created_sos_ids)
                found_alerts = [alert for alert in sos_alerts if alert.get("id") in our_alert_ids or alert.get("_id") in our_alert_ids]
                
                if len(found_alerts) > 0:
                    self.log_test(
                        "Verify Created SOS in List",
                        True,
                        f"Found {len(found_alerts)} of our created SOS alerts in admin list",
                        {"found_alerts": len(found_alerts), "created_alerts": len(self.created_sos_ids)}
                    )
                else:
                    self.log_test(
                        "Verify Created SOS in List",
                        False,
                        "None of our created SOS alerts found in admin list"
                    )
            else:
                self.log_test(
                    "GET SOS Alerts List",
                    False,
                    f"Failed to get SOS alerts with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "GET SOS Alerts List",
                False,
                f"Error getting SOS alerts: {str(e)}"
            )
        
        # Test SOS deletion after activation - DELETE /api/admin/sos/{sos_id}
        print("\n--- Testing SOS Deletion (DELETE /api/admin/sos/{sos_id}) ---")
        
        if len(self.created_sos_ids) > 1:
            # Delete the last SOS alert
            sos_id = self.created_sos_ids[-1]
            
            try:
                response = self.session.delete(
                    f"{self.base_url}/admin/sos/{sos_id}",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "DELETE SOS Alert",
                        True,
                        f"SOS alert deleted successfully from list",
                        {"sos_id": sos_id}
                    )
                    self.created_sos_ids.remove(sos_id)
                    
                    # Verify it's removed from the list
                    try:
                        verify_response = self.session.get(
                            f"{self.base_url}/admin/sos-alerts",
                            headers=self.get_auth_headers(self.admin_token)
                        )
                        
                        if verify_response.status_code == 200:
                            remaining_alerts = verify_response.json()
                            deleted_found = any(alert.get("id") == sos_id or alert.get("_id") == sos_id for alert in remaining_alerts)
                            
                            if not deleted_found:
                                self.log_test(
                                    "Verify SOS Deletion",
                                    True,
                                    "Deleted SOS alert no longer appears in admin list"
                                )
                            else:
                                self.log_test(
                                    "Verify SOS Deletion",
                                    False,
                                    "Deleted SOS alert still appears in admin list"
                                )
                    except Exception as e:
                        self.log_test(
                            "Verify SOS Deletion",
                            False,
                            f"Error verifying deletion: {str(e)}"
                        )
                else:
                    self.log_test(
                        "DELETE SOS Alert",
                        False,
                        f"Failed to delete SOS alert with status {response.status_code}",
                        {"response_text": response.text, "sos_id": sos_id}
                    )
            except Exception as e:
                self.log_test(
                    "DELETE SOS Alert",
                    False,
                    f"Error deleting SOS alert: {str(e)}"
                )
        else:
            self.log_test(
                "DELETE SOS Alert",
                False,
                "Not enough SOS alerts for deletion testing"
            )

    def test_data_persistence(self):
        """Test that all changes are persistent and stored correctly"""
        print("\n=== Testing Data Persistence ===")
        
        if not self.admin_token:
            self.log_test("Data Persistence", False, "No admin token available")
            return
        
        # Test 1: Verify channel changes are persistent
        print("\n--- Testing Channel Persistence ---")
        if self.created_group_ids:
            try:
                response = self.session.get(
                    f"{self.base_url}/admin/chat/groups",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    channels = response.json()
                    
                    # Look for our updated channels (should have "Aktualisiert" in name)
                    updated_channels = [ch for ch in channels if "Aktualisiert" in ch.get("name", "")]
                    
                    if len(updated_channels) > 0:
                        self.log_test(
                            "Channel Updates Persistent",
                            True,
                            f"Found {len(updated_channels)} channels with persistent updates",
                            {"updated_channels": [ch.get("name") for ch in updated_channels]}
                        )
                    else:
                        self.log_test(
                            "Channel Updates Persistent",
                            False,
                            "No updated channels found - changes may not be persistent"
                        )
                else:
                    self.log_test(
                        "Channel Updates Persistent",
                        False,
                        f"Failed to verify channel persistence with status {response.status_code}"
                    )
            except Exception as e:
                self.log_test(
                    "Channel Updates Persistent",
                    False,
                    f"Error verifying channel persistence: {str(e)}"
                )
        
        # Test 2: Verify user role changes are persistent
        print("\n--- Testing User Role Persistence ---")
        if self.test_user_id:
            try:
                response = self.session.get(
                    f"{self.base_url}/admin/users",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    users = response.json()
                    
                    # Find our test user
                    test_user = None
                    for user in users:
                        if user.get("id") == self.test_user_id or user.get("_id") == self.test_user_id:
                            test_user = user
                            break
                    
                    if test_user:
                        current_role = test_user.get("role", "unknown")
                        self.log_test(
                            "User Role Persistent",
                            True,
                            f"Test user role is persistent: {current_role}",
                            {"user_id": self.test_user_id, "current_role": current_role}
                        )
                    else:
                        self.log_test(
                            "User Role Persistent",
                            False,
                            "Test user not found in users list"
                        )
                else:
                    self.log_test(
                        "User Role Persistent",
                        False,
                        f"Failed to verify user role persistence with status {response.status_code}"
                    )
            except Exception as e:
                self.log_test(
                    "User Role Persistent",
                    False,
                    f"Error verifying user role persistence: {str(e)}"
                )
        
        # Test 3: Verify SOS alerts are properly stored
        print("\n--- Testing SOS Alerts Persistence ---")
        if self.created_sos_ids:
            try:
                response = self.session.get(
                    f"{self.base_url}/admin/sos-alerts",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    sos_alerts = response.json()
                    
                    # Check for our remaining SOS alerts
                    our_alerts = [alert for alert in sos_alerts if alert.get("id") in self.created_sos_ids or alert.get("_id") in self.created_sos_ids]
                    
                    if len(our_alerts) > 0:
                        # Check if any have been activated (status = "active")
                        activated_alerts = [alert for alert in our_alerts if alert.get("status") == "active"]
                        
                        self.log_test(
                            "SOS Alerts Persistent",
                            True,
                            f"Found {len(our_alerts)} persistent SOS alerts ({len(activated_alerts)} activated)",
                            {"total_alerts": len(our_alerts), "activated_alerts": len(activated_alerts)}
                        )
                    else:
                        self.log_test(
                            "SOS Alerts Persistent",
                            False,
                            "No persistent SOS alerts found"
                        )
                else:
                    self.log_test(
                        "SOS Alerts Persistent",
                        False,
                        f"Failed to verify SOS persistence with status {response.status_code}"
                    )
            except Exception as e:
                self.log_test(
                    "SOS Alerts Persistent",
                    False,
                    f"Error verifying SOS persistence: {str(e)}"
                )

    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        print("\n=== Cleaning Up Test Data ===")
        
        if not self.admin_token:
            return
        
        # Clean up remaining channels
        for group_id in self.created_group_ids:
            try:
                self.session.delete(
                    f"{self.base_url}/admin/chat/groups/{group_id}",
                    headers=self.get_auth_headers(self.admin_token)
                )
            except Exception:
                pass
        
        # Clean up remaining SOS alerts
        for sos_id in self.created_sos_ids:
            try:
                self.session.delete(
                    f"{self.base_url}/admin/sos/{sos_id}",
                    headers=self.get_auth_headers(self.admin_token)
                )
            except Exception:
                pass
        
        print("✅ Cleanup completed")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("FUNKGERÄT & SOS CRUD TESTING SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n🚨 FAILED TESTS ({failed_tests}):")
            for result in self.test_results:
                if not result["success"]:
                    print(f"❌ {result['test']}: {result['message']}")
        
        print(f"\n✅ PASSED TESTS ({passed_tests}):")
        for result in self.test_results:
            if result["success"]:
                print(f"✅ {result['test']}")
        
        print("\n" + "="*80)

    def run_all_tests(self):
        """Run all CRUD tests"""
        print("🚀 Starting Comprehensive Funkgerät & SOS CRUD Testing")
        print("="*80)
        
        # Setup
        if not self.setup_admin_authentication():
            print("❌ Cannot proceed without admin authentication")
            return
        
        if not self.create_test_user():
            print("⚠️ Proceeding without test user (some tests may be skipped)")
        
        # Run all test suites
        self.test_kanal_management_crud()
        self.test_chat_message_management()
        self.test_user_group_management()
        self.test_sos_alert_management()
        self.test_data_persistence()
        
        # Cleanup and summary
        self.cleanup_test_data()
        self.print_summary()

if __name__ == "__main__":
    tester = FunkgeraetSOSCRUDTester()
    tester.run_all_tests()