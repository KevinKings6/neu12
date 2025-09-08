#!/usr/bin/env python3
"""
Simple test to verify the user role management fix
"""

import requests
import json

# Use external URL
BASE_URL = "https://emergency-sos-3.preview.emergentagent.com/api"

def test_user_role_fix():
    print("🔍 Testing User Role Management Fix")
    print("=" * 50)
    
    # Login as admin
    login_data = {"username": "admin", "password": "admin123"}
    response = requests.post(f"{BASE_URL}/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Admin login failed: {response.status_code}")
        return
    
    token_data = response.json()
    admin_token = token_data.get("access_token")
    admin_user = token_data.get("user", {})
    admin_id = admin_user.get("id")
    
    print(f"✅ Admin login successful")
    print(f"   Admin ID: {admin_id}")
    print(f"   Admin Username: {admin_user.get('username')}")
    
    # Get all users
    headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to get users: {response.status_code}")
        return
    
    users = response.json()
    print(f"✅ Retrieved {len(users)} users")
    
    # Find a non-admin user to test with
    test_user = None
    for user in users:
        if user.get("role") != "admin" and user.get("username") != "admin":
            test_user = user
            break
    
    if not test_user:
        print("❌ No non-admin user found for testing")
        return
    
    test_user_id = test_user.get("id") or test_user.get("_id")
    print(f"✅ Found test user: {test_user.get('username')} (ID: {test_user_id})")
    
    # Test role change
    role_data = {"role": "team"}
    response = requests.put(
        f"{BASE_URL}/admin/users/{test_user_id}/role",
        json=role_data,
        headers=headers
    )
    
    print(f"\n🔧 Testing role change to 'team':")
    print(f"   Request URL: {BASE_URL}/admin/users/{test_user_id}/role")
    print(f"   Request Body: {role_data}")
    print(f"   Response Status: {response.status_code}")
    print(f"   Response Body: {response.text}")
    
    if response.status_code == 200:
        print("✅ User role change SUCCESSFUL - Fix is working!")
        
        # Change back to user
        role_data = {"role": "user"}
        response = requests.put(
            f"{BASE_URL}/admin/users/{test_user_id}/role",
            json=role_data,
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Role changed back to 'user' successfully")
        else:
            print(f"⚠️  Failed to change back to user: {response.status_code}")
    else:
        print("❌ User role change FAILED - Fix is NOT working!")
        print(f"   Error: {response.text}")
    
    # Test user status toggle
    print(f"\n🔧 Testing user status toggle:")
    response = requests.post(
        f"{BASE_URL}/admin/users/{test_user_id}/toggle-status",
        headers=headers
    )
    
    print(f"   Request URL: {BASE_URL}/admin/users/{test_user_id}/toggle-status")
    print(f"   Response Status: {response.status_code}")
    print(f"   Response Body: {response.text}")
    
    if response.status_code == 200:
        print("✅ User status toggle SUCCESSFUL - Fix is working!")
        
        # Toggle back
        response = requests.post(
            f"{BASE_URL}/admin/users/{test_user_id}/toggle-status",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Status toggled back successfully")
        else:
            print(f"⚠️  Failed to toggle back: {response.status_code}")
    else:
        print("❌ User status toggle FAILED - Fix is NOT working!")
        print(f"   Error: {response.text}")

if __name__ == "__main__":
    test_user_role_fix()