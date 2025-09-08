import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  Alert,
  StatusBar,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons, MaterialIcons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useAuth } from '../contexts/AuthContext';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();

  const handleLogin = async () => {
    if (!username || !password) {
      Alert.alert('Fehler', 'Bitte geben Sie Benutzername und Passwort ein');
      return;
    }

    setIsLoading(true);
    const success = await login(username, password);
    setIsLoading(false);

    if (success) {
      router.replace('/');
    } else {
      Alert.alert('Login Fehler', 'Ungültiger Benutzername oder Passwort');
    }
  };

  const navigateToRegister = () => {
    router.push('/register');
  };

  const quickAdminLogin = async () => {
    setUsername('admin');
    setPassword('admin123');
    setIsLoading(true);
    const success = await login('admin', 'admin123');
    setIsLoading(false);

    if (success) {
      router.replace('/');
    } else {
      Alert.alert('Admin Login', 'Admin-Benutzer wurde noch nicht erstellt. Verwenden Sie den "Admin erstellen" Button.');
    }
  };

  const createAdminUser = async () => {
    try {
      const response = await fetch(`${process.env.EXPO_PUBLIC_BACKEND_URL}/api/create-admin`, {
        method: 'POST',
      });

      if (response.ok) {
        const data = await response.json();
        Alert.alert(
          'Admin erstellt',
          `Admin-Benutzer wurde erstellt.\nBenutzername: admin\nPasswort: admin123`,
          [
            { text: 'OK', onPress: () => quickAdminLogin() }
          ]
        );
      } else {
        const errorData = await response.json();
        Alert.alert('Info', errorData.message);
      }
    } catch (error) {
      console.error('Error creating admin:', error);
      Alert.alert('Fehler', 'Fehler beim Erstellen des Admin-Benutzers');
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a1a" />
      
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardContainer}
      >
        <ScrollView contentContainerStyle={styles.scrollContainer} showsVerticalScrollIndicator={false}>
          {/* Header */}
          <View style={styles.header}>
            <MaterialIcons name="emergency" size={80} color="#ff4444" />
            <Text style={styles.title}>Emergency SOS</Text>
            <Text style={styles.subtitle}>Anmelden</Text>
          </View>

          {/* Login Form */}
          <View style={styles.form}>
            <View style={styles.inputContainer}>
              <Ionicons name="person-outline" size={20} color="#888" style={styles.inputIcon} />
              <TextInput
                style={styles.textInput}
                placeholder="Benutzername"
                placeholderTextColor="#666"
                value={username}
                onChangeText={setUsername}
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>

            <View style={styles.inputContainer}>
              <Ionicons name="lock-closed-outline" size={20} color="#888" style={styles.inputIcon} />
              <TextInput
                style={styles.textInput}
                placeholder="Passwort"
                placeholderTextColor="#666"
                value={password}
                onChangeText={setPassword}
                secureTextEntry={!showPassword}
                autoCapitalize="none"
                autoCorrect={false}
              />
              <TouchableOpacity
                style={styles.eyeIcon}
                onPress={() => setShowPassword(!showPassword)}
              >
                <Ionicons 
                  name={showPassword ? "eye-outline" : "eye-off-outline"} 
                  size={20} 
                  color="#888" 
                />
              </TouchableOpacity>
            </View>

            <TouchableOpacity
              style={[styles.loginButton, isLoading && styles.loginButtonDisabled]}
              onPress={handleLogin}
              disabled={isLoading}
            >
              <Text style={styles.loginButtonText}>
                {isLoading ? 'Anmelden...' : 'Anmelden'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.registerButton} onPress={navigateToRegister}>
              <Text style={styles.registerButtonText}>
                Noch kein Konto? Jetzt registrieren
              </Text>
            </TouchableOpacity>
          </View>

          {/* Quick Access Buttons */}
          <View style={styles.quickAccess}>
            <Text style={styles.quickAccessTitle}>Schnellzugriff</Text>
            
            <TouchableOpacity style={styles.adminButton} onPress={quickAdminLogin}>
              <Ionicons name="shield-checkmark" size={24} color="#fff" />
              <Text style={styles.adminButtonText}>Admin Login</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.createAdminButton} onPress={createAdminUser}>
              <Ionicons name="person-add" size={24} color="#fff" />
              <Text style={styles.createAdminButtonText}>Admin erstellen</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a1a',
  },
  keyboardContainer: {
    flex: 1,
  },
  scrollContainer: {
    flexGrow: 1,
    padding: 20,
    justifyContent: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginTop: 16,
  },
  subtitle: {
    fontSize: 18,
    color: '#888',
    marginTop: 8,
  },
  form: {
    marginBottom: 40,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    marginBottom: 16,
    paddingHorizontal: 16,
    borderWidth: 1,
    borderColor: '#333',
  },
  inputIcon: {
    marginRight: 12,
  },
  textInput: {
    flex: 1,
    fontSize: 16,
    color: '#fff',
    paddingVertical: 16,
  },
  eyeIcon: {
    padding: 4,
  },
  loginButton: {
    backgroundColor: '#ff4444',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  loginButtonDisabled: {
    backgroundColor: '#666',
  },
  loginButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  registerButton: {
    marginTop: 16,
    alignItems: 'center',
  },
  registerButtonText: {
    color: '#ff4444',
    fontSize: 16,
  },
  quickAccess: {
    marginTop: 20,
  },
  quickAccessTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    textAlign: 'center',
    marginBottom: 16,
  },
  adminButton: {
    backgroundColor: '#2196F3',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    marginBottom: 12,
  },
  adminButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  createAdminButton: {
    backgroundColor: '#9C27B0',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  createAdminButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
});