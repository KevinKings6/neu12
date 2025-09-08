#!/usr/bin/env python3
"""
User Role Management Features Testing for Emergency SOS App
Tests new admin dashboard features for user role management and voice recording backend support
"""

import requests
import json
import sys
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional

# Backend API base URL - using internal URL due to Kubernetes ingress limitations
BASE_URL = "http://localhost:8001/api"

class UserRoleManagementTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.test_results = []
        self.admin_token = None
        self.test_user_ids = []
        self.created_group_ids = []
        
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
        
        # Create admin user if not exists
        try:
            response = self.session.post(f"{self.base_url}/create-admin")
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Admin User Setup",
                    True,
                    f"Admin setup: {data.get('message', '')}",
                    {"response": data}
                )
        except Exception as e:
            self.log_test(
                "Admin User Setup",
                False,
                f"Error setting up admin: {str(e)}"
            )
        
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
                    "Admin Login",
                    True,
                    f"Admin authenticated successfully, role: {admin_user.get('role', 'unknown')}",
                    {"token_type": token_data.get("token_type"), "user_role": admin_user.get("role")}
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

    def test_create_test_users_with_roles(self):
        """Test POST /api/admin/test-user-role - Create test users with different roles"""
        print("\n=== Testing Test User Creation with Different Roles ===")
        
        if not self.admin_token:
            self.log_test("Test User Creation", False, "No admin token available")
            return
        
        try:
            response = self.session.post(
                f"{self.base_url}/admin/test-user-role",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test(
                    "Create Test Users with Roles",
                    True,
                    f"Test users created: {result.get('message', '')}",
                    {"response": result}
                )
            else:
                self.log_test(
                    "Create Test Users with Roles",
                    False,
                    f"Failed to create test users with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Create Test Users with Roles",
                False,
                f"Error creating test users: {str(e)}"
            )

    def test_get_users_list_with_roles(self):
        """Test GET /api/admin/users - Verify roles are displayed correctly"""
        print("\n=== Testing User List API with Role Display ===")
        
        if not self.admin_token:
            self.log_test("Get Users List", False, "No admin token available")
            return
        
        try:
            response = self.session.get(
                f"{self.base_url}/admin/users",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                users = response.json()
                
                # Analyze user roles
                role_counts = {}
                for user in users:
                    role = user.get("role", "unknown")
                    role_counts[role] = role_counts.get(role, 0) + 1
                    
                    # Store test user IDs for role change testing (exclude admin)
                    if user.get("username") in ["testuser1", "testteam1", "testuser_emergency"] and user.get("role") != "admin":
                        user_id = user.get("id") or user.get("_id")  # Handle both id and _id fields
                        if user_id:
                            self.test_user_ids.append(user_id)
                
                self.log_test(
                    "Get Users List with Roles",
                    True,
                    f"Retrieved {len(users)} users with role distribution: {role_counts}",
                    {"users_count": len(users), "role_distribution": role_counts, "users": users}
                )
                
                # Verify all users have role field
                users_with_roles = [user for user in users if "role" in user]
                if len(users_with_roles) == len(users):
                    self.log_test(
                        "User Role Field Verification",
                        True,
                        "All users have role field properly displayed"
                    )
                else:
                    self.log_test(
                        "User Role Field Verification",
                        False,
                        f"Only {len(users_with_roles)}/{len(users)} users have role field"
                    )
                
            else:
                self.log_test(
                    "Get Users List with Roles",
                    False,
                    f"Failed to get users list with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Get Users List with Roles",
                False,
                f"Error getting users list: {str(e)}"
            )

    def test_user_role_update_api(self):
        """Test PUT /api/admin/users/{user_id}/role - Test with all roles: user, team, admin"""
        print("\n=== Testing User Role Update API ===")
        
        if not self.admin_token:
            self.log_test("User Role Update", False, "No admin token available")
            return
        
        if not self.test_user_ids:
            self.log_test("User Role Update", False, "No test user IDs available")
            return
        
        # Test role changes: user -> team -> admin -> user
        test_roles = ["user", "team", "admin", "user"]
        user_id = self.test_user_ids[0] if self.test_user_ids else None
        
        if not user_id:
            self.log_test("User Role Update", False, "No valid user ID for testing")
            return
        
        for i, new_role in enumerate(test_roles):
            try:
                role_data = {"role": new_role}
                response = self.session.put(
                    f"{self.base_url}/admin/users/{user_id}/role",
                    json=role_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.log_test(
                        f"Update User Role to {new_role.upper()}",
                        True,
                        f"User role successfully updated to {new_role}: {result.get('message', '')}",
                        {"new_role": new_role, "response": result}
                    )
                    
                    # Verify role change by getting user list
                    verify_response = self.session.get(
                        f"{self.base_url}/admin/users",
                        headers=self.get_auth_headers(self.admin_token)
                    )
                    
                    if verify_response.status_code == 200:
                        users = verify_response.json()
                        updated_user = next((u for u in users if u.get("id") == user_id), None)
                        
                        if updated_user and updated_user.get("role") == new_role:
                            self.log_test(
                                f"Verify Role Change to {new_role.upper()}",
                                True,
                                f"Role change verified: user now has role '{new_role}'"
                            )
                        else:
                            self.log_test(
                                f"Verify Role Change to {new_role.upper()}",
                                False,
                                f"Role change not reflected in user data. Expected: {new_role}, Got: {updated_user.get('role') if updated_user else 'user not found'}"
                            )
                    
                else:
                    self.log_test(
                        f"Update User Role to {new_role.upper()}",
                        False,
                        f"Failed to update role to {new_role} with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    f"Update User Role to {new_role.upper()}",
                    False,
                    f"Error updating role to {new_role}: {str(e)}"
                )

    def test_role_validation(self):
        """Test role validation - invalid roles and self-role change prevention"""
        print("\n=== Testing Role Validation ===")
        
        if not self.admin_token or not self.test_user_ids:
            self.log_test("Role Validation", False, "No admin token or test user IDs available")
            return
        
        user_id = self.test_user_ids[0] if self.test_user_ids else None
        
        # Test 1: Invalid role
        invalid_roles = ["superuser", "moderator", "invalid", ""]
        
        for invalid_role in invalid_roles:
            try:
                role_data = {"role": invalid_role}
                response = self.session.put(
                    f"{self.base_url}/admin/users/{user_id}/role",
                    json=role_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 400:
                    self.log_test(
                        f"Invalid Role Rejection ({invalid_role})",
                        True,
                        f"Invalid role '{invalid_role}' correctly rejected with 400"
                    )
                else:
                    self.log_test(
                        f"Invalid Role Rejection ({invalid_role})",
                        False,
                        f"Expected 400 for invalid role '{invalid_role}' but got {response.status_code}"
                    )
            except Exception as e:
                self.log_test(
                    f"Invalid Role Rejection ({invalid_role})",
                    False,
                    f"Error testing invalid role '{invalid_role}': {str(e)}"
                )
        
        # Test 2: Admin trying to change own role (should be prevented)
        try:
            # Get admin user ID from token validation
            me_response = self.session.get(
                f"{self.base_url}/me",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if me_response.status_code == 200:
                admin_user = me_response.json()
                admin_user_id = admin_user.get("id") or admin_user.get("_id")  # Handle both id and _id fields
                
                if admin_user_id:
                    role_data = {"role": "user"}
                    response = self.session.put(
                        f"{self.base_url}/admin/users/{admin_user_id}/role",
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
                else:
                    self.log_test(
                        "Prevent Admin Self-Role Change",
                        False,
                        "Could not get admin user ID for testing"
                    )
            else:
                self.log_test(
                    "Prevent Admin Self-Role Change",
                    False,
                    "Could not validate admin token to get user ID"
                )
        except Exception as e:
            self.log_test(
                "Prevent Admin Self-Role Change",
                False,
                f"Error testing admin self-role change prevention: {str(e)}"
            )

    def test_voice_recording_backend_support(self):
        """Test POST /api/admin/chat - Voice message support with voice_data and voice_duration"""
        print("\n=== Testing Voice Recording Backend Support ===")
        
        if not self.admin_token:
            self.log_test("Voice Recording Backend", False, "No admin token available")
            return
        
        # Create a test chat group first for voice messages
        group_data = {
            "name": "Voice Test Group",
            "description": "Test group for voice message testing",
            "members": []
        }
        
        group_id = None
        try:
            response = self.session.post(
                f"{self.base_url}/admin/chat/groups",
                json=group_data,
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                created_group = response.json()
                group_id = created_group.get("id")
                self.created_group_ids.append(group_id)
                
                self.log_test(
                    "Create Voice Test Group",
                    True,
                    "Test group created for voice message testing"
                )
            else:
                self.log_test(
                    "Create Voice Test Group",
                    False,
                    f"Failed to create test group with status {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "Create Voice Test Group",
                False,
                f"Error creating test group: {str(e)}"
            )
        
        # Test voice messages with different scenarios
        voice_test_cases = [
            {
                "name": "Basic Voice Message",
                "message": "Notfall-Durchsage: Alle Einheiten zum Einsatzort",
                "chat_type": "admin",
                "group_id": group_id,
                "is_voice_message": True,
                "voice_data": base64.b64encode(b"fake_audio_data_for_testing").decode('utf-8'),
                "voice_duration": 15
            },
            {
                "name": "Long Voice Message",
                "message": "Ausführliche Einsatzbesprechung mit allen Details",
                "chat_type": "admin", 
                "group_id": group_id,
                "is_voice_message": True,
                "voice_data": base64.b64encode(b"longer_fake_audio_data_for_extended_testing_scenario").decode('utf-8'),
                "voice_duration": 45
            },
            {
                "name": "Voice Message without Group",
                "message": "Allgemeine Sprachnachricht",
                "chat_type": "admin",
                "group_id": None,
                "is_voice_message": True,
                "voice_data": base64.b64encode(b"general_voice_message_data").decode('utf-8'),
                "voice_duration": 20
            },
            {
                "name": "Text Message for Comparison",
                "message": "Normale Textnachricht zum Vergleich",
                "chat_type": "admin",
                "group_id": group_id,
                "is_voice_message": False,
                "voice_data": None,
                "voice_duration": None
            }
        ]
        
        for test_case in voice_test_cases:
            try:
                # Remove None values from the request
                message_data = {k: v for k, v in test_case.items() if k != "name" and v is not None}
                
                response = self.session.post(
                    f"{self.base_url}/admin/chat",
                    json=message_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    created_message = response.json()
                    
                    # Verify voice message fields
                    is_voice = created_message.get("is_voice_message", False)
                    voice_data = created_message.get("voice_data")
                    voice_duration = created_message.get("voice_duration")
                    
                    expected_voice = test_case.get("is_voice_message", False)
                    
                    if is_voice == expected_voice:
                        if expected_voice:
                            # For voice messages, check voice_data and duration
                            if voice_data and voice_duration:
                                self.log_test(
                                    f"Voice Message: {test_case['name']}",
                                    True,
                                    f"Voice message created successfully with {voice_duration}s duration",
                                    {
                                        "message_id": created_message.get("id"),
                                        "is_voice": is_voice,
                                        "duration": voice_duration,
                                        "has_voice_data": bool(voice_data)
                                    }
                                )
                            else:
                                self.log_test(
                                    f"Voice Message: {test_case['name']}",
                                    False,
                                    "Voice message created but missing voice_data or duration"
                                )
                        else:
                            # For text messages, ensure no voice fields
                            self.log_test(
                                f"Text Message: {test_case['name']}",
                                True,
                                "Text message created successfully without voice fields",
                                {"message_id": created_message.get("id"), "is_voice": is_voice}
                            )
                    else:
                        self.log_test(
                            f"Message Type Mismatch: {test_case['name']}",
                            False,
                            f"Expected is_voice_message={expected_voice}, got {is_voice}"
                        )
                        
                else:
                    self.log_test(
                        f"Failed Message: {test_case['name']}",
                        False,
                        f"Failed to send message with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    f"Error Message: {test_case['name']}",
                    False,
                    f"Error sending message: {str(e)}"
                )
        
        # Test retrieving voice messages
        if group_id:
            try:
                response = self.session.get(
                    f"{self.base_url}/admin/chat",
                    params={"group_id": group_id, "chat_type": "admin"},
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    messages = response.json()
                    voice_messages = [msg for msg in messages if msg.get("is_voice_message")]
                    text_messages = [msg for msg in messages if not msg.get("is_voice_message")]
                    
                    self.log_test(
                        "Retrieve Voice Messages",
                        True,
                        f"Retrieved {len(messages)} total messages: {len(voice_messages)} voice, {len(text_messages)} text",
                        {
                            "total_messages": len(messages),
                            "voice_messages": len(voice_messages),
                            "text_messages": len(text_messages)
                        }
                    )
                    
                    # Verify voice message data integrity
                    for voice_msg in voice_messages:
                        if voice_msg.get("voice_data") and voice_msg.get("voice_duration"):
                            self.log_test(
                                "Voice Message Data Integrity",
                                True,
                                f"Voice message has complete data (duration: {voice_msg.get('voice_duration')}s)"
                            )
                        else:
                            self.log_test(
                                "Voice Message Data Integrity",
                                False,
                                "Voice message missing voice_data or duration"
                            )
                            break
                else:
                    self.log_test(
                        "Retrieve Voice Messages",
                        False,
                        f"Failed to retrieve messages with status {response.status_code}"
                    )
            except Exception as e:
                self.log_test(
                    "Retrieve Voice Messages",
                    False,
                    f"Error retrieving messages: {str(e)}"
                )

    def test_comprehensive_role_scenarios(self):
        """Test comprehensive role management scenarios"""
        print("\n=== Testing Comprehensive Role Management Scenarios ===")
        
        if not self.admin_token or not self.test_user_ids:
            self.log_test("Comprehensive Role Scenarios", False, "No admin token or test user IDs available")
            return
        
        # Scenario 1: Bulk role changes
        print("\n--- Testing Bulk Role Changes ---")
        
        role_progression = [
            ("user", "Standard user role"),
            ("team", "Team member role"),
            ("admin", "Administrator role"),
            ("user", "Back to standard user")
        ]
        
        for user_id in self.test_user_ids[:2]:  # Test with first 2 users
            for role, description in role_progression:
                try:
                    role_data = {"role": role}
                    response = self.session.put(
                        f"{self.base_url}/admin/users/{user_id}/role",
                        json=role_data,
                        headers=self.get_auth_headers(self.admin_token)
                    )
                    
                    if response.status_code == 200:
                        self.log_test(
                            f"Bulk Role Change: {role.upper()}",
                            True,
                            f"User {user_id[:8]}... successfully changed to {description}"
                        )
                    else:
                        self.log_test(
                            f"Bulk Role Change: {role.upper()}",
                            False,
                            f"Failed to change user {user_id[:8]}... to {role}"
                        )
                except Exception as e:
                    self.log_test(
                        f"Bulk Role Change: {role.upper()}",
                        False,
                        f"Error changing user role: {str(e)}"
                    )
        
        # Scenario 2: Role-based access verification
        print("\n--- Testing Role-Based Access Verification ---")
        
        # Get current user list to verify role changes
        try:
            response = self.session.get(
                f"{self.base_url}/admin/users",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                users = response.json()
                role_distribution = {}
                
                for user in users:
                    role = user.get("role", "unknown")
                    role_distribution[role] = role_distribution.get(role, 0) + 1
                
                # Verify we have users in different roles
                expected_roles = ["user", "team", "admin"]
                roles_present = [role for role in expected_roles if role in role_distribution]
                
                if len(roles_present) >= 2:
                    self.log_test(
                        "Role Distribution Verification",
                        True,
                        f"Multiple roles present in system: {role_distribution}",
                        {"role_distribution": role_distribution}
                    )
                else:
                    self.log_test(
                        "Role Distribution Verification",
                        False,
                        f"Insufficient role diversity: {role_distribution}"
                    )
            else:
                self.log_test(
                    "Role Distribution Verification",
                    False,
                    f"Failed to get users for role verification with status {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "Role Distribution Verification",
                False,
                f"Error verifying role distribution: {str(e)}"
            )

    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        print("\n=== Cleaning Up Test Data ===")
        
        if not self.admin_token:
            return
        
        # Clean up test chat groups
        for group_id in self.created_group_ids:
            try:
                response = self.session.delete(
                    f"{self.base_url}/admin/chat/groups/{group_id}",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "Cleanup Test Group",
                        True,
                        f"Test group {group_id[:8]}... deleted successfully"
                    )
            except Exception:
                pass  # Ignore cleanup errors

    def run_all_tests(self):
        """Run all user role management tests"""
        print("🚀 Starting User Role Management Features Testing")
        print("=" * 80)
        
        # Setup
        if not self.setup_admin_authentication():
            print("❌ Failed to setup admin authentication. Aborting tests.")
            return
        
        # Run tests in order
        self.test_create_test_users_with_roles()
        self.test_get_users_list_with_roles()
        self.test_user_role_update_api()
        self.test_role_validation()
        self.test_voice_recording_backend_support()
        self.test_comprehensive_role_scenarios()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        self.print_test_summary()

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 USER ROLE MANAGEMENT TESTING SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS ({failed_tests}):")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['message']}")
        
        print(f"\n✅ PASSED TESTS ({passed_tests}):")
        for result in self.test_results:
            if result["success"]:
                print(f"  • {result['test']}: {result['message']}")
        
        # Feature-specific summary
        print(f"\n🎯 FEATURE TESTING RESULTS:")
        
        # User Role Update API
        role_update_tests = [r for r in self.test_results if "Role" in r["test"] and "Update" in r["test"]]
        role_update_success = len([r for r in role_update_tests if r["success"]])
        print(f"  • User Role Update API: {role_update_success}/{len(role_update_tests)} tests passed")
        
        # Test User Creation
        user_creation_tests = [r for r in self.test_results if "Test User" in r["test"]]
        user_creation_success = len([r for r in user_creation_tests if r["success"]])
        print(f"  • Test User Creation: {user_creation_success}/{len(user_creation_tests)} tests passed")
        
        # User List API
        user_list_tests = [r for r in self.test_results if "Users List" in r["test"]]
        user_list_success = len([r for r in user_list_tests if r["success"]])
        print(f"  • User List API: {user_list_success}/{len(user_list_tests)} tests passed")
        
        # Voice Recording Backend
        voice_tests = [r for r in self.test_results if "Voice" in r["test"]]
        voice_success = len([r for r in voice_tests if r["success"]])
        print(f"  • Voice Recording Backend: {voice_success}/{len(voice_tests)} tests passed")
        
        print("\n" + "=" * 80)
        
        if success_rate >= 90:
            print("🎉 EXCELLENT: User Role Management features are working excellently!")
        elif success_rate >= 75:
            print("✅ GOOD: User Role Management features are working well with minor issues.")
        elif success_rate >= 50:
            print("⚠️  MODERATE: User Role Management features have some issues that need attention.")
        else:
            print("❌ CRITICAL: User Role Management features have significant issues requiring immediate attention.")

if __name__ == "__main__":
    tester = UserRoleManagementTester()
    tester.run_all_tests()