#!/usr/bin/env python3
"""
FINAL CRUD TEST: All CRUD Operations After URL Fix
Testing all critical CRUD operations that should be 100% functional after URL and Pydantic v2 migration
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Backend API base URL - Correct Kubernetes Ingress URL
BASE_URL = "https://ba41d31d-12ea-486d-ae78-9bc529c512b8.preview.emergentagent.com/api"

class FinalCRUDTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.test_results = []
        self.admin_token = None
        self.test_user_ids = []
        self.test_sos_ids = []
        self.test_group_ids = []
        
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
        print("\n=== SETUP: Admin Login ===")
        
        # Create admin if not exists
        try:
            response = self.session.post(f"{self.base_url}/create-admin")
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
                f"{self.base_url}/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.admin_token = token_data.get("access_token")
                self.log_test(
                    "Admin Login Setup",
                    True,
                    f"Admin login successful, token length: {len(self.admin_token) if self.admin_token else 0}"
                )
                return True
            else:
                self.log_test(
                    "Admin Login Setup",
                    False,
                    f"Admin login failed with status {response.status_code}",
                    {"response_text": response.text}
                )
                return False
        except Exception as e:
            self.log_test(
                "Admin Login Setup",
                False,
                f"Error during admin login: {str(e)}"
            )
            return False

    def test_user_management_crud(self):
        """Test User Management CRUD - SHOULD BE 100% FUNCTIONAL"""
        print("\n=== TESTING USER MANAGEMENT CRUD (EXPECTED 100% SUCCESS) ===")
        
        if not self.admin_token:
            self.log_test("User Management CRUD", False, "No admin token available")
            return
        
        # First, create test users for role management
        test_users = [
            {
                "username": "testuser_role1",
                "email": "role1@test.com",
                "full_name": "Test User Role 1",
                "password": "test123",
                "role": "user"
            },
            {
                "username": "testuser_role2", 
                "email": "role2@test.com",
                "full_name": "Test User Role 2",
                "password": "test123",
                "role": "user"
            }
        ]
        
        # Create test users
        for i, user_data in enumerate(test_users):
            try:
                response = self.session.post(
                    f"{self.base_url}/register",
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
                    # User exists, get from admin users list
                    try:
                        users_response = self.session.get(
                            f"{self.base_url}/admin/users",
                            headers=self.get_auth_headers(self.admin_token)
                        )
                        if users_response.status_code == 200:
                            users = users_response.json()
                            existing_user = next((u for u in users if u.get("username") == user_data["username"]), None)
                            if existing_user:
                                user_id = existing_user.get("id")
                                if user_id:
                                    self.test_user_ids.append(user_id)
                                self.log_test(
                                    f"Get Existing Test User {i+1}",
                                    True,
                                    f"Found existing user '{user_data['username']}'",
                                    {"user_id": user_id}
                                )
                    except Exception as e:
                        self.log_test(
                            f"Get Existing Test User {i+1}",
                            False,
                            f"Error finding existing user: {str(e)}"
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
        
        # Test 1: PUT /api/admin/users/{user_id}/role (Change user role)
        print("\n--- Testing User Role Changes ---")
        
        if self.test_user_ids:
            user_id = self.test_user_ids[0]
            
            # Test changing to different roles
            roles_to_test = ["team", "admin", "emergency", "user"]
            
            for role in roles_to_test:
                try:
                    role_data = {"role": role}
                    response = self.session.put(
                        f"{self.base_url}/admin/users/{user_id}/role",
                        json=role_data,
                        headers=self.get_auth_headers(self.admin_token)
                    )
                    
                    if response.status_code == 200:
                        self.log_test(
                            f"Change User Role to {role.upper()}",
                            True,
                            f"User role successfully changed to {role}"
                        )
                    else:
                        self.log_test(
                            f"Change User Role to {role.upper()}",
                            False,
                            f"Failed to change role to {role} with status {response.status_code}",
                            {"response_text": response.text, "user_id": user_id}
                        )
                except Exception as e:
                    self.log_test(
                        f"Change User Role to {role.upper()}",
                        False,
                        f"Error changing role to {role}: {str(e)}"
                    )
        
        # Test 2: POST /api/admin/users/{user_id}/toggle-status (Lock/unlock user)
        print("\n--- Testing User Status Toggle ---")
        
        if len(self.test_user_ids) > 1:
            user_id = self.test_user_ids[1]
            
            # Test toggling user status (lock/unlock)
            for action in ["lock", "unlock"]:
                try:
                    response = self.session.post(
                        f"{self.base_url}/admin/users/{user_id}/toggle-status",
                        headers=self.get_auth_headers(self.admin_token)
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        is_active = response_data.get("is_active", True)
                        status_text = "unlocked" if is_active else "locked"
                        self.log_test(
                            f"Toggle User Status ({action})",
                            True,
                            f"User status toggled successfully - user is now {status_text}",
                            {"is_active": is_active}
                        )
                    else:
                        self.log_test(
                            f"Toggle User Status ({action})",
                            False,
                            f"Failed to toggle user status with status {response.status_code}",
                            {"response_text": response.text, "user_id": user_id}
                        )
                except Exception as e:
                    self.log_test(
                        f"Toggle User Status ({action})",
                        False,
                        f"Error toggling user status: {str(e)}"
                    )

    def test_sos_alert_management(self):
        """Test SOS Alert Management - SHOULD WORK NOW"""
        print("\n=== TESTING SOS ALERT MANAGEMENT (EXPECTED TO WORK) ===")
        
        if not self.admin_token:
            self.log_test("SOS Alert Management", False, "No admin token available")
            return
        
        # First create some test SOS alerts
        print("\n--- Creating Test SOS Alerts ---")
        
        test_sos_alerts = [
            {
                "location_lat": 52.52,
                "location_lng": 13.405,
                "location_address": "Berlin, Germany",
                "alert_type": "emergency",
                "message": "Test emergency alert for activation testing"
            },
            {
                "location_lat": 48.8566,
                "location_lng": 2.3522,
                "location_address": "Paris, France", 
                "alert_type": "medical",
                "message": "Test medical alert for filtering testing"
            }
        ]
        
        # Create test user first to create SOS alerts
        test_user_data = {
            "username": "testuser_sos",
            "email": "sos@test.com",
            "full_name": "Test SOS User",
            "password": "test123",
            "role": "user"
        }
        
        user_token = None
        try:
            # Register or login test user
            response = self.session.post(
                f"{self.base_url}/register",
                json=test_user_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200 or (response.status_code == 400 and "already registered" in response.text):
                # Login the user
                login_response = self.session.post(
                    f"{self.base_url}/login",
                    json={"username": test_user_data["username"], "password": test_user_data["password"]},
                    headers={"Content-Type": "application/json"}
                )
                
                if login_response.status_code == 200:
                    token_data = login_response.json()
                    user_token = token_data.get("access_token")
        except Exception as e:
            print(f"Error setting up test user: {e}")
        
        # Create SOS alerts as user
        if user_token:
            for i, sos_data in enumerate(test_sos_alerts):
                try:
                    response = self.session.post(
                        f"{self.base_url}/sos-alert",
                        json=sos_data,
                        headers=self.get_auth_headers(user_token)
                    )
                    
                    if response.status_code == 200:
                        created_sos = response.json()
                        sos_id = created_sos.get("id")
                        if sos_id:
                            self.test_sos_ids.append(sos_id)
                        self.log_test(
                            f"Create Test SOS Alert {i+1}",
                            True,
                            f"SOS alert created successfully: {sos_data['alert_type']}",
                            {"sos_id": sos_id}
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
        
        # Test 1: PUT /api/admin/sos/{sos_id}/activate (Activate SOS)
        print("\n--- Testing SOS Activation ---")
        
        if self.test_sos_ids:
            sos_id = self.test_sos_ids[0]
            
            try:
                response = self.session.put(
                    f"{self.base_url}/admin/sos/{sos_id}/activate",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    self.log_test(
                        "Activate SOS Alert",
                        True,
                        f"SOS alert activated successfully: {response_data.get('message', '')}",
                        {"response": response_data}
                    )
                else:
                    self.log_test(
                        "Activate SOS Alert",
                        False,
                        f"Failed to activate SOS alert with status {response.status_code}",
                        {"response_text": response.text, "sos_id": sos_id}
                    )
            except Exception as e:
                self.log_test(
                    "Activate SOS Alert",
                    False,
                    f"Error activating SOS alert: {str(e)}"
                )
        
        # Test 2: GET /api/admin/sos-alerts (Show only pending SOS)
        print("\n--- Testing SOS Alerts Filtering ---")
        
        try:
            response = self.session.get(
                f"{self.base_url}/admin/sos-alerts",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                sos_alerts = response.json()
                
                # Check if activated SOS is removed from pending list
                activated_sos_found = any(alert.get("id") == self.test_sos_ids[0] for alert in sos_alerts) if self.test_sos_ids else False
                
                self.log_test(
                    "Get Pending SOS Alerts",
                    True,
                    f"Retrieved {len(sos_alerts)} pending SOS alerts (activated SOS in list: {activated_sos_found})",
                    {"alerts_count": len(sos_alerts), "activated_in_pending": activated_sos_found}
                )
                
                # Verify filtering works - activated alerts should not be in pending list
                if self.test_sos_ids and not activated_sos_found:
                    self.log_test(
                        "SOS Filtering After Activation",
                        True,
                        "Activated SOS correctly removed from pending list"
                    )
                elif self.test_sos_ids and activated_sos_found:
                    self.log_test(
                        "SOS Filtering After Activation",
                        False,
                        "Activated SOS still appears in pending list - filtering not working"
                    )
            else:
                self.log_test(
                    "Get Pending SOS Alerts",
                    False,
                    f"Failed to get SOS alerts with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Get Pending SOS Alerts",
                False,
                f"Error getting SOS alerts: {str(e)}"
            )

    def test_radio_channel_management(self):
        """Test Radio Channel Management CRUD - SHOULD BE 100% FUNCTIONAL"""
        print("\n=== TESTING RADIO CHANNEL MANAGEMENT CRUD (EXPECTED 100% SUCCESS) ===")
        
        if not self.admin_token:
            self.log_test("Radio Channel Management", False, "No admin token available")
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
            }
        ]
        
        # Test 1: POST /api/admin/chat/groups (Create channel)
        print("\n--- Testing Channel Creation ---")
        
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
                        self.test_group_ids.append(channel_id)
                    self.log_test(
                        f"Create Channel {i+1} ({channel_data['name']})",
                        True,
                        f"Channel '{channel_data['name']}' created successfully",
                        {"channel_id": channel_id}
                    )
                else:
                    self.log_test(
                        f"Create Channel {i+1} ({channel_data['name']})",
                        False,
                        f"Failed to create channel with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    f"Create Channel {i+1} ({channel_data['name']})",
                    False,
                    f"Error creating channel: {str(e)}"
                )
        
        # Test 2: GET /api/admin/chat/groups (Read channels)
        print("\n--- Testing Channel Retrieval ---")
        
        try:
            response = self.session.get(
                f"{self.base_url}/admin/chat/groups",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                channels = response.json()
                self.log_test(
                    "Get All Channels",
                    True,
                    f"Retrieved {len(channels)} channels successfully",
                    {"channels_count": len(channels)}
                )
            else:
                self.log_test(
                    "Get All Channels",
                    False,
                    f"Failed to get channels with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Get All Channels",
                False,
                f"Error getting channels: {str(e)}"
            )
        
        # Test 3: PUT /api/admin/chat/groups/{id} (Update channel)
        print("\n--- Testing Channel Updates ---")
        
        if self.test_group_ids:
            channel_id = self.test_group_ids[0]
            update_data = {
                "name": "Einsatzleitung (Aktualisiert)",
                "description": "Aktualisierte Hauptkommunikation für Einsatzleitung - Test Update",
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
                        "Update Channel",
                        True,
                        f"Channel updated successfully: '{updated_channel.get('name', '')}'",
                        {"updated_channel": updated_channel}
                    )
                else:
                    self.log_test(
                        "Update Channel",
                        False,
                        f"Failed to update channel with status {response.status_code}",
                        {"response_text": response.text, "channel_id": channel_id}
                    )
            except Exception as e:
                self.log_test(
                    "Update Channel",
                    False,
                    f"Error updating channel: {str(e)}"
                )
        
        # Test 4: DELETE /api/admin/chat/groups/{id} (Delete channel)
        print("\n--- Testing Channel Deletion ---")
        
        if len(self.test_group_ids) > 1:
            channel_id = self.test_group_ids[1]
            
            try:
                response = self.session.delete(
                    f"{self.base_url}/admin/chat/groups/{channel_id}",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "Delete Channel",
                        True,
                        "Channel deleted successfully"
                    )
                    # Remove from our list since it's deleted
                    self.test_group_ids.remove(channel_id)
                else:
                    self.log_test(
                        "Delete Channel",
                        False,
                        f"Failed to delete channel with status {response.status_code}",
                        {"response_text": response.text, "channel_id": channel_id}
                    )
            except Exception as e:
                self.log_test(
                    "Delete Channel",
                    False,
                    f"Error deleting channel: {str(e)}"
                )

    def test_login_system(self):
        """Test Login System - CONFIRMED WORKING"""
        print("\n=== TESTING LOGIN SYSTEM (CONFIRMED FUNCTIONAL) ===")
        
        # Test 1: POST /api/login
        print("\n--- Testing Login API ---")
        
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
                token = token_data.get("access_token")
                user = token_data.get("user", {})
                
                self.log_test(
                    "Login API Test",
                    True,
                    f"Login successful - Token: {len(token) if token else 0} chars, Role: {user.get('role', 'unknown')}",
                    {"token_length": len(token) if token else 0, "user_role": user.get("role")}
                )
            else:
                self.log_test(
                    "Login API Test",
                    False,
                    f"Login failed with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Login API Test",
                False,
                f"Error during login: {str(e)}"
            )
        
        # Test 2: GET /api/me
        print("\n--- Testing User Authentication ---")
        
        if self.admin_token:
            try:
                response = self.session.get(
                    f"{self.base_url}/me",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    self.log_test(
                        "User Authentication Test",
                        True,
                        f"Authentication successful - User: {user_data.get('username', 'unknown')}, Role: {user_data.get('role', 'unknown')}",
                        {"user": user_data}
                    )
                else:
                    self.log_test(
                        "User Authentication Test",
                        False,
                        f"Authentication failed with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    "User Authentication Test",
                    False,
                    f"Error during authentication: {str(e)}"
                )

    def run_all_tests(self):
        """Run all CRUD tests"""
        print("🚨 FINAL CRUD TEST: ALL CRUD OPERATIONS AFTER URL-FIX")
        print("=" * 80)
        print("Testing all critical CRUD operations that should be 100% functional")
        print("after URL fix and Pydantic v2 migration")
        print("=" * 80)
        
        # Setup
        if not self.setup_admin_login():
            print("❌ CRITICAL: Admin login failed - cannot proceed with tests")
            return
        
        # Run all tests
        self.test_login_system()
        self.test_user_management_crud()
        self.test_sos_alert_management()
        self.test_radio_channel_management()
        
        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🎯 FINAL TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Group results by category
        categories = {
            "Login System": [],
            "User Management": [],
            "SOS Alert Management": [],
            "Radio Channel Management": [],
            "Setup": []
        }
        
        for result in self.test_results:
            test_name = result["test"]
            if "Login" in test_name or "Authentication" in test_name:
                categories["Login System"].append(result)
            elif "User" in test_name and ("Role" in test_name or "Status" in test_name or "Toggle" in test_name):
                categories["User Management"].append(result)
            elif "SOS" in test_name or "Activate" in test_name:
                categories["SOS Alert Management"].append(result)
            elif "Channel" in test_name or "Group" in test_name:
                categories["Radio Channel Management"].append(result)
            else:
                categories["Setup"].append(result)
        
        print("\n📊 RESULTS BY CATEGORY:")
        for category, results in categories.items():
            if results:
                passed = sum(1 for r in results if r["success"])
                total = len(results)
                rate = (passed / total * 100) if total > 0 else 0
                status = "✅" if rate == 100 else "⚠️" if rate >= 50 else "❌"
                print(f"{status} {category}: {passed}/{total} ({rate:.1f}%)")
        
        # Show failed tests
        failed_results = [r for r in self.test_results if not r["success"]]
        if failed_results:
            print(f"\n❌ FAILED TESTS ({len(failed_results)}):")
            for result in failed_results:
                print(f"   • {result['test']}: {result['message']}")
        
        # Final verdict
        print(f"\n🎯 FINAL VERDICT:")
        if success_rate >= 90:
            print("✅ EXCELLENT: All major CRUD operations working as expected!")
        elif success_rate >= 70:
            print("⚠️ GOOD: Most CRUD operations working, minor issues remain")
        else:
            print("❌ CRITICAL: Major CRUD problems still exist - fixes needed")
        
        print("=" * 80)

if __name__ == "__main__":
    tester = FinalCRUDTester()
    tester.run_all_tests()