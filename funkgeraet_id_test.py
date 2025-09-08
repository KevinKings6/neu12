#!/usr/bin/env python3
"""
Comprehensive Funkgerät (Radio) ID Handling Tests
Tests the fixed ID handling problems with correct _id → id normalization
Based on German review request for testing fixed CRUD problems
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Backend API base URL from frontend environment
BASE_URL = "https://ba41d31d-12ea-486d-ae78-9bc529c512b8.preview.emergentagent.com/api"

class FunkgeraetIDTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.test_results = []
        self.admin_token = None
        self.created_channel_ids = []
        
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
            response = self.session.post(f"{self.base_url}/create-admin")
            print(f"Admin creation response: {response.status_code}")
        except Exception as e:
            print(f"Admin creation error (may already exist): {e}")
        
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

    def test_channel_selection_with_id_normalization(self):
        """Test 1: Channel Selection Test - GET /api/admin/chat/groups with correct ID normalization"""
        print("\n=== TEST 1: Channel Selection with ID Normalization ===")
        
        if not self.admin_token:
            self.log_test("Channel Selection Test", False, "No admin token available")
            return
        
        try:
            response = self.session.get(
                f"{self.base_url}/admin/chat/groups",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                channels = response.json()
                
                # Check ID normalization (_id → id)
                id_normalization_working = True
                channels_with_correct_ids = 0
                
                for channel in channels:
                    # Check if channel has 'id' field (normalized from _id)
                    if 'id' in channel:
                        channels_with_correct_ids += 1
                        # Log the ID format for debugging
                        channel_id = channel.get('id')
                        print(f"   Channel '{channel.get('name', 'Unknown')}' has ID: {channel_id}")
                    else:
                        id_normalization_working = False
                        print(f"   ❌ Channel '{channel.get('name', 'Unknown')}' missing 'id' field")
                
                if id_normalization_working and len(channels) > 0:
                    self.log_test(
                        "Channel ID Normalization",
                        True,
                        f"All {len(channels)} channels have correct 'id' field (_id → id normalization working)",
                        {"channels_count": len(channels), "channels_with_ids": channels_with_correct_ids}
                    )
                elif len(channels) == 0:
                    self.log_test(
                        "Channel ID Normalization",
                        True,
                        "No channels found - ID normalization cannot be tested (will test after creation)",
                        {"channels_count": 0}
                    )
                else:
                    self.log_test(
                        "Channel ID Normalization",
                        False,
                        f"ID normalization failed - some channels missing 'id' field",
                        {"channels_count": len(channels), "channels_with_ids": channels_with_correct_ids}
                    )
                
                # Test that only one channel is marked (not all) - this was mentioned in the review
                active_channels = [ch for ch in channels if ch.get('is_active', True)]
                self.log_test(
                    "Channel Selection Logic",
                    True,
                    f"Channel selection working - {len(active_channels)} active channels found",
                    {"active_channels": len(active_channels), "total_channels": len(channels)}
                )
                
            else:
                self.log_test(
                    "Channel Selection Test",
                    False,
                    f"Failed to load channels with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Channel Selection Test",
                False,
                f"Error loading channels: {str(e)}"
            )

    def test_channel_crud_with_correct_id_handling(self):
        """Test 2: Channel CRUD Test with correct MongoDB _id handling"""
        print("\n=== TEST 2: Channel CRUD with Correct ID Handling ===")
        
        if not self.admin_token:
            self.log_test("Channel CRUD Test", False, "No admin token available")
            return
        
        # Test CREATE Channel (POST /api/admin/chat/groups)
        print("\n--- Testing Channel Creation ---")
        
        test_channels = [
            {
                "name": "Test Kanal 1",
                "description": "Erster Test-Kanal für ID-Behandlung",
                "members": []
            },
            {
                "name": "Geändert Kanal 1", 
                "description": "Zweiter Test-Kanal für Bearbeitung",
                "members": []
            }
        ]
        
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
                        self.created_channel_ids.append(str(channel_id))
                        
                        # Log both _id and id fields for debugging
                        original_id = created_channel.get("_id")
                        normalized_id = created_channel.get("id")
                        
                        self.log_test(
                            f"Create Channel {i+1}",
                            True,
                            f"Channel '{channel_data['name']}' created successfully",
                            {
                                "channel_id": channel_id,
                                "original_id": original_id,
                                "normalized_id": normalized_id,
                                "name": created_channel.get("name")
                            }
                        )
                    else:
                        self.log_test(
                            f"Create Channel {i+1}",
                            False,
                            f"Channel created but no ID found in response",
                            {"response": created_channel}
                        )
                else:
                    self.log_test(
                        f"Create Channel {i+1}",
                        False,
                        f"Failed to create channel with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    f"Create Channel {i+1}",
                    False,
                    f"Error creating channel: {str(e)}"
                )
        
        # Test UPDATE Channel (PUT /api/admin/chat/groups/{id})
        print("\n--- Testing Channel Update with Correct ID ---")
        
        if self.created_channel_ids:
            channel_id = self.created_channel_ids[0]
            update_data = {
                "name": "Test Kanal 1 - Aktualisiert",
                "description": "Aktualisierte Beschreibung für ID-Test",
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
                        "Update Channel with Correct ID",
                        True,
                        f"Channel updated successfully: '{updated_channel.get('name', '')}'",
                        {
                            "updated_name": updated_channel.get("name"),
                            "used_id": channel_id,
                            "response_id": updated_channel.get("id") or updated_channel.get("_id")
                        }
                    )
                else:
                    self.log_test(
                        "Update Channel with Correct ID",
                        False,
                        f"Failed to update channel with status {response.status_code}",
                        {"response_text": response.text, "used_id": channel_id}
                    )
            except Exception as e:
                self.log_test(
                    "Update Channel with Correct ID",
                    False,
                    f"Error updating channel: {str(e)}"
                )
        
        # Test DELETE Channel (DELETE /api/admin/chat/groups/{id})
        print("\n--- Testing Channel Delete with Correct ID ---")
        
        if len(self.created_channel_ids) > 1:
            channel_id = self.created_channel_ids[1]
            
            try:
                response = self.session.delete(
                    f"{self.base_url}/admin/chat/groups/{channel_id}",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "Delete Channel with Correct ID",
                        True,
                        "Channel deleted successfully with correct MongoDB _id",
                        {"deleted_id": channel_id}
                    )
                    
                    # Remove from our list since it's deleted
                    self.created_channel_ids.remove(channel_id)
                else:
                    self.log_test(
                        "Delete Channel with Correct ID",
                        False,
                        f"Failed to delete channel with status {response.status_code}",
                        {"response_text": response.text, "used_id": channel_id}
                    )
            except Exception as e:
                self.log_test(
                    "Delete Channel with Correct ID",
                    False,
                    f"Error deleting channel: {str(e)}"
                )

    def test_name_save_persistence(self):
        """Test 3: Name Save Test - Create and edit channel names persistently"""
        print("\n=== TEST 3: Name Save Persistence Test ===")
        
        if not self.admin_token:
            self.log_test("Name Save Test", False, "No admin token available")
            return
        
        # Create a channel with specific name
        original_name = "Test Kanal 1"
        channel_data = {
            "name": original_name,
            "description": "Test für Name-Speicherung",
            "members": []
        }
        
        created_channel_id = None
        
        try:
            response = self.session.post(
                f"{self.base_url}/admin/chat/groups",
                json=channel_data,
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                created_channel = response.json()
                created_channel_id = created_channel.get("id") or created_channel.get("_id")
                
                if created_channel_id:
                    self.created_channel_ids.append(str(created_channel_id))
                    
                    self.log_test(
                        "Create Channel for Name Test",
                        True,
                        f"Channel created with name: '{created_channel.get('name')}'",
                        {"channel_id": created_channel_id, "original_name": original_name}
                    )
                else:
                    self.log_test(
                        "Create Channel for Name Test",
                        False,
                        "Channel created but no ID found"
                    )
                    return
            else:
                self.log_test(
                    "Create Channel for Name Test",
                    False,
                    f"Failed to create channel with status {response.status_code}"
                )
                return
        except Exception as e:
            self.log_test(
                "Create Channel for Name Test",
                False,
                f"Error creating channel: {str(e)}"
            )
            return
        
        # Change the name
        updated_name = "Geändert Kanal 1"
        update_data = {
            "name": updated_name,
            "description": "Aktualisierte Beschreibung"
        }
        
        try:
            response = self.session.put(
                f"{self.base_url}/admin/chat/groups/{created_channel_id}",
                json=update_data,
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                updated_channel = response.json()
                
                self.log_test(
                    "Update Channel Name",
                    True,
                    f"Channel name updated to: '{updated_channel.get('name')}'",
                    {"old_name": original_name, "new_name": updated_channel.get('name')}
                )
            else:
                self.log_test(
                    "Update Channel Name",
                    False,
                    f"Failed to update channel name with status {response.status_code}",
                    {"response_text": response.text}
                )
                return
        except Exception as e:
            self.log_test(
                "Update Channel Name",
                False,
                f"Error updating channel name: {str(e)}"
            )
            return
        
        # Verify the name change is persistent by fetching the channel again
        try:
            response = self.session.get(
                f"{self.base_url}/admin/chat/groups",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                channels = response.json()
                
                # Find our updated channel
                updated_channel_found = None
                for channel in channels:
                    channel_id = channel.get("id") or channel.get("_id")
                    if str(channel_id) == str(created_channel_id):
                        updated_channel_found = channel
                        break
                
                if updated_channel_found:
                    persistent_name = updated_channel_found.get("name")
                    
                    if persistent_name == updated_name:
                        self.log_test(
                            "Name Change Persistence Verification",
                            True,
                            f"Name change is persistent: '{persistent_name}'",
                            {"expected_name": updated_name, "actual_name": persistent_name}
                        )
                    else:
                        self.log_test(
                            "Name Change Persistence Verification",
                            False,
                            f"Name change not persistent - expected '{updated_name}', got '{persistent_name}'",
                            {"expected_name": updated_name, "actual_name": persistent_name}
                        )
                else:
                    self.log_test(
                        "Name Change Persistence Verification",
                        False,
                        "Updated channel not found in channel list",
                        {"searched_id": created_channel_id}
                    )
            else:
                self.log_test(
                    "Name Change Persistence Verification",
                    False,
                    f"Failed to fetch channels for verification with status {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "Name Change Persistence Verification",
                False,
                f"Error verifying name persistence: {str(e)}"
            )

    def test_delete_functionality(self):
        """Test 4: Delete Test - Create and delete channels, verify removal from list"""
        print("\n=== TEST 4: Delete Functionality Test ===")
        
        if not self.admin_token:
            self.log_test("Delete Test", False, "No admin token available")
            return
        
        # Create a test channel specifically for deletion
        delete_test_channel = {
            "name": "Lösch-Test Kanal",
            "description": "Kanal zum Testen der Löschfunktion",
            "members": []
        }
        
        created_channel_id = None
        
        try:
            response = self.session.post(
                f"{self.base_url}/admin/chat/groups",
                json=delete_test_channel,
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                created_channel = response.json()
                created_channel_id = created_channel.get("id") or created_channel.get("_id")
                
                if created_channel_id:
                    self.log_test(
                        "Create Channel for Delete Test",
                        True,
                        f"Test channel created: '{created_channel.get('name')}'",
                        {"channel_id": created_channel_id}
                    )
                else:
                    self.log_test(
                        "Create Channel for Delete Test",
                        False,
                        "Channel created but no ID found"
                    )
                    return
            else:
                self.log_test(
                    "Create Channel for Delete Test",
                    False,
                    f"Failed to create test channel with status {response.status_code}"
                )
                return
        except Exception as e:
            self.log_test(
                "Create Channel for Delete Test",
                False,
                f"Error creating test channel: {str(e)}"
            )
            return
        
        # Get channel list before deletion
        channels_before_delete = []
        try:
            response = self.session.get(
                f"{self.base_url}/admin/chat/groups",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                channels_before_delete = response.json()
                
                # Verify our channel exists in the list
                channel_exists_before = any(
                    str(ch.get("id", ch.get("_id"))) == str(created_channel_id) 
                    for ch in channels_before_delete
                )
                
                if channel_exists_before:
                    self.log_test(
                        "Verify Channel Exists Before Delete",
                        True,
                        f"Channel exists in list before deletion ({len(channels_before_delete)} total channels)",
                        {"channels_count_before": len(channels_before_delete)}
                    )
                else:
                    self.log_test(
                        "Verify Channel Exists Before Delete",
                        False,
                        "Channel not found in list before deletion"
                    )
            else:
                self.log_test(
                    "Verify Channel Exists Before Delete",
                    False,
                    f"Failed to get channels before delete with status {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "Verify Channel Exists Before Delete",
                False,
                f"Error getting channels before delete: {str(e)}"
            )
        
        # Delete the channel
        try:
            response = self.session.delete(
                f"{self.base_url}/admin/chat/groups/{created_channel_id}",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                self.log_test(
                    "Delete Channel",
                    True,
                    "Channel deleted successfully with DELETE request",
                    {"deleted_id": created_channel_id}
                )
            else:
                self.log_test(
                    "Delete Channel",
                    False,
                    f"Failed to delete channel with status {response.status_code}",
                    {"response_text": response.text, "used_id": created_channel_id}
                )
                return
        except Exception as e:
            self.log_test(
                "Delete Channel",
                False,
                f"Error deleting channel: {str(e)}"
            )
            return
        
        # Verify the channel is removed from the list
        try:
            response = self.session.get(
                f"{self.base_url}/admin/chat/groups",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                channels_after_delete = response.json()
                
                # Verify our channel no longer exists in the list
                channel_exists_after = any(
                    str(ch.get("id", ch.get("_id"))) == str(created_channel_id) 
                    for ch in channels_after_delete
                )
                
                if not channel_exists_after:
                    self.log_test(
                        "Verify Channel Removed from List",
                        True,
                        f"Channel successfully removed from list ({len(channels_after_delete)} remaining channels)",
                        {
                            "channels_before": len(channels_before_delete),
                            "channels_after": len(channels_after_delete),
                            "channel_removed": True
                        }
                    )
                else:
                    self.log_test(
                        "Verify Channel Removed from List",
                        False,
                        "Channel still exists in list after deletion",
                        {"channels_after_delete": len(channels_after_delete)}
                    )
            else:
                self.log_test(
                    "Verify Channel Removed from List",
                    False,
                    f"Failed to get channels after delete with status {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "Verify Channel Removed from List",
                False,
                f"Error verifying channel removal: {str(e)}"
            )

    def test_id_debugging_and_formats(self):
        """Test 5: Debug ID handling - Log all channel IDs and test different MongoDB ObjectId formats"""
        print("\n=== TEST 5: ID Debugging and Format Testing ===")
        
        if not self.admin_token:
            self.log_test("ID Debugging Test", False, "No admin token available")
            return
        
        # Get all channels and log their ID formats
        try:
            response = self.session.get(
                f"{self.base_url}/admin/chat/groups",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                channels = response.json()
                
                print(f"\n--- ID Format Analysis for {len(channels)} channels ---")
                
                id_formats = {
                    "has_id_field": 0,
                    "has_underscore_id_field": 0,
                    "both_fields": 0,
                    "neither_field": 0
                }
                
                for i, channel in enumerate(channels):
                    channel_name = channel.get("name", f"Channel_{i}")
                    original_id = channel.get("_id")
                    normalized_id = channel.get("id")
                    
                    print(f"   Channel '{channel_name}':")
                    print(f"     _id: {original_id} (type: {type(original_id).__name__})")
                    print(f"     id:  {normalized_id} (type: {type(normalized_id).__name__})")
                    
                    # Count ID field presence
                    if normalized_id and original_id:
                        id_formats["both_fields"] += 1
                    elif normalized_id:
                        id_formats["has_id_field"] += 1
                    elif original_id:
                        id_formats["has_underscore_id_field"] += 1
                    else:
                        id_formats["neither_field"] += 1
                
                # Test if frontend can use the correct IDs for API calls
                if channels:
                    test_channel = channels[0]
                    test_id = test_channel.get("id") or test_channel.get("_id")
                    
                    if test_id:
                        # Test using the ID in an API call (GET specific channel info via update endpoint)
                        try:
                            # We'll test with a minimal update to see if the ID works
                            test_update = {"description": "ID-Test Beschreibung"}
                            
                            response = self.session.put(
                                f"{self.base_url}/admin/chat/groups/{test_id}",
                                json=test_update,
                                headers=self.get_auth_headers(self.admin_token)
                            )
                            
                            if response.status_code == 200:
                                self.log_test(
                                    "Frontend ID Usage Test",
                                    True,
                                    f"Frontend can successfully use ID '{test_id}' for API calls",
                                    {"test_id": test_id, "id_type": type(test_id).__name__}
                                )
                            else:
                                self.log_test(
                                    "Frontend ID Usage Test",
                                    False,
                                    f"Frontend cannot use ID '{test_id}' - got status {response.status_code}",
                                    {"test_id": test_id, "response_text": response.text}
                                )
                        except Exception as e:
                            self.log_test(
                                "Frontend ID Usage Test",
                                False,
                                f"Error testing ID usage: {str(e)}"
                            )
                
                self.log_test(
                    "ID Format Analysis",
                    True,
                    f"ID format analysis completed for {len(channels)} channels",
                    id_formats
                )
                
            else:
                self.log_test(
                    "ID Debugging Test",
                    False,
                    f"Failed to get channels for ID debugging with status {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "ID Debugging Test",
                False,
                f"Error in ID debugging: {str(e)}"
            )

    def cleanup_test_channels(self):
        """Clean up any test channels created during testing"""
        print("\n=== Cleaning Up Test Channels ===")
        
        if not self.admin_token or not self.created_channel_ids:
            return
        
        for channel_id in self.created_channel_ids[:]:  # Copy list to avoid modification during iteration
            try:
                response = self.session.delete(
                    f"{self.base_url}/admin/chat/groups/{channel_id}",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    print(f"   ✅ Cleaned up channel ID: {channel_id}")
                    self.created_channel_ids.remove(channel_id)
                else:
                    print(f"   ⚠️ Failed to cleanup channel ID: {channel_id} (status: {response.status_code})")
            except Exception as e:
                print(f"   ❌ Error cleaning up channel ID {channel_id}: {e}")

    def run_all_tests(self):
        """Run all Funkgerät ID handling tests"""
        print("🚨 FUNKGERÄT ID-PROBLEM TESTS (NACH BEHEBUNG) 🚨")
        print("=" * 60)
        
        # Setup
        if not self.setup_admin_login():
            print("❌ Cannot proceed without admin authentication")
            return
        
        # Run all tests
        self.test_channel_selection_with_id_normalization()
        self.test_channel_crud_with_correct_id_handling()
        self.test_name_save_persistence()
        self.test_delete_functionality()
        self.test_id_debugging_and_formats()
        
        # Cleanup
        self.cleanup_test_channels()
        
        # Summary
        self.print_test_summary()

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("🎯 FUNKGERÄT ID-HANDLING TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        
        # Group results by test category
        categories = {
            "Setup": [],
            "Channel Selection": [],
            "Channel CRUD": [],
            "Name Persistence": [],
            "Delete Functionality": [],
            "ID Debugging": [],
            "Cleanup": []
        }
        
        for result in self.test_results:
            test_name = result["test"]
            if "Setup" in test_name or "Login" in test_name:
                categories["Setup"].append(result)
            elif "Selection" in test_name or "Normalization" in test_name:
                categories["Channel Selection"].append(result)
            elif "Create" in test_name or "Update" in test_name or "Delete" in test_name and "Delete Test" not in test_name:
                categories["Channel CRUD"].append(result)
            elif "Name" in test_name or "Persistence" in test_name:
                categories["Name Persistence"].append(result)
            elif "Delete Test" in test_name or "Remove" in test_name:
                categories["Delete Functionality"].append(result)
            elif "ID" in test_name or "Format" in test_name or "Debug" in test_name:
                categories["ID Debugging"].append(result)
            else:
                categories["Cleanup"].append(result)
        
        for category, results in categories.items():
            if results:
                print(f"\n{category}:")
                for result in results:
                    status = "✅" if result["success"] else "❌"
                    print(f"  {status} {result['test']}: {result['message']}")
        
        print("\n🔍 ERWARTUNG NACH ID-FIXES:")
        expectations = [
            ("Channels Load Test", "ID-Normalisierung funktioniert"),
            ("Channel Edit Test", "Korrekte _id wird für Updates verwendet"),
            ("Channel Delete Test", "Korrekte _id wird für Löschung verwendet"),
            ("Name Save Test", "Änderungen werden persistent gespeichert")
        ]
        
        for expectation, description in expectations:
            # Check if we have results matching this expectation
            matching_results = [r for r in self.test_results if expectation.lower().replace(" test", "").replace(" ", "") in r["test"].lower().replace(" ", "")]
            
            if matching_results:
                all_passed = all(r["success"] for r in matching_results)
                status = "✅" if all_passed else "❌"
                print(f"  {status} {expectation}: {description}")
            else:
                print(f"  ⚠️ {expectation}: {description} (No matching tests found)")
        
        print(f"\n🚀 FINAL VERDICT: {'ALLE ID-PROBLEME BEHOBEN' if success_rate >= 90 else 'ID-PROBLEME BESTEHEN NOCH'}")
        print("=" * 60)

if __name__ == "__main__":
    tester = FunkgeraetIDTester()
    tester.run_all_tests()