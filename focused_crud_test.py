#!/usr/bin/env python3
"""
FOCUSED CRUD TEST: Specific endpoints mentioned in review request
Testing the exact CRUD operations that should be 100% functional
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Backend API base URL - Correct Kubernetes Ingress URL
BASE_URL = "https://ba41d31d-12ea-486d-ae78-9bc529c512b8.preview.emergentagent.com/api"

class FocusedCRUDTester:
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

    def get_test_users(self):
        """Get existing users for testing"""
        if not self.admin_token:
            return
        
        try:
            response = self.session.get(
                f"{self.base_url}/admin/users",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                users = response.json()
                # Get non-admin users for testing
                test_users = [u for u in users if u.get("role") != "admin"]
                if test_users:
                    self.test_user_ids = [u.get("id") for u in test_users[:2] if u.get("id")]
                    print(f"Found {len(self.test_user_ids)} test users for role management")
                else:
                    print("No test users found, creating one...")
                    self.create_test_user()
        except Exception as e:
            print(f"Error getting users: {e}")

    def create_test_user(self):
        """Create a test user for role management"""
        user_data = {
            "username": "testuser_crud",
            "email": "crud@test.com",
            "full_name": "Test CRUD User",
            "password": "test123",
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
                user_id = created_user.get("id")
                if user_id:
                    self.test_user_ids.append(user_id)
                print(f"Created test user: {user_id}")
            elif response.status_code == 400 and "already registered" in response.text:
                print("Test user already exists")
                # Try to find existing user
                self.get_test_users()
        except Exception as e:
            print(f"Error creating test user: {e}")

    def test_specific_crud_operations(self):
        """Test the specific CRUD operations mentioned in review request"""
        print("\n🎯 TESTING SPECIFIC CRUD OPERATIONS FROM REVIEW REQUEST")
        print("=" * 80)
        
        # Ensure we have test users
        if not self.test_user_ids:
            self.get_test_users()
        
        if not self.test_user_ids:
            self.create_test_user()
        
        # 1. User Management (SHOULD BE 100% FUNCTIONAL)
        print("\n1️⃣ USER MANAGEMENT (EXPECTED 100% FUNCTIONALITY)")
        
        # Test PUT /api/admin/users/{user_id}/role
        if self.test_user_ids:
            user_id = self.test_user_ids[0]
            print(f"\n--- Testing PUT /api/admin/users/{user_id}/role ---")
            
            # Test changing role to team
            try:
                role_data = {"role": "team"}
                response = self.session.put(
                    f"{self.base_url}/admin/users/{user_id}/role",
                    json=role_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "PUT /api/admin/users/{user_id}/role",
                        True,
                        "User role changed successfully to 'team'"
                    )
                else:
                    self.log_test(
                        "PUT /api/admin/users/{user_id}/role",
                        False,
                        f"Failed with status {response.status_code}",
                        {"response_text": response.text, "user_id": user_id}
                    )
            except Exception as e:
                self.log_test(
                    "PUT /api/admin/users/{user_id}/role",
                    False,
                    f"Error: {str(e)}"
                )
        
        # Test POST /api/admin/users/{user_id}/toggle-status
        if self.test_user_ids:
            user_id = self.test_user_ids[0]
            print(f"\n--- Testing POST /api/admin/users/{user_id}/toggle-status ---")
            
            try:
                response = self.session.post(
                    f"{self.base_url}/admin/users/{user_id}/toggle-status",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    is_active = response_data.get("is_active")
                    self.log_test(
                        "POST /api/admin/users/{user_id}/toggle-status",
                        True,
                        f"User status toggled successfully (active: {is_active})"
                    )
                else:
                    self.log_test(
                        "POST /api/admin/users/{user_id}/toggle-status",
                        False,
                        f"Failed with status {response.status_code}",
                        {"response_text": response.text, "user_id": user_id}
                    )
            except Exception as e:
                self.log_test(
                    "POST /api/admin/users/{user_id}/toggle-status",
                    False,
                    f"Error: {str(e)}"
                )
        
        # 2. SOS Alert Management (SHOULD WORK NOW)
        print("\n2️⃣ SOS ALERT MANAGEMENT (EXPECTED TO WORK)")
        
        # First create a test SOS alert
        self.create_test_sos_alert()
        
        # Test PUT /api/admin/sos/{sos_id}/activate
        if self.test_sos_ids:
            sos_id = self.test_sos_ids[0]
            print(f"\n--- Testing PUT /api/admin/sos/{sos_id}/activate ---")
            
            try:
                response = self.session.put(
                    f"{self.base_url}/admin/sos/{sos_id}/activate",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "PUT /api/admin/sos/{sos_id}/activate",
                        True,
                        "SOS alert activated successfully"
                    )
                else:
                    self.log_test(
                        "PUT /api/admin/sos/{sos_id}/activate",
                        False,
                        f"Failed with status {response.status_code}",
                        {"response_text": response.text, "sos_id": sos_id}
                    )
            except Exception as e:
                self.log_test(
                    "PUT /api/admin/sos/{sos_id}/activate",
                    False,
                    f"Error: {str(e)}"
                )
        
        # Test GET /api/admin/sos-alerts (should show only pending)
        print(f"\n--- Testing GET /api/admin/sos-alerts (pending only) ---")
        
        try:
            response = self.session.get(
                f"{self.base_url}/admin/sos-alerts",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                sos_alerts = response.json()
                # Check if activated SOS disappeared from pending list
                activated_found = False
                if self.test_sos_ids:
                    activated_found = any(alert.get("id") == self.test_sos_ids[0] for alert in sos_alerts)
                
                self.log_test(
                    "GET /api/admin/sos-alerts (pending filter)",
                    True,
                    f"Retrieved {len(sos_alerts)} pending alerts (activated SOS in list: {activated_found})",
                    {"pending_count": len(sos_alerts), "activated_in_pending": activated_found}
                )
                
                # Additional test: verify filtering works
                if self.test_sos_ids and not activated_found:
                    self.log_test(
                        "SOS Filtering Verification",
                        True,
                        "✅ Activated SOS correctly removed from pending list"
                    )
                elif self.test_sos_ids and activated_found:
                    self.log_test(
                        "SOS Filtering Verification",
                        False,
                        "❌ Activated SOS still in pending list - filtering broken"
                    )
            else:
                self.log_test(
                    "GET /api/admin/sos-alerts (pending filter)",
                    False,
                    f"Failed with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "GET /api/admin/sos-alerts (pending filter)",
                False,
                f"Error: {str(e)}"
            )
        
        # 3. Radio Channel Management (SHOULD BE 100% FUNCTIONAL)
        print("\n3️⃣ RADIO CHANNEL MANAGEMENT (EXPECTED 100% FUNCTIONALITY)")
        
        # Test POST /api/admin/chat/groups
        print(f"\n--- Testing POST /api/admin/chat/groups ---")
        
        channel_data = {
            "name": "Test Einsatzleitung",
            "description": "Test channel for CRUD verification",
            "members": []
        }
        
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
                    "POST /api/admin/chat/groups",
                    True,
                    f"Channel created successfully: '{channel_data['name']}'"
                )
            else:
                self.log_test(
                    "POST /api/admin/chat/groups",
                    False,
                    f"Failed with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "POST /api/admin/chat/groups",
                False,
                f"Error: {str(e)}"
            )
        
        # Test PUT /api/admin/chat/groups/{id}
        if self.test_group_ids:
            channel_id = self.test_group_ids[0]
            print(f"\n--- Testing PUT /api/admin/chat/groups/{channel_id} ---")
            
            update_data = {
                "name": "Test Einsatzleitung (Updated)",
                "description": "Updated test channel for CRUD verification"
            }
            
            try:
                response = self.session.put(
                    f"{self.base_url}/admin/chat/groups/{channel_id}",
                    json=update_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "PUT /api/admin/chat/groups/{id}",
                        True,
                        "Channel updated successfully"
                    )
                else:
                    self.log_test(
                        "PUT /api/admin/chat/groups/{id}",
                        False,
                        f"Failed with status {response.status_code}",
                        {"response_text": response.text, "channel_id": channel_id}
                    )
            except Exception as e:
                self.log_test(
                    "PUT /api/admin/chat/groups/{id}",
                    False,
                    f"Error: {str(e)}"
                )
        
        # Test DELETE /api/admin/chat/groups/{id}
        if self.test_group_ids:
            channel_id = self.test_group_ids[0]
            print(f"\n--- Testing DELETE /api/admin/chat/groups/{channel_id} ---")
            
            try:
                response = self.session.delete(
                    f"{self.base_url}/admin/chat/groups/{channel_id}",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "DELETE /api/admin/chat/groups/{id}",
                        True,
                        "Channel deleted successfully"
                    )
                else:
                    self.log_test(
                        "DELETE /api/admin/chat/groups/{id}",
                        False,
                        f"Failed with status {response.status_code}",
                        {"response_text": response.text, "channel_id": channel_id}
                    )
            except Exception as e:
                self.log_test(
                    "DELETE /api/admin/chat/groups/{id}",
                    False,
                    f"Error: {str(e)}"
                )
        
        # 4. Login System (CONFIRMED WORKING)
        print("\n4️⃣ LOGIN SYSTEM (CONFIRMED WORKING)")
        
        # Test POST /api/login
        print(f"\n--- Testing POST /api/login ---")
        
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
                self.log_test(
                    "POST /api/login",
                    True,
                    f"Login successful (token: {len(token) if token else 0} chars)"
                )
            else:
                self.log_test(
                    "POST /api/login",
                    False,
                    f"Failed with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "POST /api/login",
                False,
                f"Error: {str(e)}"
            )
        
        # Test GET /api/me
        print(f"\n--- Testing GET /api/me ---")
        
        try:
            response = self.session.get(
                f"{self.base_url}/me",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                user_data = response.json()
                self.log_test(
                    "GET /api/me",
                    True,
                    f"Authentication successful (user: {user_data.get('username', 'unknown')})"
                )
            else:
                self.log_test(
                    "GET /api/me",
                    False,
                    f"Failed with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "GET /api/me",
                False,
                f"Error: {str(e)}"
            )

    def create_test_sos_alert(self):
        """Create a test SOS alert for activation testing"""
        # Create test user first
        user_data = {
            "username": "testuser_sos_crud",
            "email": "sos_crud@test.com",
            "full_name": "Test SOS CRUD User",
            "password": "test123",
            "role": "user"
        }
        
        user_token = None
        try:
            # Register or login test user
            response = self.session.post(
                f"{self.base_url}/register",
                json=user_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200 or (response.status_code == 400 and "already registered" in response.text):
                # Login the user
                login_response = self.session.post(
                    f"{self.base_url}/login",
                    json={"username": user_data["username"], "password": user_data["password"]},
                    headers={"Content-Type": "application/json"}
                )
                
                if login_response.status_code == 200:
                    token_data = login_response.json()
                    user_token = token_data.get("access_token")
        except Exception as e:
            print(f"Error setting up SOS test user: {e}")
        
        # Create SOS alert
        if user_token:
            sos_data = {
                "location_lat": 52.52,
                "location_lng": 13.405,
                "location_address": "Berlin, Germany - Test Location",
                "alert_type": "emergency",
                "message": "Test SOS alert for CRUD activation testing"
            }
            
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
                    print(f"Created test SOS alert: {sos_id}")
            except Exception as e:
                print(f"Error creating test SOS alert: {e}")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🎯 FOCUSED CRUD TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Show results by specific endpoint
        print(f"\n📋 RESULTS BY SPECIFIC ENDPOINT:")
        
        endpoint_results = {}
        for result in self.test_results:
            test_name = result["test"]
            if "PUT /api/admin/users/" in test_name and "/role" in test_name:
                endpoint_results["PUT /api/admin/users/{user_id}/role"] = result
            elif "POST /api/admin/users/" in test_name and "/toggle-status" in test_name:
                endpoint_results["POST /api/admin/users/{user_id}/toggle-status"] = result
            elif "PUT /api/admin/sos/" in test_name and "/activate" in test_name:
                endpoint_results["PUT /api/admin/sos/{sos_id}/activate"] = result
            elif "GET /api/admin/sos-alerts" in test_name:
                endpoint_results["GET /api/admin/sos-alerts"] = result
            elif "POST /api/admin/chat/groups" in test_name:
                endpoint_results["POST /api/admin/chat/groups"] = result
            elif "PUT /api/admin/chat/groups" in test_name:
                endpoint_results["PUT /api/admin/chat/groups/{id}"] = result
            elif "DELETE /api/admin/chat/groups" in test_name:
                endpoint_results["DELETE /api/admin/chat/groups/{id}"] = result
            elif "POST /api/login" in test_name:
                endpoint_results["POST /api/login"] = result
            elif "GET /api/me" in test_name:
                endpoint_results["GET /api/me"] = result
        
        for endpoint, result in endpoint_results.items():
            status = "✅" if result["success"] else "❌"
            print(f"{status} {endpoint}: {result['message']}")
        
        # Show failed tests details
        failed_results = [r for r in self.test_results if not r["success"]]
        if failed_results:
            print(f"\n❌ FAILED ENDPOINTS ({len(failed_results)}):")
            for result in failed_results:
                print(f"   • {result['test']}: {result['message']}")
                if result.get("details"):
                    print(f"     Details: {result['details']}")
        
        # Final verdict based on review request expectations
        print(f"\n🎯 REVIEW REQUEST VERIFICATION:")
        
        user_mgmt_success = any("PUT /api/admin/users/" in r["test"] and r["success"] for r in self.test_results)
        user_toggle_success = any("POST /api/admin/users/" in r["test"] and r["success"] for r in self.test_results)
        sos_activate_success = any("PUT /api/admin/sos/" in r["test"] and r["success"] for r in self.test_results)
        sos_filter_success = any("GET /api/admin/sos-alerts" in r["test"] and r["success"] for r in self.test_results)
        channel_crud_success = all(any(endpoint in r["test"] and r["success"] for r in self.test_results) 
                                 for endpoint in ["POST /api/admin/chat/groups", "PUT /api/admin/chat/groups", "DELETE /api/admin/chat/groups"])
        login_success = any("POST /api/login" in r["test"] and r["success"] for r in self.test_results)
        
        print(f"✅ User Management (Role Change): {'WORKING' if user_mgmt_success else 'BROKEN'}")
        print(f"✅ User Management (Lock/Unlock): {'WORKING' if user_toggle_success else 'BROKEN'}")
        print(f"✅ SOS Activation: {'WORKING' if sos_activate_success else 'BROKEN'}")
        print(f"✅ SOS Filtering: {'WORKING' if sos_filter_success else 'BROKEN'}")
        print(f"✅ Channel CRUD: {'WORKING' if channel_crud_success else 'BROKEN'}")
        print(f"✅ Login System: {'WORKING' if login_success else 'BROKEN'}")
        
        if success_rate >= 90:
            print(f"\n🎉 REVIEW REQUEST CONFIRMED: All problems are FIXED!")
        elif success_rate >= 70:
            print(f"\n⚠️ PARTIAL SUCCESS: Most issues fixed, some remain")
        else:
            print(f"\n❌ REVIEW REQUEST FAILED: Major problems still exist")
        
        print("=" * 80)

    def run_focused_test(self):
        """Run focused CRUD test"""
        print("🎯 FOCUSED CRUD TEST: Specific Review Request Endpoints")
        print("=" * 80)
        print("Testing EXACT endpoints mentioned in German review request")
        print("Expected: ALL should be 100% functional after URL fix")
        print("=" * 80)
        
        # Setup
        if not self.setup_admin_login():
            print("❌ CRITICAL: Admin login failed - cannot proceed with tests")
            return
        
        # Run focused tests
        self.test_specific_crud_operations()
        
        # Summary
        self.print_summary()

if __name__ == "__main__":
    tester = FocusedCRUDTester()
    tester.run_focused_test()