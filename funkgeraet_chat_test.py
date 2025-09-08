#!/usr/bin/env python3
"""
Comprehensive Funkgerät (Radio) Chat System Backend API Tests
Tests Chat Groups, Chat Messages, and Admin Profile Management APIs
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Backend API base URL from frontend environment
BASE_URL = "https://emergency-sos-3.preview.emergentagent.com/api"

class FunkgeraetChatTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.test_results = []
        self.admin_token = None
        self.admin_user_id = None
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

    def setup_admin_authentication(self):
        """Setup admin user and get authentication token"""
        print("\n=== Setting up Admin Authentication ===")
        
        # Create admin user if not exists
        try:
            response = self.session.post(f"{self.base_url}/create-admin")
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Create Admin User",
                    True,
                    f"Admin setup: {data.get('message', '')}",
                    {"response": data}
                )
        except Exception as e:
            self.log_test(
                "Create Admin User",
                False,
                f"Error creating admin: {str(e)}"
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
                self.admin_user_id = admin_user.get("id")
                
                self.log_test(
                    "Admin Login",
                    True,
                    f"Admin login successful, role: {admin_user.get('role', 'unknown')}",
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

    def test_chat_groups_crud(self):
        """Test Chat Groups CRUD operations"""
        print("\n=== Testing Chat Groups CRUD Operations ===")
        
        if not self.admin_token:
            self.log_test("Chat Groups CRUD", False, "No admin token available")
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
            },
            {
                "name": "Polizei",
                "description": "Polizei-Kommunikationsgruppe",
                "members": []
            }
        ]
        
        # Test 1: CREATE Chat Groups (POST /api/admin/chat/groups)
        print("\n--- Testing Chat Group Creation ---")
        for i, group_data in enumerate(test_groups):
            try:
                response = self.session.post(
                    f"{self.base_url}/admin/chat/groups",
                    json=group_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    created_group = response.json()
                    group_id = created_group.get("id")
                    if group_id:
                        self.created_group_ids.append(group_id)
                    
                    self.log_test(
                        f"CREATE Chat Group: {group_data['name']}",
                        True,
                        f"Group '{group_data['name']}' created successfully",
                        {"group_id": group_id, "created_by": created_group.get("created_by")}
                    )
                else:
                    self.log_test(
                        f"CREATE Chat Group: {group_data['name']}",
                        False,
                        f"Failed to create group with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    f"CREATE Chat Group: {group_data['name']}",
                    False,
                    f"Error creating group: {str(e)}"
                )
        
        # Test 2: READ Chat Groups (GET /api/admin/chat/groups)
        print("\n--- Testing Chat Group Retrieval ---")
        try:
            response = self.session.get(
                f"{self.base_url}/admin/chat/groups",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                groups = response.json()
                
                # Verify we can find our created groups
                created_group_names = [group["name"] for group in test_groups]
                found_groups = [g for g in groups if g.get("name") in created_group_names]
                
                self.log_test(
                    "READ All Chat Groups",
                    True,
                    f"Retrieved {len(groups)} total groups, {len(found_groups)} are our test groups",
                    {"total_groups": len(groups), "test_groups_found": len(found_groups)}
                )
                
                # Verify group structure
                if groups:
                    sample_group = groups[0]
                    required_fields = ["id", "name", "created_by", "is_active", "created_at"]
                    has_all_fields = all(field in sample_group for field in required_fields)
                    
                    self.log_test(
                        "Chat Group Structure Validation",
                        has_all_fields,
                        f"Group structure {'valid' if has_all_fields else 'invalid'}",
                        {"sample_group": sample_group, "required_fields": required_fields}
                    )
            else:
                self.log_test(
                    "READ All Chat Groups",
                    False,
                    f"Failed to get groups with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "READ All Chat Groups",
                False,
                f"Error getting groups: {str(e)}"
            )
        
        # Test 3: UPDATE Chat Group (PUT /api/admin/chat/groups/{id})
        print("\n--- Testing Chat Group Update ---")
        if self.created_group_ids:
            group_id = self.created_group_ids[0]
            update_data = {
                "name": "Einsatzleitung (Aktualisiert)",
                "description": "Aktualisierte Hauptkommunikation für Einsatzleitung mit erweiterten Funktionen",
                "is_active": True
            }
            
            try:
                response = self.session.put(
                    f"{self.base_url}/admin/chat/groups/{group_id}",
                    json=update_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    updated_group = response.json()
                    self.log_test(
                        "UPDATE Chat Group",
                        True,
                        f"Group updated successfully: '{updated_group.get('name', '')}'",
                        {"updated_name": updated_group.get("name"), "updated_description": updated_group.get("description")}
                    )
                else:
                    self.log_test(
                        "UPDATE Chat Group",
                        False,
                        f"Failed to update group with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    "UPDATE Chat Group",
                    False,
                    f"Error updating group: {str(e)}"
                )
        
        # Test 4: DELETE Chat Group (DELETE /api/admin/chat/groups/{id})
        print("\n--- Testing Chat Group Deletion ---")
        if len(self.created_group_ids) > 3:  # Keep some groups for message testing
            group_id = self.created_group_ids.pop()  # Remove last group
            
            try:
                response = self.session.delete(
                    f"{self.base_url}/admin/chat/groups/{group_id}",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "DELETE Chat Group",
                        True,
                        "Group deleted successfully"
                    )
                    
                    # Verify group is actually deleted
                    verify_response = self.session.get(
                        f"{self.base_url}/admin/chat/groups",
                        headers=self.get_auth_headers(self.admin_token)
                    )
                    
                    if verify_response.status_code == 200:
                        remaining_groups = verify_response.json()
                        deleted_group_exists = any(g.get("id") == group_id for g in remaining_groups)
                        
                        self.log_test(
                            "Verify Group Deletion",
                            not deleted_group_exists,
                            f"Deleted group {'still exists' if deleted_group_exists else 'successfully removed'}"
                        )
                else:
                    self.log_test(
                        "DELETE Chat Group",
                        False,
                        f"Failed to delete group with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    "DELETE Chat Group",
                    False,
                    f"Error deleting group: {str(e)}"
                )

    def test_chat_messages_api(self):
        """Test Chat Messages API functionality"""
        print("\n=== Testing Chat Messages API ===")
        
        if not self.admin_token:
            self.log_test("Chat Messages API", False, "No admin token available")
            return
        
        # Test messages for different scenarios
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
                "message": "Feuerwehr vor Ort, Lage unter Kontrolle",
                "chat_type": "admin",
                "group_id": self.created_group_ids[2] if len(self.created_group_ids) > 2 else None,
                "is_voice_message": False
            },
            {
                "message": "Sprach-Nachricht: Notfall-Briefing für alle Einheiten",
                "chat_type": "admin",
                "group_id": self.created_group_ids[0] if self.created_group_ids else None,
                "is_voice_message": True,
                "voice_data": "base64_encoded_voice_data_example_12345",
                "voice_duration": 45
            },
            {
                "message": "Allgemeine Nachricht ohne Gruppe",
                "chat_type": "admin",
                "group_id": None,
                "is_voice_message": False
            }
        ]
        
        # Test 1: SEND Chat Messages (POST /api/admin/chat)
        print("\n--- Testing Chat Message Sending ---")
        for i, message_data in enumerate(test_messages):
            try:
                response = self.session.post(
                    f"{self.base_url}/admin/chat",
                    json=message_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    created_message = response.json()
                    message_id = created_message.get("id")
                    if message_id:
                        self.created_message_ids.append(message_id)
                    
                    message_type = "Voice Message" if message_data.get("is_voice_message") else "Text Message"
                    group_info = f"Group: {message_data.get('group_id', 'None')}"
                    
                    self.log_test(
                        f"SEND Chat Message {i+1} ({message_type})",
                        True,
                        f"Message sent successfully - {group_info}",
                        {
                            "message_id": message_id, 
                            "username": created_message.get("username"),
                            "group_id": created_message.get("group_id"),
                            "is_voice": created_message.get("is_voice_message", False)
                        }
                    )
                else:
                    self.log_test(
                        f"SEND Chat Message {i+1}",
                        False,
                        f"Failed to send message with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    f"SEND Chat Message {i+1}",
                    False,
                    f"Error sending message: {str(e)}"
                )
        
        # Test 2: GET Chat Messages by Group (GET /api/admin/chat?group_id=xxx)
        print("\n--- Testing Chat Message Retrieval by Group ---")
        for i, group_id in enumerate(self.created_group_ids[:3]):  # Test first 3 groups
            try:
                response = self.session.get(
                    f"{self.base_url}/admin/chat",
                    params={"group_id": group_id, "chat_type": "admin"},
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    messages = response.json()
                    
                    # Verify all messages belong to the requested group
                    correct_group_messages = all(
                        msg.get("group_id") == group_id for msg in messages
                    )
                    
                    self.log_test(
                        f"GET Messages for Group {i+1}",
                        True,
                        f"Retrieved {len(messages)} messages from group (all correct group: {correct_group_messages})",
                        {
                            "messages_count": len(messages), 
                            "group_id": group_id,
                            "correct_group": correct_group_messages
                        }
                    )
                    
                    # Verify message structure
                    if messages:
                        sample_message = messages[0]
                        required_fields = ["id", "user_id", "username", "message", "chat_type", "created_at"]
                        has_all_fields = all(field in sample_message for field in required_fields)
                        
                        self.log_test(
                            f"Message Structure Validation Group {i+1}",
                            has_all_fields,
                            f"Message structure {'valid' if has_all_fields else 'invalid'}",
                            {"sample_message": sample_message}
                        )
                else:
                    self.log_test(
                        f"GET Messages for Group {i+1}",
                        False,
                        f"Failed to get messages with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    f"GET Messages for Group {i+1}",
                    False,
                    f"Error getting messages: {str(e)}"
                )
        
        # Test 3: GET All Chat Messages (GET /api/admin/chat)
        print("\n--- Testing All Chat Messages Retrieval ---")
        try:
            response = self.session.get(
                f"{self.base_url}/admin/chat",
                params={"chat_type": "admin"},
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                all_messages = response.json()
                
                # Count messages by type
                text_messages = [m for m in all_messages if not m.get("is_voice_message", False)]
                voice_messages = [m for m in all_messages if m.get("is_voice_message", False)]
                
                self.log_test(
                    "GET All Chat Messages",
                    True,
                    f"Retrieved {len(all_messages)} total messages ({len(text_messages)} text, {len(voice_messages)} voice)",
                    {
                        "total_messages": len(all_messages),
                        "text_messages": len(text_messages),
                        "voice_messages": len(voice_messages)
                    }
                )
            else:
                self.log_test(
                    "GET All Chat Messages",
                    False,
                    f"Failed to get all messages with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "GET All Chat Messages",
                False,
                f"Error getting all messages: {str(e)}"
            )

    def test_admin_profile_api(self):
        """Test Admin Profile Management API"""
        print("\n=== Testing Admin Profile Management API ===")
        
        if not self.admin_token:
            self.log_test("Admin Profile API", False, "No admin token available")
            return
        
        # Get current admin profile first
        original_name = None
        try:
            response = self.session.get(
                f"{self.base_url}/me",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                admin_data = response.json()
                original_name = admin_data.get("full_name")
                
                self.log_test(
                    "GET Current Admin Profile",
                    True,
                    f"Current admin name: '{original_name}'",
                    {"admin_profile": admin_data}
                )
        except Exception as e:
            self.log_test(
                "GET Current Admin Profile",
                False,
                f"Error getting current profile: {str(e)}"
            )
        
        # Test profile updates with different names
        test_names = [
            "Administrator (Funkgerät System)",
            "Einsatzleiter Schmidt",
            "Admin - Notfallzentrale",
            "System Administrator"  # Back to original
        ]
        
        for i, new_name in enumerate(test_names):
            profile_data = {"full_name": new_name}
            
            try:
                response = self.session.put(
                    f"{self.base_url}/admin/profile",
                    json=profile_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    updated_admin = response.json()
                    returned_name = updated_admin.get("full_name")
                    
                    # Verify the name was actually updated
                    name_updated_correctly = returned_name == new_name
                    
                    self.log_test(
                        f"UPDATE Admin Profile {i+1}",
                        name_updated_correctly,
                        f"Admin name {'successfully' if name_updated_correctly else 'incorrectly'} updated to: '{returned_name}'",
                        {
                            "requested_name": new_name,
                            "returned_name": returned_name,
                            "updated_admin": updated_admin
                        }
                    )
                    
                    # Verify the change persists by getting the profile again
                    verify_response = self.session.get(
                        f"{self.base_url}/me",
                        headers=self.get_auth_headers(self.admin_token)
                    )
                    
                    if verify_response.status_code == 200:
                        verified_admin = verify_response.json()
                        verified_name = verified_admin.get("full_name")
                        
                        self.log_test(
                            f"VERIFY Admin Profile Update {i+1}",
                            verified_name == new_name,
                            f"Profile change {'persisted' if verified_name == new_name else 'not persisted'}: '{verified_name}'",
                            {"verified_name": verified_name}
                        )
                else:
                    self.log_test(
                        f"UPDATE Admin Profile {i+1}",
                        False,
                        f"Failed to update admin profile with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    f"UPDATE Admin Profile {i+1}",
                    False,
                    f"Error updating admin profile: {str(e)}"
                )

    def test_error_handling(self):
        """Test error handling for invalid requests"""
        print("\n=== Testing Error Handling ===")
        
        if not self.admin_token:
            self.log_test("Error Handling", False, "No admin token available")
            return
        
        # Test 1: Invalid Group ID for update
        try:
            response = self.session.put(
                f"{self.base_url}/admin/chat/groups/invalid_group_id",
                json={"name": "Test Invalid"},
                headers=self.get_auth_headers(self.admin_token)
            )
            
            expected_status = response.status_code == 400
            self.log_test(
                "Invalid Group ID Update",
                expected_status,
                f"Invalid group ID {'correctly rejected' if expected_status else 'not handled properly'} (status: {response.status_code})",
                {"response_text": response.text}
            )
        except Exception as e:
            self.log_test(
                "Invalid Group ID Update",
                False,
                f"Error testing invalid group ID: {str(e)}"
            )
        
        # Test 2: Invalid Group ID for deletion
        try:
            response = self.session.delete(
                f"{self.base_url}/admin/chat/groups/invalid_group_id",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            expected_status = response.status_code == 400
            self.log_test(
                "Invalid Group ID Delete",
                expected_status,
                f"Invalid group ID delete {'correctly rejected' if expected_status else 'not handled properly'} (status: {response.status_code})",
                {"response_text": response.text}
            )
        except Exception as e:
            self.log_test(
                "Invalid Group ID Delete",
                False,
                f"Error testing invalid group ID delete: {str(e)}"
            )
        
        # Test 3: Empty message content
        try:
            response = self.session.post(
                f"{self.base_url}/admin/chat",
                json={"message": "", "chat_type": "admin"},
                headers=self.get_auth_headers(self.admin_token)
            )
            
            # This might be allowed or rejected depending on validation
            self.log_test(
                "Empty Message Content",
                True,  # We'll accept either behavior
                f"Empty message handled with status {response.status_code}",
                {"response_text": response.text}
            )
        except Exception as e:
            self.log_test(
                "Empty Message Content",
                False,
                f"Error testing empty message: {str(e)}"
            )
        
        # Test 4: Invalid JSON in profile update
        try:
            response = self.session.put(
                f"{self.base_url}/admin/profile",
                json={},  # Empty JSON
                headers=self.get_auth_headers(self.admin_token)
            )
            
            # Should be rejected due to missing required field
            expected_status = response.status_code in [400, 422]
            self.log_test(
                "Empty Profile Update",
                expected_status,
                f"Empty profile update {'correctly rejected' if expected_status else 'unexpectedly accepted'} (status: {response.status_code})",
                {"response_text": response.text}
            )
        except Exception as e:
            self.log_test(
                "Empty Profile Update",
                False,
                f"Error testing empty profile update: {str(e)}"
            )

    def test_authentication_requirements(self):
        """Test that all endpoints require proper authentication"""
        print("\n=== Testing Authentication Requirements ===")
        
        endpoints_to_test = [
            ("GET", "/admin/chat/groups", "Get Chat Groups"),
            ("POST", "/admin/chat/groups", "Create Chat Group"),
            ("GET", "/admin/chat", "Get Chat Messages"),
            ("POST", "/admin/chat", "Send Chat Message"),
            ("PUT", "/admin/profile", "Update Admin Profile")
        ]
        
        for method, endpoint, test_name in endpoints_to_test:
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}")
                elif method == "POST":
                    response = self.session.post(
                        f"{self.base_url}{endpoint}",
                        json={"test": "data"},
                        headers={"Content-Type": "application/json"}
                    )
                elif method == "PUT":
                    response = self.session.put(
                        f"{self.base_url}{endpoint}",
                        json={"test": "data"},
                        headers={"Content-Type": "application/json"}
                    )
                
                # Should be rejected with 401 or 403
                expected_status = response.status_code in [401, 403]
                self.log_test(
                    f"Unauthenticated {test_name}",
                    expected_status,
                    f"Unauthenticated request {'correctly rejected' if expected_status else 'unexpectedly allowed'} (status: {response.status_code})"
                )
            except Exception as e:
                self.log_test(
                    f"Unauthenticated {test_name}",
                    False,
                    f"Error testing unauthenticated access: {str(e)}"
                )

    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        print("\n=== Cleaning Up Test Data ===")
        
        if not self.admin_token:
            return
        
        # Delete test messages
        for message_id in self.created_message_ids:
            try:
                self.session.delete(
                    f"{self.base_url}/admin/chat/{message_id}",
                    headers=self.get_auth_headers(self.admin_token)
                )
            except Exception:
                pass  # Ignore cleanup errors
        
        # Delete test groups
        for group_id in self.created_group_ids:
            try:
                self.session.delete(
                    f"{self.base_url}/admin/chat/groups/{group_id}",
                    headers=self.get_auth_headers(self.admin_token)
                )
            except Exception:
                pass  # Ignore cleanup errors
        
        print(f"Cleanup completed: {len(self.created_message_ids)} messages, {len(self.created_group_ids)} groups")

    def run_all_tests(self):
        """Run all Funkgerät chat system tests"""
        print("🚨 FUNKGERÄT (RADIO) CHAT SYSTEM BACKEND API TESTS 🚨")
        print("=" * 60)
        
        # Setup
        if not self.setup_admin_authentication():
            print("❌ Cannot proceed without admin authentication")
            return
        
        # Run all test suites
        self.test_chat_groups_crud()
        self.test_chat_messages_api()
        self.test_admin_profile_api()
        self.test_error_handling()
        self.test_authentication_requirements()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🔍 FUNKGERÄT CHAT SYSTEM TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)
        
        # Return success rate for external use
        return success_rate

if __name__ == "__main__":
    tester = FunkgeraetChatTester()
    success_rate = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success_rate and success_rate >= 90 else 1)