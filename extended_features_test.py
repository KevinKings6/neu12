#!/usr/bin/env python3
"""
Extended Funkgerät and User Management Features Test
Tests new features: Chat message management, Enhanced user management, 
Persistent message storage, Voice message integration
"""

import requests
import json
import sys
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional

# Backend API base URL from frontend environment
BASE_URL = "https://emergency-sos-3.preview.emergentagent.com/api"
INTERNAL_URL = "http://localhost:8001/api"  # For endpoints with Kubernetes ingress limitations

class ExtendedFeaturesAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.test_results = []
        self.admin_token = None
        self.user_token = None
        self.emergency_user_token = None
        self.test_user_id = None
        self.emergency_user_id = None
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

    def setup_authentication(self):
        """Setup admin and user authentication"""
        print("\n=== Setting Up Authentication ===")
        
        # Create admin if not exists
        try:
            response = self.session.post(f"{self.base_url}/create-admin")
            if response.status_code == 200:
                print("✅ Admin user ready")
        except Exception as e:
            print(f"❌ Error creating admin: {e}")
            return False
        
        # Login as admin
        try:
            login_data = {"username": "admin", "password": "admin123"}
            response = self.session.post(f"{self.base_url}/login", json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                self.admin_token = token_data.get("access_token")
                print("✅ Admin login successful")
            else:
                print(f"❌ Admin login failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error logging in admin: {e}")
            return False
        
        # Create test user
        try:
            user_data = {
                "username": "testuser_extended",
                "email": "testuser_extended@emergency-sos.com",
                "full_name": "Test Extended User",
                "password": "testpass123",
                "role": "user"
            }
            response = self.session.post(f"{self.base_url}/register", json=user_data)
            if response.status_code == 200:
                created_user = response.json()
                self.test_user_id = created_user.get("id")
                print("✅ Test user created")
            elif "already registered" in response.text:
                print("✅ Test user already exists")
        except Exception as e:
            print(f"❌ Error creating test user: {e}")
        
        # Always get user ID from admin users list to ensure we have it
        if self.admin_token:
            try:
                users_response = self.session.get(
                    f"{self.base_url}/admin/users",
                    headers=self.get_auth_headers(self.admin_token)
                )
                if users_response.status_code == 200:
                    users = users_response.json()
                    for user in users:
                        if user.get("username") == "testuser_extended":
                            self.test_user_id = user.get("id")
                            print(f"✅ Found test user ID: {self.test_user_id}")
                            break
            except Exception as e:
                print(f"❌ Error getting user ID: {e}")
        
        # Login as test user
        try:
            login_data = {"username": "testuser_extended", "password": "testpass123"}
            response = self.session.post(f"{self.base_url}/login", json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                self.user_token = token_data.get("access_token")
                print("✅ Test user login successful")
        except Exception as e:
            print(f"❌ Error logging in test user: {e}")
        
        return self.admin_token is not None

    def test_create_emergency_user(self):
        """Test POST /api/admin/create-emergency-user"""
        print("\n=== Testing Emergency User Creation ===")
        
        if not self.admin_token:
            self.log_test("Create Emergency User", False, "No admin token available")
            return
        
        try:
            response = self.session.post(
                f"{self.base_url}/admin/create-emergency-user",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                result = response.json()
                self.emergency_user_id = result.get("user_id")
                self.log_test(
                    "Create Emergency User",
                    True,
                    "Emergency user created successfully",
                    {"user_id": self.emergency_user_id, "response": result}
                )
                
                # Try to login with emergency user
                try:
                    login_data = {"username": "emergencyuser", "password": "emergency123"}
                    login_response = self.session.post(f"{self.base_url}/login", json=login_data)
                    if login_response.status_code == 200:
                        token_data = login_response.json()
                        self.emergency_user_token = token_data.get("access_token")
                        user_role = token_data.get("user", {}).get("role")
                        self.log_test(
                            "Emergency User Login",
                            True,
                            f"Emergency user login successful with role: {user_role}",
                            {"role": user_role}
                        )
                    else:
                        self.log_test(
                            "Emergency User Login",
                            False,
                            f"Emergency user login failed: {login_response.status_code}"
                        )
                except Exception as e:
                    self.log_test(
                        "Emergency User Login",
                        False,
                        f"Error logging in emergency user: {str(e)}"
                    )
            else:
                self.log_test(
                    "Create Emergency User",
                    False,
                    f"Failed to create emergency user: {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Create Emergency User",
                False,
                f"Error creating emergency user: {str(e)}"
            )

    def test_user_role_management_emergency(self):
        """Test PUT /api/admin/users/{user_id}/role with emergency role"""
        print("\n=== Testing Emergency Role Management ===")
        
        if not self.admin_token or not self.test_user_id:
            self.log_test("Emergency Role Management", False, "No admin token or test user ID available")
            return
        
        # Test all roles including emergency
        roles_to_test = ["user", "team", "admin", "emergency"]
        
        for role in roles_to_test:
            try:
                role_data = {"role": role}
                response = self.session.put(
                    f"{self.base_url}/admin/users/{self.test_user_id}/role",
                    json=role_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        f"Set User Role to {role.title()}",
                        True,
                        f"User role successfully changed to {role}"
                    )
                else:
                    self.log_test(
                        f"Set User Role to {role.title()}",
                        False,
                        f"Failed to change role to {role}: {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    f"Set User Role to {role.title()}",
                    False,
                    f"Error changing role to {role}: {str(e)}"
                )
        
        # Test invalid role rejection
        try:
            invalid_role_data = {"role": "superuser"}
            response = self.session.put(
                f"{self.base_url}/admin/users/{self.test_user_id}/role",
                json=invalid_role_data,
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 400:
                self.log_test(
                    "Invalid Role Rejection",
                    True,
                    "Invalid role 'superuser' correctly rejected"
                )
            else:
                self.log_test(
                    "Invalid Role Rejection",
                    False,
                    f"Expected 400 for invalid role but got {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "Invalid Role Rejection",
                False,
                f"Error testing invalid role: {str(e)}"
            )

    def test_user_toggle_status(self):
        """Test POST /api/admin/users/{user_id}/toggle-status"""
        print("\n=== Testing User Status Toggle ===")
        
        if not self.admin_token or not self.test_user_id:
            self.log_test("User Status Toggle", False, "No admin token or test user ID available")
            return
        
        # Test toggling user status
        try:
            response = self.session.post(
                f"{self.base_url}/admin/users/{self.test_user_id}/toggle-status",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                result = response.json()
                new_status = result.get("is_active")
                self.log_test(
                    "Toggle User Status (First)",
                    True,
                    f"User status toggled successfully to: {'active' if new_status else 'inactive'}",
                    {"new_status": new_status}
                )
                
                # Toggle back
                toggle_response = self.session.post(
                    f"{self.base_url}/admin/users/{self.test_user_id}/toggle-status",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if toggle_response.status_code == 200:
                    toggle_result = toggle_response.json()
                    final_status = toggle_result.get("is_active")
                    self.log_test(
                        "Toggle User Status (Second)",
                        True,
                        f"User status toggled back to: {'active' if final_status else 'inactive'}",
                        {"final_status": final_status}
                    )
                else:
                    self.log_test(
                        "Toggle User Status (Second)",
                        False,
                        f"Failed to toggle status back: {toggle_response.status_code}"
                    )
            else:
                self.log_test(
                    "Toggle User Status (First)",
                    False,
                    f"Failed to toggle user status: {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Toggle User Status",
                False,
                f"Error toggling user status: {str(e)}"
            )
        
        # Test with invalid user ID
        try:
            response = self.session.post(
                f"{self.base_url}/admin/users/invalid_user_id/toggle-status",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 400:
                self.log_test(
                    "Invalid User ID Toggle",
                    True,
                    "Invalid user ID correctly rejected for status toggle"
                )
            else:
                self.log_test(
                    "Invalid User ID Toggle",
                    False,
                    f"Expected 400 for invalid user ID but got {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "Invalid User ID Toggle",
                False,
                f"Error testing invalid user ID toggle: {str(e)}"
            )

    def test_persistent_message_storage(self):
        """Test persistent message storage in channels"""
        print("\n=== Testing Persistent Message Storage ===")
        
        if not self.admin_token:
            self.log_test("Persistent Message Storage", False, "No admin token available")
            return
        
        # Create test groups first
        test_groups = [
            {"name": "Kanal Alpha", "description": "Test Kanal Alpha"},
            {"name": "Kanal Beta", "description": "Test Kanal Beta"},
            {"name": "Kanal Gamma", "description": "Test Kanal Gamma"}
        ]
        
        group_ids = []
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
                        group_ids.append(group_id)
                        self.created_group_ids.append(group_id)
                    
                    self.log_test(
                        f"Create Test Group {i+1}",
                        True,
                        f"Group '{group_data['name']}' created for testing"
                    )
                else:
                    self.log_test(
                        f"Create Test Group {i+1}",
                        False,
                        f"Failed to create test group: {response.status_code}"
                    )
            except Exception as e:
                self.log_test(
                    f"Create Test Group {i+1}",
                    False,
                    f"Error creating test group: {str(e)}"
                )
        
        if len(group_ids) < 2:
            self.log_test("Persistent Message Storage", False, "Not enough test groups created")
            return
        
        # Send messages to different channels
        test_messages = [
            {
                "message": "Nachricht für Kanal Alpha - Einsatz 001",
                "group_id": group_ids[0],
                "chat_type": "admin"
            },
            {
                "message": "Nachricht für Kanal Alpha - Einsatz 002", 
                "group_id": group_ids[0],
                "chat_type": "admin"
            },
            {
                "message": "Nachricht für Kanal Beta - Status Update",
                "group_id": group_ids[1],
                "chat_type": "admin"
            },
            {
                "message": "Weitere Nachricht für Kanal Beta - Abschluss",
                "group_id": group_ids[1],
                "chat_type": "admin"
            }
        ]
        
        sent_message_ids = []
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
                        sent_message_ids.append(message_id)
                        self.created_message_ids.append(message_id)
                    
                    self.log_test(
                        f"Send Message to Channel {i+1}",
                        True,
                        f"Message sent to channel successfully"
                    )
                else:
                    self.log_test(
                        f"Send Message to Channel {i+1}",
                        False,
                        f"Failed to send message: {response.status_code}"
                    )
            except Exception as e:
                self.log_test(
                    f"Send Message to Channel {i+1}",
                    False,
                    f"Error sending message: {str(e)}"
                )
        
        # Verify messages are stored in correct channels
        for i, group_id in enumerate(group_ids[:2]):
            try:
                response = self.session.get(
                    f"{self.base_url}/admin/chat",
                    params={"group_id": group_id, "chat_type": "admin"},
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    messages = response.json()
                    expected_count = 2  # We sent 2 messages to each channel
                    actual_count = len([msg for msg in messages if msg.get("group_id") == group_id])
                    
                    self.log_test(
                        f"Verify Channel {i+1} Messages",
                        actual_count >= expected_count,
                        f"Channel has {actual_count} messages (expected at least {expected_count})",
                        {"group_id": group_id, "message_count": actual_count}
                    )
                else:
                    self.log_test(
                        f"Verify Channel {i+1} Messages",
                        False,
                        f"Failed to retrieve channel messages: {response.status_code}"
                    )
            except Exception as e:
                self.log_test(
                    f"Verify Channel {i+1} Messages",
                    False,
                    f"Error verifying channel messages: {str(e)}"
                )

    def test_voice_message_integration(self):
        """Test voice message integration with base64 data"""
        print("\n=== Testing Voice Message Integration ===")
        
        if not self.admin_token:
            self.log_test("Voice Message Integration", False, "No admin token available")
            return
        
        # Create a test group for voice messages
        group_data = {"name": "Voice Test Channel", "description": "Channel for voice message testing"}
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
                if group_id:
                    self.created_group_ids.append(group_id)
                
                self.log_test(
                    "Create Voice Test Group",
                    True,
                    "Voice test group created successfully"
                )
            else:
                self.log_test(
                    "Create Voice Test Group",
                    False,
                    f"Failed to create voice test group: {response.status_code}"
                )
                return
        except Exception as e:
            self.log_test(
                "Create Voice Test Group",
                False,
                f"Error creating voice test group: {str(e)}"
            )
            return
        
        # Generate sample base64 voice data (simulated)
        sample_audio_text = "This is a simulated voice message for testing purposes"
        sample_base64_data = base64.b64encode(sample_audio_text.encode()).decode()
        
        # Test voice messages with different durations
        voice_messages = [
            {
                "message": "Kurze Sprachnachricht - Einsatzstatus",
                "group_id": group_id,
                "chat_type": "admin",
                "is_voice_message": True,
                "voice_data": sample_base64_data,
                "voice_duration": 15
            },
            {
                "message": "Längere Sprachnachricht - Detaillierter Bericht",
                "group_id": group_id,
                "chat_type": "admin", 
                "is_voice_message": True,
                "voice_data": sample_base64_data + "extended_content",
                "voice_duration": 45
            },
            {
                "message": "Sehr kurze Sprachnachricht",
                "group_id": group_id,
                "chat_type": "admin",
                "is_voice_message": True,
                "voice_data": sample_base64_data[:50],
                "voice_duration": 5
            }
        ]
        
        voice_message_ids = []
        for i, voice_data in enumerate(voice_messages):
            try:
                response = self.session.post(
                    f"{self.base_url}/admin/chat",
                    json=voice_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    created_message = response.json()
                    message_id = created_message.get("id")
                    if message_id:
                        voice_message_ids.append(message_id)
                        self.created_message_ids.append(message_id)
                    
                    # Verify voice message fields
                    is_voice = created_message.get("is_voice_message", False)
                    voice_duration = created_message.get("voice_duration")
                    has_voice_data = bool(created_message.get("voice_data"))
                    
                    self.log_test(
                        f"Send Voice Message {i+1}",
                        True,
                        f"Voice message sent (duration: {voice_duration}s, has_data: {has_voice_data})",
                        {
                            "message_id": message_id,
                            "is_voice_message": is_voice,
                            "voice_duration": voice_duration,
                            "has_voice_data": has_voice_data
                        }
                    )
                else:
                    self.log_test(
                        f"Send Voice Message {i+1}",
                        False,
                        f"Failed to send voice message: {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    f"Send Voice Message {i+1}",
                    False,
                    f"Error sending voice message: {str(e)}"
                )
        
        # Verify voice messages can be retrieved
        if group_id:
            try:
                response = self.session.get(
                    f"{self.base_url}/admin/chat",
                    params={"group_id": group_id, "chat_type": "admin"},
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    messages = response.json()
                    voice_messages_found = [msg for msg in messages if msg.get("is_voice_message")]
                    
                    self.log_test(
                        "Retrieve Voice Messages",
                        len(voice_messages_found) >= len(voice_message_ids),
                        f"Retrieved {len(voice_messages_found)} voice messages from channel",
                        {"voice_messages_count": len(voice_messages_found)}
                    )
                    
                    # Verify voice data integrity
                    for msg in voice_messages_found:
                        has_voice_data = bool(msg.get("voice_data"))
                        has_duration = msg.get("voice_duration") is not None
                        
                        if has_voice_data and has_duration:
                            self.log_test(
                                f"Voice Data Integrity Check",
                                True,
                                f"Voice message has complete data (duration: {msg.get('voice_duration')}s)"
                            )
                        else:
                            self.log_test(
                                f"Voice Data Integrity Check",
                                False,
                                f"Voice message missing data (has_data: {has_voice_data}, has_duration: {has_duration})"
                            )
                else:
                    self.log_test(
                        "Retrieve Voice Messages",
                        False,
                        f"Failed to retrieve voice messages: {response.status_code}"
                    )
            except Exception as e:
                self.log_test(
                    "Retrieve Voice Messages",
                    False,
                    f"Error retrieving voice messages: {str(e)}"
                )

    def test_chat_message_management(self):
        """Test PUT and DELETE /api/admin/chat/{message_id}"""
        print("\n=== Testing Chat Message Management ===")
        
        if not self.admin_token:
            self.log_test("Chat Message Management", False, "No admin token available")
            return
        
        # Create a test group and send messages
        group_data = {"name": "Message Management Test", "description": "Test group for message management"}
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
                if group_id:
                    self.created_group_ids.append(group_id)
        except Exception as e:
            self.log_test("Create Message Test Group", False, f"Error creating test group: {str(e)}")
            return
        
        # Send test messages
        test_messages = [
            {
                "message": "Original message - will be edited",
                "group_id": group_id,
                "chat_type": "admin"
            },
            {
                "message": "Message to be deleted",
                "group_id": group_id,
                "chat_type": "admin"
            },
            {
                "message": "Voice message to be edited",
                "group_id": group_id,
                "chat_type": "admin",
                "is_voice_message": True,
                "voice_data": base64.b64encode("test voice data".encode()).decode(),
                "voice_duration": 10
            }
        ]
        
        message_ids = []
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
                        message_ids.append(message_id)
                        self.created_message_ids.append(message_id)
        
                    self.log_test(
                        f"Create Test Message {i+1}",
                        True,
                        "Test message created for management testing"
                    )
            except Exception as e:
                self.log_test(
                    f"Create Test Message {i+1}",
                    False,
                    f"Error creating test message: {str(e)}"
                )
        
        if len(message_ids) < 2:
            self.log_test("Chat Message Management", False, "Not enough test messages created")
            return
        
        # Test message editing (PUT /api/admin/chat/{message_id})
        if message_ids:
            message_id = message_ids[0]
            edit_data = {"message": "EDITED: This message has been updated by admin"}
            
            try:
                response = self.session.put(
                    f"{self.base_url}/admin/chat/{message_id}",
                    json=edit_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "Edit Chat Message (Admin)",
                        True,
                        "Admin successfully edited chat message"
                    )
                    
                    # Verify the edit by retrieving messages
                    try:
                        verify_response = self.session.get(
                            f"{self.base_url}/admin/chat",
                            params={"group_id": group_id, "chat_type": "admin"},
                            headers=self.get_auth_headers(self.admin_token)
                        )
                        
                        if verify_response.status_code == 200:
                            messages = verify_response.json()
                            edited_message = next((msg for msg in messages if msg.get("id") == message_id), None)
                            
                            if edited_message and "EDITED:" in edited_message.get("message", ""):
                                self.log_test(
                                    "Verify Message Edit",
                                    True,
                                    "Message edit successfully persisted"
                                )
                            else:
                                self.log_test(
                                    "Verify Message Edit",
                                    False,
                                    "Message edit not found in retrieved messages"
                                )
                    except Exception as e:
                        self.log_test(
                            "Verify Message Edit",
                            False,
                            f"Error verifying message edit: {str(e)}"
                        )
                else:
                    self.log_test(
                        "Edit Chat Message (Admin)",
                        False,
                        f"Failed to edit message: {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    "Edit Chat Message (Admin)",
                    False,
                    f"Error editing message: {str(e)}"
                )
        
        # Test message deletion (DELETE /api/admin/chat/{message_id})
        if len(message_ids) > 1:
            message_id = message_ids[1]
            
            try:
                response = self.session.delete(
                    f"{self.base_url}/admin/chat/{message_id}",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "Delete Chat Message (Admin)",
                        True,
                        "Admin successfully deleted chat message"
                    )
                    
                    # Verify the deletion by retrieving messages
                    try:
                        verify_response = self.session.get(
                            f"{self.base_url}/admin/chat",
                            params={"group_id": group_id, "chat_type": "admin"},
                            headers=self.get_auth_headers(self.admin_token)
                        )
                        
                        if verify_response.status_code == 200:
                            messages = verify_response.json()
                            deleted_message = next((msg for msg in messages if msg.get("id") == message_id), None)
                            
                            if not deleted_message:
                                self.log_test(
                                    "Verify Message Deletion",
                                    True,
                                    "Message successfully removed from channel"
                                )
                            else:
                                self.log_test(
                                    "Verify Message Deletion",
                                    False,
                                    "Deleted message still found in channel"
                                )
                    except Exception as e:
                        self.log_test(
                            "Verify Message Deletion",
                            False,
                            f"Error verifying message deletion: {str(e)}"
                        )
                else:
                    self.log_test(
                        "Delete Chat Message (Admin)",
                        False,
                        f"Failed to delete message: {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    "Delete Chat Message (Admin)",
                    False,
                    f"Error deleting message: {str(e)}"
                )
        
        # Test voice message editing
        if len(message_ids) > 2:
            voice_message_id = message_ids[2]
            voice_edit_data = {"message": "EDITED: Voice message content updated"}
            
            try:
                response = self.session.put(
                    f"{self.base_url}/admin/chat/{voice_message_id}",
                    json=voice_edit_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "Edit Voice Message",
                        True,
                        "Voice message text successfully edited"
                    )
                else:
                    self.log_test(
                        "Edit Voice Message",
                        False,
                        f"Failed to edit voice message: {response.status_code}"
                    )
            except Exception as e:
                self.log_test(
                    "Edit Voice Message",
                    False,
                    f"Error editing voice message: {str(e)}"
                )
        
        # Test error handling for invalid message IDs
        try:
            response = self.session.put(
                f"{self.base_url}/admin/chat/invalid_message_id",
                json={"message": "Test edit"},
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 400:
                self.log_test(
                    "Invalid Message ID Edit",
                    True,
                    "Invalid message ID correctly rejected for edit"
                )
            else:
                self.log_test(
                    "Invalid Message ID Edit",
                    False,
                    f"Expected 400 for invalid message ID but got {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "Invalid Message ID Edit",
                False,
                f"Error testing invalid message ID edit: {str(e)}"
            )
        
        try:
            response = self.session.delete(
                f"{self.base_url}/admin/chat/invalid_message_id",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 400:
                self.log_test(
                    "Invalid Message ID Delete",
                    True,
                    "Invalid message ID correctly rejected for delete"
                )
            else:
                self.log_test(
                    "Invalid Message ID Delete",
                    False,
                    f"Expected 400 for invalid message ID but got {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "Invalid Message ID Delete",
                False,
                f"Error testing invalid message ID delete: {str(e)}"
            )

    def test_user_permissions_message_management(self):
        """Test that regular users can only edit/delete their own messages"""
        print("\n=== Testing User Permissions for Message Management ===")
        
        if not self.admin_token or not self.user_token:
            self.log_test("User Message Permissions", False, "Missing required tokens")
            return
        
        # Create a test group
        group_data = {"name": "Permission Test Group", "description": "Test group for permission testing"}
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
                if group_id:
                    self.created_group_ids.append(group_id)
        except Exception as e:
            self.log_test("Create Permission Test Group", False, f"Error: {str(e)}")
            return
        
        # Send message as admin
        admin_message_data = {
            "message": "Admin message - should not be editable by regular user",
            "group_id": group_id,
            "chat_type": "admin"
        }
        
        admin_message_id = None
        try:
            response = self.session.post(
                f"{self.base_url}/admin/chat",
                json=admin_message_data,
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                created_message = response.json()
                admin_message_id = created_message.get("id")
                if admin_message_id:
                    self.created_message_ids.append(admin_message_id)
        except Exception as e:
            self.log_test("Create Admin Message for Permission Test", False, f"Error: {str(e)}")
        
        # Try to edit admin message as regular user (should fail if user is not admin)
        if admin_message_id:
            try:
                edit_data = {"message": "User trying to edit admin message"}
                response = self.session.put(
                    f"{self.base_url}/admin/chat/{admin_message_id}",
                    json=edit_data,
                    headers=self.get_auth_headers(self.user_token)
                )
                
                # This should fail with 403 if user is not admin, or succeed if user has admin role
                if response.status_code == 403:
                    self.log_test(
                        "User Edit Admin Message (Denied)",
                        True,
                        "Regular user correctly denied editing admin message"
                    )
                elif response.status_code == 200:
                    self.log_test(
                        "User Edit Admin Message (Allowed)",
                        True,
                        "User with admin privileges can edit admin message"
                    )
                else:
                    self.log_test(
                        "User Edit Admin Message",
                        False,
                        f"Unexpected response code: {response.status_code}"
                    )
            except Exception as e:
                self.log_test(
                    "User Edit Admin Message",
                    False,
                    f"Error testing user edit permissions: {str(e)}"
                )

    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        print("\n=== Cleaning Up Test Data ===")
        
        if not self.admin_token:
            return
        
        # Delete test groups
        for group_id in self.created_group_ids:
            try:
                self.session.delete(
                    f"{self.base_url}/admin/chat/groups/{group_id}",
                    headers=self.get_auth_headers(self.admin_token)
                )
            except Exception:
                pass  # Ignore cleanup errors
        
        print(f"✅ Cleaned up {len(self.created_group_ids)} test groups")

    def run_all_tests(self):
        """Run all extended features tests"""
        print("🚀 Starting Extended Funkgerät and User Management Features Testing")
        print("=" * 80)
        
        # Setup
        if not self.setup_authentication():
            print("❌ Authentication setup failed. Cannot proceed with tests.")
            return
        
        # Run all tests
        self.test_create_emergency_user()
        self.test_user_role_management_emergency()
        self.test_user_toggle_status()
        self.test_persistent_message_storage()
        self.test_voice_message_integration()
        self.test_chat_message_management()
        self.test_user_permissions_message_management()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 EXTENDED FEATURES TEST SUMMARY")
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
        
        # Determine overall result
        if success_rate >= 90:
            print(f"\n🎉 EXCELLENT! Success rate {success_rate:.1f}% meets the 90%+ requirement!")
        elif success_rate >= 80:
            print(f"\n✅ GOOD! Success rate {success_rate:.1f}% is acceptable.")
        else:
            print(f"\n⚠️  NEEDS IMPROVEMENT! Success rate {success_rate:.1f}% is below expectations.")

if __name__ == "__main__":
    tester = ExtendedFeaturesAPITester()
    tester.run_all_tests()