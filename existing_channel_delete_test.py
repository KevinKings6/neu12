#!/usr/bin/env python3
"""
🚨 NOTFALL: TEST MIT EXISTIERENDEN KANÄLEN
Teste DELETE mit bereits vorhandenen Kanälen aus der Liste
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Backend API base URL from frontend environment
BASE_URL = "https://ba41d31d-12ea-486d-ae78-9bc529c512b8.preview.emergentagent.com/api"

class ExistingChannelDeleteTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.test_results = []
        self.admin_token = None
        
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
            print(f"   Details: {json.dumps(details, indent=2)}")

    def get_auth_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """Get authorization headers with Bearer token"""
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def setup_admin_login(self):
        """Setup admin authentication"""
        print("\n🔐 === ADMIN LOGIN SETUP ===")
        
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

    def get_existing_channels(self):
        """Hole alle existierenden Kanäle"""
        print("\n📋 === EXISTIERENDE KANÄLE ABRUFEN ===")
        
        if not self.admin_token:
            self.log_test("Get Existing Channels", False, "No admin token available")
            return []
        
        try:
            response = self.session.get(
                f"{self.base_url}/admin/chat/groups",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                channels = response.json()
                self.log_test(
                    "Get Existing Channels",
                    True,
                    f"Erfolgreich {len(channels)} existierende Kanäle abgerufen",
                    {"channels_count": len(channels)}
                )
                
                print("\n📋 VERFÜGBARE KANÄLE:")
                for i, channel in enumerate(channels):
                    print(f"{i+1}. ID: {channel.get('id', 'N/A')} | Name: {channel.get('name', 'N/A')}")
                
                return channels
            else:
                self.log_test(
                    "Get Existing Channels",
                    False,
                    f"Fehler beim Abrufen der Kanäle: Status {response.status_code}",
                    {"response_text": response.text}
                )
                return []
        except Exception as e:
            self.log_test(
                "Get Existing Channels",
                False,
                f"Fehler beim Abrufen der Kanäle: {str(e)}"
            )
            return []

    def test_delete_existing_channel(self, channel):
        """Teste DELETE mit einem existierenden Kanal"""
        channel_id = channel.get("id") or channel.get("_id")
        channel_name = channel.get("name", "Unknown")
        
        print(f"\n🗑️ === DELETE TEST: {channel_name} (ID: {channel_id}) ===")
        
        if not self.admin_token or not channel_id:
            self.log_test(f"Delete Channel {channel_name}", False, "No admin token or channel ID")
            return False
        
        try:
            # Logge die exakte URL die verwendet wird
            delete_url = f"{self.base_url}/admin/chat/groups/{channel_id}"
            print(f"DELETE URL: {delete_url}")
            print(f"Channel ID: {channel_id}")
            print(f"Channel Name: {channel_name}")
            
            response = self.session.delete(
                delete_url,
                headers=self.get_auth_headers(self.admin_token)
            )
            
            print(f"DELETE Response Status: {response.status_code}")
            print(f"DELETE Response Text: {response.text}")
            
            if response.status_code == 200:
                response_data = response.json() if response.text else {}
                self.log_test(
                    f"Delete Channel {channel_name}",
                    True,
                    f"Kanal '{channel_name}' (ID: {channel_id}) erfolgreich gelöscht",
                    {
                        "delete_url": delete_url,
                        "response_status": response.status_code,
                        "response_data": response_data
                    }
                )
                return True
            elif response.status_code == 404:
                self.log_test(
                    f"Delete Channel {channel_name}",
                    False,
                    f"Kanal '{channel_name}' nicht gefunden (404) - ID-Problem?",
                    {
                        "delete_url": delete_url,
                        "response_status": response.status_code,
                        "response_text": response.text,
                        "channel_id": channel_id
                    }
                )
                return False
            elif response.status_code == 400:
                self.log_test(
                    f"Delete Channel {channel_name}",
                    False,
                    f"Ungültige Kanal-ID (400) für '{channel_name}'",
                    {
                        "delete_url": delete_url,
                        "channel_id": channel_id,
                        "response_status": response.status_code,
                        "response_text": response.text
                    }
                )
                return False
            else:
                self.log_test(
                    f"Delete Channel {channel_name}",
                    False,
                    f"DELETE fehlgeschlagen für '{channel_name}' mit Status {response.status_code}",
                    {
                        "delete_url": delete_url,
                        "response_status": response.status_code,
                        "response_text": response.text
                    }
                )
                return False
        except Exception as e:
            self.log_test(
                f"Delete Channel {channel_name}",
                False,
                f"Fehler beim Löschen von '{channel_name}': {str(e)}",
                {"channel_id": channel_id, "error_type": type(e).__name__}
            )
            return False

    def verify_channel_deleted(self, channel_id, channel_name):
        """Verifiziere dass der Kanal wirklich gelöscht wurde"""
        print(f"\n✅ === LÖSCHUNG VERIFIZIEREN: {channel_name} ===")
        
        if not self.admin_token:
            self.log_test(f"Verify {channel_name} Deleted", False, "No admin token available")
            return False
        
        try:
            response = self.session.get(
                f"{self.base_url}/admin/chat/groups",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                channels = response.json()
                
                # Suche nach dem gelöschten Kanal
                found_channel = None
                for channel in channels:
                    if (channel.get("id") == channel_id or 
                        channel.get("_id") == channel_id or
                        str(channel.get("_id")) == channel_id):
                        found_channel = channel
                        break
                
                if not found_channel:
                    self.log_test(
                        f"Verify {channel_name} Deleted",
                        True,
                        f"Kanal '{channel_name}' erfolgreich aus der DB gelöscht",
                        {
                            "searched_id": channel_id,
                            "total_remaining_channels": len(channels)
                        }
                    )
                    return True
                else:
                    self.log_test(
                        f"Verify {channel_name} Deleted",
                        False,
                        f"KRITISCH: Kanal '{channel_name}' ist IMMER NOCH in der DB!",
                        {
                            "found_channel": found_channel,
                            "total_channels": len(channels)
                        }
                    )
                    return False
            else:
                self.log_test(
                    f"Verify {channel_name} Deleted",
                    False,
                    f"Fehler beim Abrufen der Kanäle für Verifikation: Status {response.status_code}",
                    {"response_text": response.text}
                )
                return False
        except Exception as e:
            self.log_test(
                f"Verify {channel_name} Deleted",
                False,
                f"Fehler bei der Lösch-Verifikation: {str(e)}"
            )
            return False

    def run_existing_channel_delete_test(self):
        """Führe DELETE-Tests mit existierenden Kanälen durch"""
        print("🚨 NOTFALL: DELETE-TEST MIT EXISTIERENDEN KANÄLEN")
        print("=" * 60)
        
        # Setup
        if not self.setup_admin_login():
            print("❌ KRITISCH: Admin-Login fehlgeschlagen - Tests abgebrochen")
            return
        
        # Hole existierende Kanäle
        existing_channels = self.get_existing_channels()
        if not existing_channels:
            print("❌ KRITISCH: Keine existierenden Kanäle gefunden - Tests abgebrochen")
            return
        
        print(f"\n🎯 TESTE DELETE MIT {len(existing_channels)} EXISTIERENDEN KANÄLEN")
        
        # Teste DELETE mit den ersten 3 Kanälen (um nicht alle zu löschen)
        test_channels = existing_channels[:3]
        
        deleted_channels = []
        
        for i, channel in enumerate(test_channels):
            channel_id = channel.get("id") or channel.get("_id")
            channel_name = channel.get("name", f"Channel {i+1}")
            
            print(f"\n--- Test {i+1}/{len(test_channels)}: {channel_name} ---")
            
            # Teste DELETE
            delete_success = self.test_delete_existing_channel(channel)
            
            if delete_success:
                deleted_channels.append((channel_id, channel_name))
                # Verifiziere Löschung
                self.verify_channel_deleted(channel_id, channel_name)
        
        # Zusammenfassung
        self.print_summary(deleted_channels)

    def print_summary(self, deleted_channels):
        """Drucke Test-Zusammenfassung"""
        print("\n" + "=" * 60)
        print("🚨 EXISTIERENDE KANÄLE DELETE-TEST ZUSAMMENFASSUNG")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Gesamt Tests: {total_tests}")
        print(f"✅ Erfolgreich: {passed_tests}")
        print(f"❌ Fehlgeschlagen: {failed_tests}")
        print(f"Erfolgsrate: {(passed_tests/total_tests*100):.1f}%")
        
        print(f"\n🗑️ GELÖSCHTE KANÄLE: {len(deleted_channels)}")
        for channel_id, channel_name in deleted_channels:
            print(f"   ✅ {channel_name} (ID: {channel_id})")
        
        print("\n📋 DETAILLIERTE ERGEBNISSE:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        print("\n🔍 KRITISCHE BEFUNDE:")
        critical_issues = [result for result in self.test_results if not result["success"]]
        
        if not critical_issues:
            print("✅ KEINE KRITISCHEN PROBLEME GEFUNDEN - Kanal-Löschen funktioniert mit existierenden Kanälen!")
        else:
            for issue in critical_issues:
                print(f"❌ {issue['test']}: {issue['message']}")
        
        print("\n🎯 FAZIT:")
        if len(deleted_channels) > 0:
            print(f"✅ DELETE funktioniert: {len(deleted_channels)} Kanäle erfolgreich gelöscht")
            print("✅ Das Problem liegt NICHT am Backend DELETE-Endpunkt")
            print("🔍 Mögliche Ursachen für Benutzer-Problem:")
            print("   → Frontend sendet falsche ID")
            print("   → Frontend verwendet falschen HTTP-Method")
            print("   → Frontend hat Authorization-Problem")
            print("   → Browser-Cache oder Session-Problem")
        else:
            print("❌ DELETE funktioniert NICHT mit existierenden Kanälen")
            print("🔧 Backend DELETE-Endpunkt hat Probleme")

if __name__ == "__main__":
    tester = ExistingChannelDeleteTester()
    tester.run_existing_channel_delete_test()