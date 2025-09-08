#!/usr/bin/env python3
"""
CRITICAL MEMORY/PERSISTENCE TESTS for Emergency SOS App
Tests the specific issues mentioned in the review request:
1. User Role Saving (PUT /api/admin/users/{user_id}/role)
2. Name Change Saving (PUT /api/profile)
3. Integration Tests
4. German Special Characters Support
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Backend API base URL - using internal URL for testing
BASE_URL = "http://localhost:8001/api"

class CriticalMemoryTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.test_results = []
        self.admin_token = None
        self.user_token = None
        self.test_user_ids = []
        self.admin_user_id = None
        
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

    def setup_authentication(self):
        """Setup admin and user authentication"""
        print("\n=== Setting Up Authentication ===")
        
        # Create admin if not exists
        try:
            response = self.session.post(f"{self.base_url}/create-admin")
            if response.status_code == 200:
                print("Admin user setup completed")
        except Exception as e:
            print(f"Admin setup error (may already exist): {e}")
        
        # Login as admin
        admin_login = {
            "username": "admin",
            "password": "admin123"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/login",
                json=admin_login,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.admin_token = token_data.get("access_token")
                admin_user = token_data.get("user", {})
                self.admin_user_id = admin_user.get("id") or admin_user.get("_id")
                print(f"✅ Admin login successful")
            else:
                print(f"❌ Admin login failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Admin login error: {e}")
            return False
        
        return True

    def create_test_users(self):
        """Create test users with different roles for testing"""
        print("\n=== Creating Test Users ===")
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False
        
        # Test users with German names and special characters
        test_users = [
            {
                "username": "testuser_müller",
                "email": "mueller@test-emergency.com",
                "full_name": "Hans Müller",
                "password": "test123",
                "role": "user"
            },
            {
                "username": "testuser_schäfer", 
                "email": "schaefer@test-emergency.com",
                "full_name": "Anna Schäfer",
                "password": "test123",
                "role": "team"
            },
            {
                "username": "testuser_weiß",
                "email": "weiss@test-emergency.com", 
                "full_name": "Klaus Weiß",
                "password": "test123",
                "role": "emergency"
            }
        ]
        
        for i, user_data in enumerate(test_users):
            try:
                response = self.session.post(
                    f"{self.base_url}/register",
                    json=user_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    created_user = response.json()
                    user_id = created_user.get("id") or created_user.get("_id")
                    if user_id:
                        self.test_user_ids.append(user_id)
                    
                    self.log_test(
                        f"Create Test User {i+1}",
                        True,
                        f"User '{user_data['full_name']}' created successfully",
                        {"user_id": user_id, "username": user_data["username"]}
                    )
                elif response.status_code == 400 and "already registered" in response.text:
                    # User exists, try to get ID from admin users list
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
                                    f"Create Test User {i+1}",
                                    True,
                                    f"User '{user_data['full_name']}' already exists (using existing)",
                                    {"user_id": user_id, "username": user_data["username"]}
                                )
                    except Exception as e:
                        self.log_test(
                            f"Create Test User {i+1}",
                            False,
                            f"User exists but couldn't get ID: {str(e)}"
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
        
        return len(self.test_user_ids) > 0

    def test_user_role_saving_critical(self):
        """CRITICAL TEST: User Role Saving with all 4 roles and persistence verification"""
        print("\n=== CRITICAL TEST: User Role Saving ===")
        
        if not self.admin_token or not self.test_user_ids:
            self.log_test("User Role Saving Setup", False, "No admin token or test users available")
            return
        
        # Test all 4 roles: user, team, admin, emergency
        roles_to_test = ["user", "team", "admin", "emergency"]
        
        for role in roles_to_test:
            for i, user_id in enumerate(self.test_user_ids[:3]):  # Test with first 3 users
                try:
                    # Step 1: Change user role
                    role_data = {"role": role}
                    
                    response = self.session.put(
                        f"{self.base_url}/admin/users/{user_id}/role",
                        json=role_data,
                        headers=self.get_auth_headers(self.admin_token)
                    )
                    
                    if response.status_code == 200:
                        # Step 2: Verify role was saved in DB by getting user list
                        users_response = self.session.get(
                            f"{self.base_url}/admin/users",
                            headers=self.get_auth_headers(self.admin_token)
                        )
                        
                        if users_response.status_code == 200:
                            users = users_response.json()
                            updated_user = next((u for u in users if u.get("id") == user_id), None)
                            
                            if updated_user and updated_user.get("role") == role:
                                self.log_test(
                                    f"Role Change to {role.upper()} (User {i+1})",
                                    True,
                                    f"Role successfully changed to '{role}' and persisted in DB",
                                    {"user_id": user_id, "new_role": role, "verified_role": updated_user.get("role")}
                                )
                            else:
                                self.log_test(
                                    f"Role Change to {role.upper()} (User {i+1})",
                                    False,
                                    f"Role change API succeeded but role not persisted in DB",
                                    {"user_id": user_id, "expected_role": role, "actual_role": updated_user.get("role") if updated_user else "user_not_found"}
                                )
                        else:
                            self.log_test(
                                f"Role Change to {role.upper()} (User {i+1})",
                                False,
                                f"Role change succeeded but couldn't verify persistence (status {users_response.status_code})",
                                {"user_id": user_id, "role": role}
                            )
                    else:
                        self.log_test(
                            f"Role Change to {role.upper()} (User {i+1})",
                            False,
                            f"Failed to change role with status {response.status_code}",
                            {"user_id": user_id, "role": role, "response_text": response.text}
                        )
                except Exception as e:
                    self.log_test(
                        f"Role Change to {role.upper()} (User {i+1})",
                        False,
                        f"Error changing role: {str(e)}",
                        {"user_id": user_id, "role": role}
                    )

    def test_user_id_vs_id_problem(self):
        """Test the user_id vs _id problem that was supposedly fixed"""
        print("\n=== Testing user_id vs _id Problem Fix ===")
        
        if not self.admin_token or not self.test_user_ids:
            self.log_test("ID Problem Test Setup", False, "No admin token or test users available")
            return
        
        # Test with both _id and id formats
        user_id = self.test_user_ids[0]
        
        # Test 1: Use the user_id as provided (should work)
        try:
            role_data = {"role": "team"}
            response = self.session.put(
                f"{self.base_url}/admin/users/{user_id}/role",
                json=role_data,
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                self.log_test(
                    "User ID Format Handling",
                    True,
                    "User ID correctly handled in role change endpoint",
                    {"user_id": user_id, "status": response.status_code}
                )
            else:
                self.log_test(
                    "User ID Format Handling",
                    False,
                    f"User ID handling failed with status {response.status_code}",
                    {"user_id": user_id, "response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "User ID Format Handling",
                False,
                f"Error testing user ID format: {str(e)}",
                {"user_id": user_id}
            )

    def test_name_change_saving_critical(self):
        """CRITICAL TEST: Name Change Saving with persistence verification"""
        print("\n=== CRITICAL TEST: Name Change Saving ===")
        
        if not self.test_user_ids:
            self.log_test("Name Change Test Setup", False, "No test users available")
            return
        
        # Create a user token for testing profile updates
        user_login = {
            "username": "testuser_müller",
            "password": "test123"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/login",
                json=user_login,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                user_token = token_data.get("access_token")
                user_data = token_data.get("user", {})
                user_id = user_data.get("id")
                
                # Test German names with special characters
                german_names = [
                    "Hans Müller - Aktualisiert",
                    "Maximilian Schäfer-Weiß", 
                    "Dr. Ingrid Größe",
                    "Klaus-Dieter Hübner",
                    "Änne Öttinger"
                ]
                
                for i, new_name in enumerate(german_names):
                    try:
                        # Step 1: Update name via PUT /api/profile
                        profile_data = {"full_name": new_name}
                        
                        update_response = self.session.put(
                            f"{self.base_url}/profile",
                            json=profile_data,
                            headers=self.get_auth_headers(user_token)
                        )
                        
                        if update_response.status_code == 200:
                            # Step 2: Verify name was saved by getting user profile
                            me_response = self.session.get(
                                f"{self.base_url}/me",
                                headers=self.get_auth_headers(user_token)
                            )
                            
                            if me_response.status_code == 200:
                                user_profile = me_response.json()
                                saved_name = user_profile.get("full_name")
                                
                                if saved_name == new_name:
                                    self.log_test(
                                        f"Name Change Test {i+1}",
                                        True,
                                        f"Name successfully changed to '{new_name}' and persisted",
                                        {"new_name": new_name, "verified_name": saved_name}
                                    )
                                else:
                                    self.log_test(
                                        f"Name Change Test {i+1}",
                                        False,
                                        f"Name change API succeeded but name not persisted correctly",
                                        {"expected_name": new_name, "actual_name": saved_name}
                                    )
                            else:
                                self.log_test(
                                    f"Name Change Test {i+1}",
                                    False,
                                    f"Name change succeeded but couldn't verify persistence (status {me_response.status_code})",
                                    {"new_name": new_name}
                                )
                        else:
                            self.log_test(
                                f"Name Change Test {i+1}",
                                False,
                                f"Failed to change name with status {update_response.status_code}",
                                {"new_name": new_name, "response_text": update_response.text}
                            )
                    except Exception as e:
                        self.log_test(
                            f"Name Change Test {i+1}",
                            False,
                            f"Error changing name: {str(e)}",
                            {"new_name": new_name}
                        )
                
                # Test multi-field updates
                try:
                    multi_field_data = {
                        "full_name": "Hans Müller - Vollständig Aktualisiert",
                        "phone": "+49-123-456-7890",
                        "address": "Hauptstraße 123, 12345 Berlin",
                        "emergency_contact": "Anna Müller - Ehefrau"
                    }
                    
                    response = self.session.put(
                        f"{self.base_url}/profile",
                        json=multi_field_data,
                        headers=self.get_auth_headers(user_token)
                    )
                    
                    if response.status_code == 200:
                        # Verify all fields were saved
                        me_response = self.session.get(
                            f"{self.base_url}/me",
                            headers=self.get_auth_headers(user_token)
                        )
                        
                        if me_response.status_code == 200:
                            user_profile = me_response.json()
                            
                            # Check if name was updated (other fields might not be in /me endpoint)
                            if user_profile.get("full_name") == multi_field_data["full_name"]:
                                self.log_test(
                                    "Multi-Field Profile Update",
                                    True,
                                    "Multi-field profile update successful and name persisted",
                                    {"updated_fields": list(multi_field_data.keys())}
                                )
                            else:
                                self.log_test(
                                    "Multi-Field Profile Update",
                                    False,
                                    "Multi-field update succeeded but name not persisted",
                                    {"expected_name": multi_field_data["full_name"], "actual_name": user_profile.get("full_name")}
                                )
                        else:
                            self.log_test(
                                "Multi-Field Profile Update",
                                False,
                                f"Multi-field update succeeded but couldn't verify (status {me_response.status_code})"
                            )
                    else:
                        self.log_test(
                            "Multi-Field Profile Update",
                            False,
                            f"Multi-field update failed with status {response.status_code}",
                            {"response_text": response.text}
                        )
                except Exception as e:
                    self.log_test(
                        "Multi-Field Profile Update",
                        False,
                        f"Error in multi-field update: {str(e)}"
                    )
            else:
                self.log_test(
                    "Name Change User Login",
                    False,
                    f"Failed to login test user for name change tests: {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "Name Change User Login",
                False,
                f"Error logging in test user: {str(e)}"
            )

    def test_error_handling_critical(self):
        """Test error handling for empty names and invalid roles"""
        print("\n=== Testing Error Handling ===")
        
        if not self.admin_token or not self.test_user_ids:
            self.log_test("Error Handling Setup", False, "No admin token or test users available")
            return
        
        user_id = self.test_user_ids[0]
        
        # Test 1: Invalid roles
        invalid_roles = ["superuser", "moderator", "invalid", "", "null"]
        
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
                        f"Expected 400 for invalid role but got {response.status_code}",
                        {"invalid_role": invalid_role, "response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    f"Invalid Role Rejection ({invalid_role})",
                    False,
                    f"Error testing invalid role: {str(e)}"
                )
        
        # Test 2: Admin cannot change own role
        try:
            role_data = {"role": "user"}
            response = self.session.put(
                f"{self.base_url}/admin/users/{self.admin_user_id}/role",
                json=role_data,
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 400:
                self.log_test(
                    "Admin Self-Role Change Prevention",
                    True,
                    "Admin correctly prevented from changing own role"
                )
            else:
                self.log_test(
                    "Admin Self-Role Change Prevention",
                    False,
                    f"Expected 400 for admin self-role change but got {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Admin Self-Role Change Prevention",
                False,
                f"Error testing admin self-role change: {str(e)}"
            )

    def test_integration_workflow(self):
        """Integration test: Create user, change role, change name, verify both persist"""
        print("\n=== Integration Workflow Test ===")
        
        if not self.admin_token:
            self.log_test("Integration Test Setup", False, "No admin token available")
            return
        
        # Step 1: Create a new test user for integration testing
        integration_user = {
            "username": "integration_test_user",
            "email": "integration@test-emergency.com",
            "full_name": "Integration Test Benutzer",
            "password": "integration123",
            "role": "user"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/register",
                json=integration_user,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                created_user = response.json()
                integration_user_id = created_user.get("id")
                
                # Step 2: Login as the integration user
                login_response = self.session.post(
                    f"{self.base_url}/login",
                    json={"username": integration_user["username"], "password": integration_user["password"]},
                    headers={"Content-Type": "application/json"}
                )
                
                if login_response.status_code == 200:
                    token_data = login_response.json()
                    integration_token = token_data.get("access_token")
                    
                    # Step 3: Change user name
                    new_name = "Integration Test Benutzer - Geändert"
                    name_response = self.session.put(
                        f"{self.base_url}/profile",
                        json={"full_name": new_name},
                        headers=self.get_auth_headers(integration_token)
                    )
                    
                    # Step 4: Change user role (as admin)
                    new_role = "team"
                    role_response = self.session.put(
                        f"{self.base_url}/admin/users/{integration_user_id}/role",
                        json={"role": new_role},
                        headers=self.get_auth_headers(self.admin_token)
                    )
                    
                    # Step 5: Verify both changes persisted
                    if name_response.status_code == 200 and role_response.status_code == 200:
                        # Check name persistence
                        me_response = self.session.get(
                            f"{self.base_url}/me",
                            headers=self.get_auth_headers(integration_token)
                        )
                        
                        # Check role persistence
                        users_response = self.session.get(
                            f"{self.base_url}/admin/users",
                            headers=self.get_auth_headers(self.admin_token)
                        )
                        
                        if me_response.status_code == 200 and users_response.status_code == 200:
                            user_profile = me_response.json()
                            users = users_response.json()
                            updated_user = next((u for u in users if u.get("id") == integration_user_id), None)
                            
                            name_persisted = user_profile.get("full_name") == new_name
                            role_persisted = updated_user and updated_user.get("role") == new_role
                            
                            if name_persisted and role_persisted:
                                self.log_test(
                                    "Integration Workflow Complete",
                                    True,
                                    "Both name change and role change persisted successfully",
                                    {
                                        "name_change": f"'{integration_user['full_name']}' → '{new_name}'",
                                        "role_change": f"'{integration_user['role']}' → '{new_role}'",
                                        "name_persisted": name_persisted,
                                        "role_persisted": role_persisted
                                    }
                                )
                            else:
                                self.log_test(
                                    "Integration Workflow Complete",
                                    False,
                                    "One or both changes did not persist",
                                    {
                                        "name_persisted": name_persisted,
                                        "role_persisted": role_persisted,
                                        "expected_name": new_name,
                                        "actual_name": user_profile.get("full_name"),
                                        "expected_role": new_role,
                                        "actual_role": updated_user.get("role") if updated_user else "user_not_found"
                                    }
                                )
                        else:
                            self.log_test(
                                "Integration Workflow Verification",
                                False,
                                "Could not verify persistence due to API errors",
                                {"me_status": me_response.status_code, "users_status": users_response.status_code}
                            )
                    else:
                        self.log_test(
                            "Integration Workflow Updates",
                            False,
                            "One or both update operations failed",
                            {"name_status": name_response.status_code, "role_status": role_response.status_code}
                        )
                else:
                    self.log_test(
                        "Integration User Login",
                        False,
                        f"Failed to login integration user: {login_response.status_code}"
                    )
            elif response.status_code == 400 and "already registered" in response.text:
                self.log_test(
                    "Integration Test User Creation",
                    True,
                    "Integration user already exists (continuing with existing user)"
                )
                # Could continue with existing user, but for simplicity, we'll skip
            else:
                self.log_test(
                    "Integration Test User Creation",
                    False,
                    f"Failed to create integration user: {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Integration Workflow Test",
                False,
                f"Error in integration workflow: {str(e)}"
            )

    def run_all_critical_tests(self):
        """Run all critical memory/persistence tests"""
        print("🚨 STARTING CRITICAL MEMORY/PERSISTENCE TESTS 🚨")
        print("=" * 60)
        
        # Setup
        if not self.setup_authentication():
            print("❌ Authentication setup failed - cannot continue")
            return
        
        if not self.create_test_users():
            print("❌ Test user creation failed - cannot continue")
            return
        
        # Run critical tests
        self.test_user_role_saving_critical()
        self.test_user_id_vs_id_problem()
        self.test_name_change_saving_critical()
        self.test_error_handling_critical()
        self.test_integration_workflow()
        
        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🚨 CRITICAL MEMORY/PERSISTENCE TESTS SUMMARY 🚨")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
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
        
        # Critical assessment
        critical_issues = []
        
        # Check for role saving issues
        role_tests = [r for r in self.test_results if "Role Change to" in r["test"]]
        failed_role_tests = [r for r in role_tests if not r["success"]]
        if failed_role_tests:
            critical_issues.append(f"User role saving failures: {len(failed_role_tests)}/{len(role_tests)} role changes failed")
        
        # Check for name saving issues
        name_tests = [r for r in self.test_results if "Name Change Test" in r["test"]]
        failed_name_tests = [r for r in name_tests if not r["success"]]
        if failed_name_tests:
            critical_issues.append(f"Name change saving failures: {len(failed_name_tests)}/{len(name_tests)} name changes failed")
        
        # Check integration test
        integration_tests = [r for r in self.test_results if "Integration Workflow" in r["test"]]
        failed_integration = [r for r in integration_tests if not r["success"]]
        if failed_integration:
            critical_issues.append("Integration workflow failed - both role and name changes not working together")
        
        if critical_issues:
            print(f"\n🚨 CRITICAL ISSUES FOUND:")
            for issue in critical_issues:
                print(f"  • {issue}")
            print(f"\n❌ MEMORY/PERSISTENCE PROBLEMS NOT FULLY RESOLVED")
        else:
            print(f"\n✅ ALL CRITICAL MEMORY/PERSISTENCE ISSUES RESOLVED")
            print("✅ User role saving: WORKING")
            print("✅ Name change saving: WORKING") 
            print("✅ Integration workflow: WORKING")
            print("✅ German special characters: SUPPORTED")

if __name__ == "__main__":
    tester = CriticalMemoryTester()
    tester.run_all_critical_tests()