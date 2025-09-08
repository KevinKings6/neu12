#!/usr/bin/env python3
"""
Corrected CRUD Tests for Funkgerät (Radio) and SOS Management
Addresses the specific issues found in initial testing
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# URLs - Internal for chat groups, External for others
BASE_URL_EXTERNAL = "https://emergency-sos-3.preview.emergentagent.com/api"
BASE_URL_INTERNAL = "http://localhost:8001/api"

class CorrectedCRUDTester:
    def __init__(self):
        self.external_url = BASE_URL_EXTERNAL
        self.internal_url = BASE_URL_INTERNAL
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
        """Setup admin authentication"""
        print("\n=== Setting up Admin Authentication ===")
        
        # Login as admin
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
                
                self.log_test(
                    "Admin Authentication Setup",
                    True,
                    f"Admin login successful",
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

    def get_test_user_id(self):
        """Get test user ID from admin users list"""
        try:
            response = self.session.get(
                f"{self.external_url}/admin/users",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                users = response.json()
                for user in users:
                    if user.get("username") == "testuser_funkgeraet":
                        self.test_user_id = user.get("id") or user.get("_id")
                        return True
                        
                # If user doesn't exist, create one
                user_data = {
                    "username": "testuser_funkgeraet",
                    "email": "testuser_funkgeraet@emergency-sos.com",
                    "full_name": "Test Funkgerät User",
                    "password": "testpass123",
                    "role": "user"
                }
                
                response = self.session.post(
                    f"{self.external_url}/register",
                    json=user_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    created_user = response.json()
                    self.test_user_id = created_user.get("id")
                    return True
                    
        except Exception as e:
            print(f"Error getting test user: {e}")
        
        return False

    def test_funkgeraet_kanal_management(self):
        """Test Funkgerät Kanal Management using internal URL"""
        print("\n=== Testing Funkgerät Kanal-Management (Internal URL) ===")
        
        if not self.admin_token:
            self.log_test("Funkgerät Kanal Management", False, "No admin token available")
            return
        
        # Test channels data
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
            }
        ]
        
        # 1. CREATE - POST /api/admin/chat/groups (Internal URL)
        print("\n--- Testing Channel Creation (Internal URL) ---")
        for i, channel_data in enumerate(test_channels):
            try:
                response = self.session.post(
                    f"{self.internal_url}/admin/chat/groups",
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
                        f"Channel created successfully (Internal URL)",
                        {"channel_id": channel_id}
                    )
                else:
                    self.log_test(
                        f"CREATE Channel {i+1}: {channel_data['name']}",
                        False,
                        f"Failed to create channel with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    f"CREATE Channel {i+1}: {channel_data['name']}",
                    False,
                    f"Error creating channel: {str(e)}"
                )
        
        # 2. READ - GET /api/admin/chat/groups (Internal URL)
        print("\n--- Testing Channel Listing (Internal URL) ---")
        try:
            response = self.session.get(
                f"{self.internal_url}/admin/chat/groups",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                channels = response.json()
                self.log_test(
                    "READ All Channels (Internal)",
                    True,
                    f"Retrieved {len(channels)} channels successfully",
                    {"channels_count": len(channels)}
                )
            else:
                self.log_test(
                    "READ All Channels (Internal)",
                    False,
                    f"Failed to get channels with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "READ All Channels (Internal)",
                False,
                f"Error getting channels: {str(e)}"
            )
        
        # 3. UPDATE - PUT /api/admin/chat/groups/{id} (Internal URL)
        print("\n--- Testing Channel Updates (Internal URL) ---")
        if self.created_group_ids:
            channel_id = self.created_group_ids[0]
            update_data = {
                "name": "Einsatzleitung Zentral (Aktualisiert)",
                "description": "UPDATED: Hauptkommunikation mit neuen Protokollen",
                "is_active": True
            }
            
            try:
                response = self.session.put(
                    f"{self.internal_url}/admin/chat/groups/{channel_id}",
                    json=update_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    updated_channel = response.json()
                    self.log_test(
                        "UPDATE Channel (Internal)",
                        True,
                        f"Channel updated successfully",
                        {"channel_id": channel_id}
                    )
                else:
                    self.log_test(
                        "UPDATE Channel (Internal)",
                        False,
                        f"Failed to update channel with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    "UPDATE Channel (Internal)",
                    False,
                    f"Error updating channel: {str(e)}"
                )
        
        # 4. DELETE - DELETE /api/admin/chat/groups/{id} (Internal URL)
        print("\n--- Testing Channel Deletion (Internal URL) ---")
        if len(self.created_group_ids) > 1:
            channel_id = self.created_group_ids[-1]  # Delete last one
            
            try:
                response = self.session.delete(
                    f"{self.internal_url}/admin/chat/groups/{channel_id}",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "DELETE Channel (Internal)",
                        True,
                        f"Channel deleted successfully",
                        {"channel_id": channel_id}
                    )
                    self.created_group_ids.remove(channel_id)
                else:
                    self.log_test(
                        "DELETE Channel (Internal)",
                        False,
                        f"Failed to delete channel with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    "DELETE Channel (Internal)",
                    False,
                    f"Error deleting channel: {str(e)}"
                )

    def test_chat_message_management(self):
        """Test Chat Message Management"""
        print("\n=== Testing Chat Message Management ===")
        
        if not self.admin_token:
            self.log_test("Chat Message Management", False, "No admin token available")
            return
        
        # Create test messages first (External URL works for messages)
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
            }
        ]
        
        # Create messages
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
                        self.created_message_ids.append(message_id)
                    
                    self.log_test(
                        f"Create Test Message {i+1}",
                        True,
                        f"Message created successfully",
                        {"message_id": message_id}
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
        
        # Test message editing - Try both internal and external URLs
        print("\n--- Testing Message Editing ---")
        if self.created_message_ids:
            message_id = self.created_message_ids[0]
            updated_message_data = {
                "message": f"AKTUALISIERT: Einsatz Hauptstraße 123 - Status: Bearbeitet um {datetime.now().strftime('%H:%M')}"
            }
            
            # Try external URL first
            try:
                response = self.session.put(
                    f"{self.external_url}/admin/chat/{message_id}",
                    json=updated_message_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "EDIT Message (External URL)",
                        True,
                        f"Message edited successfully via external URL",
                        {"message_id": message_id}
                    )
                elif response.status_code == 405:
                    # Try internal URL
                    response = self.session.put(
                        f"{self.internal_url}/admin/chat/{message_id}",
                        json=updated_message_data,
                        headers=self.get_auth_headers(self.admin_token)
                    )
                    
                    if response.status_code == 200:
                        self.log_test(
                            "EDIT Message (Internal URL)",
                            True,
                            f"Message edited successfully via internal URL",
                            {"message_id": message_id}
                        )
                    else:
                        self.log_test(
                            "EDIT Message (Internal URL)",
                            False,
                            f"Failed to edit message with status {response.status_code}",
                            {"response_text": response.text}
                        )
                else:
                    self.log_test(
                        "EDIT Message (External URL)",
                        False,
                        f"Failed to edit message with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    "EDIT Message",
                    False,
                    f"Error editing message: {str(e)}"
                )
        
        # Test message deletion
        print("\n--- Testing Message Deletion ---")
        if len(self.created_message_ids) > 1:
            message_id = self.created_message_ids[-1]
            
            try:
                response = self.session.delete(
                    f"{self.external_url}/admin/chat/{message_id}",
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
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    "DELETE Message",
                    False,
                    f"Error deleting message: {str(e)}"
                )

    def test_user_group_management_corrected(self):
        """Test User Group Management with corrected endpoints"""
        print("\n=== Testing User Group Management (Corrected) ===")
        
        if not self.admin_token:
            self.log_test("User Group Management", False, "No admin token available")
            return
        
        # Get test user ID
        if not self.get_test_user_id():
            self.log_test("User Group Management", False, "Could not get test user ID")
            return
        
        print(f"Using test user ID: {self.test_user_id}")
        
        # Test user role changes - Use correct endpoint format
        print("\n--- Testing User Role Changes ---")
        
        # The endpoint might need ObjectId format, let's try both
        role_data = {"role": "team"}
        
        try:
            response = self.session.put(
                f"{self.external_url}/admin/users/{self.test_user_id}/role",
                json=role_data,
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                self.log_test(
                    "Change User Role to TEAM",
                    True,
                    f"User role successfully changed to team",
                    {"user_id": self.test_user_id}
                )
            elif response.status_code == 404:
                # Try with ObjectId conversion or different format
                self.log_test(
                    "Change User Role to TEAM",
                    False,
                    f"User not found (404) - may be ObjectId format issue",
                    {"user_id": self.test_user_id, "response": response.text}
                )
            else:
                self.log_test(
                    "Change User Role to TEAM",
                    False,
                    f"Failed to change role with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Change User Role to TEAM",
                False,
                f"Error changing role: {str(e)}"
            )
        
        # Test user status toggle
        print("\n--- Testing User Status Toggle ---")
        
        try:
            response = self.session.post(
                f"{self.external_url}/admin/users/{self.test_user_id}/toggle-status",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                response_data = response.json()
                new_status = response_data.get("is_active")
                self.log_test(
                    "Toggle User Status",
                    True,
                    f"User status toggled successfully to: {'Active' if new_status else 'Inactive'}",
                    {"user_id": self.test_user_id, "new_status": new_status}
                )
            elif response.status_code == 404:
                self.log_test(
                    "Toggle User Status",
                    False,
                    f"User not found (404) - may be ObjectId format issue",
                    {"user_id": self.test_user_id, "response": response.text}
                )
            else:
                self.log_test(
                    "Toggle User Status",
                    False,
                    f"Failed to toggle status with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Toggle User Status",
                False,
                f"Error toggling status: {str(e)}"
            )

    def test_sos_alert_management_corrected(self):
        """Test SOS Alert Management with corrected endpoints"""
        print("\n=== Testing SOS Alert Management (Corrected) ===")
        
        if not self.admin_token:
            self.log_test("SOS Alert Management", False, "No admin token available")
            return
        
        # Get existing SOS alerts first
        try:
            response = self.session.get(
                f"{self.external_url}/admin/sos-alerts",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                existing_alerts = response.json()
                print(f"Found {len(existing_alerts)} existing SOS alerts")
                
                if existing_alerts:
                    # Test with existing alert
                    test_sos_id = existing_alerts[0].get("id") or existing_alerts[0].get("_id")
                    print(f"Testing with SOS ID: {test_sos_id}")
                    
                    # Test SOS status update (this works, not activation)
                    print("\n--- Testing SOS Status Update ---")
                    try:
                        response = self.session.put(
                            f"{self.external_url}/admin/sos-alerts/{test_sos_id}/status",
                            params={"status": "admin_active"},
                            headers=self.get_auth_headers(self.admin_token)
                        )
                        
                        if response.status_code == 200:
                            self.log_test(
                                "SOS Status Update to admin_active",
                                True,
                                f"SOS alert status updated successfully",
                                {"sos_id": test_sos_id}
                            )
                        else:
                            self.log_test(
                                "SOS Status Update to admin_active",
                                False,
                                f"Failed to update SOS status with {response.status_code}",
                                {"response_text": response.text}
                            )
                    except Exception as e:
                        self.log_test(
                            "SOS Status Update to admin_active",
                            False,
                            f"Error updating SOS status: {str(e)}"
                        )
                    
                    # Test getting admin active alerts
                    print("\n--- Testing Admin Active Alerts ---")
                    try:
                        response = self.session.get(
                            f"{self.external_url}/admin/active-alerts",
                            headers=self.get_auth_headers(self.admin_token)
                        )
                        
                        if response.status_code == 200:
                            active_alerts = response.json()
                            self.log_test(
                                "GET Admin Active Alerts",
                                True,
                                f"Retrieved {len(active_alerts)} admin-active alerts",
                                {"active_alerts_count": len(active_alerts)}
                            )
                        else:
                            self.log_test(
                                "GET Admin Active Alerts",
                                False,
                                f"Failed to get active alerts with {response.status_code}",
                                {"response_text": response.text}
                            )
                    except Exception as e:
                        self.log_test(
                            "GET Admin Active Alerts",
                            False,
                            f"Error getting active alerts: {str(e)}"
                        )
                    
                    # Test SOS deletion (use correct endpoint)
                    print("\n--- Testing SOS Deletion ---")
                    if len(existing_alerts) > 1:
                        delete_sos_id = existing_alerts[-1].get("id") or existing_alerts[-1].get("_id")
                        
                        try:
                            response = self.session.delete(
                                f"{self.external_url}/admin/sos-alerts/{delete_sos_id}",
                                headers=self.get_auth_headers(self.admin_token)
                            )
                            
                            if response.status_code == 200:
                                self.log_test(
                                    "DELETE SOS Alert",
                                    True,
                                    f"SOS alert deleted successfully",
                                    {"sos_id": delete_sos_id}
                                )
                            else:
                                self.log_test(
                                    "DELETE SOS Alert",
                                    False,
                                    f"Failed to delete SOS with {response.status_code}",
                                    {"response_text": response.text}
                                )
                        except Exception as e:
                            self.log_test(
                                "DELETE SOS Alert",
                                False,
                                f"Error deleting SOS: {str(e)}"
                            )
                    else:
                        self.log_test(
                            "DELETE SOS Alert",
                            False,
                            "Not enough SOS alerts for deletion testing"
                        )
                else:
                    self.log_test(
                        "SOS Alert Management",
                        False,
                        "No existing SOS alerts found for testing"
                    )
            else:
                self.log_test(
                    "Get SOS Alerts for Testing",
                    False,
                    f"Failed to get SOS alerts with {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "SOS Alert Management Setup",
                False,
                f"Error setting up SOS tests: {str(e)}"
            )

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("CORRECTED FUNKGERÄT & SOS CRUD TESTING SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Group results by category
        categories = {
            "Kanal Management": [],
            "Message Management": [],
            "User Management": [],
            "SOS Management": [],
            "Other": []
        }
        
        for result in self.test_results:
            test_name = result["test"]
            if "Channel" in test_name or "Kanal" in test_name:
                categories["Kanal Management"].append(result)
            elif "Message" in test_name:
                categories["Message Management"].append(result)
            elif "User" in test_name and "Role" in test_name or "Status" in test_name:
                categories["User Management"].append(result)
            elif "SOS" in test_name:
                categories["SOS Management"].append(result)
            else:
                categories["Other"].append(result)
        
        for category, results in categories.items():
            if results:
                passed = len([r for r in results if r["success"]])
                total = len(results)
                print(f"\n📊 {category}: {passed}/{total} passed")
                
                for result in results:
                    status = "✅" if result["success"] else "❌"
                    print(f"  {status} {result['test']}")
        
        print("\n" + "="*80)
        
        # Infrastructure notes
        print("\n🏗️ INFRASTRUCTURE NOTES:")
        print("• Chat Groups API requires internal URL (localhost:8001) due to Kubernetes ingress restrictions")
        print("• Message editing may have similar restrictions (405 Method Not Allowed on external URL)")
        print("• User management endpoints may have ObjectId format requirements")
        print("• SOS activation endpoint (/admin/sos/{id}/activate) not found - use status update instead")

    def run_all_tests(self):
        """Run all corrected CRUD tests"""
        print("🚀 Starting Corrected Funkgerät & SOS CRUD Testing")
        print("="*80)
        
        # Setup
        if not self.setup_admin_authentication():
            print("❌ Cannot proceed without admin authentication")
            return
        
        # Run all test suites
        self.test_funkgeraet_kanal_management()
        self.test_chat_message_management()
        self.test_user_group_management_corrected()
        self.test_sos_alert_management_corrected()
        
        # Summary
        self.print_summary()

if __name__ == "__main__":
    tester = CorrectedCRUDTester()
    tester.run_all_tests()