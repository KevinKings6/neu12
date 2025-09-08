import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  TextInput,
  StatusBar,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Modal,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons, MaterialIcons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useAuth } from '../../contexts/AuthContext';
import Constants from 'expo-constants';
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';

const BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface ChatMessage {
  id: string;
  user_id: string;
  username: string;
  message: string;
  chat_type: string;
  group_id?: string;
  is_voice_message: boolean;
  voice_data?: string;
  voice_duration?: number;
  created_at: string;
}

interface ChatGroup {
  id: string;
  name: string;
  description?: string;
  created_by: string;
  members: string[];
  is_active: boolean;
  created_at: string;
}

interface User {
  id: string;
  username: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

export default function AdminChat() {
  const { user, token } = useAuth(); // Entferne isAdmin Hook
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [selectedGroup, setSelectedGroup] = useState<string | null>(null);
  const [sound, setSound] = useState<Audio.Sound | null>(null);
  const [showChannelManager, setShowChannelManager] = useState(false);
  const [showAllChannels, setShowAllChannels] = useState(false); // Switch für alle Kanäle
  const flatListRef = useRef<FlatList>(null);

  // Funkgerät Kanäle (von Backend geladen)
  const [channels, setChannels] = useState<ChatGroup[]>([]);

  // Voice recording states
  const [isRecordingVoice, setIsRecordingVoice] = useState(false);
  const [recordingUri, setRecordingUri] = useState<string | null>(null);
  const [voiceRecording, setVoiceRecording] = useState<Audio.Recording | null>(null);
  const [playingMessageId, setPlayingMessageId] = useState<string | null>(null);

  // Modal states
  const [adminProfileModalVisible, setAdminProfileModalVisible] = useState(false);
  const [adminName, setAdminName] = useState('');

  const openAdminProfileModal = () => {
    setAdminName(user?.full_name || '');
    setAdminProfileModalVisible(true);
  };

  // Voice recording functions
  const requestAudioPermission = async () => {
    try {
      const permission = await Audio.requestPermissionsAsync();
      return permission.status === 'granted';
    } catch (error) {
      console.error('Error requesting audio permission:', error);
      return false;
    }
  };

  const startRecording = async () => {
    try {
      const hasPermission = await requestAudioPermission();
      if (!hasPermission) {
        Alert.alert('Berechtigung erforderlich', 'Mikrofonzugriff ist erforderlich für Sprachnachrichten');
        return;
      }

      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      const newRecording = new Audio.Recording();
      await newRecording.prepareToRecordAsync(Audio.RECORDING_OPTIONS_PRESET_HIGH_QUALITY);
      await newRecording.startAsync();
      
      setVoiceRecording(newRecording);
      setIsRecordingVoice(true);
    } catch (error) {
      console.error('Failed to start recording:', error);
      Alert.alert('Fehler', 'Aufnahme konnte nicht gestartet werden');
    }
  };

  const stopRecording = async () => {
    if (!recording) return;

    try {
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      setRecordingUri(uri);
      setIsRecording(false);
      setRecording(null);
    } catch (error) {
      console.error('Failed to stop recording:', error);
      Alert.alert('Fehler', 'Aufnahme konnte nicht gestoppt werden');
    }
  };

  const sendVoiceMessage = async () => {
    if (!recordingUri || !token) return;

    setLoading(true);
    
    try {
      // Convert audio file to base64
      const audioBase64 = await FileSystem.readAsStringAsync(recordingUri, {
        encoding: FileSystem.EncodingType.Base64,
      });

      const messageData = {
        message: 'Sprachnachricht',
        chat_type: 'admin',
        group_id: selectedGroup,
        is_voice_message: true,
        voice_data: audioBase64,
        voice_duration: await getAudioDuration(recordingUri)
      };

      const response = await fetch(`${BACKEND_URL}/api/admin/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(messageData)
      });

      if (response.ok) {
        const sentMessage = await response.json();
        
        const newMsg: ChatMessage = {
          id: sentMessage.id || sentMessage._id || Date.now().toString(),
          user_id: user?.id || '1',
          username: user?.full_name || 'Admin',
          message: 'Sprachnachricht',
          chat_type: 'admin',
          group_id: selectedGroup,
          is_voice_message: true,
          voice_data: audioBase64,
          voice_duration: messageData.voice_duration,
          created_at: new Date().toISOString()
        };

        setMessages(prev => [...prev, newMsg]);
        setRecordingUri(null);
        
        setTimeout(() => {
          flatListRef.current?.scrollToEnd({ animated: true });
        }, 100);
      } else {
        Alert.alert('Fehler', 'Sprachnachricht konnte nicht gesendet werden');
      }
    } catch (error) {
      console.error('Error sending voice message:', error);
      Alert.alert('Fehler', 'Fehler beim Senden der Sprachnachricht');
    } finally {
      setLoading(false);
    }
  };

  const getAudioDuration = async (uri: string) => {
    try {
      const { sound } = await Audio.Sound.createAsync({ uri });
      const status = await sound.getStatusAsync();
      if (status.isLoaded) {
        return Math.floor((status.durationMillis || 0) / 1000);
      }
      return 0;
    } catch (error) {
      return 0;
    }
  };

  const playVoiceMessage = async (messageId: string, voiceData: string) => {
    try {
      if (playingMessageId === messageId) {
        setPlayingMessageId(null);
        return;
      }

      // Create temp file
      const tempUri = `${FileSystem.documentDirectory}temp_voice_${messageId}.m4a`;
      await FileSystem.writeAsStringAsync(tempUri, voiceData, {
        encoding: FileSystem.EncodingType.Base64,
      });

      const { sound } = await Audio.Sound.createAsync({ uri: tempUri });
      setPlayingMessageId(messageId);
      
      sound.setOnPlaybackStatusUpdate((status) => {
        if (status.isLoaded && status.didJustFinish) {
          setPlayingMessageId(null);
        }
      });

      await sound.playAsync();
    } catch (error) {
      console.error('Error playing voice message:', error);
      setPlayingMessageId(null);
      Alert.alert('Fehler', 'Sprachnachricht konnte nicht abgespielt werden');
    }
  };

  const saveAdminProfile = async () => {
    if (!adminName.trim() || !token) {
      Alert.alert('Fehler', 'Bitte geben Sie einen Namen ein');
      return;
    }

    setLoading(true);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ full_name: adminName })
      });

      if (response.ok) {
        setAdminProfileModalVisible(false);
        Alert.alert('Erfolg', 'Ihr Name wurde aktualisiert!');
      } else {
        Alert.alert('Fehler', 'Name konnte nicht aktualisiert werden');
      }
    } catch (error) {
      console.error('Error updating admin profile:', error);
      Alert.alert('Fehler', 'Fehler beim Aktualisieren des Profils');
    } finally {
      setLoading(false);
    }
  };
  const [channelModalVisible, setChannelModalVisible] = useState(false);
  const [editingChannel, setEditingChannel] = useState<ChatGroup | null>(null);
  const [channelForm, setChannelForm] = useState({
    name: '',
    description: '',
  });

  useEffect(() => {
    // Lade Kanäle und Nachrichten beim Start
    loadChannels();
    loadMessages();
  }, []);

  useEffect(() => {
    // Nachrichten neu laden wenn Kanal gewechselt wird
    loadMessages();
  }, [selectedGroup]);

  const loadChannels = async () => {
    if (!token) return;
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/chat/groups`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const channelsData = await response.json();
        setChannels(channelsData);
      } else {
        console.error('Failed to load channels:', response.status);
        // Fallback zu Standard-Kanälen wenn API fehlt
        setChannels([
          { id: '1', name: 'Kanal 1', description: 'Einsatzleitung', created_by: 'admin', members: [], is_active: true, created_at: new Date().toISOString() },
          { id: '2', name: 'Kanal 2', description: 'Rettungsdienst', created_by: 'admin', members: [], is_active: true, created_at: new Date().toISOString() },
          { id: '3', name: 'Kanal 3', description: 'Feuerwehr', created_by: 'admin', members: [], is_active: true, created_at: new Date().toISOString() },
        ]);
      }
    } catch (error) {
      console.error('Error loading channels:', error);
      // Fallback zu Standard-Kanälen
      setChannels([
        { id: '1', name: 'Kanal 1', description: 'Einsatzleitung', created_by: 'admin', members: [], is_active: true, created_at: new Date().toISOString() },
        { id: '2', name: 'Kanal 2', description: 'Rettungsdienst', created_by: 'admin', members: [], is_active: true, created_at: new Date().toISOString() },
        { id: '3', name: 'Kanal 3', description: 'Feuerwehr', created_by: 'admin', members: [], is_active: true, created_at: new Date().toISOString() },
      ]);
    }
  };

  const loadMessages = async () => {
    if (!token) return;
    
    try {
      const queryParams = new URLSearchParams({
        chat_type: 'admin',
        ...(selectedGroup && { group_id: selectedGroup })
      });
      
      const response = await fetch(`${BACKEND_URL}/api/admin/chat?${queryParams}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const messagesData = await response.json();
        setMessages(messagesData);
      } else {
        console.error('Failed to load messages:', response.status);
        // Fallback zu Demo-Nachrichten
        const demoMessages: ChatMessage[] = [
          {
            id: '1',
            user_id: user?.id || '1',
            username: 'Einsatzleiter Schmidt',
            message: 'Alle Einheiten, Lage-Update erforderlich',
            chat_type: 'admin',
            group_id: selectedGroup,
            is_voice_message: false,
            created_at: new Date(Date.now() - 300000).toISOString()
          },
          {
            id: '2',
            user_id: '2',
            username: 'RTW-1',
            message: 'Sprach-Nachricht',
            chat_type: 'admin',
            group_id: selectedGroup,
            is_voice_message: true,
            created_at: new Date(Date.now() - 120000).toISOString()
          }
        ];
        
        const filteredMessages = selectedGroup 
          ? demoMessages.filter(msg => msg.group_id === selectedGroup)
          : demoMessages;
        
        setMessages(filteredMessages);
      }
    } catch (error) {
      console.error('Error loading messages:', error);
      // Fallback zu Demo-Nachrichten bei Fehler
      setMessages([]);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !token) {
      Alert.alert('Fehler', 'Bitte geben Sie eine Nachricht ein');
      return;
    }

    setLoading(true);
    
    try {
      const messageData = {
        message: newMessage,
        chat_type: 'admin',
        group_id: selectedGroup,
        is_voice_message: false
      };

      const response = await fetch(`${BACKEND_URL}/api/admin/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(messageData)
      });

      if (response.ok) {
        const sentMessage = await response.json();
        
        // Nachricht zur lokalen Liste hinzufügen
        const newMsg: ChatMessage = {
          id: sentMessage.id || sentMessage._id || Date.now().toString(),
          user_id: user?.id || '1',
          username: user?.full_name || 'Admin',
          message: newMessage,
          chat_type: 'admin',
          group_id: selectedGroup,
          is_voice_message: false,
          created_at: new Date().toISOString()
        };

        setMessages(prev => [...prev, newMsg]);
        setNewMessage('');
        
        // Scroll to bottom
        setTimeout(() => {
          flatListRef.current?.scrollToEnd({ animated: true });
        }, 100);
      } else {
        console.error('Failed to send message:', response.status);
        Alert.alert('Fehler', 'Nachricht konnte nicht gesendet werden');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      Alert.alert('Fehler', 'Fehler beim Senden der Nachricht');
    } finally {
      setLoading(false);
    }
  };

  const startVoiceRecording = async () => {
    try {
      await Audio.requestPermissionsAsync();
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      const { recording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );
      setRecording(recording);
      setIsRecording(true);
    } catch (err) {
      console.error('Failed to start recording', err);
      Alert.alert('Fehler', 'Aufnahme konnte nicht gestartet werden');
    }
  };

  const stopVoiceRecording = async () => {
    if (!recording) return;

    try {
      setIsRecording(false);
      await recording.stopAndUnloadAsync();
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
      });

      const uri = recording.getURI();
      if (uri) {
        // Simulate voice message
        const voiceMsg: ChatMessage = {
          id: Date.now().toString(),
          user_id: user?.id || '1',
          username: user?.full_name || 'Admin',
          message: 'Sprach-Nachricht',
          chat_type: 'voice',
          group_id: selectedGroup,
          is_voice_message: true,
          created_at: new Date().toISOString()
        };

        setMessages(prev => [...prev, voiceMsg]);
        setTimeout(() => {
          flatListRef.current?.scrollToEnd({ animated: true });
        }, 100);
      }
      
      setRecording(null);
    } catch (error) {
      console.error('Error stopping recording:', error);
    }
  };

  const openChannelModal = (channel?: ChatGroup) => {
    if (channel) {
      setEditingChannel(channel);
      setChannelForm({
        name: channel.name,
        description: channel.description || '',
      });
    } else {
      setEditingChannel(null);
      setChannelForm({
        name: '',
        description: '',
      });
    }
    setChannelModalVisible(true);
  };

  const saveChannel = async () => {
    if (!channelForm.name.trim() || !token) {
      Alert.alert('Fehler', 'Bitte geben Sie einen Kanal-Namen ein');
      return;
    }

    setLoading(true);
    
    try {
      if (editingChannel) {
        // Kanal bearbeiten
        const response = await fetch(`${BACKEND_URL}/api/admin/chat/groups/${editingChannel.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            name: channelForm.name,
            description: channelForm.description,
          })
        });

        if (response.ok) {
          const updatedChannel = await response.json();
          setChannels(prev => prev.map(c => 
            c.id === editingChannel.id 
              ? { ...updatedChannel, id: updatedChannel.id || updatedChannel._id }
              : c
          ));
          Alert.alert('Erfolg', 'Kanal wurde aktualisiert!');
        } else {
          Alert.alert('Fehler', 'Kanal konnte nicht aktualisiert werden');
        }
      } else {
        // Neuen Kanal erstellen
        const response = await fetch(`${BACKEND_URL}/api/admin/chat/groups`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            name: channelForm.name,
            description: channelForm.description,
            members: []
          })
        });

        if (response.ok) {
          const newChannel = await response.json();
          const channelWithId = { ...newChannel, id: newChannel.id || newChannel._id };
          setChannels(prev => [...prev, channelWithId]);
          Alert.alert('Erfolg', 'Neuer Kanal wurde erstellt!');
        } else {
          Alert.alert('Fehler', 'Kanal konnte nicht erstellt werden');
        }
      }
      
      setChannelModalVisible(false);
    } catch (error) {
      console.error('Error saving channel:', error);
      Alert.alert('Fehler', 'Fehler beim Speichern des Kanals');
    } finally {
      setLoading(false);
    }
  };

  const deleteChannel = async (channelId: string) => {
    if (!token) return;
    
    Alert.alert(
      'Kanal löschen',
      'Möchten Sie diesen Kanal wirklich löschen?',
      [
        { text: 'Abbrechen', style: 'cancel' },
        {
          text: 'Löschen',
          style: 'destructive',
          onPress: async () => {
            setLoading(true);
            
            try {
              const response = await fetch(`${BACKEND_URL}/api/admin/chat/groups/${channelId}`, {
                method: 'DELETE',
                headers: {
                  'Authorization': `Bearer ${token}`,
                },
              });

              if (response.ok) {
                setChannels(prev => prev.filter(c => c.id !== channelId));
                if (selectedGroup === channelId) {
                  setSelectedGroup(null);
                }
                Alert.alert('Erfolg', 'Kanal wurde gelöscht!');
              } else {
                Alert.alert('Fehler', 'Kanal konnte nicht gelöscht werden');
              }
            } catch (error) {
              console.error('Error deleting channel:', error);
              Alert.alert('Fehler', 'Fehler beim Löschen des Kanals');
            } finally {
              setLoading(false);
            }
          }
        }
      ]
    );
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
  };

  const getCurrentChannelName = () => {
    if (!selectedGroup) return 'Alle Kanäle';
    const channel = channels.find(c => c.id === selectedGroup);
    return channel ? `${channel.name} - ${channel.description}` : 'Unbekannter Kanal';
  };

  const renderMessage = ({ item, index }: { item: ChatMessage, index: number }) => {
    const isOwnMessage = item.user_id === user?.id;

    return (
      <View style={[styles.messageContainer, isOwnMessage && styles.ownMessageContainer]}>
        <View style={[styles.messageBubble, isOwnMessage && styles.ownMessageBubble]}>
          {!isOwnMessage && (
            <Text style={styles.senderName}>{item.username}</Text>
          )}
          
          {item.is_voice_message ? (
            <View style={styles.voiceMessage}>
              <Ionicons name="mic" size={20} color={isOwnMessage ? '#fff' : '#ff4444'} />
              <Text style={[styles.messageText, isOwnMessage && styles.ownMessageText]}>
                Sprach-Nachricht
              </Text>
              <TouchableOpacity style={styles.playButton}>
                <Ionicons name="play" size={16} color={isOwnMessage ? '#fff' : '#ff4444'} />
              </TouchableOpacity>
            </View>
          ) : (
            <Text style={[styles.messageText, isOwnMessage && styles.ownMessageText]}>
              {item.message}
            </Text>
          )}
          
          <Text style={[styles.messageTime, isOwnMessage && styles.ownMessageTime]}>
            {formatTime(item.created_at)}
          </Text>
        </View>
      </View>
    );
  };

  if (showChannelManager) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="light-content" backgroundColor="#1a1a1a" />
        
        {/* Kanal-Verwaltung Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => setShowChannelManager(false)}>
            <Ionicons name="arrow-back" size={24} color="#fff" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>📻 Kanal-Verwaltung</Text>
          <TouchableOpacity onPress={() => openChannelModal()}>
            <Ionicons name="add" size={24} color="#fff" />
          </TouchableOpacity>
        </View>

        {/* Verwaltungs-Statistiken */}
        <View style={styles.managementStats}>
          <View style={styles.statCard}>
            <Text style={styles.statCardNumber}>{channels.length}</Text>
            <Text style={styles.statCardLabel}>Kanäle</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statCardNumber}>{channels.filter(c => c.is_active).length}</Text>
            <Text style={styles.statCardLabel}>Aktiv</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statCardNumber}>{selectedGroup ? '1' : '0'}</Text>
            <Text style={styles.statCardLabel}>Ausgewählt</Text>
          </View>
        </View>

        {/* Schnell-Aktionen */}
        <View style={styles.quickActionsBar}>
          <TouchableOpacity
            style={styles.quickActionBtn}
            onPress={() => openChannelModal()}
          >
            <Ionicons name="add-circle" size={20} color="#4CAF50" />
            <Text style={styles.quickActionBtnText}>Neuer Kanal</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.quickActionBtn}
            onPress={() => {
              // Alle Kanäle aktivieren
              setChannels(prev => prev.map(c => ({ ...c, is_active: true })));
              Alert.alert('Erfolg', 'Alle Kanäle aktiviert');
            }}
          >
            <Ionicons name="radio-button-on" size={20} color="#ff9800" />
            <Text style={styles.quickActionBtnText}>Alle aktivieren</Text>
          </TouchableOpacity>
        </View>

        {/* Kanal-Liste */}
        <FlatList
          data={channels}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.channelList}
          renderItem={({ item, index }) => (
            <View style={styles.channelManagerCard}>
              <View style={styles.channelCardLeft}>
                <View style={styles.channelNumberBadge}>
                  <Text style={styles.channelNumber}>{index + 1}</Text>
                </View>
                <View style={styles.channelCardInfo}>
                  <Text style={styles.channelManagerName}>{item.name}</Text>
                  <Text style={styles.channelManagerDesc}>{item.description}</Text>
                  <View style={styles.channelStatusRow}>
                    <View style={[styles.statusDot, { backgroundColor: item.is_active ? '#4CAF50' : '#666' }]} />
                    <Text style={styles.channelStatus}>
                      {item.is_active ? 'Aktiv' : 'Inaktiv'}
                    </Text>
                  </View>
                </View>
              </View>
              
              <View style={styles.channelCardActions}>
                <TouchableOpacity
                  style={styles.editChannelBtn}
                  onPress={() => openChannelModal(item)}
                >
                  <Ionicons name="create-outline" size={18} color="#4CAF50" />
                </TouchableOpacity>
                
                <TouchableOpacity
                  style={styles.duplicateChannelBtn}
                  onPress={() => {
                    const newChannel: ChatGroup = {
                      id: Date.now().toString(),
                      name: `${item.name} (Kopie)`,
                      description: item.description,
                      created_by: user?.id || 'admin',
                      members: [],
                      is_active: true,
                      created_at: new Date().toISOString()
                    };
                    setChannels(prev => [...prev, newChannel]);
                    Alert.alert('Erfolg', 'Kanal dupliziert!');
                  }}
                >
                  <Ionicons name="copy-outline" size={18} color="#2196F3" />
                </TouchableOpacity>
                
                <TouchableOpacity
                  style={styles.deleteChannelBtn}
                  onPress={() => deleteChannel(item.id)}
                >
                  <Ionicons name="trash-outline" size={18} color="#ff4444" />
                </TouchableOpacity>
              </View>
            </View>
          )}
          ListEmptyComponent={
            <View style={styles.emptyChannelState}>
              <Ionicons name="radio" size={80} color="#666" />
              <Text style={styles.emptyChannelText}>Keine Kanäle vorhanden</Text>
              <TouchableOpacity
                style={styles.createFirstChannelBtn}
                onPress={() => openChannelModal()}
              >
                <Text style={styles.createFirstChannelText}>Ersten Kanal erstellen</Text>
              </TouchableOpacity>
            </View>
          }
        />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a1a" />
      
      {/* Funkgerät Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle}>📻 FUNKGERÄT</Text>
          <Text style={styles.headerSubtitle}>{getCurrentChannelName()}</Text>
        </View>
        <View style={styles.headerActions}>
          <TouchableOpacity onPress={openAdminProfileModal} style={styles.headerActionButton}>
            <Ionicons name="person-circle" size={24} color="#fff" />
          </TouchableOpacity>
          <TouchableOpacity onPress={() => setShowChannelManager(true)} style={styles.headerActionButton}>
            <Ionicons name="settings" size={24} color="#fff" />
          </TouchableOpacity>
        </View>
      </View>

      {/* Status Bar */}
      <View style={styles.statusBar}>
        <View style={styles.statusIndicator}>
          <View style={[styles.statusDot, { backgroundColor: selectedGroup ? '#4CAF50' : '#ff9800' }]} />
          <Text style={styles.statusText}>
            {selectedGroup ? 'KANAL AKTIV' : 'ALLE KANÄLE'}
          </Text>
        </View>
        <Text style={styles.signalStrength}>📶 Signal: Stark</Text>
      </View>

      {/* Channel Selection mit Switch */}
      <View style={styles.channelSection}>
        <View style={styles.channelSectionHeader}>
          <Text style={styles.channelSectionTitle}>KANÄLE</Text>
          <View style={styles.channelControls}>
            <Text style={styles.channelToggleLabel}>Alle anzeigen</Text>
            <TouchableOpacity
              style={[styles.channelToggle, showAllChannels && styles.channelToggleActive]}
              onPress={() => setShowAllChannels(!showAllChannels)}
            >
              <View style={[styles.channelToggleThumb, showAllChannels && styles.channelToggleThumbActive]} />
            </TouchableOpacity>
          </View>
        </View>
        
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.channelScroll}>
          <TouchableOpacity
            style={[styles.channelButton, !selectedGroup && styles.activeChannelButton]}
            onPress={() => setSelectedGroup(null)}
          >
            <Text style={[styles.channelButtonText, !selectedGroup && styles.activeChannelButtonText]}>
              ALLE
            </Text>
          </TouchableOpacity>
          {channels.slice(0, showAllChannels ? channels.length : 3).map((channel) => (
            <TouchableOpacity
              key={channel.id}
              style={[styles.channelButton, selectedGroup === channel.id && styles.activeChannelButton]}
              onPress={() => setSelectedGroup(channel.id)}
            >
              <Text style={[styles.channelButtonText, selectedGroup === channel.id && styles.activeChannelButtonText]}>
                {channel.name}
              </Text>
              <Text style={[styles.channelButtonDesc, selectedGroup === channel.id && styles.activeChannelButtonDesc]}>
                {channel.description}
              </Text>
            </TouchableOpacity>
          ))}
          {!showAllChannels && channels.length > 3 && (
            <TouchableOpacity
              style={styles.moreChannelsButton}
              onPress={() => setShowAllChannels(true)}
            >
              <Text style={styles.moreChannelsText}>+{channels.length - 3}</Text>
            </TouchableOpacity>
          )}
        </ScrollView>
      </View>

      {/* 📻 Kanal-Verwaltung Sektion */}
      <View style={styles.channelManagementSection}>
        <TouchableOpacity
          style={styles.channelManagementButton}
          onPress={() => setShowChannelManager(true)}
        >
          <Ionicons name="radio" size={20} color="#fff" />
          <Text style={styles.channelManagementText}>📻 Kanal-Verwaltung</Text>
          <View style={styles.channelManagementBadge}>
            <Text style={styles.channelManagementBadgeText}>{channels.length}</Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color="#888" />
        </TouchableOpacity>
        
        <View style={styles.quickChannelActions}>
          <TouchableOpacity
            style={styles.quickActionButton}
            onPress={() => openChannelModal()}
          >
            <Ionicons name="add" size={16} color="#4CAF50" />
            <Text style={styles.quickActionText}>Hinzufügen</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Messages */}
      <FlatList
        ref={flatListRef}
        data={messages}
        renderItem={renderMessage}
        keyExtractor={(item) => item.id}
        style={styles.messagesList}
        contentContainerStyle={styles.messagesContainer}
        showsVerticalScrollIndicator={false}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Ionicons name="radio" size={80} color="#666" />
            <Text style={styles.emptyText}>Noch keine Nachrichten</Text>
            <Text style={styles.emptySubtext}>
              {selectedGroup ? `in ${getCurrentChannelName()}` : 'in allen Kanälen'}
            </Text>
          </View>
        }
      />

      {/* Funkgerät Input Area */}
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.inputContainer}
      >
        <View style={styles.inputRow}>
          <TextInput
            style={styles.textInput}
            value={newMessage}
            onChangeText={setNewMessage}
            placeholder="Funkspruch eingeben..."
            placeholderTextColor="#666"
            multiline
            maxLength={500}
          />
          
          <TouchableOpacity
            style={[styles.voiceButton, isRecording && styles.voiceButtonActive]}
            onPress={isRecording ? stopVoiceRecording : startVoiceRecording}
          >
            <Ionicons 
              name={isRecording ? 'stop' : 'mic'} 
              size={24} 
              color={isRecording ? '#fff' : '#ff4444'} 
            />
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.sendButton, !newMessage.trim() && styles.sendButtonDisabled]}
            onPress={sendMessage}
            disabled={!newMessage.trim()}
          >
            <Ionicons name="send" size={24} color="#fff" />
          </TouchableOpacity>
        </View>
        
        {isRecording && (
          <View style={styles.recordingIndicator}>
            <View style={styles.recordingDot} />
            <Text style={styles.recordingText}>Aufnahme läuft...</Text>
          </View>
        )}
      </KeyboardAvoidingView>

      {/* Channel Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={channelModalVisible}
        onRequestClose={() => setChannelModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <TouchableOpacity onPress={() => setChannelModalVisible(false)}>
                <Text style={styles.cancelButton}>Abbrechen</Text>
              </TouchableOpacity>
              <Text style={styles.modalTitle}>
                📻 {editingChannel ? 'Kanal bearbeiten' : 'Neuer Kanal'}
              </Text>
              <TouchableOpacity onPress={saveChannel}>
                <Text style={styles.saveButton}>Speichern</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.modalForm}>
              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Kanal-Name *</Text>
                <TextInput
                  style={styles.textModalInput}
                  value={channelForm.name}
                  onChangeText={(text) => setChannelForm({ ...channelForm, name: text })}
                  placeholder="z.B. Kanal 7"
                  placeholderTextColor="#666"
                  maxLength={20}
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Beschreibung</Text>
                <TextInput
                  style={styles.textModalInput}
                  value={channelForm.description}
                  onChangeText={(text) => setChannelForm({ ...channelForm, description: text })}
                  placeholder="z.B. Spezialeinsatz"
                  placeholderTextColor="#666"
                  maxLength={50}
                />
              </View>

              {editingChannel && (
                <TouchableOpacity 
                  style={styles.deleteButton}
                  onPress={() => {
                    setChannelModalVisible(false);
                    deleteChannel(editingChannel.id);
                  }}
                >
                  <Ionicons name="trash" size={20} color="#fff" />
                  <Text style={styles.deleteButtonText}>Kanal löschen</Text>
                </TouchableOpacity>
              )}
            </View>
          </View>
        </View>
      </Modal>
      {/* Admin Profile Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={adminProfileModalVisible}
        onRequestClose={() => setAdminProfileModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <TouchableOpacity onPress={() => setAdminProfileModalVisible(false)}>
                <Text style={styles.cancelButton}>Abbrechen</Text>
              </TouchableOpacity>
              <Text style={styles.modalTitle}>👤 Admin Profil</Text>
              <TouchableOpacity onPress={saveAdminProfile}>
                <Text style={styles.saveButton}>Speichern</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.modalForm}>
              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Anzeigename *</Text>
                <TextInput
                  style={styles.textModalInput}
                  value={adminName}
                  onChangeText={setAdminName}
                  placeholder="Ihr Name im Chat"
                  placeholderTextColor="#666"
                  maxLength={50}
                />
              </View>
              
              <Text style={styles.profileHint}>
                Dieser Name wird in Chat-Nachrichten angezeigt
              </Text>
            </View>
          </View>
        </View>
      </Modal>
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
    backgroundColor: '#2a2a2a',
    borderBottomWidth: 1,
    borderBottomColor: '#ff4444',
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerActionButton: {
    marginLeft: 15,
    padding: 5,
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    letterSpacing: 1,
  },
  headerSubtitle: {
    fontSize: 12,
    color: '#888',
    marginTop: 2,
  },
  statusBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 8,
    backgroundColor: '#333',
  },
  statusIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  statusText: {
    fontSize: 12,
    color: '#fff',
    fontWeight: '600',
  },
  signalStrength: {
    fontSize: 12,
    color: '#888',
  },
  channelSection: {
    backgroundColor: '#2a2a2a',
    paddingVertical: 12,
  },
  channelSectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    marginBottom: 8,
  },
  channelSectionTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#ff4444',
    letterSpacing: 1,
  },
  channelControls: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  channelToggleLabel: {
    fontSize: 12,
    color: '#888',
  },
  channelToggle: {
    width: 40,
    height: 20,
    backgroundColor: '#333',
    borderRadius: 10,
    justifyContent: 'center',
    paddingHorizontal: 2,
  },
  channelToggleActive: {
    backgroundColor: '#ff4444',
  },
  channelToggleThumb: {
    width: 16,
    height: 16,
    backgroundColor: '#666',
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  channelToggleThumbActive: {
    backgroundColor: '#fff',
    alignSelf: 'flex-end',
  },
  moreChannelsButton: {
    backgroundColor: '#333',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    marginHorizontal: 4,
    minWidth: 60,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#ff4444',
    borderStyle: 'dashed',
  },
  moreChannelsText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#ff4444',
  },
  channelManagementSection: {
    backgroundColor: '#2a2a2a',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  channelManagementButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#333',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    marginBottom: 8,
  },
  channelManagementText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
    marginLeft: 8,
    flex: 1,
  },
  channelManagementBadge: {
    backgroundColor: '#ff4444',
    borderRadius: 10,
    paddingHorizontal: 8,
    paddingVertical: 2,
    marginRight: 8,
  },
  channelManagementBadgeText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#fff',
  },
  quickChannelActions: {
    flexDirection: 'row',
    gap: 8,
  },
  quickActionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#4CAF50',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    gap: 4,
  },
  quickActionText: {
    fontSize: 12,
    color: '#fff',
    fontWeight: '600',
  },
  // Kanal-Verwaltung Styles
  managementStats: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 16,
    gap: 12,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#2a2a2a',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#333',
  },
  statCardNumber: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#ff4444',
  },
  statCardLabel: {
    fontSize: 10,
    color: '#888',
    marginTop: 4,
    textAlign: 'center',
  },
  quickActionsBar: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingBottom: 16,
    gap: 12,
  },
  quickActionBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#333',
    paddingVertical: 10,
    borderRadius: 8,
    gap: 6,
  },
  quickActionBtnText: {
    fontSize: 12,
    color: '#fff',
    fontWeight: '600',
  },
  channelManagerCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#333',
  },
  channelCardLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  channelNumberBadge: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#ff4444',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  channelNumber: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#fff',
  },
  channelCardInfo: {
    flex: 1,
  },
  channelStatusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
    gap: 4,
  },
  channelStatus: {
    fontSize: 12,
    color: '#888',
  },
  channelCardActions: {
    flexDirection: 'row',
    gap: 8,
  },
  duplicateChannelBtn: {
    backgroundColor: '#2196F3',
    padding: 8,
    borderRadius: 8,
  },
  emptyChannelState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 100,
  },
  emptyChannelText: {
    fontSize: 18,
    color: '#666',
    marginTop: 16,
    textAlign: 'center',
  },
  createFirstChannelBtn: {
    backgroundColor: '#ff4444',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    marginTop: 16,
  },
  createFirstChannelText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  channelScroll: {
    paddingHorizontal: 16,
  },
  channelButton: {
    backgroundColor: '#333',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    marginHorizontal: 4,
    minWidth: 80,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#444',
  },
  activeChannelButton: {
    backgroundColor: '#ff4444',
    borderColor: '#ff6666',
  },
  channelButtonText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#888',
  },
  activeChannelButtonText: {
    color: '#fff',
  },
  channelButtonDesc: {
    fontSize: 10,
    color: '#666',
    marginTop: 2,
  },
  activeChannelButtonDesc: {
    color: '#ffdddd',
  },
  messagesList: {
    flex: 1,
  },
  messagesContainer: {
    padding: 16,
    flexGrow: 1,
  },
  messageContainer: {
    marginBottom: 12,
    alignItems: 'flex-start',
  },
  ownMessageContainer: {
    alignItems: 'flex-end',
  },
  messageBubble: {
    backgroundColor: '#333',
    borderRadius: 16,
    padding: 12,
    maxWidth: '80%',
    borderBottomLeftRadius: 4,
  },
  ownMessageBubble: {
    backgroundColor: '#ff4444',
    borderBottomLeftRadius: 16,
    borderBottomRightRadius: 4,
  },
  senderName: {
    fontSize: 12,
    color: '#ff4444',
    fontWeight: '600',
    marginBottom: 4,
  },
  messageText: {
    fontSize: 16,
    color: '#fff',
    lineHeight: 20,
  },
  ownMessageText: {
    color: '#fff',
  },
  voiceMessage: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  playButton: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    borderRadius: 12,
    padding: 4,
  },
  messageTime: {
    fontSize: 11,
    color: '#888',
    marginTop: 4,
  },
  ownMessageTime: {
    color: '#ddd',
  },
  inputContainer: {
    borderTopWidth: 1,
    borderTopColor: '#333',
    backgroundColor: '#2a2a2a',
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 8,
  },
  textInput: {
    flex: 1,
    backgroundColor: '#333',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 16,
    color: '#fff',
    maxHeight: 100,
    borderWidth: 1,
    borderColor: '#444',
  },
  voiceButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#333',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#ff4444',
  },
  voiceButtonActive: {
    backgroundColor: '#ff4444',
    borderColor: '#fff',
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#ff4444',
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: '#666',
  },
  recordingIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    gap: 8,
  },
  recordingDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#ff4444',
  },
  recordingText: {
    fontSize: 14,
    color: '#ff4444',
    fontWeight: '600',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 100,
  },
  emptyText: {
    fontSize: 18,
    color: '#666',
    marginTop: 16,
    textAlign: 'center',
  },
  emptySubtext: {
    fontSize: 14,
    color: '#888',
    marginTop: 8,
    textAlign: 'center',
  },
  // Channel Manager Styles
  channelList: {
    padding: 20,
  },
  channelManagerCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#333',
  },
  channelInfo: {
    flex: 1,
  },
  channelManagerName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  channelManagerDesc: {
    fontSize: 14,
    color: '#888',
    marginTop: 4,
  },
  channelActions: {
    flexDirection: 'row',
    gap: 8,
  },
  editChannelBtn: {
    backgroundColor: '#4CAF50',
    padding: 8,
    borderRadius: 8,
  },
  deleteChannelBtn: {
    backgroundColor: '#ff4444',
    padding: 8,
    borderRadius: 8,
  },
  // Modal Styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#1a1a1a',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '60%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  cancelButton: {
    fontSize: 16,
    color: '#888',
  },
  saveButton: {
    fontSize: 16,
    color: '#ff4444',
    fontWeight: '600',
  },
  modalForm: {
    padding: 20,
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
  textModalInput: {
    backgroundColor: '#2a2a2a',
    borderRadius: 8,
    padding: 16,
    fontSize: 16,
    color: '#fff',
    borderWidth: 1,
    borderColor: '#333',
  },
  deleteButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#ff4444',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    marginTop: 20,
  },
  deleteButtonText: {
    color: '#fff',
    fontSize: 16,
    profileHint: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
    marginTop: 10,
    fontStyle: 'italic',
  },
  textModalInput: {
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#333',
    borderWidth: 1,
    borderColor: '#ddd',
  },
});