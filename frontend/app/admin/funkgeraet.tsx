import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  Alert,
  Modal,
  StyleSheet,
  SafeAreaView,
  Dimensions,
  ActivityIndicator,
  Platform
} from 'react-native';
import { Ionicons, MaterialIcons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useAuth } from '../../contexts/AuthContext';
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';

const { width } = Dimensions.get('window');
const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'https://emergency-sos-3.preview.emergentagent.com';

interface ChatGroup {
  id: string;
  name: string;
  description: string;
  created_by: string;
  members: string[];
  is_active: boolean;
  created_at: string;
}

interface ChatMessage {
  id: string;
  user_id: string;
  username: string;
  message: string;
  chat_type: string;
  group_id?: string | null;
  is_voice_message: boolean;
  voice_data?: string;
  voice_duration?: number;
  created_at: string;
}

export default function FunkgeraetScreen() {
  const { user, token } = useAuth();
  const flatListRef = useRef<FlatList>(null);

  // States
  const [selectedGroup, setSelectedGroup] = useState<string | null>(null);
  const [newMessage, setNewMessage] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [channels, setChannels] = useState<ChatGroup[]>([]);
  const [loading, setLoading] = useState(false);

  // Voice recording states
  const [isRecordingVoice, setIsRecordingVoice] = useState(false);
  const [recordingUri, setRecordingUri] = useState<string | null>(null);
  const [voiceRecording, setVoiceRecording] = useState<Audio.Recording | null>(null);
  const [playingMessageId, setPlayingMessageId] = useState<string | null>(null);

  // Message management states
  const [editingMessage, setEditingMessage] = useState<ChatMessage | null>(null);
  const [editMessageModalVisible, setEditMessageModalVisible] = useState(false);
  const [editMessageText, setEditMessageText] = useState('');

  // Modal states
  const [showChannelManager, setShowChannelManager] = useState(false);
  const [channelModalVisible, setChannelModalVisible] = useState(false);
  const [editingChannel, setEditingChannel] = useState<ChatGroup | null>(null);
  const [adminProfileModalVisible, setAdminProfileModalVisible] = useState(false);
  const [adminName, setAdminName] = useState('');

  const [channelForm, setChannelForm] = useState({
    name: '',
    description: ''
  });

  useEffect(() => {
    loadChannels();
    loadMessages();
  }, []);

  useEffect(() => {
    loadMessages();
  }, [selectedGroup]);

  // BACKEND INTEGRATION FUNCTIONS
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
        setChannels([
          { id: '1', name: 'Einsatzleitung', description: 'Hauptkoordination', created_by: 'admin', members: [], is_active: true, created_at: new Date().toISOString() },
          { id: '2', name: 'Rettungsdienst', description: 'Rettungskräfte', created_by: 'admin', members: [], is_active: true, created_at: new Date().toISOString() },
          { id: '3', name: 'Feuerwehr', description: 'Feuerwehreinsätze', created_by: 'admin', members: [], is_active: true, created_at: new Date().toISOString() },
          { id: '4', name: 'Polizei', description: 'Polizeieinsätze', created_by: 'admin', members: [], is_active: true, created_at: new Date().toISOString() },
        ]);
      }
    } catch (error) {
      console.error('Error loading channels:', error);
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
        const demoMessages: ChatMessage[] = [
          {
            id: '1',
            user_id: user?.id || '1',
            username: 'Einsatzleiter Schmidt',
            message: 'Alle Einheiten, Status-Update erforderlich',
            chat_type: 'admin',
            group_id: selectedGroup,
            is_voice_message: false,
            created_at: new Date(Date.now() - 300000).toISOString()
          }
        ];
        
        const filteredMessages = selectedGroup 
          ? demoMessages.filter(msg => msg.group_id === selectedGroup)
          : demoMessages;
        
        setMessages(filteredMessages);
      }
    } catch (error) {
      console.error('Error loading messages:', error);
    }
  };

  // VOICE RECORDING FUNCTIONS
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
    if (!voiceRecording) return;

    try {
      await voiceRecording.stopAndUnloadAsync();
      const uri = voiceRecording.getURI();
      setRecordingUri(uri);
      setIsRecordingVoice(false);
      setVoiceRecording(null);
    } catch (error) {
      console.error('Failed to stop recording:', error);
      Alert.alert('Fehler', 'Aufnahme konnte nicht gestoppt werden');
    }
  };

  const playVoiceMessage = async (messageId: string, voiceData: string) => {
    try {
      if (playingMessageId === messageId) {
        setPlayingMessageId(null);
        return;
      }

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

  // MESSAGE MANAGEMENT FUNCTIONS
  const editMessage = (message: ChatMessage) => {
    if (message.user_id !== user?.id) {
      Alert.alert('Fehler', 'Sie können nur Ihre eigenen Nachrichten bearbeiten');
      return;
    }
    
    setEditingMessage(message);
    setEditMessageText(message.message);
    setEditMessageModalVisible(true);
  };

  const saveEditedMessage = async () => {
    if (!editingMessage || !editMessageText.trim() || !token) {
      Alert.alert('Fehler', 'Bitte geben Sie eine Nachricht ein');
      return;
    }

    setLoading(true);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/chat/${editingMessage.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ message: editMessageText })
      });

      if (response.ok) {
        // Update local messages
        setMessages(prev => prev.map(msg => 
          msg.id === editingMessage.id 
            ? { ...msg, message: editMessageText }
            : msg
        ));
        
        setEditMessageModalVisible(false);
        setEditingMessage(null);
        setEditMessageText('');
        Alert.alert('Erfolg', 'Nachricht wurde aktualisiert!');
      } else {
        Alert.alert('Fehler', 'Nachricht konnte nicht aktualisiert werden');
      }
    } catch (error) {
      console.error('Error editing message:', error);
      Alert.alert('Fehler', 'Fehler beim Bearbeiten der Nachricht');
    } finally {
      setLoading(false);
    }
  };

  const deleteMessage = async (messageId: string, userId: string) => {
    if (userId !== user?.id) {
      Alert.alert('Fehler', 'Sie können nur Ihre eigenen Nachrichten löschen');
      return;
    }

    Alert.alert(
      'Nachricht löschen',
      'Möchten Sie diese Nachricht wirklich löschen?',
      [
        { text: 'Abbrechen', style: 'cancel' },
        {
          text: 'Löschen',
          style: 'destructive',
          onPress: async () => {
            setLoading(true);
            
            try {
              const response = await fetch(`${BACKEND_URL}/api/admin/chat/${messageId}`, {
                method: 'DELETE',
                headers: {
                  'Authorization': `Bearer ${token}`,
                },
              });

              if (response.ok) {
                // Remove from local messages
                setMessages(prev => prev.filter(msg => msg.id !== messageId));
                Alert.alert('Erfolg', 'Nachricht wurde gelöscht!');
              } else {
                Alert.alert('Fehler', 'Nachricht konnte nicht gelöscht werden');
              }
            } catch (error) {
              console.error('Error deleting message:', error);
              Alert.alert('Fehler', 'Fehler beim Löschen der Nachricht');
            } finally {
              setLoading(false);
            }
          }
        }
      ]
    );
  };

  // SEND MESSAGE FUNCTIONS
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
        
        setTimeout(() => {
          flatListRef.current?.scrollToEnd({ animated: true });
        }, 100);
      } else {
        Alert.alert('Fehler', 'Nachricht konnte nicht gesendet werden');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      Alert.alert('Fehler', 'Fehler beim Senden der Nachricht');
    } finally {
      setLoading(false);
    }
  };

  const sendVoiceMessage = async () => {
    if (!recordingUri || !token) return;

    setLoading(true);
    
    try {
      const audioBase64 = await FileSystem.readAsStringAsync(recordingUri, {
        encoding: FileSystem.EncodingType.Base64,
      });

      const messageData = {
        message: 'Sprachnachricht',
        chat_type: 'admin',
        group_id: selectedGroup,
        is_voice_message: true,
        voice_data: audioBase64,
        voice_duration: 5 // Placeholder
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
        const newMsg: ChatMessage = {
          id: Date.now().toString(),
          user_id: user?.id || '1',
          username: user?.full_name || 'Admin',
          message: 'Sprachnachricht',
          chat_type: 'admin',
          group_id: selectedGroup,
          is_voice_message: true,
          voice_data: audioBase64,
          voice_duration: 5,
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

  // CHANNEL MANAGEMENT FUNCTIONS
  const saveChannel = async () => {
    if (!channelForm.name.trim() || !token) {
      Alert.alert('Fehler', 'Bitte geben Sie einen Kanal-Namen ein');
      return;
    }

    setLoading(true);
    
    try {
      if (editingChannel) {
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
      setChannelForm({ name: '', description: '' });
      setEditingChannel(null);
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

  const editChannel = (channel: ChatGroup) => {
    setEditingChannel(channel);
    setChannelForm({
      name: channel.name,
      description: channel.description
    });
    setChannelModalVisible(true);
  };

  const openAdminProfileModal = () => {
    setAdminName(user?.full_name || '');
    setAdminProfileModalVisible(true);
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

  // RENDER FUNCTIONS
  const renderMessage = ({ item }: { item: ChatMessage }) => {
    const isOwnMessage = item.user_id === user?.id;
    const messageTime = new Date(item.created_at).toLocaleTimeString('de-DE', {
      hour: '2-digit',
      minute: '2-digit'
    });

    return (
      <View style={[
        styles.messageContainer,
        isOwnMessage ? styles.ownMessage : styles.otherMessage
      ]}>
        <View style={styles.messageHeader}>
          <Text style={styles.senderName}>{item.username}</Text>
          <Text style={styles.messageTime}>{messageTime}</Text>
        </View>
        
        {item.is_voice_message ? (
          <View style={styles.voiceMessageContainer}>
            <TouchableOpacity
              style={styles.playButton}
              onPress={() => item.voice_data && playVoiceMessage(item.id, item.voice_data)}
            >
              <Ionicons 
                name={playingMessageId === item.id ? "pause" : "play"} 
                size={20} 
                color="#fff" 
              />
            </TouchableOpacity>
            <Text style={styles.voiceMessageText}>
              Sprachnachricht ({item.voice_duration || 0}s)
            </Text>
            
            {/* Voice Message Actions */}
            {isOwnMessage && (
              <View style={styles.messageActions}>
                <TouchableOpacity
                  style={styles.deleteMessageButton}
                  onPress={() => deleteMessage(item.id, item.user_id)}
                >
                  <Ionicons name="trash" size={16} color="#fff" />
                </TouchableOpacity>
              </View>
            )}
          </View>
        ) : (
          <View>
            <Text style={styles.messageText}>{item.message}</Text>
            
            {/* Text Message Actions */}
            {isOwnMessage && (
              <View style={styles.messageActions}>
                <TouchableOpacity
                  style={styles.editMessageButton}
                  onPress={() => editMessage(item)}
                >
                  <Ionicons name="pencil" size={16} color="#fff" />
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.deleteMessageButton}
                  onPress={() => deleteMessage(item.id, item.user_id)}
                >
                  <Ionicons name="trash" size={16} color="#fff" />
                </TouchableOpacity>
              </View>
            )}
          </View>
        )}
      </View>
    );
  };

  const renderChannel = ({ item }: { item: ChatGroup }) => (
    <View style={styles.channelRow}>
      <TouchableOpacity
        style={[
          styles.channelButton,
          selectedGroup === item.id && styles.selectedChannel
        ]}
        onPress={() => setSelectedGroup(item.id)}
      >
        <View style={styles.channelContent}>
          <Text style={styles.channelName}>{item.name}</Text>
          <Text style={styles.channelDescription}>{item.description}</Text>
        </View>
      </TouchableOpacity>
      
      <View style={styles.channelActions}>
        <TouchableOpacity
          style={[styles.actionButton, styles.editButton]}
          onPress={() => editChannel(item)}
        >
          <Ionicons name="pencil" size={16} color="#fff" />
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.actionButton, styles.deleteButton]}
          onPress={() => deleteChannel(item.id)}
        >
          <Ionicons name="trash" size={16} color="#fff" />
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle}>📻 Funkgerät</Text>
          {selectedGroup && (
            <Text style={styles.selectedChannelText}>
              {channels.find(c => c.id === selectedGroup)?.name || 'Kanal'}
            </Text>
          )}
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

      {/* Main Content */}
      {selectedGroup ? (
        <View style={styles.chatArea}>
          {/* Messages */}
          <FlatList
            ref={flatListRef}
            data={messages}
            renderItem={renderMessage}
            keyExtractor={(item) => item.id}
            style={styles.messagesList}
            showsVerticalScrollIndicator={false}
          />

          {/* Recording UI */}
          {recordingUri && (
            <View style={styles.recordingPreview}>
              <Text style={styles.recordingText}>Sprachnachricht aufgenommen</Text>
              <View style={styles.recordingActions}>
                <TouchableOpacity 
                  style={styles.discardButton}
                  onPress={() => setRecordingUri(null)}
                >
                  <Ionicons name="trash" size={20} color="#fff" />
                </TouchableOpacity>
                <TouchableOpacity 
                  style={styles.sendVoiceButton}
                  onPress={sendVoiceMessage}
                  disabled={loading}
                >
                  <Ionicons name="send" size={20} color="#fff" />
                </TouchableOpacity>
              </View>
            </View>
          )}

          {/* Input Area */}
          <View style={styles.inputContainer}>
            <TextInput
              style={styles.textInput}
              value={newMessage}
              onChangeText={setNewMessage}
              placeholder="Nachricht eingeben..."
              placeholderTextColor="#666"
              multiline
              maxLength={500}
            />
            
            <TouchableOpacity
              style={styles.voiceButton}
              onPressIn={startRecording}
              onPressOut={stopRecording}
              disabled={loading}
            >
              <MaterialIcons 
                name={isRecordingVoice ? "stop" : "mic"} 
                size={24} 
                color={isRecordingVoice ? "#ff4444" : "#fff"} 
              />
            </TouchableOpacity>
            
            <TouchableOpacity
              style={styles.sendButton}
              onPress={sendMessage}
              disabled={loading || !newMessage.trim()}
            >
              {loading ? (
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <Ionicons name="send" size={20} color="#fff" />
              )}
            </TouchableOpacity>
          </View>
        </View>
      ) : (
        <View style={styles.noChannelSelected}>
          <Ionicons name="radio" size={80} color="#666" />
          <Text style={styles.noChannelText}>Wählen Sie einen Kanal aus</Text>
          <TouchableOpacity
            style={styles.manageChannelsButton}
            onPress={() => setShowChannelManager(true)}
          >
            <Text style={styles.manageChannelsText}>Kanäle verwalten</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Channel Manager Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={showChannelManager}
        onRequestClose={() => setShowChannelManager(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.channelManagerModal}>
            <View style={styles.modalHeader}>
              <TouchableOpacity onPress={() => setShowChannelManager(false)}>
                <Text style={styles.cancelButton}>Schließen</Text>
              </TouchableOpacity>
              <Text style={styles.modalTitle}>📻 Kanal-Verwaltung</Text>
              <TouchableOpacity onPress={() => {
                setEditingChannel(null);
                setChannelForm({ name: '', description: '' });
                setChannelModalVisible(true);
              }}>
                <Text style={styles.addButton}>+ Neu</Text>
              </TouchableOpacity>
            </View>

            <FlatList
              data={channels}
              renderItem={renderChannel}
              keyExtractor={(item) => item.id}
              style={styles.channelsList}
            />
          </View>
        </View>
      </Modal>

      {/* Channel Create/Edit Modal */}
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
                {editingChannel ? '✏️ Kanal bearbeiten' : '➕ Neuer Kanal'}
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
                  onChangeText={(text) => setChannelForm(prev => ({ ...prev, name: text }))}
                  placeholder="z.B. Einsatzleitung"
                  placeholderTextColor="#666"
                  maxLength={50}
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Beschreibung</Text>
                <TextInput
                  style={styles.textModalInput}
                  value={channelForm.description}
                  onChangeText={(text) => setChannelForm(prev => ({ ...prev, description: text }))}
                  placeholder="Beschreibung des Kanals"
                  placeholderTextColor="#666"
                  maxLength={100}
                />
              </View>
            </View>
          </View>
        </View>
      </Modal>

      {/* Edit Message Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={editMessageModalVisible}
        onRequestClose={() => setEditMessageModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <TouchableOpacity onPress={() => setEditMessageModalVisible(false)}>
                <Text style={styles.cancelButton}>Abbrechen</Text>
              </TouchableOpacity>
              <Text style={styles.modalTitle}>✏️ Nachricht bearbeiten</Text>
              <TouchableOpacity onPress={saveEditedMessage}>
                <Text style={styles.saveButton}>Speichern</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.modalForm}>
              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Nachricht *</Text>
                <TextInput
                  style={styles.textModalInput}
                  value={editMessageText}
                  onChangeText={setEditMessageText}
                  placeholder="Nachricht eingeben..."
                  placeholderTextColor="#666"
                  multiline
                  maxLength={500}
                />
              </View>
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
    backgroundColor: '#c41e3a',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#a01527',
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
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  selectedChannelText: {
    color: '#ffcccc',
    fontSize: 12,
  },
  chatArea: {
    flex: 1,
  },
  messagesList: {
    flex: 1,
    paddingHorizontal: 15,
    paddingVertical: 10,
  },
  messageContainer: {
    marginVertical: 4,
    padding: 12,
    borderRadius: 12,
    maxWidth: '80%',
  },
  ownMessage: {
    backgroundColor: '#c41e3a',
    alignSelf: 'flex-end',
  },
  otherMessage: {
    backgroundColor: '#333',
    alignSelf: 'flex-start',
  },
  messageHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  senderName: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  messageTime: {
    color: '#ccc',
    fontSize: 10,
  },
  messageText: {
    color: '#fff',
    fontSize: 14,
  },
  voiceMessageContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  playButton: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    borderRadius: 15,
    width: 30,
    height: 30,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 10,
  },
  voiceMessageText: {
    color: '#fff',
    fontSize: 14,
  },
  messageActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: 8,
    gap: 8,
  },
  editMessageButton: {
    backgroundColor: '#007bff',
    borderRadius: 12,
    width: 24,
    height: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  deleteMessageButton: {
    backgroundColor: '#dc3545',
    borderRadius: 12,
    width: 24,
    height: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 15,
    backgroundColor: '#2a2a2a',
    borderTopWidth: 1,
    borderTopColor: '#444',
  },
  textInput: {
    flex: 1,
    backgroundColor: '#333',
    borderRadius: 20,
    paddingHorizontal: 15,
    paddingVertical: 10,
    marginRight: 10,
    color: '#fff',
    maxHeight: 100,
  },
  voiceButton: {
    backgroundColor: '#666',
    borderRadius: 20,
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 10,
  },
  sendButton: {
    backgroundColor: '#c41e3a',
    borderRadius: 20,
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  recordingPreview: {
    backgroundColor: '#444',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 15,
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: '#555',
  },
  recordingText: {
    color: '#fff',
    fontSize: 14,
  },
  recordingActions: {
    flexDirection: 'row',
  },
  discardButton: {
    backgroundColor: '#666',
    borderRadius: 15,
    width: 30,
    height: 30,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 10,
  },
  sendVoiceButton: {
    backgroundColor: '#c41e3a',
    borderRadius: 15,
    width: 30,
    height: 30,
    justifyContent: 'center',
    alignItems: 'center',
  },
  noChannelSelected: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  noChannelText: {
    color: '#666',
    fontSize: 18,
    marginTop: 20,
    textAlign: 'center',
  },
  manageChannelsButton: {
    backgroundColor: '#c41e3a',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 25,
    marginTop: 30,
  },
  manageChannelsText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  channelManagerModal: {
    width: width * 0.9,
    maxHeight: '80%',
    backgroundColor: '#2a2a2a',
    borderRadius: 20,
    padding: 20,
  },
  modalContent: {
    width: width * 0.9,
    backgroundColor: '#2a2a2a',
    borderRadius: 20,
    padding: 20,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  cancelButton: {
    color: '#666',
    fontSize: 16,
  },
  addButton: {
    color: '#c41e3a',
    fontSize: 16,
    fontWeight: 'bold',
  },
  saveButton: {
    color: '#c41e3a',
    fontSize: 16,
    fontWeight: 'bold',
  },
  channelsList: {
    maxHeight: 400,
  },
  channelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  channelButton: {
    flex: 1,
    backgroundColor: '#333',
    padding: 15,
    borderRadius: 10,
    marginRight: 10,
  },
  selectedChannel: {
    backgroundColor: '#c41e3a',
  },
  channelContent: {
    flex: 1,
  },
  channelName: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  channelDescription: {
    color: '#ccc',
    fontSize: 12,
    marginTop: 2,
  },
  channelActions: {
    flexDirection: 'row',
  },
  actionButton: {
    borderRadius: 15,
    width: 30,
    height: 30,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 5,
  },
  editButton: {
    backgroundColor: '#007bff', // Blau für bearbeiten
  },
  deleteButton: {
    backgroundColor: '#dc3545', // Rot für löschen
  },
  modalForm: {
    gap: 15,
  },
  inputGroup: {
    gap: 8,
  },
  inputLabel: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
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
  profileHint: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
    marginTop: 10,
    fontStyle: 'italic',
  },
});