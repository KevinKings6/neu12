#!/usr/bin/env python3
"""
Funkgerät (Radio) System API Tests - Using Internal URL for Ingress-Blocked Endpoints
Tests the new radio system functionality with admin authentication
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Use internal URL for endpoints blocked by ingress
INTERNAL_URL = "http://localhost:8001/api"
EXTERNAL_URL = "https://emergency-sos-3.preview.emergentagent.com/api"

class FunkgeraetAPITester:
    def __init__(self):
        self.internal_url = INTERNAL_URL
        self.external_url = EXTERNAL_URL
        self.session = requests.Session()
        self.test_results = []
        self.admin_token = None
        self.user_token = None
        self.test_user_id = None
        self.created_group_ids = []
        self.created_message_ids = []
        
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

    def login_admin(self):
        """Login as admin to get token"""
        print("=== Logging in as Admin ===")
        
        login_data = {"username": "admin", "password": "admin123"}
        
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
                    "Admin Login",
                    True,
                    f"Admin login successful, role: {admin_user.get('role', 'unknown')}"
                )
                return True
            else:
                self.log_test(
                    "Admin Login",
                    False,
                    f"Failed to login admin with status {response.status_code}",
                    {"response_text": response.text}
                )
                return False
        except Exception as e:
            self.log_test(
                "Admin Login",
                False,
                f"Error logging in admin: {str(e)}"
            )
            return False

    def get_test_user_id(self):
        """Get test user ID from admin users list"""
        if not self.admin_token:
            return
        
        try:
            response = self.session.get(
                f"{self.external_url}/admin/users",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                users = response.json()
                for user in users:
                    if user.get("username") == "testuser_emergency":
                        self.test_user_id = user.get("id") or user.get("_id")
                        break
        except Exception:
            pass  # Ignore errors

    def test_chat_groups_management(self):
        """Test Chat Groups Management (POST, GET, PUT, DELETE /api/admin/chat/groups)"""
        print("\n=== Testing Chat Groups Management ===")
        
        if not self.admin_token:
            self.log_test("Chat Groups Management", False, "No admin token available")
            return
        
        # Test data for chat groups
        test_groups = [
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
        
        # Test 1: Create Chat Groups (POST /api/admin/chat/groups)
        for i, group_data in enumerate(test_groups):
            try:
                response = self.session.post(
                    f"{self.internal_url}/admin/chat/groups",
                    json=group_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    created_group = response.json()
                    group_id = created_group.get("_id") or created_group.get("id")
                    if group_id:
                        self.created_group_ids.append(group_id)
                    
                    self.log_test(
                        f"Create Chat Group {i+1}",
                        True,
                        f"Group '{group_data['name']}' created successfully",
                        {"group_id": group_id}
                    )
                else:
                    self.log_test(
                        f"Create Chat Group {i+1}",
                        False,
                        f"Failed to create group with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    f"Create Chat Group {i+1}",
                    False,
                    f"Error creating group: {str(e)}"
                )
        
        # Test 2: Get All Chat Groups (GET /api/admin/chat/groups)
        try:
            response = self.session.get(
                f"{self.internal_url}/admin/chat/groups",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                groups = response.json()
                self.log_test(
                    "Get All Chat Groups",
                    True,
                    f"Retrieved {len(groups)} chat groups"
                )
            else:
                self.log_test(
                    "Get All Chat Groups",
                    False,
                    f"Failed to get groups with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Get All Chat Groups",
                False,
                f"Error getting groups: {str(e)}"
            )
        
        # Test 3: Update Chat Group (PUT /api/admin/chat/groups/{id})
        if self.created_group_ids:
            group_id = self.created_group_ids[0]
            update_data = {
                "name": "Einsatzleitung (Aktualisiert)",
                "description": "Aktualisierte Hauptkommunikation für Einsatzleitung"
            }
            
            try:
                response = self.session.put(
                    f"{self.internal_url}/admin/chat/groups/{group_id}",
                    json=update_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    updated_group = response.json()
                    self.log_test(
                        "Update Chat Group",
                        True,
                        f"Group updated successfully: '{updated_group.get('name', '')}'",
                    )
                else:
                    self.log_test(
                        "Update Chat Group",
                        False,
                        f"Failed to update group with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    "Update Chat Group",
                    False,
                    f"Error updating group: {str(e)}"
                )
        
        # Test 4: Delete Chat Group (DELETE /api/admin/chat/groups/{id})
        if len(self.created_group_ids) > 2:  # Keep some groups, delete one for testing
            group_id = self.created_group_ids.pop()  # Remove last group from list and delete it
            
            try:
                response = self.session.delete(
                    f"{self.internal_url}/admin/chat/groups/{group_id}",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "Delete Chat Group",
                        True,
                        "Chat group deleted successfully"
                    )
                else:
                    self.log_test(
                        "Delete Chat Group",
                        False,
                        f"Failed to delete group with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    "Delete Chat Group",
                    False,
                    f"Error deleting group: {str(e)}"
                )

    def test_chat_messages(self):
        """Test Chat Messages (POST, GET /api/admin/chat)"""
        print("\n=== Testing Chat Messages ===")
        
        if not self.admin_token:
            self.log_test("Chat Messages", False, "No admin token available")
            return
        
        # Test messages with different types
        test_messages = [
            {
                "message": "Einsatz in der Hauptstraße 123 - Verkehrsunfall mit Personenschaden",
                "chat_type": "admin",
                "group_id": self.created_group_ids[0] if self.created_group_ids else None,
                "is_voice_message": False
            },
            {
                "message": "Rettungswagen ist unterwegs, ETA 5 Minuten",
                "chat_type": "admin",
                "group_id": self.created_group_ids[1] if len(self.created_group_ids) > 1 else None,
                "is_voice_message": False
            },
            {
                "message": "Sprach-Nachricht: Notfall-Briefing",
                "chat_type": "admin",
                "group_id": self.created_group_ids[0] if self.created_group_ids else None,
                "is_voice_message": True,
                "voice_data": "base64_encoded_voice_data_example",
                "voice_duration": 30
            }
        ]
        
        # Test 1: Send Chat Messages (POST /api/admin/chat)
        for i, message_data in enumerate(test_messages):
            try:
                response = self.session.post(
                    f"{self.external_url}/admin/chat",  # This endpoint works on external URL
                    json=message_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    created_message = response.json()
                    message_id = created_message.get("_id") or created_message.get("id")
                    if message_id:
                        self.created_message_ids.append(message_id)
                    
                    message_type = "Voice Message" if message_data.get("is_voice_message") else "Text Message"
                    self.log_test(
                        f"Send Chat Message {i+1} ({message_type})",
                        True,
                        f"Message sent successfully to group"
                    )
                else:
                    self.log_test(
                        f"Send Chat Message {i+1}",
                        False,
                        f"Failed to send message with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    f"Send Chat Message {i+1}",
                    False,
                    f"Error sending message: {str(e)}"
                )
        
        # Test 2: Get Chat Messages by Group (GET /api/admin/chat?group_id=xxx)
        if self.created_group_ids:
            group_id = self.created_group_ids[0]
            try:
                response = self.session.get(
                    f"{self.external_url}/admin/chat",  # This endpoint works on external URL
                    params={"group_id": group_id, "chat_type": "admin"},
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    messages = response.json()
                    self.log_test(
                        "Get Chat Messages by Group",
                        True,
                        f"Retrieved {len(messages)} messages from group"
                    )
                else:
                    self.log_test(
                        "Get Chat Messages by Group",
                        False,
                        f"Failed to get messages with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    "Get Chat Messages by Group",
                    False,
                    f"Error getting messages: {str(e)}"
                )

    def test_user_role_management(self):
        """Test User Role Management (PUT /api/admin/users/{user_id}/role)"""
        print("\n=== Testing User Role Management ===")
        
        if not self.admin_token or not self.test_user_id:
            self.log_test("User Role Management", False, "No admin token or test user ID available")
            return
        
        # Test changing user role to admin
        role_data = {"role": "admin"}
        
        try:
            response = self.session.put(
                f"{self.internal_url}/admin/users/{self.test_user_id}/role",  # Use internal URL
                json=role_data,
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                self.log_test(
                    "Change User Role to Admin",
                    True,
                    "User role successfully changed to admin"
                )
                
                # Change back to user role
                role_data = {"role": "user"}
                response = self.session.put(
                    f"{self.internal_url}/admin/users/{self.test_user_id}/role",
                    json=role_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "Change User Role back to User",
                        True,
                        "User role successfully changed back to user"
                    )
                else:
                    self.log_test(
                        "Change User Role back to User",
                        False,
                        f"Failed to change role back with status {response.status_code}"
                    )
            else:
                self.log_test(
                    "Change User Role to Admin",
                    False,
                    f"Failed to change user role with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Change User Role to Admin",
                False,
                f"Error changing user role: {str(e)}"
            )

    def test_user_group_assignments(self):
        """Test User Group Assignments (PUT /api/admin/users/{user_id}/groups)"""
        print("\n=== Testing User Group Assignments ===")
        
        if not self.admin_token or not self.test_user_id or not self.created_group_ids:
            self.log_test("User Group Assignments", False, "Missing admin token, user ID, or group IDs")
            return
        
        # Assign user to multiple groups
        groups_data = {"group_ids": self.created_group_ids[:2]}  # Assign to first 2 groups
        
        try:
            response = self.session.put(
                f"{self.internal_url}/admin/users/{self.test_user_id}/groups",  # Use internal URL
                json=groups_data,
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                self.log_test(
                    "Assign User to Groups",
                    True,
                    f"User successfully assigned to {len(groups_data['group_ids'])} groups"
                )
            else:
                self.log_test(
                    "Assign User to Groups",
                    False,
                    f"Failed to assign user to groups with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Assign User to Groups",
                False,
                f"Error assigning user to groups: {str(e)}"
            )

    def test_admin_profile_update(self):
        """Test Admin Profile Update (PUT /api/admin/profile)"""
        print("\n=== Testing Admin Profile Update ===")
        
        if not self.admin_token:
            self.log_test("Admin Profile Update", False, "No admin token available")
            return
        
        profile_data = {"full_name": "Administrator (Funkgerät System)"}
        
        try:
            response = self.session.put(
                f"{self.internal_url}/admin/profile",  # Use internal URL
                json=profile_data,
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                updated_admin = response.json()
                self.log_test(
                    "Update Admin Profile",
                    True,
                    f"Admin name updated to: '{updated_admin.get('full_name', '')}'"
                )
                
                # Change back to original name
                original_profile_data = {"full_name": "System Administrator"}
                self.session.put(
                    f"{self.internal_url}/admin/profile",
                    json=original_profile_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
            else:
                self.log_test(
                    "Update Admin Profile",
                    False,
                    f"Failed to update admin profile with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Update Admin Profile",
                False,
                f"Error updating admin profile: {str(e)}"
            )

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n=== Cleaning Up Test Data ===")
        
        # Delete remaining groups
        for group_id in self.created_group_ids:
            try:
                self.session.delete(
                    f"{self.internal_url}/admin/chat/groups/{group_id}",
                    headers=self.get_auth_headers(self.admin_token)
                )
            except Exception:
                pass  # Ignore cleanup errors

    def run_all_tests(self):
        """Run all Funkgerät system tests"""
        print("🚨 Funkgerät (Radio) System API Testing Started")
        print(f"External URL: {self.external_url}")
        print(f"Internal URL: {self.internal_url}")
        print("=" * 80)
        
        # Login as admin
        if not self.login_admin():
            print("❌ Cannot proceed without admin login")
            return False
        
        # Get test user ID
        self.get_test_user_id()
        
        # Run all test suites
        self.test_chat_groups_management()
        self.test_chat_messages()
        self.test_user_role_management()
        self.test_user_group_assignments()
        self.test_admin_profile_update()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Print summary
        self.print_summary()
        
        return len([r for r in self.test_results if not r["success"]]) == 0

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🚨 FUNKGERÄT SYSTEM API TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("=" * 60)


def main():
    """Main function to run Funkgerät tests"""
    tester = FunkgeraetAPITester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()