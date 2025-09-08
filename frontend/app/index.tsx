import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  Dimensions,
  StatusBar,
  Platform
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons, MaterialIcons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import * as Linking from 'expo-linking';
import * as Location from 'expo-location';
import { router } from 'expo-router';
import Constants from 'expo-constants';
import { useAuth } from '../contexts/AuthContext';

const { width, height } = Dimensions.get('window');
const BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

export default function Index() {
  const { user, token, isAdmin, logout, isLoading } = useAuth();
  const [isSOSPressed, setIsSOSPressed] = useState(false);
  const [userProfile, setUserProfile] = useState(null);

  console.log('Index component rendering...', { user, isLoading });

  useEffect(() => {
    // Check authentication after component mounts
    const checkAuth = async () => {
      console.log('Checking auth...', { user, isLoading });
      if (!isLoading) {
        if (!user) {
          console.log('No user, redirecting to login...');
          router.replace('/login');
          return;
        }
        if (user) {
          console.log('User found, loading profile...');
          loadUserProfile();
        }
      }
    };
    
    checkAuth();
  }, [user, isLoading]);

  const loadUserProfile = async () => {
    if (!token) return;
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/user-profile`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const profile = await response.json();
        setUserProfile(profile);
      }
    } catch (error) {
      console.log('Error loading user profile:', error);
    }
  };

  const handleSOSPress = () => {
    setIsSOSPressed(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
    
    Alert.alert(
      "Emergency SOS",
      "Möchten Sie den Notfall-SOS aktivieren?",
      [
        {
          text: "Abbrechen",
          style: "cancel",
          onPress: () => setIsSOSPressed(false)
        },
        {
          text: "Notfall",
          style: "destructive",
          onPress: () => activateEmergencySOS()
        }
      ]
    );
  };

  const getCurrentLocation = async () => {
    try {
      // Request location permissions
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Berechtigung benötigt', 'Standortberechtigung ist für Emergency SOS erforderlich.');
        return null;
      }

      // Get current position
      const location = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.High,
        timeout: 10000,
      });

      // Get address from coordinates
      try {
        const [address] = await Location.reverseGeocodeAsync({
          latitude: location.coords.latitude,
          longitude: location.coords.longitude,
        });

        const addressString = [
          address.street,
          address.streetNumber,
          address.city,
          address.postalCode,
          address.country
        ].filter(Boolean).join(', ');

        return {
          latitude: location.coords.latitude,
          longitude: location.coords.longitude,
          address: addressString || 'Adresse nicht verfügbar'
        };
      } catch (addressError) {
        console.log('Address lookup failed:', addressError);
        return {
          latitude: location.coords.latitude,
          longitude: location.coords.longitude,
          address: `Koordinaten: ${location.coords.latitude.toFixed(6)}, ${location.coords.longitude.toFixed(6)}`
        };
      }
    } catch (error) {
      console.error('Location error:', error);
      Alert.alert('Standort-Fehler', 'Standort konnte nicht ermittelt werden. SOS wird ohne Standortdaten gesendet.');
      return null;
    }
  };

  const activateEmergencySOS = async () => {
    try {
      // Get current location
      const locationData = await getCurrentLocation();

      // Create SOS alert in database with location
      const response = await fetch(`${BACKEND_URL}/api/sos-alert`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          alert_type: 'emergency',
          message: isAdmin() ? 'Admin Emergency SOS activated' : `Emergency SOS von ${user?.full_name || 'Benutzer'}`,
          location_lat: locationData?.latitude,
          location_lng: locationData?.longitude,
          location_address: locationData?.address
        })
      });

      if (response.ok) {
        const alert = await response.json();
        
        // If admin pressed SOS, move directly to ACTIVE
        if (isAdmin()) {
          await fetch(`${BACKEND_URL}/api/admin/sos-alerts/${alert.id}/status?status=admin_active`, {
            method: 'PUT',
            headers: {
              'Authorization': `Bearer ${token}`,
            }
          });
        }

        // Alert admins instead of calling police
        Alert.alert(
          "SOS Alarm mit Standort gesendet!",
          `Alle Administratoren wurden über Ihren Notfall benachrichtigt und kennen Ihren Standort${locationData ? `:\n${locationData.address}` : ''}`,
          [
            {
              text: "OK",
              onPress: () => {
                // Optional: Show admin contacts or further instructions
              }
            }
          ]
        );
      }
    } catch (error) {
      console.error('Error activating SOS:', error);
      Alert.alert("Fehler", "Notfall-Alarm konnte nicht gesendet werden. Bitte kontaktieren Sie die Administratoren direkt.");
    } finally {
      setIsSOSPressed(false);
    }
  };

  const alertAdmins = async (service: string) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    
    try {
      // Get current location
      const locationData = await getCurrentLocation();

      // Create specific SOS alert for the service type
      const response = await fetch(`${BACKEND_URL}/api/sos-alert`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          alert_type: service.toLowerCase(),
          message: `${service} Notfall von ${user?.full_name || 'Benutzer'} - Sofortige Hilfe benötigt!`,
          location_lat: locationData?.latitude,
          location_lng: locationData?.longitude,
          location_address: locationData?.address
        })
      });

      if (response.ok) {
        Alert.alert(
          `${service} Alarm mit Standort gesendet!`,
          `Alle Administratoren wurden über Ihren ${service}-Notfall benachrichtigt und kennen Ihren Standort${locationData ? `:\n${locationData.address}` : ''}`,
          [
            {
              text: "OK"
            }
          ]
        );
      } else {
        Alert.alert("Fehler", `${service}-Alarm konnte nicht gesendet werden. Bitte kontaktieren Sie die Administratoren direkt.`);
      }
    } catch (error) {
      console.error(`Error sending ${service} alert:`, error);
      Alert.alert("Fehler", `${service}-Alarm konnte nicht gesendet werden. Bitte kontaktieren Sie die Administratoren direkt.`);
    }
  };

  const navigateToContacts = () => {
    router.push('/contacts');
  };

  const navigateToProfile = () => {
    router.push('/profile');
  };

  const navigateToNews = () => {
    if (isAdmin()) {
      router.push('/admin/dashboard');
    } else {
      router.push('/news');
    }
  };

  const navigateToAdminPanel = () => {
    if (isAdmin()) {
      router.push('/admin/dashboard');
    } else {
      Alert.alert('Zugriff verweigert', 'Sie haben keine Berechtigung für den Admin-Bereich');
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a1a" />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Emergency SOS</Text>
        <View style={styles.userInfo}>
          <Text style={styles.userName}>{user?.full_name}</Text>
          <View style={[styles.roleBadge, { backgroundColor: isAdmin() ? '#ff4444' : '#2196F3' }]}>
            <Text style={styles.roleText}>{isAdmin() ? 'ADMIN' : 'USER'}</Text>
          </View>
          <TouchableOpacity style={styles.logoutButton} onPress={logout}>
            <Ionicons name="log-out-outline" size={20} color="#ff4444" />
          </TouchableOpacity>
        </View>
      </View>

      {/* Main SOS Button */}
      <View style={styles.sosContainer}>
        <TouchableOpacity
          style={[styles.sosButton, isSOSPressed && styles.sosButtonPressed]}
          onPress={handleSOSPress}
          activeOpacity={0.8}
        >
          <MaterialIcons name="emergency" size={80} color="#fff" />
          <Text style={styles.sosText}>SOS</Text>
          <Text style={styles.sosSubtext}>Emergency</Text>
        </TouchableOpacity>
        
        <Text style={styles.instructionText}>
          Press and hold for emergency services
        </Text>
      </View>

      {/* Quick Action Buttons */}
      <View style={styles.quickActions}>
        <View style={styles.actionRow}>
          <TouchableOpacity
            style={[styles.actionButton, styles.policeButton]}
            onPress={() => alertAdmins('Polizei')}
          >
            <Ionicons name="shield-outline" size={28} color="#fff" />
            <Text style={styles.actionText}>Polizei</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.actionButton, styles.fireButton]}
            onPress={() => alertAdmins('Feuerwehr')}
          >
            <MaterialIcons name="local-fire-department" size={28} color="#fff" />
            <Text style={styles.actionText}>Feuerwehr</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.actionRow}>
          <TouchableOpacity
            style={[styles.actionButton, styles.medicalButton]}
            onPress={() => alertAdmins('Medizin')}
          >
            <MaterialIcons name="medical-services" size={28} color="#fff" />
            <Text style={styles.actionText}>Medizin</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.actionButton, styles.contactsButton]}
            onPress={navigateToContacts}
          >
            <Ionicons name="people-outline" size={28} color="#fff" />
            <Text style={styles.actionText}>Contacts</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Bottom Navigation */}
      <View style={styles.bottomNav}>
        <TouchableOpacity style={styles.navButton} onPress={navigateToNews}>
          {isAdmin() ? (
            <>
              <MaterialIcons name="admin-panel-settings" size={24} color="#888" />
              <Text style={styles.navText}>Admin</Text>
            </>
          ) : (
            <>
              <MaterialIcons name="article" size={24} color="#888" />
              <Text style={styles.navText}>News</Text>
            </>
          )}
        </TouchableOpacity>

        <TouchableOpacity style={[styles.navButton, styles.activeNavButton]}>
          <MaterialIcons name="emergency" size={24} color="#ff4444" />
          <Text style={[styles.navText, styles.activeNavText]}>Notfall</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.navButton} onPress={navigateToProfile}>
          <Ionicons name="settings-outline" size={24} color="#888" />
          <Text style={styles.navText}>Profil</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a1a',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  userName: {
    fontSize: 14,
    color: '#fff',
    fontWeight: '600',
  },
  roleBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  roleText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#fff',
  },
  logoutButton: {
    padding: 4,
  },
  sosContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  sosButton: {
    width: width * 0.6,
    height: width * 0.6,
    borderRadius: width * 0.3,
    backgroundColor: '#ff4444',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#ff4444',
    shadowOffset: {
      width: 0,
      height: 8,
    },
    shadowOpacity: 0.4,
    shadowRadius: 16,
    elevation: 16,
    borderWidth: 4,
    borderColor: '#ff2222',
  },
  sosButtonPressed: {
    backgroundColor: '#cc3333',
    transform: [{ scale: 0.95 }],
  },
  sosText: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginTop: 8,
  },
  sosSubtext: {
    fontSize: 16,
    color: '#fff',
    opacity: 0.9,
  },
  instructionText: {
    fontSize: 16,
    color: '#888',
    textAlign: 'center',
    marginTop: 24,
    paddingHorizontal: 20,
  },
  quickActions: {
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  actionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  actionButton: {
    flex: 1,
    height: 80,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 8,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 8,
  },
  policeButton: {
    backgroundColor: '#2196F3',
  },
  fireButton: {
    backgroundColor: '#FF9800',
  },
  medicalButton: {
    backgroundColor: '#4CAF50',
  },
  contactsButton: {
    backgroundColor: '#9C27B0',
  },
  actionText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    marginTop: 4,
  },
  bottomNav: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderTopWidth: 1,
    borderTopColor: '#333',
    backgroundColor: '#2a2a2a',
  },
  navButton: {
    alignItems: 'center',
    padding: 8,
  },
  activeNavButton: {
    backgroundColor: '#333',
    borderRadius: 8,
    paddingHorizontal: 12,
  },
  navText: {
    fontSize: 12,
    color: '#888',
    marginTop: 4,
  },
  activeNavText: {
    color: '#ff4444',
  },
});