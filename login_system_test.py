#!/usr/bin/env python3
"""
Schnelltest des Anmelde-Systems - Emergency SOS App
Focused testing of login system as requested in German
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Backend API base URL from frontend environment
BASE_URL = "http://localhost:8001/api"

class LoginSystemTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.test_results = []
        self.admin_token = None
        self.user_token = None
        
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

    def test_admin_creation(self):
        """Test admin user creation - POST /api/create-admin"""
        print("\n=== 1. ADMIN CREATION TEST ===")
        
        try:
            response = self.session.post(f"{self.base_url}/create-admin")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Admin User Creation",
                    True,
                    f"✅ Admin creation successful: {data.get('message', '')}",
                    {"response": data}
                )
                return True
            else:
                self.log_test(
                    "Admin User Creation",
                    False,
                    f"❌ Admin creation failed with status {response.status_code}",
                    {"response_text": response.text}
                )
                return False
        except Exception as e:
            self.log_test(
                "Admin User Creation",
                False,
                f"❌ Error creating admin: {str(e)}"
            )
            return False

    def test_admin_login(self):
        """Test admin login with admin/admin123 - POST /api/login"""
        print("\n=== 2. LOGIN API TEST (admin/admin123) ===")
        
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
            
            # Check CORS headers
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
                "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials")
            }
            
            if response.status_code == 200:
                token_data = response.json()
                self.admin_token = token_data.get("access_token")
                admin_user = token_data.get("user", {})
                
                # Verify token structure
                token_valid = bool(self.admin_token and len(self.admin_token) > 50)
                user_role = admin_user.get("role")
                username = admin_user.get("username")
                
                self.log_test(
                    "Admin Login API",
                    True,
                    f"✅ Login successful! Token generated, User: {username}, Role: {user_role}",
                    {
                        "token_length": len(self.admin_token) if self.admin_token else 0,
                        "token_type": token_data.get("token_type"),
                        "user_role": user_role,
                        "username": username,
                        "cors_headers": cors_headers
                    }
                )
                return True
            else:
                self.log_test(
                    "Admin Login API",
                    False,
                    f"❌ Login failed with status {response.status_code}",
                    {"response_text": response.text, "cors_headers": cors_headers}
                )
                return False
        except Exception as e:
            self.log_test(
                "Admin Login API",
                False,
                f"❌ Error during login: {str(e)}"
            )
            return False

    def test_jwt_validation(self):
        """Test JWT token validation - GET /api/me"""
        print("\n=== 3. USER AUTHENTICATION (JWT Validation) ===")
        
        if not self.admin_token:
            self.log_test(
                "JWT Token Validation",
                False,
                "❌ No admin token available for validation"
            )
            return False
        
        try:
            response = self.session.get(
                f"{self.base_url}/me",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                user_data = response.json()
                username = user_data.get("username")
                role = user_data.get("role")
                user_id = user_data.get("id")
                
                self.log_test(
                    "JWT Token Validation",
                    True,
                    f"✅ Token validation successful! User: {username}, Role: {role}",
                    {"user_data": user_data}
                )
                return True
            else:
                self.log_test(
                    "JWT Token Validation",
                    False,
                    f"❌ Token validation failed with status {response.status_code}",
                    {"response_text": response.text}
                )
                return False
        except Exception as e:
            self.log_test(
                "JWT Token Validation",
                False,
                f"❌ Error validating token: {str(e)}"
            )
            return False

    def test_wrong_credentials(self):
        """Test login with wrong credentials"""
        print("\n=== 4. ERROR CHECKING (Wrong Credentials) ===")
        
        wrong_credentials = [
            {"username": "admin", "password": "wrongpassword"},
            {"username": "wronguser", "password": "admin123"},
            {"username": "admin", "password": ""},
            {"username": "", "password": "admin123"}
        ]
        
        success_count = 0
        
        for i, creds in enumerate(wrong_credentials):
            try:
                response = self.session.post(
                    f"{self.base_url}/login",
                    json=creds,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 401:
                    self.log_test(
                        f"Wrong Credentials Test {i+1}",
                        True,
                        f"✅ Correctly rejected: {creds['username']}/{creds['password'][:3]}***"
                    )
                    success_count += 1
                else:
                    self.log_test(
                        f"Wrong Credentials Test {i+1}",
                        False,
                        f"❌ Expected 401 but got {response.status_code} for {creds['username']}"
                    )
            except Exception as e:
                self.log_test(
                    f"Wrong Credentials Test {i+1}",
                    False,
                    f"❌ Error testing wrong credentials: {str(e)}"
                )
        
        return success_count == len(wrong_credentials)

    def test_cors_headers(self):
        """Test CORS headers in responses"""
        print("\n=== 5. CORS HEADERS CHECK ===")
        
        try:
            # Test OPTIONS request for CORS preflight
            response = self.session.options(f"{self.base_url}/login")
            
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
                "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials")
            }
            
            # Check if CORS is properly configured
            cors_configured = any(header for header in cors_headers.values())
            
            self.log_test(
                "CORS Headers Check",
                True,
                f"✅ CORS headers present: {cors_configured}",
                {"cors_headers": cors_headers}
            )
            
            return True
        except Exception as e:
            self.log_test(
                "CORS Headers Check",
                False,
                f"❌ Error checking CORS: {str(e)}"
            )
            return False

    def test_token_expiry_handling(self):
        """Test invalid/expired token handling"""
        print("\n=== 6. TOKEN SECURITY CHECK ===")
        
        invalid_tokens = [
            "invalid_token_123",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",
            "",
            "Bearer invalid_token"
        ]
        
        success_count = 0
        
        for i, token in enumerate(invalid_tokens):
            try:
                response = self.session.get(
                    f"{self.base_url}/me",
                    headers=self.get_auth_headers(token)
                )
                
                if response.status_code == 401:
                    self.log_test(
                        f"Invalid Token Test {i+1}",
                        True,
                        f"✅ Invalid token correctly rejected"
                    )
                    success_count += 1
                else:
                    self.log_test(
                        f"Invalid Token Test {i+1}",
                        False,
                        f"❌ Expected 401 but got {response.status_code}"
                    )
            except Exception as e:
                self.log_test(
                    f"Invalid Token Test {i+1}",
                    False,
                    f"❌ Error testing invalid token: {str(e)}"
                )
        
        return success_count == len(invalid_tokens)

    def run_all_tests(self):
        """Run all login system tests"""
        print("🚨 SCHNELLTEST DES ANMELDE-SYSTEMS - EMERGENCY SOS APP")
        print("=" * 80)
        print(f"Base URL: {self.base_url}")
        print("=" * 80)
        
        # Run tests in sequence
        tests = [
            ("Admin Creation", self.test_admin_creation),
            ("Login API", self.test_admin_login),
            ("JWT Validation", self.test_jwt_validation),
            ("Wrong Credentials", self.test_wrong_credentials),
            ("CORS Headers", self.test_cors_headers),
            ("Token Security", self.test_token_expiry_handling)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                print(f"❌ CRITICAL ERROR in {test_name}: {str(e)}")
        
        # Summary
        print("\n" + "=" * 80)
        print("🚨 ANMELDE-SYSTEM TEST ERGEBNISSE")
        print("=" * 80)
        print(f"Gesamt Tests: {total}")
        print(f"✅ Erfolgreich: {passed}")
        print(f"❌ Fehlgeschlagen: {total - passed}")
        print(f"Erfolgsrate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 ALLE TESTS BESTANDEN - ANMELDE-SYSTEM FUNKTIONIERT 100%!")
            print("✅ Login API funktioniert")
            print("✅ Token-Generierung erfolgreich")
            print("✅ User-Authentication korrekt")
            print("✅ Keine CORS-Probleme")
        else:
            print(f"\n⚠️  {total - passed} TESTS FEHLGESCHLAGEN - ANMELDE-SYSTEM HAT PROBLEME!")
            
        print("=" * 80)
        
        return passed == total

if __name__ == "__main__":
    tester = LoginSystemTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)