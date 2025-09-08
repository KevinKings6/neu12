#!/usr/bin/env python3
"""
Simple test to verify the SOS activation and list filtering fix
"""

import requests
import json

# Use external URL
BASE_URL = "https://emergency-sos-3.preview.emergentagent.com/api"

def test_sos_fix():
    print("🔍 Testing SOS Activation and List Filtering Fix")
    print("=" * 60)
    
    # Login as admin
    login_data = {"username": "admin", "password": "admin123"}
    response = requests.post(f"{BASE_URL}/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Admin login failed: {response.status_code}")
        return
    
    token_data = response.json()
    admin_token = token_data.get("access_token")
    
    print(f"✅ Admin login successful")
    
    headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    # Create a test SOS alert
    sos_data = {
        "location_lat": 52.52,
        "location_lng": 13.405,
        "location_address": "Berlin Test Location",
        "alert_type": "emergency",
        "message": "Test SOS für Aktivierung"
    }
    
    response = requests.post(f"{BASE_URL}/sos-alert", json=sos_data, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to create SOS alert: {response.status_code}")
        return
    
    created_sos = response.json()
    sos_id = created_sos.get("id") or created_sos.get("_id")
    print(f"✅ Created test SOS alert (ID: {sos_id})")
    
    # Check SOS list before activation
    response = requests.get(f"{BASE_URL}/admin/sos-alerts", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to get SOS alerts: {response.status_code}")
        return
    
    sos_alerts_before = response.json()
    print(f"📋 SOS alerts before activation: {len(sos_alerts_before)} alerts")
    
    # Check status distribution
    status_counts_before = {}
    for alert in sos_alerts_before:
        status = alert.get("status", "unknown")
        status_counts_before[status] = status_counts_before.get(status, 0) + 1
    
    print(f"   Status distribution: {status_counts_before}")
    
    # Test SOS activation
    print(f"\n🔧 Testing SOS activation:")
    response = requests.put(f"{BASE_URL}/admin/sos/{sos_id}/activate", headers=headers)
    
    print(f"   Request URL: {BASE_URL}/admin/sos/{sos_id}/activate")
    print(f"   Response Status: {response.status_code}")
    print(f"   Response Body: {response.text}")
    
    if response.status_code == 200:
        print("✅ SOS activation SUCCESSFUL - Fix is working!")
        
        # Check SOS list after activation (should have fewer alerts)
        response = requests.get(f"{BASE_URL}/admin/sos-alerts", headers=headers)
        
        if response.status_code == 200:
            sos_alerts_after = response.json()
            print(f"📋 SOS alerts after activation: {len(sos_alerts_after)} alerts")
            
            # Check status distribution
            status_counts_after = {}
            for alert in sos_alerts_after:
                status = alert.get("status", "unknown")
                status_counts_after[status] = status_counts_after.get(status, 0) + 1
            
            print(f"   Status distribution: {status_counts_after}")
            
            # Check if activated SOS is filtered out
            activated_sos_found = any(alert.get("id") == sos_id or alert.get("_id") == sos_id for alert in sos_alerts_after)
            
            if not activated_sos_found:
                print("✅ SOS list filtering SUCCESSFUL - Activated SOS correctly filtered out!")
            else:
                print("❌ SOS list filtering FAILED - Activated SOS still in list!")
            
            # Check if all alerts in list have pending/new status
            invalid_status_alerts = [alert for alert in sos_alerts_after if alert.get("status") not in ["pending", "new"]]
            
            if len(invalid_status_alerts) == 0:
                print("✅ SOS status filtering SUCCESSFUL - Only pending/new alerts in list!")
            else:
                print(f"❌ SOS status filtering FAILED - {len(invalid_status_alerts)} alerts with invalid status!")
                for alert in invalid_status_alerts:
                    print(f"   - Alert {alert.get('id', 'unknown')} has status: {alert.get('status')}")
        else:
            print(f"❌ Failed to get SOS alerts after activation: {response.status_code}")
    else:
        print("❌ SOS activation FAILED - Fix is NOT working!")
        print(f"   Error: {response.text}")

if __name__ == "__main__":
    test_sos_fix()