import React, { useState, useEffect } from 'react';
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

interface ChatMessage {
  id: string;
  user_id: string;
  username: string;
  message: string;
  group_id?: string;
  is_voice_message: boolean;
  created_at: string;
}

interface ChatGroup {
  id: string;
  name: string;
  description?: string;
  members: string[];
}

export default function Funkgeraet() {
  const { user, isAdmin } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [selectedGroup, setSelectedGroup] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [adminName, setAdminName] = useState(user?.full_name || 'Admin');
  
  // Funktionierende Gruppen (ohne API-Abhängigkeiten)
  const [groups, setGroups] = useState<ChatGroup[]>([
    { id: '1', name: 'Einsatzleitung', description: 'Hauptkommunikation', members: [] },
    { id: '2', name: 'Rettungsdienst', description: 'Rettungskräfte', members: [] },
    { id: '3', name: 'Feuerwehr', description: 'Feuerwehr-Kommunikation', members: [] },
    { id: '4', name: 'Polizei', description: 'Polizei-Kommunikation', members: [] }
  ]);

  // Modal states
  const [groupModalVisible, setGroupModalVisible] = useState(false);
  const [editingGroup, setEditingGroup] = useState<ChatGroup | null>(null);
  const [groupForm, setGroupForm] = useState({ name: '', description: '' });
  const [profileModalVisible, setProfileModalVisible] = useState(false);
  const [newDisplayName, setNewDisplayName] = useState(adminName);

  useEffect(() => {
    if (!isAdmin()) {
      Alert.alert('Zugriff verweigert', 'Sie haben keine Berechtigung für diesen Bereich');
      router.replace('/');
      return;
    }
  }, []);

  const sendMessage = async () => {
    if (!newMessage.trim()) {
      Alert.alert('Fehler', 'Bitte geben Sie eine Nachricht ein');
      return;
    }

    const newMsg: ChatMessage = {
      id: Date.now().toString(),
      user_id: user?.id || '1',
      username: adminName,
      message: newMessage,
      group_id: selectedGroup,
      is_voice_message: false,
      created_at: new Date().toISOString()
    };

    setMessages(prev => [...prev, newMsg]);
    setNewMessage('');
    
    Alert.alert('Erfolg', 'Nachricht gesendet!');
  };

  const startVoiceRecording = () => {
    setIsRecording(true);
    
    // Simuliere Sprachaufnahme
    setTimeout(() => {
      setIsRecording(false);
      
      const voiceMsg: ChatMessage = {
        id: Date.now().toString(),
        user_id: user?.id || '1',
        username: adminName,
        message: 'Sprach-Nachricht',
        group_id: selectedGroup,
        is_voice_message: true,
        created_at: new Date().toISOString()
      };

      setMessages(prev => [...prev, voiceMsg]);
      Alert.alert('Erfolg', 'Sprach-Nachricht gesendet!');
    }, 2000);
  };

  const openGroupModal = (group?: ChatGroup) => {
    if (group) {
      setEditingGroup(group);
      setGroupForm({ name: group.name, description: group.description || '' });
    } else {
      setEditingGroup(null);
      setGroupForm({ name: '', description: '' });
    }
    setGroupModalVisible(true);
  };

  const saveGroup = () => {
    if (!groupForm.name.trim()) {
      Alert.alert('Fehler', 'Bitte geben Sie einen Gruppennamen ein');
      return;
    }

    if (editingGroup) {
      // Bearbeiten
      setGroups(prev => prev.map(g => 
        g.id === editingGroup.id 
          ? { ...g, name: groupForm.name, description: groupForm.description }
          : g
      ));
      Alert.alert('Erfolg', 'Gruppe wurde aktualisiert!');
    } else {
      // Neu erstellen
      const newGroup: ChatGroup = {
        id: Date.now().toString(),
        name: groupForm.name,
        description: groupForm.description,
        members: []
      };
      setGroups(prev => [...prev, newGroup]);
      Alert.alert('Erfolg', 'Neue Gruppe wurde erstellt!');
    }

    setGroupModalVisible(false);
  };

  const deleteGroup = (groupId: string) => {
    Alert.alert(
      'Gruppe löschen',
      'Möchten Sie diese Gruppe wirklich löschen?',
      [
        { text: 'Abbrechen', style: 'cancel' },
        {
          text: 'Löschen',
          style: 'destructive',
          onPress: () => {
            setGroups(prev => prev.filter(g => g.id !== groupId));
            if (selectedGroup === groupId) {
              setSelectedGroup(null);
            }
            Alert.alert('Erfolg', 'Gruppe wurde gelöscht!');
          }
        }
      ]
    );
  };

  const updateProfile = () => {
    if (!newDisplayName.trim()) {
      Alert.alert('Fehler', 'Bitte geben Sie einen Namen ein');
      return;
    }

    setAdminName(newDisplayName);
    setProfileModalVisible(false);
    Alert.alert('Erfolg', 'Anzeigename wurde aktualisiert!');
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
  };

  const getFilteredMessages = () => {
    if (!selectedGroup) return messages;
    return messages.filter(msg => msg.group_id === selectedGroup);
  };

  const currentGroupName = selectedGroup ? groups.find(g => g.id === selectedGroup)?.name : 'Alle Gruppen';

  const renderMessage = ({ item }: { item: ChatMessage }) => {
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

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a1a" />
      
      {/* Header mit verbesserter Navigation */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle}>🔊 Funkgerät</Text>
          <Text style={styles.headerSubtitle}>{currentGroupName}</Text>
        </View>
        <View style={styles.headerActions}>
          <TouchableOpacity 
            onPress={() => setProfileModalVisible(true)}
            style={styles.headerButton}
          >
            <Ionicons name="person" size={20} color="#fff" />
          </TouchableOpacity>
        </View>
      </View>

      {/* NEUE PROMINENTE KANAL-KATEGORIE-SEKTION */}
      <View style={styles.channelCategorySection}>
        <View style={styles.categoryHeader}>
          <View style={styles.categoryTitleContainer}>
            <Ionicons name="radio" size={24} color="#ff4444" />
            <Text style={styles.categoryMainTitle}>KANAL-VERWALTUNG</Text>
          </View>
          <Text style={styles.categorySubtitle}>Funkkanäle erstellen • bearbeiten • löschen</Text>
        </View>
        
        <View style={styles.categoryActions}>
          <TouchableOpacity 
            onPress={() => openGroupModal()}
            style={styles.newChannelMainButton}
          >
            <Ionicons name="add-circle" size={24} color="#fff" />
            <Text style={styles.newChannelMainText}>NEUER KANAL</Text>
            <Ionicons name="chevron-forward" size={20} color="#fff" />
          </TouchableOpacity>
          
          <View style={styles.categoryStats}>
            <View style={styles.statItem}>
              <Text style={styles.statNumber}>{groups.length}</Text>
              <Text style={styles.statLabel}>Kanäle</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statItem}>
              <Text style={styles.statNumber}>{getFilteredMessages().length}</Text>
              <Text style={styles.statLabel}>Nachrichten</Text>
            </View>
          </View>
        </View>
      </View>

      {/* ERWEITERTE KANAL-NAVIGATION MIT MANAGEMENT-FUNKTIONEN */}
      <View style={styles.activeChannelsSection}>
        <Text style={styles.activeChannelsTitle}>📡 AKTIVE FUNKKANÄLE</Text>
        
        <ScrollView horizontal style={styles.channelsScrollContainer} showsHorizontalScrollIndicator={false}>
          {/* Alle Kanäle Button */}
          <TouchableOpacity
            style={[styles.channelCard, !selectedGroup && styles.activeChannelCard]}
            onPress={() => setSelectedGroup(null)}
          >
            <View style={styles.channelCardContent}>
              <Ionicons name="radio" size={20} color={!selectedGroup ? '#fff' : '#888'} />
              <Text style={[styles.channelCardTitle, !selectedGroup && styles.activeChannelCardTitle]}>
                ALLE KANÄLE
              </Text>
              <Text style={[styles.channelCardSubtitle, !selectedGroup && styles.activeChannelCardSubtitle]}>
                Gesamtkommunikation
              </Text>
            </View>
          </TouchableOpacity>

          {/* Individuelle Kanal-Karten */}
          {groups.map((group) => (
            <View key={group.id} style={styles.channelCardWrapper}>
              <TouchableOpacity
                style={[styles.channelCard, selectedGroup === group.id && styles.activeChannelCard]}
                onPress={() => setSelectedGroup(group.id)}
              >
                <View style={styles.channelCardContent}>
                  <Ionicons 
                    name="wifi" 
                    size={20} 
                    color={selectedGroup === group.id ? '#fff' : '#888'} 
                  />
                  <Text style={[styles.channelCardTitle, selectedGroup === group.id && styles.activeChannelCardTitle]}>
                    {group.name.toUpperCase()}
                  </Text>
                  <Text style={[styles.channelCardSubtitle, selectedGroup === group.id && styles.activeChannelCardSubtitle]}>
                    {group.description || 'Funkkanal'}
                  </Text>
                  {selectedGroup === group.id && (
                    <View style={styles.activeIndicator}>
                      <Ionicons name="radio-button-on" size={12} color="#4CAF50" />
                      <Text style={styles.activeText}>AKTIV</Text>
                    </View>
                  )}
                </View>
              </TouchableOpacity>
              
              {/* Kanal-Management-Buttons */}
              <View style={styles.channelManagementButtons}>
                <TouchableOpacity
                  style={styles.editChannelButton}
                  onPress={() => openGroupModal(group)}
                >
                  <Ionicons name="create-outline" size={16} color="#4CAF50" />
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.deleteChannelButton}
                  onPress={() => deleteGroup(group.id)}
                >
                  <Ionicons name="trash-outline" size={16} color="#ff4444" />
                </TouchableOpacity>
              </View>
            </View>
          ))}
          
          {/* Neuer Kanal Schnell-Button */}
          <TouchableOpacity
            style={styles.quickAddChannelCard}
            onPress={() => openGroupModal()}
          >
            <View style={styles.quickAddContent}>
              <Ionicons name="add-circle" size={32} color="#ff4444" />
              <Text style={styles.quickAddText}>NEUER</Text>
              <Text style={styles.quickAddText}>KANAL</Text>
            </View>
          </TouchableOpacity>
        </ScrollView>
      </View>

      {/* Nachrichten */}
      <FlatList
        data={getFilteredMessages()}
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
              Senden Sie die erste Nachricht in {currentGroupName}
            </Text>
          </View>
        }
      />

      {/* Eingabebereich */}
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
            onPress={startVoiceRecording}
            disabled={isRecording}
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
      </KeyboardAvoidingView>

      {/* Kanal/Kategorie Management Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={groupModalVisible}
        onRequestClose={() => setGroupModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <TouchableOpacity onPress={() => setGroupModalVisible(false)}>
                <Text style={styles.cancelButton}>Abbrechen</Text>
              </TouchableOpacity>
              <Text style={styles.modalTitle}>
                📻 {editingGroup ? 'Kanal bearbeiten' : 'Neuer Kanal'}
              </Text>
              <TouchableOpacity onPress={saveGroup}>
                <Text style={styles.saveButton}>Speichern</Text>
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalForm} showsVerticalScrollIndicator={false}>
              <Text style={styles.sectionTitle}>Kanal-Information</Text>
              
              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>🏷️ Kanal-Name *</Text>
                <TextInput
                  style={styles.textModalInput}
                  value={groupForm.name}
                  onChangeText={(text) => setGroupForm({ ...groupForm, name: text })}
                  placeholder="z.B. Einsatzleitung, Rettungsdienst, SEK-Team..."
                  placeholderTextColor="#666"
                  maxLength={50}
                />
                <Text style={styles.helperText}>Eindeutiger Name für diesen Funkkanal</Text>
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>📝 Beschreibung</Text>
                <TextInput
                  style={[styles.textModalInput, styles.textArea]}
                  value={groupForm.description}
                  onChangeText={(text) => setGroupForm({ ...groupForm, description: text })}
                  placeholder="Beschreibung des Kanals und Verwendungszweck..."
                  placeholderTextColor="#666"
                  multiline
                  numberOfLines={3}
                  maxLength={200}
                />
                <Text style={styles.helperText}>Optional: Beschreibung für andere Nutzer</Text>
              </View>

              {/* Kanal-Beispiele */}
              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>💡 Kanal-Vorschläge</Text>
                <View style={styles.suggestionContainer}>
                  {[
                    { name: 'Einsatzleitung', desc: 'Hauptkommunikation' },
                    { name: 'Rettungsdienst', desc: 'Medizinische Notfälle' },
                    { name: 'Feuerwehr', desc: 'Brand- und Rettungseinsätze' },
                    { name: 'Polizei', desc: 'Sicherheit und Ordnung' },
                    { name: 'SEK-Team', desc: 'Spezialeinheiten' },
                    { name: 'Technischer Dienst', desc: 'Infrastruktur' }
                  ].map((suggestion, index) => (
                    <TouchableOpacity
                      key={index}
                      style={styles.suggestionButton}
                      onPress={() => setGroupForm({ 
                        name: suggestion.name, 
                        description: suggestion.desc 
                      })}
                    >
                      <Text style={styles.suggestionName}>📡 {suggestion.name}</Text>
                      <Text style={styles.suggestionDesc}>{suggestion.desc}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>

              {/* Erweiterte Optionen für bestehende Kanäle */}
              {editingGroup && (
                <View style={styles.inputGroup}>
                  <Text style={styles.sectionTitle}>⚙️ Kanal-Verwaltung</Text>
                  
                  <View style={styles.actionButtonsContainer}>
                    <TouchableOpacity 
                      style={styles.duplicateChannelButton}
                      onPress={() => {
                        // Kanal duplizieren
                        setGroupForm({ 
                          name: `${groupForm.name} (Kopie)`, 
                          description: groupForm.description 
                        });
                        setEditingGroup(null);
                        Alert.alert('Info', 'Kanal wird als Kopie erstellt. Geben Sie einen neuen Namen ein.');
                      }}
                    >
                      <Ionicons name="copy" size={20} color="#fff" />
                      <Text style={styles.actionButtonText}>Kanal duplizieren</Text>
                    </TouchableOpacity>
                    
                    <TouchableOpacity 
                      style={styles.deleteChannelButton}
                      onPress={() => {
                        setGroupModalVisible(false);
                        deleteGroup(editingGroup.id);
                      }}
                    >
                      <Ionicons name="trash" size={20} color="#fff" />
                      <Text style={styles.actionButtonText}>Kanal löschen</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              )}
            </ScrollView>
          </View>
        </View>
      </Modal>

      {/* Profil Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={profileModalVisible}
        onRequestClose={() => setProfileModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.profileModalContent}>
            <View style={styles.modalHeader}>
              <TouchableOpacity onPress={() => setProfileModalVisible(false)}>
                <Text style={styles.cancelButton}>Abbrechen</Text>
              </TouchableOpacity>
              <Text style={styles.modalTitle}>Anzeigename ändern</Text>
              <TouchableOpacity onPress={updateProfile}>
                <Text style={styles.saveButton}>Speichern</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.profileForm}>
              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Anzeigename *</Text>
                <TextInput
                  style={styles.textModalInput}
                  value={newDisplayName}
                  onChangeText={setNewDisplayName}
                  placeholder="Ihr Anzeigename"
                  placeholderTextColor="#666"
                  maxLength={50}
                />
              </View>
              <Text style={styles.helpText}>
                Dieser Name wird anderen Admins im Funkgerät angezeigt
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
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  headerSubtitle: {
    fontSize: 12,
    color: '#888',
    marginTop: 2,
  },
  headerActions: {
    flexDirection: 'row',
    gap: 8,
  },
  headerButton: {
    padding: 8,
    borderRadius: 8,
    backgroundColor: '#333',
  },
  // NEUE PROMINENTE KANAL-KATEGORIE-SEKTION STYLES
  channelCategorySection: {
    backgroundColor: '#2a2a2a',
    borderBottomWidth: 2,
    borderBottomColor: '#ff4444',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  categoryHeader: {
    alignItems: 'center',
    marginBottom: 16,
  },
  categoryTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 4,
  },
  categoryMainTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    letterSpacing: 1,
  },
  categorySubtitle: {
    fontSize: 12,
    color: '#888',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  categoryActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  newChannelMainButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ff4444',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 25,
    gap: 8,
    elevation: 3,
    shadowColor: '#ff4444',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
  },
  newChannelMainText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    letterSpacing: 0.5,
  },
  categoryStats: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#333',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  statItem: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ff4444',
  },
  statLabel: {
    fontSize: 10,
    color: '#888',
    marginTop: 2,
  },
  statDivider: {
    width: 1,
    height: 20,
    backgroundColor: '#555',
    marginHorizontal: 12,
  },
  // ERWEITERTE KANAL-NAVIGATION STYLES
  activeChannelsSection: {
    backgroundColor: '#1a1a1a',
    paddingVertical: 16,
  },
  activeChannelsTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#ff4444',
    textAlign: 'center',
    marginBottom: 12,
    letterSpacing: 1,
  },
  channelsScrollContainer: {
    paddingHorizontal: 16,
  },
  channelCardWrapper: {
    marginRight: 12,
  },
  channelCard: {
    backgroundColor: '#333',
    borderRadius: 12,
    padding: 16,
    minWidth: 140,
    minHeight: 100,
    borderWidth: 2,
    borderColor: '#444',
  },
  activeChannelCard: {
    backgroundColor: '#ff4444',
    borderColor: '#ff6666',
    elevation: 4,
    shadowColor: '#ff4444',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
  },
  channelCardContent: {
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
  },
  channelCardTitle: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#888',
    textAlign: 'center',
    marginTop: 8,
    marginBottom: 4,
  },
  activeChannelCardTitle: {
    color: '#fff',
  },
  channelCardSubtitle: {
    fontSize: 10,
    color: '#666',
    textAlign: 'center',
  },
  activeChannelCardSubtitle: {
    color: '#ffdddd',
  },
  activeIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 6,
    gap: 4,
  },
  activeText: {
    fontSize: 8,
    color: '#4CAF50',
    fontWeight: 'bold',
  },
  channelManagementButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  editChannelButton: {
    backgroundColor: '#4CAF50',
    padding: 8,
    borderRadius: 8,
    flex: 1,
    marginRight: 4,
    alignItems: 'center',
  },
  deleteChannelButton: {
    backgroundColor: '#ff4444',
    padding: 8,
    borderRadius: 8,
    flex: 1,
    marginLeft: 4,
    alignItems: 'center',
  },
  quickAddChannelCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    padding: 16,
    minWidth: 100,
    minHeight: 100,
    borderWidth: 2,
    borderColor: '#ff4444',
    borderStyle: 'dashed',
    marginRight: 16,
  },
  quickAddContent: {
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
  },
  quickAddText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#ff4444',
    textAlign: 'center',
    marginTop: 4,
  },
  channelManagement: {
    backgroundColor: '#2a2a2a',
    borderBottomWidth: 1,
    borderBottomColor: '#333',
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  channelHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  channelTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  newChannelButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ff4444',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    gap: 6,
  },
  newChannelText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  groupsContainer: {
    backgroundColor: '#2a2a2a',
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  channelChipContainer: {
    flexDirection: 'column',
    alignItems: 'center',
    marginRight: 8,
  },
  channelChip: {
    backgroundColor: '#333',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 12,
    marginLeft: 8,
    marginVertical: 8,
    minWidth: 120,
  },
  activeChannelChip: {
    backgroundColor: '#ff4444',
  },
  channelChipContent: {
    alignItems: 'center',
  },
  channelChipText: {
    fontSize: 12,
    color: '#888',
    fontWeight: '600',
    textAlign: 'center',
  },
  activeChannelChipText: {
    color: '#fff',
    fontWeight: '600',
  },
  channelDescription: {
    fontSize: 10,
    color: '#666',
    marginTop: 2,
    textAlign: 'center',
  },
  activeChannelDescription: {
    color: '#ddd',
  },
  channelActions: {
    flexDirection: 'row',
    gap: 4,
    marginTop: 4,
  },
  channelActionButton: {
    padding: 4,
    borderRadius: 8,
    backgroundColor: '#333',
  },
  groupChipContainer: {
    flexDirection: 'column',
    alignItems: 'center',
    marginRight: 8,
  },
  groupChip: {
    backgroundColor: '#333',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginLeft: 8,
    marginVertical: 12,
  },
  activeGroupChip: {
    backgroundColor: '#ff4444',
  },
  groupChipText: {
    fontSize: 14,
    color: '#888',
  },
  activeGroupChipText: {
    color: '#fff',
    fontWeight: '600',
  },
  groupEditButton: {
    padding: 4,
    marginLeft: 4,
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
  },
  voiceButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#333',
    justifyContent: 'center',
    alignItems: 'center',
  },
  voiceButtonActive: {
    backgroundColor: '#ff4444',
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
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#1a1a1a',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '70%',
  },
  profileModalContent: {
    backgroundColor: '#1a1a1a',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '50%',
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
  profileForm: {
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
  textArea: {
    height: 80,
    textAlignVertical: 'top',
  },
  deleteGroupButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#ff4444',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    marginTop: 20,
  },
  deleteGroupText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  helpText: {
    fontSize: 14,
    color: '#888',
    textAlign: 'center',
    marginTop: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ff4444',
    marginBottom: 16,
    textAlign: 'center',
  },
  helperText: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
    fontStyle: 'italic',
  },
  suggestionContainer: {
    gap: 8,
  },
  suggestionButton: {
    backgroundColor: '#2a2a2a',
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#444',
  },
  suggestionName: {
    fontSize: 14,
    color: '#fff',
    fontWeight: '600',
  },
  suggestionDesc: {
    fontSize: 12,
    color: '#888',
    marginTop: 2,
  },
  actionButtonsContainer: {
    gap: 12,
  },
  duplicateChannelButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#4CAF50',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  deleteChannelButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#ff4444',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
});