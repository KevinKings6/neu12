#!/usr/bin/env python3
"""
🚨 NOTFALL: KANAL-LÖSCHEN DIAGNOSE TEST
Sofortige und detaillierte Tests für DELETE /api/admin/chat/groups/{id}

Benutzer meldet: "kanäle löchen geht immer noch nicht"
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Backend API base URL from frontend environment
BASE_URL = "https://ba41d31d-12ea-486d-ae78-9bc529c512b8.preview.emergentagent.com/api"

class ChannelDeleteTester:
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

    def test_1_create_test_channel(self):
        """Test 1: Erstelle einen Test-Kanal über POST /api/admin/chat/groups"""
        print("\n📝 === TEST 1: KANAL ERSTELLEN ===")
        
        if not self.admin_token:
            self.log_test("Create Test Channel", False, "No admin token available")
            return None
        
        channel_data = {
            "name": "Test Lösch-Kanal",
            "description": "Dieser Kanal wird für DELETE-Tests erstellt",
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
                    self.created_channel_ids.append(channel_id)
                    self.log_test(
                        "Create Test Channel",
                        True,
                        f"Kanal '{channel_data['name']}' erfolgreich erstellt mit ID: {channel_id}",
                        {
                            "channel_id": channel_id,
                            "channel_data": created_channel,
                            "has_id_field": "id" in created_channel,
                            "has_underscore_id_field": "_id" in created_channel
                        }
                    )
                    return channel_id
                else:
                    self.log_test(
                        "Create Test Channel",
                        False,
                        "Kanal erstellt aber keine ID zurückgegeben",
                        {"response": created_channel}
                    )
                    return None
            else:
                self.log_test(
                    "Create Test Channel",
                    False,
                    f"Kanal-Erstellung fehlgeschlagen mit Status {response.status_code}",
                    {"response_text": response.text}
                )
                return None
        except Exception as e:
            self.log_test(
                "Create Test Channel",
                False,
                f"Fehler beim Erstellen des Kanals: {str(e)}"
            )
            return None

    def test_2_verify_channel_exists(self, channel_id: str):
        """Test 2: Verifiziere dass der Kanal in der Liste existiert"""
        print("\n🔍 === TEST 2: KANAL EXISTENZ PRÜFEN ===")
        
        if not self.admin_token or not channel_id:
            self.log_test("Verify Channel Exists", False, "No admin token or channel ID")
            return False
        
        try:
            response = self.session.get(
                f"{self.base_url}/admin/chat/groups",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                channels = response.json()
                
                # Suche nach dem erstellten Kanal
                found_channel = None
                for channel in channels:
                    if (channel.get("id") == channel_id or 
                        channel.get("_id") == channel_id or
                        str(channel.get("_id")) == channel_id):
                        found_channel = channel
                        break
                
                if found_channel:
                    self.log_test(
                        "Verify Channel Exists",
                        True,
                        f"Kanal mit ID {channel_id} gefunden in der Liste",
                        {
                            "found_channel": found_channel,
                            "total_channels": len(channels),
                            "channel_name": found_channel.get("name")
                        }
                    )
                    return True
                else:
                    self.log_test(
                        "Verify Channel Exists",
                        False,
                        f"Kanal mit ID {channel_id} NICHT in der Liste gefunden",
                        {
                            "searched_id": channel_id,
                            "available_channels": [
                                {
                                    "id": ch.get("id"),
                                    "_id": ch.get("_id"),
                                    "name": ch.get("name")
                                } for ch in channels
                            ]
                        }
                    )
                    return False
            else:
                self.log_test(
                    "Verify Channel Exists",
                    False,
                    f"Fehler beim Abrufen der Kanäle: Status {response.status_code}",
                    {"response_text": response.text}
                )
                return False
        except Exception as e:
            self.log_test(
                "Verify Channel Exists",
                False,
                f"Fehler beim Prüfen der Kanal-Existenz: {str(e)}"
            )
            return False

    def test_3_delete_channel_direct(self, channel_id: str):
        """Test 3: Teste DELETE /api/admin/chat/groups/{id} direkt"""
        print("\n🗑️ === TEST 3: KANAL LÖSCHEN (DIREKT) ===")
        
        if not self.admin_token or not channel_id:
            self.log_test("Delete Channel Direct", False, "No admin token or channel ID")
            return False
        
        try:
            # Logge die exakte URL die verwendet wird
            delete_url = f"{self.base_url}/admin/chat/groups/{channel_id}"
            print(f"DELETE URL: {delete_url}")
            print(f"Channel ID: {channel_id}")
            print(f"Admin Token: {self.admin_token[:20]}..." if self.admin_token else "None")
            
            response = self.session.delete(
                delete_url,
                headers=self.get_auth_headers(self.admin_token)
            )
            
            print(f"DELETE Response Status: {response.status_code}")
            print(f"DELETE Response Headers: {dict(response.headers)}")
            print(f"DELETE Response Text: {response.text}")
            
            if response.status_code == 200:
                response_data = response.json() if response.text else {}
                self.log_test(
                    "Delete Channel Direct",
                    True,
                    f"Kanal mit ID {channel_id} erfolgreich gelöscht",
                    {
                        "delete_url": delete_url,
                        "response_status": response.status_code,
                        "response_data": response_data
                    }
                )
                return True
            elif response.status_code == 404:
                self.log_test(
                    "Delete Channel Direct",
                    False,
                    f"Kanal mit ID {channel_id} nicht gefunden (404) - ID-Problem?",
                    {
                        "delete_url": delete_url,
                        "response_status": response.status_code,
                        "response_text": response.text,
                        "possible_issue": "ID format mismatch or channel doesn't exist"
                    }
                )
                return False
            elif response.status_code == 400:
                self.log_test(
                    "Delete Channel Direct",
                    False,
                    f"Ungültige Kanal-ID (400) - ID-Format-Problem",
                    {
                        "delete_url": delete_url,
                        "channel_id": channel_id,
                        "response_status": response.status_code,
                        "response_text": response.text,
                        "possible_issue": "Invalid ObjectId format"
                    }
                )
                return False
            elif response.status_code == 403:
                self.log_test(
                    "Delete Channel Direct",
                    False,
                    f"Keine Berechtigung zum Löschen (403) - Authorization-Problem",
                    {
                        "delete_url": delete_url,
                        "response_status": response.status_code,
                        "response_text": response.text,
                        "admin_token_present": bool(self.admin_token)
                    }
                )
                return False
            else:
                self.log_test(
                    "Delete Channel Direct",
                    False,
                    f"DELETE fehlgeschlagen mit unerwarteten Status {response.status_code}",
                    {
                        "delete_url": delete_url,
                        "response_status": response.status_code,
                        "response_text": response.text,
                        "response_headers": dict(response.headers)
                    }
                )
                return False
        except Exception as e:
            self.log_test(
                "Delete Channel Direct",
                False,
                f"Fehler beim Löschen des Kanals: {str(e)}",
                {"channel_id": channel_id, "error_type": type(e).__name__}
            )
            return False

    def test_4_verify_channel_deleted(self, channel_id: str):
        """Test 4: Verifiziere dass der Kanal wirklich aus der DB gelöscht wurde"""
        print("\n✅ === TEST 4: LÖSCHUNG VERIFIZIEREN ===")
        
        if not self.admin_token or not channel_id:
            self.log_test("Verify Channel Deleted", False, "No admin token or channel ID")
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
                        "Verify Channel Deleted",
                        True,
                        f"Kanal mit ID {channel_id} erfolgreich aus der DB gelöscht",
                        {
                            "searched_id": channel_id,
                            "total_remaining_channels": len(channels)
                        }
                    )
                    return True
                else:
                    self.log_test(
                        "Verify Channel Deleted",
                        False,
                        f"KRITISCH: Kanal mit ID {channel_id} ist IMMER NOCH in der DB!",
                        {
                            "found_channel": found_channel,
                            "total_channels": len(channels),
                            "issue": "DELETE operation did not remove channel from database"
                        }
                    )
                    return False
            else:
                self.log_test(
                    "Verify Channel Deleted",
                    False,
                    f"Fehler beim Abrufen der Kanäle für Verifikation: Status {response.status_code}",
                    {"response_text": response.text}
                )
                return False
        except Exception as e:
            self.log_test(
                "Verify Channel Deleted",
                False,
                f"Fehler bei der Lösch-Verifikation: {str(e)}"
            )
            return False

    def test_5_id_format_debugging(self):
        """Test 5: Debugging verschiedener ID-Formate"""
        print("\n🔧 === TEST 5: ID-FORMAT DEBUGGING ===")
        
        if not self.admin_token:
            self.log_test("ID Format Debugging", False, "No admin token available")
            return
        
        # Erstelle einen neuen Kanal für ID-Format-Tests
        channel_data = {
            "name": "ID-Format-Test-Kanal",
            "description": "Für ID-Format-Debugging",
            "members": []
        }
        
        try:
            # Erstelle Kanal
            response = self.session.post(
                f"{self.base_url}/admin/chat/groups",
                json=channel_data,
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                created_channel = response.json()
                
                # Analysiere alle verfügbaren ID-Felder
                id_analysis = {
                    "id_field": created_channel.get("id"),
                    "_id_field": created_channel.get("_id"),
                    "id_field_type": type(created_channel.get("id")).__name__,
                    "_id_field_type": type(created_channel.get("_id")).__name__,
                    "full_response": created_channel
                }
                
                self.log_test(
                    "ID Format Analysis",
                    True,
                    "ID-Format-Analyse abgeschlossen",
                    id_analysis
                )
                
                # Teste DELETE mit beiden ID-Formaten
                test_ids = []
                if created_channel.get("id"):
                    test_ids.append(("id", created_channel.get("id")))
                if created_channel.get("_id"):
                    test_ids.append(("_id", created_channel.get("_id")))
                
                for id_type, test_id in test_ids:
                    print(f"\n--- Testing DELETE with {id_type}: {test_id} ---")
                    
                    try:
                        delete_response = self.session.delete(
                            f"{self.base_url}/admin/chat/groups/{test_id}",
                            headers=self.get_auth_headers(self.admin_token)
                        )
                        
                        self.log_test(
                            f"DELETE with {id_type} field",
                            delete_response.status_code == 200,
                            f"DELETE mit {id_type}={test_id} -> Status: {delete_response.status_code}",
                            {
                                "id_type": id_type,
                                "id_value": test_id,
                                "response_status": delete_response.status_code,
                                "response_text": delete_response.text
                            }
                        )
                        
                        # Wenn erfolgreich, breche ab (Kanal ist gelöscht)
                        if delete_response.status_code == 200:
                            break
                            
                    except Exception as e:
                        self.log_test(
                            f"DELETE with {id_type} field",
                            False,
                            f"Fehler beim DELETE mit {id_type}: {str(e)}"
                        )
            else:
                self.log_test(
                    "ID Format Debugging Setup",
                    False,
                    f"Konnte Test-Kanal für ID-Debugging nicht erstellen: {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "ID Format Debugging",
                False,
                f"Fehler beim ID-Format-Debugging: {str(e)}"
            )

    def test_6_authorization_debugging(self):
        """Test 6: Authorization Headers Debugging"""
        print("\n🔐 === TEST 6: AUTHORIZATION DEBUGGING ===")
        
        if not self.admin_token:
            self.log_test("Authorization Debugging", False, "No admin token available")
            return
        
        # Teste verschiedene Authorization-Header-Formate
        auth_tests = [
            ("Bearer Token", f"Bearer {self.admin_token}"),
            ("Token Only", self.admin_token),
            ("No Auth", None)
        ]
        
        # Erstelle einen Test-Kanal für Authorization-Tests
        channel_data = {
            "name": "Auth-Test-Kanal",
            "description": "Für Authorization-Debugging",
            "members": []
        }
        
        try:
            # Erstelle Kanal mit korrekter Authorization
            response = self.session.post(
                f"{self.base_url}/admin/chat/groups",
                json=channel_data,
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                created_channel = response.json()
                test_channel_id = created_channel.get("id") or created_channel.get("_id")
                
                if test_channel_id:
                    # Teste DELETE mit verschiedenen Authorization-Formaten
                    for auth_name, auth_value in auth_tests:
                        print(f"\n--- Testing DELETE with {auth_name} ---")
                        
                        headers = {"Content-Type": "application/json"}
                        if auth_value:
                            if auth_name == "Bearer Token":
                                headers["Authorization"] = auth_value
                            else:
                                headers["Authorization"] = f"Bearer {auth_value}"
                        
                        try:
                            delete_response = self.session.delete(
                                f"{self.base_url}/admin/chat/groups/{test_channel_id}",
                                headers=headers
                            )
                            
                            self.log_test(
                                f"DELETE with {auth_name}",
                                delete_response.status_code == 200,
                                f"DELETE mit {auth_name} -> Status: {delete_response.status_code}",
                                {
                                    "auth_type": auth_name,
                                    "auth_header": headers.get("Authorization", "None")[:50] + "..." if headers.get("Authorization") else "None",
                                    "response_status": delete_response.status_code,
                                    "response_text": delete_response.text
                                }
                            )
                            
                            # Wenn erfolgreich, breche ab (Kanal ist gelöscht)
                            if delete_response.status_code == 200:
                                break
                                
                        except Exception as e:
                            self.log_test(
                                f"DELETE with {auth_name}",
                                False,
                                f"Fehler beim DELETE mit {auth_name}: {str(e)}"
                            )
                else:
                    self.log_test(
                        "Authorization Debugging Setup",
                        False,
                        "Konnte Test-Kanal-ID für Authorization-Tests nicht ermitteln"
                    )
            else:
                self.log_test(
                    "Authorization Debugging Setup",
                    False,
                    f"Konnte Test-Kanal für Authorization-Tests nicht erstellen: {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "Authorization Debugging",
                False,
                f"Fehler beim Authorization-Debugging: {str(e)}"
            )

    def run_comprehensive_delete_test(self):
        """Führe alle DELETE-Tests durch"""
        print("🚨 NOTFALL: KANAL-LÖSCHEN DIAGNOSE GESTARTET")
        print("=" * 60)
        
        # Setup
        if not self.setup_admin_login():
            print("❌ KRITISCH: Admin-Login fehlgeschlagen - Tests abgebrochen")
            return
        
        # Test 1: Kanal erstellen
        channel_id = self.test_1_create_test_channel()
        if not channel_id:
            print("❌ KRITISCH: Kanal-Erstellung fehlgeschlagen - Tests abgebrochen")
            return
        
        # Test 2: Kanal-Existenz prüfen
        if not self.test_2_verify_channel_exists(channel_id):
            print("❌ KRITISCH: Erstellter Kanal nicht in Liste gefunden")
        
        # Test 3: Kanal löschen
        delete_success = self.test_3_delete_channel_direct(channel_id)
        
        # Test 4: Löschung verifizieren
        if delete_success:
            self.test_4_verify_channel_deleted(channel_id)
        
        # Test 5: ID-Format-Debugging
        self.test_5_id_format_debugging()
        
        # Test 6: Authorization-Debugging
        self.test_6_authorization_debugging()
        
        # Zusammenfassung
        self.print_summary()

    def print_summary(self):
        """Drucke Test-Zusammenfassung"""
        print("\n" + "=" * 60)
        print("🚨 NOTFALL DIAGNOSE ZUSAMMENFASSUNG")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Gesamt Tests: {total_tests}")
        print(f"✅ Erfolgreich: {passed_tests}")
        print(f"❌ Fehlgeschlagen: {failed_tests}")
        print(f"Erfolgsrate: {(passed_tests/total_tests*100):.1f}%")
        
        print("\n📋 DETAILLIERTE ERGEBNISSE:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        print("\n🔍 KRITISCHE BEFUNDE:")
        critical_issues = [result for result in self.test_results if not result["success"]]
        
        if not critical_issues:
            print("✅ KEINE KRITISCHEN PROBLEME GEFUNDEN - Kanal-Löschen funktioniert!")
        else:
            for issue in critical_issues:
                print(f"❌ {issue['test']}: {issue['message']}")
                if issue.get("details"):
                    print(f"   Details: {json.dumps(issue['details'], indent=4)}")
        
        print("\n🎯 DIAGNOSE-EMPFEHLUNGEN:")
        
        # Analysiere häufige Fehlertypen
        error_types = {}
        for result in self.test_results:
            if not result["success"]:
                if "404" in result["message"]:
                    error_types["ID_NOT_FOUND"] = error_types.get("ID_NOT_FOUND", 0) + 1
                elif "400" in result["message"]:
                    error_types["INVALID_ID"] = error_types.get("INVALID_ID", 0) + 1
                elif "403" in result["message"]:
                    error_types["AUTHORIZATION"] = error_types.get("AUTHORIZATION", 0) + 1
                elif "500" in result["message"]:
                    error_types["SERVER_ERROR"] = error_types.get("SERVER_ERROR", 0) + 1
        
        if "ID_NOT_FOUND" in error_types:
            print("🔧 ID-HANDLING PROBLEM: Backend findet Kanal-ID nicht")
            print("   → Prüfe ObjectId-Konvertierung im Backend")
            print("   → Prüfe _id vs id Feld-Mapping")
        
        if "INVALID_ID" in error_types:
            print("🔧 ID-FORMAT PROBLEM: Ungültiges ObjectId-Format")
            print("   → Prüfe Frontend→Backend ID-Übertragung")
            print("   → Prüfe ObjectId.is_valid() Validierung")
        
        if "AUTHORIZATION" in error_types:
            print("🔧 AUTHORIZATION PROBLEM: Keine Berechtigung")
            print("   → Prüfe JWT-Token-Übertragung")
            print("   → Prüfe Admin-Rolle-Validierung")
        
        if "SERVER_ERROR" in error_types:
            print("🔧 SERVER ERROR: Backend-Fehler")
            print("   → Prüfe Backend-Logs für Details")
            print("   → Prüfe MongoDB-Verbindung")
        
        if not error_types:
            print("✅ ALLE TESTS ERFOLGREICH - Kanal-Löschen funktioniert korrekt!")

if __name__ == "__main__":
    tester = ChannelDeleteTester()
    tester.run_comprehensive_delete_test()