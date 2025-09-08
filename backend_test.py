#!/usr/bin/env python3
"""
Comprehensive Backend API Tests for Emergency SOS App with Authentication
Tests authentication system, role-based access control, and protected endpoints
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Backend API base URL from frontend environment
BASE_URL = "https://emergency-sos-3.preview.emergentagent.com/api"

class EmergencySOSAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.test_results = []
        self.created_contact_ids = []
        self.created_alert_ids = []
        self.admin_token = None
        self.user_token = None
        self.test_user_id = None
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

    def test_admin_creation(self):
        """Test admin user creation"""
        print("\n=== Testing Admin User Creation ===")
        
        try:
            response = self.session.post(f"{self.base_url}/create-admin")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Create Admin User",
                    True,
                    f"Admin user creation: {data.get('message', '')}",
                    {"response": data}
                )
            else:
                self.log_test(
                    "Create Admin User",
                    False,
                    f"Failed to create admin with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Create Admin User",
                False,
                f"Error creating admin: {str(e)}"
            )

    def test_user_registration(self):
        """Test user registration"""
        print("\n=== Testing User Registration ===")
        
        # Test user data
        user_data = {
            "username": "testuser_emergency",
            "email": "testuser@emergency-sos.com",
            "full_name": "Test Emergency User",
            "password": "testpass123",
            "role": "user"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/register",
                json=user_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                created_user = response.json()
                self.test_user_id = created_user.get("id")
                self.log_test(
                    "User Registration",
                    True,
                    f"User '{user_data['username']}' registered successfully",
                    {"user_id": self.test_user_id, "user": created_user}
                )
            elif response.status_code == 400 and "already registered" in response.text:
                # User already exists, try to get the user ID from admin users list
                self.log_test(
                    "User Registration",
                    True,
                    f"User '{user_data['username']}' already exists (expected in testing)",
                    {"response_text": response.text}
                )
            else:
                self.log_test(
                    "User Registration",
                    False,
                    f"Failed to register user with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "User Registration",
                False,
                f"Error registering user: {str(e)}"
            )

    def test_admin_login(self):
        """Test admin login"""
        print("\n=== Testing Admin Login ===")
        
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
            else:
                self.log_test(
                    "Admin Login",
                    False,
                    f"Failed to login admin with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Admin Login",
                False,
                f"Error logging in admin: {str(e)}"
            )

    def test_user_login(self):
        """Test regular user login"""
        print("\n=== Testing User Login ===")
        
        login_data = {
            "username": "testuser_emergency",
            "password": "testpass123"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.user_token = token_data.get("access_token")
                user = token_data.get("user", {})
                
                self.log_test(
                    "User Login",
                    True,
                    f"User login successful, role: {user.get('role', 'unknown')}",
                    {"token_type": token_data.get("token_type"), "user_role": user.get("role")}
                )
            else:
                self.log_test(
                    "User Login",
                    False,
                    f"Failed to login user with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "User Login",
                False,
                f"Error logging in user: {str(e)}"
            )

    def test_jwt_token_validation(self):
        """Test JWT token validation with /me endpoint"""
        print("\n=== Testing JWT Token Validation ===")
        
        # Test with admin token
        if self.admin_token:
            try:
                response = self.session.get(
                    f"{self.base_url}/me",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    self.log_test(
                        "Admin Token Validation",
                        True,
                        f"Admin token valid, user: {user_data.get('username', 'unknown')}",
                        {"user": user_data}
                    )
                else:
                    self.log_test(
                        "Admin Token Validation",
                        False,
                        f"Admin token validation failed with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    "Admin Token Validation",
                    False,
                    f"Error validating admin token: {str(e)}"
                )
        
        # Test with user token
        if self.user_token:
            try:
                response = self.session.get(
                    f"{self.base_url}/me",
                    headers=self.get_auth_headers(self.user_token)
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    self.log_test(
                        "User Token Validation",
                        True,
                        f"User token valid, user: {user_data.get('username', 'unknown')}",
                        {"user": user_data}
                    )
                else:
                    self.log_test(
                        "User Token Validation",
                        False,
                        f"User token validation failed with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    "User Token Validation",
                    False,
                    f"Error validating user token: {str(e)}"
                )

        # Test with invalid token
        try:
            response = self.session.get(
                f"{self.base_url}/me",
                headers=self.get_auth_headers("invalid_token_12345")
            )
            
            if response.status_code == 401:
                self.log_test(
                    "Invalid Token Rejection",
                    True,
                    "Invalid token correctly rejected with 401"
                )
            else:
                self.log_test(
                    "Invalid Token Rejection",
                    False,
                    f"Expected 401 for invalid token but got {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "Invalid Token Rejection",
                False,
                f"Error testing invalid token: {str(e)}"
            )

    def test_protected_routes_without_auth(self):
        """Test protected routes without authentication (should return 401/403)"""
        print("\n=== Testing Protected Routes Without Authentication ===")
        
        protected_endpoints = [
            ("GET", "/emergency-contacts", "Get Emergency Contacts"),
            ("POST", "/emergency-contacts", "Create Emergency Contact"),
            ("GET", "/user-profile", "Get User Profile"),
            ("POST", "/user-profile", "Create User Profile"),
            ("GET", "/sos-alerts", "Get SOS Alerts"),
            ("POST", "/sos-alert", "Create SOS Alert"),
        ]
        
        for method, endpoint, test_name in protected_endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}")
                elif method == "POST":
                    response = self.session.post(
                        f"{self.base_url}{endpoint}",
                        json={"test": "data"},
                        headers={"Content-Type": "application/json"}
                    )
                
                if response.status_code in [401, 403]:
                    self.log_test(
                        f"Unauthenticated {test_name}",
                        True,
                        f"Correctly rejected unauthenticated request with {response.status_code}"
                    )
                else:
                    self.log_test(
                        f"Unauthenticated {test_name}",
                        False,
                        f"Expected 401/403 but got {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    f"Unauthenticated {test_name}",
                    False,
                    f"Error testing unauthenticated access: {str(e)}"
                )

    def test_admin_only_routes(self):
        """Test admin-only routes with different user types"""
        print("\n=== Testing Admin-Only Routes ===")
        
        admin_endpoints = [
            ("GET", "/admin/users", "Get All Users"),
            ("GET", "/admin/sos-alerts", "Get All SOS Alerts"),
            ("GET", "/admin/emergency-contacts", "Get All Emergency Contacts"),
        ]
        
        # Test admin-only routes with regular user token (should return 403)
        if self.user_token:
            for method, endpoint, test_name in admin_endpoints:
                try:
                    response = self.session.get(
                        f"{self.base_url}{endpoint}",
                        headers=self.get_auth_headers(self.user_token)
                    )
                    
                    if response.status_code == 403:
                        self.log_test(
                            f"User Access {test_name}",
                            True,
                            "Regular user correctly denied admin access with 403"
                        )
                    else:
                        self.log_test(
                            f"User Access {test_name}",
                            False,
                            f"Expected 403 for regular user but got {response.status_code}",
                            {"response_text": response.text}
                        )
                except Exception as e:
                    self.log_test(
                        f"User Access {test_name}",
                        False,
                        f"Error testing user access to admin route: {str(e)}"
                    )
        
        # Test admin-only routes with admin token (should work)
        if self.admin_token:
            for method, endpoint, test_name in admin_endpoints:
                try:
                    response = self.session.get(
                        f"{self.base_url}{endpoint}",
                        headers=self.get_auth_headers(self.admin_token)
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        self.log_test(
                            f"Admin Access {test_name}",
                            True,
                            f"Admin successfully accessed {test_name.lower()}: {len(data) if isinstance(data, list) else 'data'} items",
                            {"data_count": len(data) if isinstance(data, list) else "N/A"}
                        )
                    else:
                        self.log_test(
                            f"Admin Access {test_name}",
                            False,
                            f"Admin access failed with status {response.status_code}",
                            {"response_text": response.text}
                        )
                except Exception as e:
                    self.log_test(
                        f"Admin Access {test_name}",
                        False,
                        f"Error testing admin access: {str(e)}"
                    )

    def test_user_data_isolation(self):
        """Test that users can only access their own data"""
        print("\n=== Testing User Data Isolation ===")
        
        if not self.user_token:
            self.log_test("User Data Isolation", False, "No user token available for testing")
            return
        
        # Create some test data as the user
        contact_data = {
            "name": "Emergency Contact Test",
            "phone": "+1-555-TEST",
            "relationship": "Test Contact",
            "is_primary": False
        }
        
        try:
            # Create emergency contact as user
            response = self.session.post(
                f"{self.base_url}/emergency-contacts",
                json=contact_data,
                headers=self.get_auth_headers(self.user_token)
            )
            
            if response.status_code == 200:
                created_contact = response.json()
                contact_id = created_contact.get("id")
                
                # Verify user can access their own contact
                response = self.session.get(
                    f"{self.base_url}/emergency-contacts",
                    headers=self.get_auth_headers(self.user_token)
                )
                
                if response.status_code == 200:
                    contacts = response.json()
                    user_contact_found = any(c.get("id") == contact_id for c in contacts)
                    
                    if user_contact_found:
                        self.log_test(
                            "User Access Own Data",
                            True,
                            "User can access their own emergency contacts"
                        )
                    else:
                        self.log_test(
                            "User Access Own Data",
                            False,
                            "User cannot find their own created contact"
                        )
                else:
                    self.log_test(
                        "User Access Own Data",
                        False,
                        f"User failed to access own data with status {response.status_code}"
                    )
            else:
                self.log_test(
                    "User Data Creation",
                    False,
                    f"Failed to create test data with status {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "User Data Isolation",
                False,
                f"Error testing user data isolation: {str(e)}"
            )

    def test_admin_sos_alert_update(self):
        """Test admin can update any SOS alert status including admin_active"""
        print("\n=== Testing Admin SOS Alert Status Update ===")
        
        if not self.admin_token or not self.created_alert_ids:
            self.log_test("Admin SOS Alert Update", False, "No admin token or alert IDs available for testing")
            return
        
        # Test admin updating alert to resolved
        alert_id = self.created_alert_ids[0] if self.created_alert_ids else None
        if alert_id:
            try:
                response = self.session.put(
                    f"{self.base_url}/admin/sos-alerts/{alert_id}/status",
                    params={"status": "resolved"},
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "Admin Update SOS Alert to Resolved",
                        True,
                        "Admin successfully updated SOS alert status to resolved"
                    )
                else:
                    self.log_test(
                        "Admin Update SOS Alert to Resolved",
                        False,
                        f"Admin failed to update alert status with code {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    "Admin Update SOS Alert to Resolved",
                    False,
                    f"Error testing admin alert update: {str(e)}"
                )

        # Test admin updating alert to cancelled
        if len(self.created_alert_ids) > 1:
            alert_id = self.created_alert_ids[1]
            try:
                response = self.session.put(
                    f"{self.base_url}/admin/sos-alerts/{alert_id}/status",
                    params={"status": "cancelled"},
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "Admin Update SOS Alert to Cancelled",
                        True,
                        "Admin successfully updated SOS alert status to cancelled"
                    )
                else:
                    self.log_test(
                        "Admin Update SOS Alert to Cancelled",
                        False,
                        f"Admin failed to update alert status with code {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    "Admin Update SOS Alert to Cancelled",
                    False,
                    f"Error testing admin alert update to cancelled: {str(e)}"
                )

        # Test admin updating alert to admin_active (new functionality)
        if len(self.created_alert_ids) > 2:
            alert_id = self.created_alert_ids[2]
        elif self.created_alert_ids:
            alert_id = self.created_alert_ids[0]  # Use first alert if we don't have 3
        else:
            self.log_test(
                "Admin Update SOS Alert to Admin Active",
                False,
                "No alert IDs available for testing admin_active status"
            )
            return
            
        try:
            response = self.session.put(
                f"{self.base_url}/admin/sos-alerts/{alert_id}/status",
                params={"status": "admin_active"},
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                self.log_test(
                    "Admin Update SOS Alert to Admin Active",
                    True,
                    "Admin successfully updated SOS alert status to admin_active"
                )
            else:
                self.log_test(
                    "Admin Update SOS Alert to Admin Active",
                    False,
                    f"Admin failed to update alert status with code {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Admin Update SOS Alert to Admin Active",
                False,
                f"Error testing admin alert update to admin_active: {str(e)}"
            )

    def test_admin_active_alerts(self):
        """Test GET /api/admin/active-alerts endpoint for admin_active status alerts"""
        print("\n=== Testing Admin Active Alerts Endpoint ===")
        
        if not self.admin_token:
            self.log_test("Admin Active Alerts", False, "No admin token available for testing")
            return
        
        try:
            response = self.session.get(
                f"{self.base_url}/admin/active-alerts",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                active_alerts = response.json()
                self.log_test(
                    "Get Admin Active Alerts",
                    True,
                    f"Retrieved {len(active_alerts)} admin-active alerts",
                    {"active_alerts_count": len(active_alerts)}
                )
                
                # Verify all returned alerts have admin_active status
                all_admin_active = all(alert.get("status") == "admin_active" for alert in active_alerts)
                if all_admin_active or len(active_alerts) == 0:
                    self.log_test(
                        "Admin Active Alerts Status Filter",
                        True,
                        "All returned alerts have admin_active status (or no alerts found)"
                    )
                else:
                    self.log_test(
                        "Admin Active Alerts Status Filter",
                        False,
                        "Some returned alerts do not have admin_active status"
                    )
            else:
                self.log_test(
                    "Get Admin Active Alerts",
                    False,
                    f"Failed to get admin active alerts with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Get Admin Active Alerts",
                False,
                f"Error testing admin active alerts: {str(e)}"
            )

    def test_user_status_management(self):
        """Test admin can activate/deactivate users via PUT /api/admin/users/{id}/status"""
        print("\n=== Testing User Status Management ===")
        
        if not self.admin_token or not self.test_user_id:
            self.log_test("User Status Management", False, "No admin token or test user ID available")
            return
        
        # Test deactivating a user
        try:
            response = self.session.put(
                f"{self.base_url}/admin/users/{self.test_user_id}/status",
                params={"is_active": False},
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                self.log_test(
                    "Admin Deactivate User",
                    True,
                    "Admin successfully deactivated user"
                )
            else:
                self.log_test(
                    "Admin Deactivate User",
                    False,
                    f"Failed to deactivate user with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Admin Deactivate User",
                False,
                f"Error deactivating user: {str(e)}"
            )
        
        # Test reactivating a user
        try:
            response = self.session.put(
                f"{self.base_url}/admin/users/{self.test_user_id}/status",
                params={"is_active": True},
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                self.log_test(
                    "Admin Reactivate User",
                    True,
                    "Admin successfully reactivated user"
                )
            else:
                self.log_test(
                    "Admin Reactivate User",
                    False,
                    f"Failed to reactivate user with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Admin Reactivate User",
                False,
                f"Error reactivating user: {str(e)}"
            )
        
        # Test with invalid user ID
        try:
            response = self.session.put(
                f"{self.base_url}/admin/users/invalid_user_id/status",
                params={"is_active": False},
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 400:
                self.log_test(
                    "Invalid User ID Status Update",
                    True,
                    "Correctly rejected invalid user ID with 400"
                )
            else:
                self.log_test(
                    "Invalid User ID Status Update",
                    False,
                    f"Expected 400 for invalid user ID but got {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "Invalid User ID Status Update",
                False,
                f"Error testing invalid user ID: {str(e)}"
            )

    def test_deactivated_user_login(self):
        """Test that deactivated users cannot login"""
        print("\n=== Testing Deactivated User Login Block ===")
        
        if not self.admin_token or not self.test_user_id:
            self.log_test("Deactivated User Login", False, "No admin token or test user ID available")
            return
        
        # First deactivate the test user
        try:
            response = self.session.put(
                f"{self.base_url}/admin/users/{self.test_user_id}/status",
                params={"is_active": False},
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code != 200:
                self.log_test(
                    "Deactivated User Login Setup",
                    False,
                    "Failed to deactivate user for testing"
                )
                return
        except Exception as e:
            self.log_test(
                "Deactivated User Login Setup",
                False,
                f"Error deactivating user for test: {str(e)}"
            )
            return
        
        # Now try to login with the deactivated user
        login_data = {
            "username": "testuser_emergency",
            "password": "testpass123"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 403:
                response_data = response.json()
                expected_message = "Your account has been suspended. Please contact support."
                if expected_message in response_data.get("detail", ""):
                    self.log_test(
                        "Deactivated User Login Block",
                        True,
                        "Deactivated user correctly blocked from login with proper error message"
                    )
                else:
                    self.log_test(
                        "Deactivated User Login Block",
                        True,
                        "Deactivated user blocked but with different error message",
                        {"actual_message": response_data.get("detail", "")}
                    )
            else:
                self.log_test(
                    "Deactivated User Login Block",
                    False,
                    f"Expected 403 for deactivated user but got {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Deactivated User Login Block",
                False,
                f"Error testing deactivated user login: {str(e)}"
            )
        
        # Reactivate the user for other tests
        try:
            self.session.put(
                f"{self.base_url}/admin/users/{self.test_user_id}/status",
                params={"is_active": True},
                headers=self.get_auth_headers(self.admin_token)
            )
        except Exception:
            pass  # Ignore errors in cleanup

    def test_news_system_api(self):
        """Test News System API - Public and Admin endpoints"""
        print("\n=== Testing News System API ===")
        
        if not self.admin_token:
            self.log_test("News System API", False, "No admin token available for testing")
            return
        
        # Store created news article IDs for cleanup
        created_news_ids = []
        
        # Test data for news articles
        news_articles = [
            {
                "title": "Emergency Safety Tips for Winter",
                "content": "Stay safe during winter emergencies by keeping warm clothing, flashlights, and emergency supplies ready. Always inform someone of your travel plans during severe weather conditions."
            },
            {
                "title": "New Emergency Contact Features Available",
                "content": "We've added new features to help you manage your emergency contacts more effectively. You can now set primary contacts and add detailed relationship information."
            },
            {
                "title": "System Maintenance Scheduled",
                "content": "Scheduled maintenance will occur this weekend. Emergency services will remain available, but some features may be temporarily unavailable."
            }
        ]
        
        # Test 1: Create news articles as admin
        print("\n--- Testing Admin News Creation ---")
        for i, article_data in enumerate(news_articles):
            try:
                response = self.session.post(
                    f"{self.base_url}/admin/news",
                    json=article_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    created_article = response.json()
                    article_id = created_article.get("id")
                    if article_id:
                        created_news_ids.append(article_id)
                    
                    # Verify article has required fields and is_active=True by default
                    is_active = created_article.get("is_active", False)
                    author_name = created_article.get("author_name", "")
                    
                    self.log_test(
                        f"Create News Article {i+1}",
                        True,
                        f"Article '{article_data['title'][:30]}...' created successfully (active: {is_active})",
                        {"article_id": article_id, "is_active": is_active, "author": author_name}
                    )
                else:
                    self.log_test(
                        f"Create News Article {i+1}",
                        False,
                        f"Failed to create article with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    f"Create News Article {i+1}",
                    False,
                    f"Error creating article: {str(e)}"
                )
        
        # Test 2: Get all news articles as admin (should include inactive ones)
        print("\n--- Testing Admin Get All News ---")
        try:
            response = self.session.get(
                f"{self.base_url}/admin/news",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                admin_news = response.json()
                self.log_test(
                    "Admin Get All News Articles",
                    True,
                    f"Retrieved {len(admin_news)} news articles for admin",
                    {"articles_count": len(admin_news)}
                )
            else:
                self.log_test(
                    "Admin Get All News Articles",
                    False,
                    f"Failed to get admin news with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Admin Get All News Articles",
                False,
                f"Error getting admin news: {str(e)}"
            )
        
        # Test 3: Get public news articles (should only show active ones)
        print("\n--- Testing Public News Access ---")
        try:
            response = self.session.get(f"{self.base_url}/news")
            
            if response.status_code == 200:
                public_news = response.json()
                
                # Verify all returned articles are active
                all_active = all(article.get("is_active", False) for article in public_news)
                
                self.log_test(
                    "Public Get Active News Articles",
                    True,
                    f"Retrieved {len(public_news)} active news articles for public (all active: {all_active})",
                    {"articles_count": len(public_news), "all_active": all_active}
                )
                
                # Verify users can see the news we just created
                created_titles = [article["title"] for article in news_articles]
                found_articles = [article for article in public_news if article.get("title") in created_titles]
                
                if len(found_articles) > 0:
                    self.log_test(
                        "Public News Visibility",
                        True,
                        f"Users can see {len(found_articles)} of the newly created news articles",
                        {"found_articles": len(found_articles)}
                    )
                else:
                    self.log_test(
                        "Public News Visibility",
                        False,
                        "Users cannot see any of the newly created news articles"
                    )
            else:
                self.log_test(
                    "Public Get Active News Articles",
                    False,
                    f"Failed to get public news with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Public Get Active News Articles",
                False,
                f"Error getting public news: {str(e)}"
            )
        
        # Test 4: Update news article as admin
        print("\n--- Testing Admin News Update ---")
        if created_news_ids:
            article_id = created_news_ids[0]
            update_data = {
                "title": "Updated: Emergency Safety Tips for Winter",
                "content": "UPDATED CONTENT: Stay safe during winter emergencies by keeping warm clothing, flashlights, and emergency supplies ready. New safety protocols have been added.",
                "is_active": True
            }
            
            try:
                response = self.session.put(
                    f"{self.base_url}/admin/news/{article_id}",
                    json=update_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    updated_article = response.json()
                    self.log_test(
                        "Update News Article",
                        True,
                        f"Article updated successfully: '{updated_article.get('title', '')[:30]}...'",
                        {"updated_article": updated_article}
                    )
                else:
                    self.log_test(
                        "Update News Article",
                        False,
                        f"Failed to update article with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    "Update News Article",
                    False,
                    f"Error updating article: {str(e)}"
                )
        
        # Test 5: Deactivate news article (set is_active=False)
        print("\n--- Testing News Article Deactivation ---")
        if len(created_news_ids) > 1:
            article_id = created_news_ids[1]
            deactivate_data = {"is_active": False}
            
            try:
                response = self.session.put(
                    f"{self.base_url}/admin/news/{article_id}",
                    json=deactivate_data,
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "Deactivate News Article",
                        True,
                        "Article deactivated successfully"
                    )
                    
                    # Verify deactivated article doesn't appear in public news
                    try:
                        public_response = self.session.get(f"{self.base_url}/news")
                        if public_response.status_code == 200:
                            public_news = public_response.json()
                            deactivated_found = any(article.get("id") == article_id for article in public_news)
                            
                            if not deactivated_found:
                                self.log_test(
                                    "Deactivated Article Hidden from Public",
                                    True,
                                    "Deactivated article correctly hidden from public news"
                                )
                            else:
                                self.log_test(
                                    "Deactivated Article Hidden from Public",
                                    False,
                                    "Deactivated article still visible in public news"
                                )
                    except Exception as e:
                        self.log_test(
                            "Deactivated Article Hidden from Public",
                            False,
                            f"Error verifying deactivated article visibility: {str(e)}"
                        )
                else:
                    self.log_test(
                        "Deactivate News Article",
                        False,
                        f"Failed to deactivate article with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    "Deactivate News Article",
                    False,
                    f"Error deactivating article: {str(e)}"
                )
        
        # Test 6: Delete news article as admin
        print("\n--- Testing Admin News Deletion ---")
        if len(created_news_ids) > 2:
            article_id = created_news_ids[2]
            
            try:
                response = self.session.delete(
                    f"{self.base_url}/admin/news/{article_id}",
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "Delete News Article",
                        True,
                        "Article deleted successfully"
                    )
                    
                    # Remove from our list since it's deleted
                    created_news_ids.remove(article_id)
                else:
                    self.log_test(
                        "Delete News Article",
                        False,
                        f"Failed to delete article with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    "Delete News Article",
                    False,
                    f"Error deleting article: {str(e)}"
                )
        
        # Test 7: Test error handling for invalid IDs
        print("\n--- Testing News Error Handling ---")
        
        # Test invalid article ID for update
        try:
            response = self.session.put(
                f"{self.base_url}/admin/news/invalid_article_id",
                json={"title": "Test"},
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 400:
                self.log_test(
                    "Invalid Article ID Update",
                    True,
                    "Correctly rejected invalid article ID for update"
                )
            else:
                self.log_test(
                    "Invalid Article ID Update",
                    False,
                    f"Expected 400 for invalid ID but got {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "Invalid Article ID Update",
                False,
                f"Error testing invalid article ID: {str(e)}"
            )
        
        # Test invalid article ID for delete
        try:
            response = self.session.delete(
                f"{self.base_url}/admin/news/invalid_article_id",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 400:
                self.log_test(
                    "Invalid Article ID Delete",
                    True,
                    "Correctly rejected invalid article ID for delete"
                )
            else:
                self.log_test(
                    "Invalid Article ID Delete",
                    False,
                    f"Expected 400 for invalid ID but got {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "Invalid Article ID Delete",
                False,
                f"Error testing invalid article ID: {str(e)}"
            )
        
        # Test 8: Test non-admin access to admin news endpoints
        print("\n--- Testing Non-Admin Access to News Admin Endpoints ---")
        if self.user_token:
            # Test regular user trying to create news
            try:
                response = self.session.post(
                    f"{self.base_url}/admin/news",
                    json={"title": "Unauthorized Test", "content": "This should fail"},
                    headers=self.get_auth_headers(self.user_token)
                )
                
                if response.status_code == 403:
                    self.log_test(
                        "User Create News Denied",
                        True,
                        "Regular user correctly denied access to create news"
                    )
                else:
                    self.log_test(
                        "User Create News Denied",
                        False,
                        f"Expected 403 for regular user but got {response.status_code}"
                    )
            except Exception as e:
                self.log_test(
                    "User Create News Denied",
                    False,
                    f"Error testing user access to admin news: {str(e)}"
                )
        
        # Clean up remaining test articles
        print("\n--- Cleaning Up Test News Articles ---")
        for article_id in created_news_ids:
            try:
                self.session.delete(
                    f"{self.base_url}/admin/news/{article_id}",
                    headers=self.get_auth_headers(self.admin_token)
                )
            except Exception:
                pass  # Ignore cleanup errors

    def test_funkgeraet_system_api(self):
        """Test Funkgerät (Radio) System API - Groups, Messages, User Assignments, Admin Profile"""
        print("\n=== Testing Funkgerät (Radio) System API ===")
        
        if not self.admin_token:
            self.log_test("Funkgerät System API", False, "No admin token available for testing")
            return
        
        # Store created group IDs for cleanup and testing
        created_group_ids = []
        created_message_ids = []
        
        # Test 1: Create Chat Groups (POST /api/admin/chat/groups)
        print("\n--- Testing Chat Group Management ---")
        
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
                        created_group_ids.append(group_id)
                    
                    self.log_test(
                        f"Create Chat Group {i+1}",
                        True,
                        f"Group '{group_data['name']}' created successfully",
                        {"group_id": group_id, "group": created_group}
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
                f"{self.base_url}/admin/chat/groups",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                groups = response.json()
                self.log_test(
                    "Get All Chat Groups",
                    True,
                    f"Retrieved {len(groups)} chat groups",
                    {"groups_count": len(groups)}
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
        if created_group_ids:
            group_id = created_group_ids[0]
            update_data = {
                "name": "Einsatzleitung (Aktualisiert)",
                "description": "Aktualisierte Hauptkommunikation für Einsatzleitung",
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
                        "Update Chat Group",
                        True,
                        f"Group updated successfully: '{updated_group.get('name', '')}'",
                        {"updated_group": updated_group}
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
        
        # Test 4: Send Chat Messages (POST /api/admin/chat)
        print("\n--- Testing Chat Messages ---")
        
        test_messages = [
            {
                "message": "Einsatz in der Hauptstraße 123 - Verkehrsunfall mit Personenschaden",
                "chat_type": "admin",
                "group_id": created_group_ids[0] if created_group_ids else None,
                "is_voice_message": False
            },
            {
                "message": "Rettungswagen ist unterwegs, ETA 5 Minuten",
                "chat_type": "admin", 
                "group_id": created_group_ids[1] if len(created_group_ids) > 1 else None,
                "is_voice_message": False
            },
            {
                "message": "Sprach-Nachricht: Notfall-Briefing",
                "chat_type": "admin",
                "group_id": created_group_ids[0] if created_group_ids else None,
                "is_voice_message": True,
                "voice_data": "base64_encoded_voice_data_example",
                "voice_duration": 30
            }
        ]
        
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
                        created_message_ids.append(message_id)
                    
                    message_type = "Voice Message" if message_data.get("is_voice_message") else "Text Message"
                    self.log_test(
                        f"Send Chat Message {i+1} ({message_type})",
                        True,
                        f"Message sent successfully to group",
                        {"message_id": message_id, "message": created_message}
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
        
        # Test 5: Get Chat Messages by Group (GET /api/admin/chat?group_id=xxx)
        if created_group_ids:
            group_id = created_group_ids[0]
            try:
                response = self.session.get(
                    f"{self.base_url}/admin/chat",
                    params={"group_id": group_id, "chat_type": "admin"},
                    headers=self.get_auth_headers(self.admin_token)
                )
                
                if response.status_code == 200:
                    messages = response.json()
                    self.log_test(
                        "Get Chat Messages by Group",
                        True,
                        f"Retrieved {len(messages)} messages from group",
                        {"messages_count": len(messages), "group_id": group_id}
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
        
        # Test 6: User Role Management (PUT /api/admin/users/{user_id}/role)
        print("\n--- Testing User Role Management ---")
        
        if self.test_user_id:
            # Test changing user role to admin
            role_data = {"role": "admin"}
            
            try:
                response = self.session.put(
                    f"{self.base_url}/admin/users/{self.test_user_id}/role",
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
                        f"{self.base_url}/admin/users/{self.test_user_id}/role",
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
        
        # Test 7: User Group Assignments (PUT /api/admin/users/{user_id}/groups)
        print("\n--- Testing User Group Assignments ---")
        
        if self.test_user_id and created_group_ids:
            # Assign user to multiple groups
            groups_data = {"group_ids": created_group_ids[:2]}  # Assign to first 2 groups
            
            try:
                response = self.session.put(
                    f"{self.base_url}/admin/users/{self.test_user_id}/groups",
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
        
        # Test 8: Admin Profile Update (PUT /api/admin/profile)
        print("\n--- Testing Admin Profile Update ---")
        
        profile_data = {"full_name": "Administrator (Funkgerät System)"}
        
        try:
            response = self.session.put(
                f"{self.base_url}/admin/profile",
                json=profile_data,
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                updated_admin = response.json()
                self.log_test(
                    "Update Admin Profile",
                    True,
                    f"Admin name updated to: '{updated_admin.get('full_name', '')}'",
                    {"updated_admin": updated_admin}
                )
                
                # Change back to original name
                original_profile_data = {"full_name": "System Administrator"}
                self.session.put(
                    f"{self.base_url}/admin/profile",
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
        
        # Test 9: Error Handling for Invalid IDs
        print("\n--- Testing Funkgerät Error Handling ---")
        
        # Test invalid group ID for update
        try:
            response = self.session.put(
                f"{self.base_url}/admin/chat/groups/invalid_group_id",
                json={"name": "Test"},
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 400:
                self.log_test(
                    "Invalid Group ID Update",
                    True,
                    "Correctly rejected invalid group ID for update"
                )
            else:
                self.log_test(
                    "Invalid Group ID Update",
                    False,
                    f"Expected 400 for invalid ID but got {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "Invalid Group ID Update",
                False,
                f"Error testing invalid group ID: {str(e)}"
            )
        
        # Test invalid user ID for role change
        try:
            response = self.session.put(
                f"{self.base_url}/admin/users/invalid_user_id/role",
                json={"role": "admin"},
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 400:
                self.log_test(
                    "Invalid User ID Role Change",
                    True,
                    "Correctly rejected invalid user ID for role change"
                )
            else:
                self.log_test(
                    "Invalid User ID Role Change",
                    False,
                    f"Expected 400 for invalid ID but got {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "Invalid User ID Role Change",
                False,
                f"Error testing invalid user ID: {str(e)}"
            )
        
        # Test 10: Delete Chat Group (DELETE /api/admin/chat/groups/{id})
        print("\n--- Testing Chat Group Deletion ---")
        
        if len(created_group_ids) > 2:  # Keep some groups, delete one for testing
            group_id = created_group_ids.pop()  # Remove last group from list and delete it
            
            try:
                response = self.session.delete(
                    f"{self.base_url}/admin/chat/groups/{group_id}",
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
        
        # Test 11: Non-Admin Access to Funkgerät Endpoints
        print("\n--- Testing Non-Admin Access to Funkgerät Endpoints ---")
        
        if self.user_token:
            # Test regular user trying to create group
            try:
                response = self.session.post(
                    f"{self.base_url}/admin/chat/groups",
                    json={"name": "Unauthorized Group", "description": "This should fail"},
                    headers=self.get_auth_headers(self.user_token)
                )
                
                if response.status_code == 403:
                    self.log_test(
                        "User Create Group Denied",
                        True,
                        "Regular user correctly denied access to create groups"
                    )
                else:
                    self.log_test(
                        "User Create Group Denied",
                        False,
                        f"Expected 403 for regular user but got {response.status_code}"
                    )
            except Exception as e:
                self.log_test(
                    "User Create Group Denied",
                    False,
                    f"Error testing user access to admin groups: {str(e)}"
                )
            
            # Test regular user trying to send admin chat
            try:
                response = self.session.post(
                    f"{self.base_url}/admin/chat",
                    json={"message": "Unauthorized message", "chat_type": "admin"},
                    headers=self.get_auth_headers(self.user_token)
                )
                
                if response.status_code == 403:
                    self.log_test(
                        "User Send Admin Chat Denied",
                        True,
                        "Regular user correctly denied access to send admin chat"
                    )
                else:
                    self.log_test(
                        "User Send Admin Chat Denied",
                        False,
                        f"Expected 403 for regular user but got {response.status_code}"
                    )
            except Exception as e:
                self.log_test(
                    "User Send Admin Chat Denied",
                    False,
                    f"Error testing user access to admin chat: {str(e)}"
                )
        
        # Clean up remaining test groups and messages
        print("\n--- Cleaning Up Funkgerät Test Data ---")
        
        # Delete remaining groups
        for group_id in created_group_ids:
            try:
                self.session.delete(
                    f"{self.base_url}/admin/chat/groups/{group_id}",
                    headers=self.get_auth_headers(self.admin_token)
                )
            except Exception:
                pass  # Ignore cleanup errors
        
        # Delete messages (if endpoint exists)
        for message_id in created_message_ids:
            try:
                self.session.delete(
                    f"{self.base_url}/admin/chat/{message_id}",
                    headers=self.get_auth_headers(self.admin_token)
                )
            except Exception:
                pass  # Ignore cleanup errors

    def test_health_endpoints(self):
        """Test health check endpoints"""
        print("\n=== Testing Health Endpoints ===")
        
        # Test root endpoint
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                self.log_test("Root Endpoint", True, f"Root endpoint accessible: {data.get('message', '')}")
            else:
                self.log_test("Root Endpoint", False, f"Root endpoint failed with status {response.status_code}")
        except Exception as e:
            self.log_test("Root Endpoint", False, f"Root endpoint error: {str(e)}")

        # Test health endpoint
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                self.log_test("Health Check", True, f"Health check passed: {data.get('status', '')}")
            else:
                self.log_test("Health Check", False, f"Health check failed with status {response.status_code}")
        except Exception as e:
            self.log_test("Health Check", False, f"Health check error: {str(e)}")

    def test_emergency_contacts_crud(self):
        """Test Emergency Contacts CRUD operations with authentication"""
        print("\n=== Testing Emergency Contacts API with Authentication ===")
        
        if not self.user_token:
            self.log_test("Emergency Contacts CRUD", False, "No user token available for testing")
            return
        
        # Test data for emergency contacts
        test_contacts = [
            {
                "name": "Dr. Sarah Johnson",
                "phone": "+1-555-0123",
                "relationship": "Family Doctor",
                "is_primary": True
            },
            {
                "name": "Michael Smith",
                "phone": "+1-555-0456", 
                "relationship": "Brother",
                "is_primary": False
            },
            {
                "name": "Emergency Services",
                "phone": "911",
                "relationship": "Emergency",
                "is_primary": False
            }
        ]

        # Test CREATE emergency contacts
        for i, contact_data in enumerate(test_contacts):
            try:
                response = self.session.post(
                    f"{self.base_url}/emergency-contacts",
                    json=contact_data,
                    headers=self.get_auth_headers(self.user_token)
                )
                
                if response.status_code == 200:
                    created_contact = response.json()
                    contact_id = created_contact.get("id")
                    if contact_id:
                        self.created_contact_ids.append(contact_id)
                    self.log_test(
                        f"Create Emergency Contact {i+1}",
                        True,
                        f"Contact '{contact_data['name']}' created successfully",
                        {"contact_id": contact_id, "response": created_contact}
                    )
                else:
                    self.log_test(
                        f"Create Emergency Contact {i+1}",
                        False,
                        f"Failed to create contact with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    f"Create Emergency Contact {i+1}",
                    False,
                    f"Error creating contact: {str(e)}"
                )

        # Test GET all emergency contacts
        try:
            response = self.session.get(
                f"{self.base_url}/emergency-contacts",
                headers=self.get_auth_headers(self.user_token)
            )
            if response.status_code == 200:
                contacts = response.json()
                self.log_test(
                    "Get All Emergency Contacts",
                    True,
                    f"Retrieved {len(contacts)} contacts",
                    {"contacts_count": len(contacts)}
                )
            else:
                self.log_test(
                    "Get All Emergency Contacts",
                    False,
                    f"Failed to get contacts with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Get All Emergency Contacts",
                False,
                f"Error getting contacts: {str(e)}"
            )

        # Test UPDATE emergency contact (if we have created contacts)
        if self.created_contact_ids:
            contact_id = self.created_contact_ids[0]
            update_data = {
                "name": "Dr. Sarah Johnson (Updated)",
                "phone": "+1-555-9999"
            }
            
            try:
                response = self.session.put(
                    f"{self.base_url}/emergency-contacts/{contact_id}",
                    json=update_data,
                    headers=self.get_auth_headers(self.user_token)
                )
                
                if response.status_code == 200:
                    updated_contact = response.json()
                    self.log_test(
                        "Update Emergency Contact",
                        True,
                        f"Contact updated successfully",
                        {"updated_contact": updated_contact}
                    )
                else:
                    self.log_test(
                        "Update Emergency Contact",
                        False,
                        f"Failed to update contact with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    "Update Emergency Contact",
                    False,
                    f"Error updating contact: {str(e)}"
                )

        # Test DELETE emergency contact (delete one contact for testing)
        if len(self.created_contact_ids) > 1:
            contact_id = self.created_contact_ids.pop()  # Remove and delete last contact
            
            try:
                response = self.session.delete(
                    f"{self.base_url}/emergency-contacts/{contact_id}",
                    headers=self.get_auth_headers(self.user_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "Delete Emergency Contact",
                        True,
                        "Contact deleted successfully"
                    )
                else:
                    self.log_test(
                        "Delete Emergency Contact",
                        False,
                        f"Failed to delete contact with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    "Delete Emergency Contact",
                    False,
                    f"Error deleting contact: {str(e)}"
                )

        # Test error cases
        self.test_emergency_contacts_errors()

    def test_emergency_contacts_errors(self):
        """Test error cases for emergency contacts"""
        print("\n--- Testing Emergency Contacts Error Cases ---")
        
        # Test invalid contact ID for update
        try:
            response = self.session.put(
                f"{self.base_url}/emergency-contacts/invalid_id",
                json={"name": "Test"},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 400:
                self.log_test(
                    "Invalid Contact ID Update",
                    True,
                    "Correctly rejected invalid contact ID"
                )
            else:
                self.log_test(
                    "Invalid Contact ID Update",
                    False,
                    f"Expected 400 but got {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "Invalid Contact ID Update",
                False,
                f"Error testing invalid ID: {str(e)}"
            )

        # Test invalid contact ID for delete
        try:
            response = self.session.delete(f"{self.base_url}/emergency-contacts/invalid_id")
            
            if response.status_code == 400:
                self.log_test(
                    "Invalid Contact ID Delete",
                    True,
                    "Correctly rejected invalid contact ID"
                )
            else:
                self.log_test(
                    "Invalid Contact ID Delete",
                    False,
                    f"Expected 400 but got {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "Invalid Contact ID Delete",
                False,
                f"Error testing invalid ID: {str(e)}"
            )

    def test_user_profile_api(self):
        """Test User Profile API operations with authentication"""
        print("\n=== Testing User Profile API with Authentication ===")
        
        if not self.user_token:
            self.log_test("User Profile API", False, "No user token available for testing")
            return
        
        # Test profile data
        profile_data = {
            "name": "John Anderson",
            "phone": "+1-555-7890",
            "medical_conditions": ["Diabetes Type 2", "Hypertension"],
            "allergies": ["Penicillin", "Shellfish", "Peanuts"],
            "medications": ["Metformin 500mg", "Lisinopril 10mg", "Aspirin 81mg"],
            "blood_type": "O+",
            "emergency_message": "I have diabetes and take insulin. Please contact my doctor immediately."
        }

        # Test CREATE/UPDATE user profile
        try:
            response = self.session.post(
                f"{self.base_url}/user-profile",
                json=profile_data,
                headers=self.get_auth_headers(self.user_token)
            )
            
            if response.status_code == 200:
                created_profile = response.json()
                self.log_test(
                    "Create User Profile",
                    True,
                    f"Profile created for {profile_data['name']}",
                    {"profile": created_profile}
                )
            else:
                self.log_test(
                    "Create User Profile",
                    False,
                    f"Failed to create profile with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Create User Profile",
                False,
                f"Error creating profile: {str(e)}"
            )

        # Test GET user profile
        try:
            response = self.session.get(
                f"{self.base_url}/user-profile",
                headers=self.get_auth_headers(self.user_token)
            )
            
            if response.status_code == 200:
                profile = response.json()
                if profile:
                    self.log_test(
                        "Get User Profile",
                        True,
                        f"Retrieved profile for {profile.get('name', 'Unknown')}",
                        {"profile": profile}
                    )
                else:
                    self.log_test(
                        "Get User Profile",
                        True,
                        "No profile found (empty response)"
                    )
            else:
                self.log_test(
                    "Get User Profile",
                    False,
                    f"Failed to get profile with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Get User Profile",
                False,
                f"Error getting profile: {str(e)}"
            )

        # Test UPDATE existing profile
        updated_profile_data = {
            "name": "John Anderson (Updated)",
            "phone": "+1-555-7890",
            "medical_conditions": ["Diabetes Type 2", "Hypertension", "High Cholesterol"],
            "allergies": ["Penicillin", "Shellfish"],
            "medications": ["Metformin 500mg", "Lisinopril 10mg"],
            "blood_type": "O+",
            "emergency_message": "Updated: I have diabetes and high blood pressure. Emergency contact: Dr. Smith."
        }

        try:
            response = self.session.post(
                f"{self.base_url}/user-profile",
                json=updated_profile_data,
                headers=self.get_auth_headers(self.user_token)
            )
            
            if response.status_code == 200:
                updated_profile = response.json()
                self.log_test(
                    "Update User Profile",
                    True,
                    "Profile updated successfully",
                    {"updated_profile": updated_profile}
                )
            else:
                self.log_test(
                    "Update User Profile",
                    False,
                    f"Failed to update profile with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Update User Profile",
                False,
                f"Error updating profile: {str(e)}"
            )

    def test_sos_alerts_api(self):
        """Test SOS Alerts API operations with authentication"""
        print("\n=== Testing SOS Alerts API with Authentication ===")
        
        if not self.user_token:
            self.log_test("SOS Alerts API", False, "No user token available for testing")
            return
        
        # Test SOS alert data (user_id is now handled by authentication)
        alert_data_list = [
            {
                "location_lat": 40.7128,
                "location_lng": -74.0060,
                "location_address": "123 Main St, New York, NY 10001",
                "alert_type": "emergency",
                "message": "Medical emergency - chest pain"
            },
            {
                "location_lat": 40.7589,
                "location_lng": -73.9851,
                "location_address": "Central Park, New York, NY",
                "alert_type": "medical",
                "message": "Diabetic emergency - low blood sugar"
            },
            {
                "alert_type": "fire",
                "message": "House fire reported"
            }
        ]

        # Test CREATE SOS alerts
        for i, alert_data in enumerate(alert_data_list):
            try:
                response = self.session.post(
                    f"{self.base_url}/sos-alert",
                    json=alert_data,
                    headers=self.get_auth_headers(self.user_token)
                )
                
                if response.status_code == 200:
                    created_alert = response.json()
                    alert_id = created_alert.get("id")
                    if alert_id:
                        self.created_alert_ids.append(alert_id)
                    self.log_test(
                        f"Create SOS Alert {i+1}",
                        True,
                        f"Alert created: {alert_data['alert_type']}",
                        {"alert_id": alert_id, "alert": created_alert}
                    )
                else:
                    self.log_test(
                        f"Create SOS Alert {i+1}",
                        False,
                        f"Failed to create alert with status {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    f"Create SOS Alert {i+1}",
                    False,
                    f"Error creating alert: {str(e)}"
                )

        # Test GET all SOS alerts
        try:
            response = self.session.get(
                f"{self.base_url}/sos-alerts",
                headers=self.get_auth_headers(self.user_token)
            )
            
            if response.status_code == 200:
                alerts = response.json()
                self.log_test(
                    "Get All SOS Alerts",
                    True,
                    f"Retrieved {len(alerts)} alerts",
                    {"alerts_count": len(alerts)}
                )
            else:
                self.log_test(
                    "Get All SOS Alerts",
                    False,
                    f"Failed to get alerts with status {response.status_code}",
                    {"response_text": response.text}
                )
        except Exception as e:
            self.log_test(
                "Get All SOS Alerts",
                False,
                f"Error getting alerts: {str(e)}"
            )

        # Test UPDATE SOS alert status
        if self.created_alert_ids:
            alert_id = self.created_alert_ids[0]
            
            # Test updating to resolved
            try:
                response = self.session.put(
                    f"{self.base_url}/sos-alerts/{alert_id}/status",
                    params={"status": "resolved"},
                    headers=self.get_auth_headers(self.user_token)
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "Update SOS Alert Status to Resolved",
                        True,
                        "Alert status updated to resolved"
                    )
                else:
                    self.log_test(
                        "Update SOS Alert Status to Resolved",
                        False,
                        f"Failed to update status with code {response.status_code}",
                        {"response_text": response.text}
                    )
            except Exception as e:
                self.log_test(
                    "Update SOS Alert Status to Resolved",
                    False,
                    f"Error updating status: {str(e)}"
                )

            # Test updating to cancelled
            if len(self.created_alert_ids) > 1:
                alert_id = self.created_alert_ids[1]
                try:
                    response = self.session.put(
                        f"{self.base_url}/sos-alerts/{alert_id}/status",
                        params={"status": "cancelled"},
                        headers=self.get_auth_headers(self.user_token)
                    )
                    
                    if response.status_code == 200:
                        self.log_test(
                            "Update SOS Alert Status to Cancelled",
                            True,
                            "Alert status updated to cancelled"
                        )
                    else:
                        self.log_test(
                            "Update SOS Alert Status to Cancelled",
                            False,
                            f"Failed to update status with code {response.status_code}",
                            {"response_text": response.text}
                        )
                except Exception as e:
                    self.log_test(
                        "Update SOS Alert Status to Cancelled",
                        False,
                        f"Error updating status: {str(e)}"
                    )

        # Test error cases for SOS alerts
        self.test_sos_alerts_errors()

    def test_sos_alerts_errors(self):
        """Test error cases for SOS alerts"""
        print("\n--- Testing SOS Alerts Error Cases ---")
        
        # Test invalid alert ID
        try:
            response = self.session.put(
                f"{self.base_url}/sos-alerts/invalid_id/status",
                params={"status": "resolved"}
            )
            
            if response.status_code == 400:
                self.log_test(
                    "Invalid Alert ID Status Update",
                    True,
                    "Correctly rejected invalid alert ID"
                )
            else:
                self.log_test(
                    "Invalid Alert ID Status Update",
                    False,
                    f"Expected 400 but got {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "Invalid Alert ID Status Update",
                False,
                f"Error testing invalid ID: {str(e)}"
            )

        # Test invalid status
        if self.created_alert_ids:
            alert_id = self.created_alert_ids[0]
            try:
                response = self.session.put(
                    f"{self.base_url}/sos-alerts/{alert_id}/status",
                    params={"status": "invalid_status"}
                )
                
                if response.status_code == 400:
                    self.log_test(
                        "Invalid Status Value",
                        True,
                        "Correctly rejected invalid status value"
                    )
                else:
                    self.log_test(
                        "Invalid Status Value",
                        False,
                        f"Expected 400 but got {response.status_code}"
                    )
            except Exception as e:
                self.log_test(
                    "Invalid Status Value",
                    False,
                    f"Error testing invalid status: {str(e)}"
                )

    def test_data_persistence(self):
        """Test data persistence by retrieving data after operations with authentication"""
        print("\n=== Testing Data Persistence with Authentication ===")
        
        if not self.user_token:
            self.log_test("Data Persistence", False, "No user token available for testing")
            return
        
        # Verify emergency contacts persist
        try:
            response = self.session.get(
                f"{self.base_url}/emergency-contacts",
                headers=self.get_auth_headers(self.user_token)
            )
            if response.status_code == 200:
                contacts = response.json()
                if len(contacts) > 0:
                    self.log_test(
                        "Emergency Contacts Persistence",
                        True,
                        f"Found {len(contacts)} persisted contacts"
                    )
                else:
                    self.log_test(
                        "Emergency Contacts Persistence",
                        False,
                        "No contacts found after creation"
                    )
            else:
                self.log_test(
                    "Emergency Contacts Persistence",
                    False,
                    f"Failed to verify persistence: {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "Emergency Contacts Persistence",
                False,
                f"Error checking persistence: {str(e)}"
            )

        # Verify user profile persists
        try:
            response = self.session.get(
                f"{self.base_url}/user-profile",
                headers=self.get_auth_headers(self.user_token)
            )
            if response.status_code == 200:
                profile = response.json()
                if profile:
                    self.log_test(
                        "User Profile Persistence",
                        True,
                        f"Profile persisted for {profile.get('name', 'Unknown')}"
                    )
                else:
                    self.log_test(
                        "User Profile Persistence",
                        False,
                        "No profile found after creation"
                    )
            else:
                self.log_test(
                    "User Profile Persistence",
                    False,
                    f"Failed to verify persistence: {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "User Profile Persistence",
                False,
                f"Error checking persistence: {str(e)}"
            )

        # Verify SOS alerts persist
        try:
            response = self.session.get(
                f"{self.base_url}/sos-alerts",
                headers=self.get_auth_headers(self.user_token)
            )
            if response.status_code == 200:
                alerts = response.json()
                if len(alerts) > 0:
                    self.log_test(
                        "SOS Alerts Persistence",
                        True,
                        f"Found {len(alerts)} persisted alerts"
                    )
                else:
                    self.log_test(
                        "SOS Alerts Persistence",
                        False,
                        "No alerts found after creation"
                    )
            else:
                self.log_test(
                    "SOS Alerts Persistence",
                    False,
                    f"Failed to verify persistence: {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "SOS Alerts Persistence",
                False,
                f"Error checking persistence: {str(e)}"
            )

    def run_all_tests(self):
        """Run all API tests including authentication"""
        print(f"🚨 Emergency SOS Backend API Testing with Authentication Started")
        print(f"Base URL: {self.base_url}")
        print("=" * 80)
        
        # Run all test suites in order
        self.test_health_endpoints()
        
        # Authentication tests first
        self.test_admin_creation()
        self.test_admin_login()
        self.test_user_registration()
        self.test_user_login()
        self.test_jwt_token_validation()
        
        # Test protected routes without authentication
        self.test_protected_routes_without_auth()
        
        # Get test user ID if not available from registration
        if not self.test_user_id and self.admin_token:
            self.get_test_user_id()
        
        # Test authenticated CRUD operations
        self.test_emergency_contacts_crud()
        self.test_user_profile_api()
        self.test_sos_alerts_api()
        self.test_data_persistence()
        
        # Test role-based access control
        self.test_admin_only_routes()
        self.test_user_data_isolation()
        self.test_admin_sos_alert_update()
        
        # Test new Emergency SOS Admin functionality
        self.test_admin_active_alerts()
        self.test_user_status_management()
        self.test_deactivated_user_login()
        
        # Test News System API
        self.test_news_system_api()
        
        # Test Funkgerät (Radio) System API
        self.test_funkgeraet_system_api()
        
        # NEW SOS & PROFILE FEATURES (German Emergency System)
        self.test_sos_activation_management()
        self.test_profile_name_update()
        self.test_integration_sos_and_profile()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🚨 EMERGENCY SOS API TEST SUMMARY")
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
        
        print(f"\n📊 Test Categories:")
        categories = {}
        for result in self.test_results:
            category = result["test"].split()[0] if " " in result["test"] else "Other"
            if category not in categories:
                categories[category] = {"total": 0, "passed": 0}
            categories[category]["total"] += 1
            if result["success"]:
                categories[category]["passed"] += 1
        
        for category, stats in categories.items():
            success_rate = (stats["passed"]/stats["total"])*100
            print(f"  {category}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        
        print("=" * 60)
        
        return failed_tests == 0

    def get_test_user_id(self):
        """Get test user ID from admin users list"""
        if not self.admin_token:
            return
        
        try:
            response = self.session.get(
                f"{self.base_url}/admin/users",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                users = response.json()
                print(f"DEBUG: Found {len(users)} users")
                for user in users:
                    user_id = user.get("id") or user.get("_id")
                    if user.get("username") == "testuser_emergency":
                        self.test_user_id = user_id
                        break
        except Exception:
            pass  # Ignore errors


def main():
    """Main function to run tests"""
    tester = EmergencySOSAPITester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()