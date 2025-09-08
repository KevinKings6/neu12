import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  Alert,
  StatusBar,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { router } from 'expo-router';
import Constants from 'expo-constants';
import { useAuth } from '../contexts/AuthContext';

const BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface UserProfile {
  id?: string;
  name: string;
  phone: string;
  medical_conditions: string[];
  allergies: string[];
  medications: string[];
  blood_type?: string;
  emergency_message?: string;
}

export default function Profile() {
  const { token } = useAuth();
  const [profile, setProfile] = useState<UserProfile>({
    name: '',
    phone: '',
    medical_conditions: [],
    allergies: [],
    medications: [],
    blood_type: '',
    emergency_message: ''
  });
  const [loading, setLoading] = useState(false);
  const [editingName, setEditingName] = useState(false);
  const [tempName, setTempName] = useState('');
  const [newCondition, setNewCondition] = useState('');
  const [newAllergy, setNewAllergy] = useState('');
  const [newMedication, setNewMedication] = useState('');

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/user-profile`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const profileData = await response.json();
        if (profileData) {
          setProfile(profileData);
        }
      }
    } catch (error) {
      console.error('Error loading profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const startEditingName = () => {
    setTempName(profile.name);
    setEditingName(true);
  };

  const cancelEditingName = () => {
    setTempName('');
    setEditingName(false);
  };

  const saveNameChange = async () => {
    if (!tempName.trim()) {
      Alert.alert('Fehler', 'Name darf nicht leer sein');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/api/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ full_name: tempName.trim() })
      });

      if (response.ok) {
        setProfile(prev => ({ ...prev, name: tempName.trim() }));
        setEditingName(false);
        setTempName('');
        Alert.alert('Erfolg', 'Ihr Name wurde erfolgreich geändert!');
      } else {
        const errorData = await response.json();
        Alert.alert('Fehler', errorData.detail || 'Name konnte nicht geändert werden');
      }
    } catch (error) {
      console.error('Error updating name:', error);
      Alert.alert('Fehler', 'Netzwerkfehler beim Ändern des Namens');
    } finally {
      setLoading(false);
    }
  };

  const saveProfile = async () => {
    if (!profile.name || !profile.phone) {
      Alert.alert('Fehler', 'Bitte geben Sie Name und Telefonnummer ein');
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/user-profile`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(profile)
      });

      if (response.ok) {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        Alert.alert('Erfolg', 'Profil erfolgreich gespeichert');
        await loadProfile(); // Reload to get updated data
      } else {
        Alert.alert('Fehler', 'Profil konnte nicht gespeichert werden');
      }
    } catch (error) {
      console.error('Error saving profile:', error);
      Alert.alert('Fehler', 'Profil konnte nicht gespeichert werden');
    } finally {
      setLoading(false);
    }
  };

  const addCondition = () => {
    if (newCondition.trim()) {
      setProfile({
        ...profile,
        medical_conditions: [...profile.medical_conditions, newCondition.trim()]
      });
      setNewCondition('');
    }
  };

  const removeCondition = (index: number) => {
    setProfile({
      ...profile,
      medical_conditions: profile.medical_conditions.filter((_, i) => i !== index)
    });
  };

  const addAllergy = () => {
    if (newAllergy.trim()) {
      setProfile({
        ...profile,
        allergies: [...profile.allergies, newAllergy.trim()]
      });
      setNewAllergy('');
    }
  };

  const removeAllergy = (index: number) => {
    setProfile({
      ...profile,
      allergies: profile.allergies.filter((_, i) => i !== index)
    });
  };

  const addMedication = () => {
    if (newMedication.trim()) {
      setProfile({
        ...profile,
        medications: [...profile.medications, newMedication.trim()]
      });
      setNewMedication('');
    }
  };

  const removeMedication = (index: number) => {
    setProfile({
      ...profile,
      medications: profile.medications.filter((_, i) => i !== index)
    });
  };

  const bloodTypes = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a1a" />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Profile & Medical Info</Text>
        <TouchableOpacity onPress={saveProfile} disabled={loading}>
          <Text style={[styles.saveButton, loading && styles.saveButtonDisabled]}>
            Save
          </Text>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Personal Information */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Personal Information</Text>
          
          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>Full Name *</Text>
            {editingName ? (
              <View style={styles.nameEditContainer}>
                <TextInput
                  style={[styles.textInput, styles.nameInput]}
                  value={tempName}
                  onChangeText={setTempName}
                  placeholder="Ihr vollständiger Name"
                  maxLength={100}
                  autoFocus
                />
                <View style={styles.nameActions}>
                  <TouchableOpacity
                    style={[styles.nameActionButton, styles.cancelButton]}
                    onPress={cancelEditingName}
                  >
                    <Text style={styles.cancelButtonText}>Abbrechen</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.nameActionButton, styles.saveButton]}
                    onPress={saveNameChange}
                    disabled={loading}
                  >
                    <Text style={styles.saveButtonText}>
                      {loading ? 'Speichern...' : 'Speichern'}
                    </Text>
                  </TouchableOpacity>
                </View>
              </View>
            ) : (
              <View style={styles.nameDisplayContainer}>
                <Text style={styles.nameDisplay}>
                  {profile.name || 'Noch kein Name eingegeben'}
                </Text>
                <TouchableOpacity
                  style={styles.editNameButton}
                  onPress={startEditingName}
                >
                  <Text style={styles.editNameButtonText}>✏️ Bearbeiten</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>Phone Number *</Text>
            <TextInput
              style={styles.textInput}
              value={profile.phone}
              onChangeText={(text) => setProfile({ ...profile, phone: text })}
              placeholder="Enter your phone number"
              placeholderTextColor="#666"
              keyboardType="phone-pad"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>Blood Type</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.bloodTypeContainer}>
              {bloodTypes.map((type) => (
                <TouchableOpacity
                  key={type}
                  style={[
                    styles.bloodTypeButton,
                    profile.blood_type === type && styles.bloodTypeButtonSelected
                  ]}
                  onPress={() => setProfile({ ...profile, blood_type: type })}
                >
                  <Text style={[
                    styles.bloodTypeText,
                    profile.blood_type === type && styles.bloodTypeTextSelected
                  ]}>
                    {type}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        </View>

        {/* Medical Conditions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Medical Conditions</Text>
          
          <View style={styles.addItemContainer}>
            <TextInput
              style={styles.addItemInput}
              value={newCondition}
              onChangeText={setNewCondition}
              placeholder="Add medical condition"
              placeholderTextColor="#666"
              onSubmitEditing={addCondition}
            />
            <TouchableOpacity style={styles.addButton} onPress={addCondition}>
              <Ionicons name="add" size={24} color="#fff" />
            </TouchableOpacity>
          </View>

          {profile.medical_conditions.map((condition, index) => (
            <View key={index} style={styles.listItem}>
              <Text style={styles.listItemText}>{condition}</Text>
              <TouchableOpacity onPress={() => removeCondition(index)}>
                <Ionicons name="close-circle" size={24} color="#ff4444" />
              </TouchableOpacity>
            </View>
          ))}
        </View>

        {/* Allergies */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Allergies</Text>
          
          <View style={styles.addItemContainer}>
            <TextInput
              style={styles.addItemInput}
              value={newAllergy}
              onChangeText={setNewAllergy}
              placeholder="Add allergy"
              placeholderTextColor="#666"
              onSubmitEditing={addAllergy}
            />
            <TouchableOpacity style={styles.addButton} onPress={addAllergy}>
              <Ionicons name="add" size={24} color="#fff" />
            </TouchableOpacity>
          </View>

          {profile.allergies.map((allergy, index) => (
            <View key={index} style={styles.listItem}>
              <Text style={styles.listItemText}>{allergy}</Text>
              <TouchableOpacity onPress={() => removeAllergy(index)}>
                <Ionicons name="close-circle" size={24} color="#ff4444" />
              </TouchableOpacity>
            </View>
          ))}
        </View>

        {/* Medications */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Current Medications</Text>
          
          <View style={styles.addItemContainer}>
            <TextInput
              style={styles.addItemInput}
              value={newMedication}
              onChangeText={setNewMedication}
              placeholder="Add medication"
              placeholderTextColor="#666"
              onSubmitEditing={addMedication}
            />
            <TouchableOpacity style={styles.addButton} onPress={addMedication}>
              <Ionicons name="add" size={24} color="#fff" />
            </TouchableOpacity>
          </View>

          {profile.medications.map((medication, index) => (
            <View key={index} style={styles.listItem}>
              <Text style={styles.listItemText}>{medication}</Text>
              <TouchableOpacity onPress={() => removeMedication(index)}>
                <Ionicons name="close-circle" size={24} color="#ff4444" />
              </TouchableOpacity>
            </View>
          ))}
        </View>

        {/* Emergency Message */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Emergency Message</Text>
          <Text style={styles.sectionDescription}>
            This message will be shared with emergency contacts when SOS is activated
          </Text>
          
          <TextInput
            style={[styles.textInput, styles.textArea]}
            value={profile.emergency_message}
            onChangeText={(text) => setProfile({ ...profile, emergency_message: text })}
            placeholder="Enter emergency instructions or important information..."
            placeholderTextColor="#666"
            multiline
            numberOfLines={4}
          />
        </View>

        <View style={styles.bottomPadding} />
      </ScrollView>
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
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  saveButton: {
    fontSize: 16,
    color: '#ff4444',
    fontWeight: '600',
  },
  saveButtonDisabled: {
    color: '#666',
  },
  scrollView: {
    flex: 1,
  },
  section: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  sectionDescription: {
    fontSize: 14,
    color: '#888',
    marginBottom: 16,
  },
  inputGroup: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 16,
    color: '#fff',
    marginBottom: 8,
    fontWeight: '600',
  },
  textInput: {
    backgroundColor: '#2a2a2a',
    borderRadius: 8,
    padding: 16,
    fontSize: 16,
    color: '#fff',
    borderWidth: 1,
    borderColor: '#333',
  },
  textArea: {
    height: 100,
    textAlignVertical: 'top',
  },
  bloodTypeContainer: {
    flexDirection: 'row',
    marginTop: 8,
  },
  bloodTypeButton: {
    backgroundColor: '#2a2a2a',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#333',
  },
  bloodTypeButtonSelected: {
    backgroundColor: '#ff4444',
    borderColor: '#ff4444',
  },
  bloodTypeText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  bloodTypeTextSelected: {
    color: '#fff',
  },
  addItemContainer: {
    flexDirection: 'row',
    marginBottom: 16,
    gap: 8,
  },
  addItemInput: {
    flex: 1,
    backgroundColor: '#2a2a2a',
    borderRadius: 8,
    padding: 16,
    fontSize: 16,
    color: '#fff',
    borderWidth: 1,
    borderColor: '#333',
  },
  addButton: {
    backgroundColor: '#ff4444',
    width: 48,
    height: 48,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  listItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#2a2a2a',
    padding: 16,
    borderRadius: 8,
    marginBottom: 8,
  },
  listItemText: {
    flex: 1,
    fontSize: 16,
    color: '#fff',
  },
  bottomPadding: {
    height: 100,
  },
});