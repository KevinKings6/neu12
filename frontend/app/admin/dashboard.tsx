import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  StatusBar,
  Alert,
  RefreshControl,
  Modal,
  ScrollView,
  TextInput,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons, MaterialIcons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useAuth } from '../../contexts/AuthContext';
import Constants from 'expo-constants';

const BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface SOSAlert {
  id: string;
  user_id: string;
  location_lat?: number;
  location_lng?: number;
  location_address?: string;
  alert_type: string;
  message?: string;
  contacts_notified: string[];
  status: string;
  created_at: string;
}

interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

interface ChatGroup {
  id: string;
  name: string;
  description?: string;
  members: string[];
  is_active: boolean;
  created_at: string;
}

export default function AdminDashboard() {
  const { user, token, logout, isAdmin } = useAuth();
  const [alerts, setAlerts] = useState<SOSAlert[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [activeTab, setActiveTab] = useState<'alerts' | 'users' | 'news' | 'chat' | 'active'>('alerts');
  const [refreshing, setRefreshing] = useState(false);
  const [activeAlerts, setActiveAlerts] = useState<SOSAlert[]>([]);
  const [newsArticles, setNewsArticles] = useState<any[]>([]);
  const [groups, setGroups] = useState<ChatGroup[]>([]);
  const [stats, setStats] = useState({
    totalAlerts: 0,
    activeAlerts: 0,
    adminActiveAlerts: 0,
    totalUsers: 0,
    adminUsers: 0,
    totalNews: 0,
  });

  // User group assignment modal
  const [userGroupModalVisible, setUserGroupModalVisible] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [userGroups, setUserGroups] = useState<string[]>([]);

  // SOS Management states
  const [selectedSOS, setSelectedSOS] = useState<SOSAlert | null>(null);
  const [sosDetailModalVisible, setSosDetailModalVisible] = useState(false);
  const [sosLocation, setSosLocation] = useState<{latitude: number, longitude: number} | null>(null);

  // User role management
  const [roleModalVisible, setRoleModalVisible] = useState(false);
  const [selectedRole, setSelectedRole] = useState<'user' | 'team' | 'admin' | 'emergency'>('user');

  useEffect(() => {
    if (!isAdmin()) {
      Alert.alert('Zugriff verweigert', 'Sie haben keine Berechtigung für diesen Bereich');
      router.replace('/');
      return;
    }
    loadData();
  }, []);

  const loadData = async () => {
    await Promise.all([loadAlerts(), loadUsers(), loadActiveAlerts(), loadNews(), loadGroups()]);
  };

  const loadAlerts = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/sos-alerts`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const alertsData = await response.json();
        setAlerts(alertsData);
        updateStats({ alerts: alertsData });
      } else {
        console.error('Failed to load alerts');
      }
    } catch (error) {
      console.error('Error loading alerts:', error);
    }
  };

  const loadActiveAlerts = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/active-alerts`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const activeAlertsData = await response.json();
        setActiveAlerts(activeAlertsData);
        updateStats({ activeAlerts: activeAlertsData });
      } else {
        console.error('Failed to load active alerts');
      }
    } catch (error) {
      console.error('Error loading active alerts:', error);
    }
  };

  const loadUsers = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/users`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const usersData = await response.json();
        setUsers(usersData);
        updateStats({ users: usersData });
      } else {
        console.error('Failed to load users');
      }
    } catch (error) {
      console.error('Error loading users:', error);
    }
  };

  const loadNews = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/news`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const newsData = await response.json();
        setNewsArticles(newsData);
        updateStats({ news: newsData });
      } else {
        console.error('Failed to load news');
      }
    } catch (error) {
      console.error('Error loading news:', error);
    }
  };

  const loadGroups = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/chat/groups`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const groupsData = await response.json();
        setGroups(groupsData);
      } else {
        console.error('Failed to load groups');
      }
    } catch (error) {
      console.error('Error loading groups:', error);
    }
  };

  const updateStats = ({ alerts: alertsData, users: usersData, activeAlerts: activeAlertsData, news: newsData }: { alerts?: SOSAlert[], users?: User[], activeAlerts?: SOSAlert[], news?: any[] }) => {
    setStats(prev => {
      const newStats = { ...prev };
      
      if (alertsData) {
        newStats.totalAlerts = alertsData.length;
        newStats.activeAlerts = alertsData.filter(a => a.status === 'active').length;
      }
      
      if (activeAlertsData) {
        newStats.adminActiveAlerts = activeAlertsData.length;
      }
      
      if (usersData) {
        newStats.totalUsers = usersData.length;
        newStats.adminUsers = usersData.filter(u => u.role === 'admin').length;
      }
      
      if (newsData) {
        newStats.totalNews = newsData.length;
      }
      
      return newStats;
    });
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const updateAlertStatus = async (alertId: string, status: string) => {
    if (!alertId || alertId === 'undefined') {
      Alert.alert('Fehler', 'Ungültige Alert-ID');
      return;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/sos-alerts/${alertId}/status?status=${status}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        await loadAlerts();
        await loadActiveAlerts(); // Reload both lists
        const statusText = status === 'resolved' ? 'gelöst' : status === 'cancelled' ? 'abgebrochen' : status;
        Alert.alert('Erfolg', `Status auf ${statusText} aktualisiert`);
      } else {
        Alert.alert('Fehler', 'Status konnte nicht aktualisiert werden');
      }
    } catch (error) {
      console.error('Error updating alert status:', error);
      Alert.alert('Fehler', 'Fehler beim Aktualisieren des Status');
    }
  };

  const deleteAlert = async (alertId: string) => {
    if (!alertId || alertId === 'undefined') {
      Alert.alert('Fehler', 'Ungültige Alert-ID');
      return;
    }

    try {
      // Completely delete the SOS alert from database
      const response = await fetch(`${BACKEND_URL}/api/admin/sos-alerts/${alertId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        await loadAlerts(); // Reload SOS tab (alert will disappear)
        await loadActiveAlerts(); // Reload ACTIVE tab in case it was there
        // No alert popup - silent deletion for better UX
      } else {
        Alert.alert('Fehler', 'SOS-Alarm konnte nicht gelöscht werden');
      }
    } catch (error) {
      console.error('Error deleting alert:', error);
      Alert.alert('Fehler', 'Fehler beim Löschen des SOS-Alarms');
    }
  };

  const moveToActiveTab = async (alertId: string) => {
    if (!alertId || alertId === 'undefined') {
      Alert.alert('Fehler', 'Ungültige Alert-ID');
      return;
    }

    try {
      // Move alert to ACTIVE (admin_active status)
      const response = await fetch(`${BACKEND_URL}/api/admin/sos-alerts/${alertId}/status?status=admin_active`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        await loadAlerts(); // Reload SOS tab (alert will disappear)
        await loadActiveAlerts(); // Reload ACTIVE tab (alert will appear)
        // No alert popup - silent move for better UX
      } else {
        Alert.alert('Fehler', 'SOS-Alarm konnte nicht zu ACTIVE verschoben werden');
      }
    } catch (error) {
      console.error('Error moving alert to active:', error);
      Alert.alert('Fehler', 'Fehler beim Verschieben des SOS-Alarms');
    }
  };

  const resolveAndRemoveFromActive = async (alertId: string) => {
    if (!alertId || alertId === 'undefined') {
      Alert.alert('Fehler', 'Ungültige Alert-ID');
      return;
    }

    try {
      // Set status to resolved - this removes it from ACTIVE
      const response = await fetch(`${BACKEND_URL}/api/admin/sos-alerts/${alertId}/status?status=resolved`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        await loadAlerts(); // Reload SOS tab
        await loadActiveAlerts(); // Reload ACTIVE tab (alert will disappear)
        // No alert popup - silent resolution for better UX
      } else {
        Alert.alert('Fehler', 'SOS-Alarm konnte nicht als gelöst markiert werden');
      }
    } catch (error) {
      console.error('Error resolving alert:', error);
      Alert.alert('Fehler', 'Fehler beim Lösen des SOS-Alarms');
    }
  };

  const toggleUserStatus = async (userId: string, currentStatus: boolean) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/users/${userId}/status?is_active=${!currentStatus}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        await loadUsers();
        Alert.alert('Erfolg', `Benutzer wurde ${!currentStatus ? 'aktiviert' : 'gesperrt'}`);
      } else {
        Alert.alert('Fehler', 'Benutzer-Status konnte nicht geändert werden');
      }
    } catch (error) {
      console.error('Error updating user status:', error);
      Alert.alert('Fehler', 'Fehler beim Ändern des Benutzer-Status');
    }
  };

  const changeUserRole = async (userId: string, newRole: string) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/users/${userId}/role`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ role: newRole })
      });

      if (response.ok) {
        await loadUsers();
        Alert.alert('Erfolg', `Benutzerrolle wurde zu ${newRole} geändert`);
      } else {
        Alert.alert('Fehler', 'Benutzerrolle konnte nicht geändert werden');
      }
    } catch (error) {
      console.error('Error updating user role:', error);
      Alert.alert('Fehler', 'Fehler beim Ändern der Benutzerrolle');
    }
  };

  const openUserGroupModal = (user: User) => {
    setSelectedUser(user);
    // Find groups this user is a member of
    const memberGroups = groups.filter(group => group.members.includes(user.id)).map(group => group.id);
    setUserGroups(memberGroups);
    setUserGroupModalVisible(true);
  };

  const toggleUserGroup = (groupId: string) => {
    const updatedGroups = [...userGroups];
    const index = updatedGroups.indexOf(groupId);
    
    if (index > -1) {
      updatedGroups.splice(index, 1);
    } else {
      updatedGroups.push(groupId);
    }
    
    setUserGroups(updatedGroups);
  };

  const saveUserGroups = async () => {
    if (!selectedUser) return;

    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/users/${selectedUser.id}/groups`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ group_ids: userGroups })
      });

      if (response.ok) {
        setUserGroupModalVisible(false);
        await loadGroups(); // Refresh groups to show updated members
        Alert.alert('Erfolg', 'Gruppen-Zuweisungen wurden aktualisiert');
      } else {
        Alert.alert('Fehler', 'Gruppen-Zuweisungen konnten nicht aktualisiert werden');
      }
    } catch (error) {
      console.error('Error updating user groups:', error);
      Alert.alert('Fehler', 'Fehler beim Aktualisieren der Gruppen-Zuweisungen');
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('de-DE') + ' ' + date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
  };

  const getAlertIcon = (alertType: string) => {
    switch (alertType) {
      case 'police':
        return 'shield-outline';
      case 'fire':
        return 'flame-outline';
      case 'medical':
        return 'medical-outline';
      default:
        return 'alert-circle-outline';
    }
  };

  const getAlertColor = (alertType: string) => {
    switch (alertType) {
      case 'police':
        return '#2196F3';
      case 'fire':
        return '#FF9800';
      case 'medical':
        return '#4CAF50';
      default:
        return '#ff4444';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return '#ff4444';
      case 'resolved':
        return '#4CAF50';
      case 'cancelled':
        return '#888';
      default:
        return '#888';
    }
  };

  const renderAlert = ({ item }: { item: SOSAlert }) => (
    <TouchableOpacity 
      style={styles.alertCard}
      onPress={() => openSosDetails(item)}
    >
      <View style={styles.alertHeader}>
        <View style={styles.alertInfo}>
          <View style={styles.alertTypeContainer}>
            <Ionicons 
              name={getAlertIcon(item.alert_type)} 
              size={20} 
              color={getAlertColor(item.alert_type)} 
            />
            <Text style={[styles.alertType, { color: getAlertColor(item.alert_type) }]}>
              {item.alert_type.toUpperCase()}
            </Text>
          </View>
          <Text style={styles.alertDate}>{formatDate(item.created_at)}</Text>
          <Text style={styles.userId}>Benutzer ID: {item.user_id.slice(-8)}</Text>
        </View>
        <View style={[styles.statusBadge, { backgroundColor: getStatusColor(item.status) + '20' }]}>
          <Text style={[styles.statusText, { color: getStatusColor(item.status) }]}>
            {item.status.toUpperCase()}
          </Text>
        </View>
      </View>

      {item.message && (
        <Text style={styles.alertMessage}>{item.message}</Text>
      )}

      {item.location_address && (
        <View style={styles.locationContainer}>
          <Ionicons name="location-outline" size={16} color="#888" />
          <Text style={styles.locationText}>{item.location_address}</Text>
        </View>
      )}

      {/* Action Hint */}
      <View style={styles.actionHint}>
        <Text style={styles.actionHintText}>👆 Antippen für Details & GPS-Position</Text>
      </View>

      {(item.status === 'active' || item.status === 'admin_active' || activeTab === 'alerts' || activeTab === 'active') && (
        <View style={styles.actionButtons}>
          <TouchableOpacity
            style={[styles.actionButton, styles.resolveButton]}
            onPress={(e) => {
              e.stopPropagation();
              resolveAndRemoveFromActive(item._id || item.id);
            }}
          >
            <Text style={styles.actionButtonText}>Gelöst</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.actionButton, styles.deleteButton]}
            onPress={() => deleteAlert(item._id || item.id)}
          >
            <Text style={styles.actionButtonText}>Löschen</Text>
          </TouchableOpacity>
          {activeTab === 'alerts' && (
            <TouchableOpacity
              style={[styles.actionButton, styles.activeButton]}
              onPress={() => moveToActiveTab(item._id || item.id)}
            >
              <Text style={styles.actionButtonText}>→ ACTIVE</Text>
            </TouchableOpacity>
          )}
        </View>
      )}
    </TouchableOpacity>
  );

  const renderUser = ({ item }: { item: User }) => (
    <TouchableOpacity
      key={item.id}
      style={[
        styles.userCard,
        !item.is_active && styles.inactiveUserCard
      ]}
      onPress={() => openRoleModal(item)}
    >
      <View style={styles.userInfo}>
        <Text style={styles.userName}>{item.full_name}</Text>
        <Text style={styles.userEmail}>{item.email}</Text>
        <View style={styles.userRoleContainer}>
          <View style={[styles.roleChip, { backgroundColor: getRoleColor(item.role) }]}>
            <Text style={styles.roleText}>{getRoleName(item.role)}</Text>
          </View>
        </View>
      </View>
      <View style={styles.userActions}>
        <TouchableOpacity
          style={[
            styles.actionButton,
            item.is_active ? styles.deactivateButton : styles.activateButton
          ]}
          onPress={() => toggleUserStatus(item.id, item.is_active)}
        >
          <Ionicons 
            name={item.is_active ? "close-circle" : "checkmark-circle"} 
            size={20} 
            color="#fff" 
          />
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );

  const [newsModalVisible, setNewsModalVisible] = useState(false);
  const [editingNews, setEditingNews] = useState<any>(null);
  const [newsForm, setNewsForm] = useState({
    title: '',
    content: ''
  });

  const openNewsModal = (article?: any) => {
    if (article) {
      setEditingNews(article);
      setNewsForm({
        title: article.title,
        content: article.content
      });
    } else {
      setEditingNews(null);
      setNewsForm({
        title: '',
        content: ''
      });
    }
    setNewsModalVisible(true);
  };

  // SOS Management functions
  const openSosDetails = async (sosAlert: SOSAlert) => {
    setSelectedSOS(sosAlert);
    
    // Parse GPS location if available
    if (sosAlert.location) {
      try {
        const locationParts = sosAlert.location.split(',');
        if (locationParts.length === 2) {
          const latitude = parseFloat(locationParts[0].trim());
          const longitude = parseFloat(locationParts[1].trim());
          setSosLocation({ latitude, longitude });
        } else {
          setSosLocation(null);
        }
      } catch (error) {
        console.error('Error parsing location:', error);
        setSosLocation(null);
      }
    } else {
      setSosLocation(null);
    }
    
    setSosDetailModalVisible(true);
  };

  const activateSOS = async (sosId: string) => {
    if (!token) return;

    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/sos/${sosId}/activate`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        // Reload SOS alerts to reflect the change
        await loadData();
        setSosDetailModalVisible(false);
        Alert.alert('Erfolg', 'SOS-Alarm wurde als AKTIV markiert und aus der Liste entfernt');
      } else {
        Alert.alert('Fehler', 'SOS-Status konnte nicht geändert werden');
      }
    } catch (error) {
      console.error('Error activating SOS:', error);
      Alert.alert('Fehler', 'Fehler beim Aktivieren des SOS-Alarms');
    }
  };

  const updateUserRole = async () => {
    if (!selectedUser || !token) return;

    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/users/${selectedUser.id}/role`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ role: selectedRole })
      });

      if (response.ok) {
        setRoleModalVisible(false);
        await loadUsers();
        Alert.alert('Erfolg', `Benutzerrang wurde auf "${selectedRole}" geändert`);
      } else {
        Alert.alert('Fehler', 'Benutzerrang konnte nicht geändert werden');
      }
    } catch (error) {
      console.error('Error updating user role:', error);
      Alert.alert('Fehler', 'Fehler beim Ändern des Benutzerrangs');
    }
  };

  const updateUserProfile = async () => {
    if (!selectedUser || !token) return;

    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/users/${selectedUser.id}/role`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ role: selectedRole })
      });

      if (response.ok) {
        setRoleModalVisible(false);
        await loadUsers();
        Alert.alert('Erfolg', `Benutzerrang wurde auf "${selectedRole}" geändert`);
      } else {
        Alert.alert('Fehler', 'Benutzerrang konnte nicht geändert werden');
      }
    } catch (error) {
      console.error('Error updating user role:', error);
      Alert.alert('Fehler', 'Fehler beim Ändern des Benutzerrangs');
    }
  };

  const openRoleModal = (user: User) => {
    setSelectedUser(user);
    setSelectedRole(user.role as 'user' | 'team' | 'admin' | 'emergency');
    setRoleModalVisible(true);
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin':
        return '#ff4444';
      case 'team':
        return '#ffaa00';
      case 'emergency':
        return '#ff6b35';
      case 'user':
        return '#00aa44';
      default:
        return '#666';
    }
  };

  const getRoleName = (role: string) => {
    switch (role) {
      case 'admin':
        return 'Admin';
      case 'team':
        return 'Team';
      case 'emergency':
        return 'Emergency';
      case 'user':
        return 'User';
      default:
        return 'Unbekannt';
    }
  };

  const saveNews = async () => {
    if (!newsForm.title.trim() || !newsForm.content.trim()) {
      Alert.alert('Fehler', 'Bitte Titel und Inhalt eingeben');
      return;
    }

    try {
      const url = editingNews 
        ? `${BACKEND_URL}/api/admin/news/${editingNews._id || editingNews.id}`
        : `${BACKEND_URL}/api/admin/news`;
      
      const method = editingNews ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(newsForm)
      });

      if (response.ok) {
        setNewsModalVisible(false);
        await loadNews();
        Alert.alert('Erfolg', editingNews ? 'Nachricht aktualisiert' : 'Nachricht erstellt');
      } else {
        Alert.alert('Fehler', 'Nachricht konnte nicht gespeichert werden');
      }
    } catch (error) {
      console.error('Error saving news:', error);
      Alert.alert('Fehler', 'Fehler beim Speichern der Nachricht');
    }
  };

  const deleteNews = async (articleId: string) => {
    Alert.alert(
      'Nachricht löschen',
      'Möchten Sie diese Nachricht wirklich löschen?',
      [
        { text: 'Abbrechen', style: 'cancel' },
        {
          text: 'Löschen',
          style: 'destructive',
          onPress: async () => {
            try {
              const response = await fetch(`${BACKEND_URL}/api/admin/news/${articleId}`, {
                method: 'DELETE',
                headers: {
                  'Authorization': `Bearer ${token}`,
                },
              });

              if (response.ok) {
                await loadNews();
                Alert.alert('Erfolg', 'Nachricht wurde gelöscht');
              } else {
                Alert.alert('Fehler', 'Nachricht konnte nicht gelöscht werden');
              }
            } catch (error) {
              console.error('Error deleting news:', error);
              Alert.alert('Fehler', 'Fehler beim Löschen der Nachricht');
            }
          }
        }
      ]
    );
  };

  const renderNewsItem = ({ item }: { item: any }) => (
    <View style={styles.newsCard}>
      <View style={styles.newsHeader}>
        <Text style={styles.newsTitle}>{item.title}</Text>
        <View style={styles.newsActions}>
          <TouchableOpacity 
            style={styles.newsEditButton}
            onPress={() => openNewsModal(item)}
          >
            <Ionicons name="edit" size={16} color="#2196F3" />
          </TouchableOpacity>
          <TouchableOpacity 
            style={styles.newsDeleteButton}
            onPress={() => deleteNews(item._id || item.id)}
          >
            <Ionicons name="trash" size={16} color="#ff4444" />
          </TouchableOpacity>
        </View>
      </View>
      <Text style={styles.newsContent} numberOfLines={3}>{item.content}</Text>
      <View style={styles.newsFooter}>
        <Text style={styles.newsAuthor}>Von: {item.author_name}</Text>
        <Text style={styles.newsDate}>{formatDate(item.created_at)}</Text>
        <View style={[styles.statusIndicator, { backgroundColor: item.is_active ? '#4CAF50' : '#888' }]} />
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a1a" />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Admin Dashboard</Text>
        <TouchableOpacity onPress={logout}>
          <Ionicons name="log-out-outline" size={24} color="#ff4444" />
        </TouchableOpacity>
      </View>

      {/* Welcome */}
      <View style={styles.welcomeSection}>
        <Text style={styles.welcomeText}>Willkommen, {user?.full_name}</Text>
        <Text style={styles.welcomeSubtext}>Emergency SOS Verwaltung</Text>
      </View>

      {/* Stats */}
      <View style={styles.statsContainer}>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>{stats.totalAlerts}</Text>
          <Text style={styles.statLabel}>SOS Alarme</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={[styles.statNumber, { color: '#ff4444' }]}>{stats.adminActiveAlerts}</Text>
          <Text style={styles.statLabel}>ACTIVE</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>{stats.totalUsers}</Text>
          <Text style={styles.statLabel}>Benutzer</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={[styles.statNumber, { color: '#4CAF50' }]}>{stats.totalNews}</Text>
          <Text style={styles.statLabel}>News</Text>
        </View>
      </View>

      {/* Tabs */}
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'alerts' && styles.activeTab]}
          onPress={() => setActiveTab('alerts')}
        >
          <MaterialIcons name="emergency" size={14} color={activeTab === 'alerts' ? '#ff4444' : '#888'} />
          <Text style={[styles.tabText, activeTab === 'alerts' && styles.activeTabText]}>
            SOS
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'active' && styles.activeTab]}
          onPress={() => setActiveTab('active')}
        >
          <MaterialIcons name="priority-high" size={14} color={activeTab === 'active' ? '#ff4444' : '#888'} />
          <Text style={[styles.tabText, activeTab === 'active' && styles.activeTabText]}>
            ACTIVE
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'users' && styles.activeTab]}
          onPress={() => setActiveTab('users')}
        >
          <Ionicons name="people-outline" size={14} color={activeTab === 'users' ? '#ff4444' : '#888'} />
          <Text style={[styles.tabText, activeTab === 'users' && styles.activeTabText]}>
            User
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'news' && styles.activeTab]}
          onPress={() => setActiveTab('news')}
        >
          <MaterialIcons name="article" size={14} color={activeTab === 'news' ? '#ff4444' : '#888'} />
          <Text style={[styles.tabText, activeTab === 'news' && styles.activeTabText]}>
            News
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'chat' && styles.activeTab]}
          onPress={() => router.push('/admin/funkgeraet')}
        >
          <MaterialIcons name="radio" size={14} color={activeTab === 'chat' ? '#ff4444' : '#888'} />
          <Text style={[styles.tabText, activeTab === 'chat' && styles.activeTabText]}>
            Funkgerät
          </Text>
        </TouchableOpacity>
      </View>

      {/* News Add Button */}
      {activeTab === 'news' && (
        <View style={styles.newsHeaderContainer}>
          <TouchableOpacity
            style={styles.addNewsButton}
            onPress={() => openNewsModal()}
          >
            <Ionicons name="add" size={24} color="#fff" />
            <Text style={styles.addNewsText}>Neue Nachricht</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Content */}
      <FlatList
        data={activeTab === 'alerts' ? alerts : activeTab === 'active' ? activeAlerts : activeTab === 'users' ? users : newsArticles}
        renderItem={activeTab === 'alerts' || activeTab === 'active' ? renderAlert : activeTab === 'users' ? renderUser : renderNewsItem}
        keyExtractor={(item) => item.id || item._id}
        contentContainerStyle={styles.listContainer}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#ff4444" />
        }
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <MaterialIcons 
              name={activeTab === 'alerts' ? 'emergency' : activeTab === 'active' ? 'priority-high' : activeTab === 'users' ? 'people' : 'article'} 
              size={80} 
              color="#666" 
            />
            <Text style={styles.emptyText}>
              {activeTab === 'alerts' ? 'Keine SOS Alarme' : 
               activeTab === 'active' ? 'Keine ACTIVE Alarme' :
               activeTab === 'users' ? 'Keine Benutzer' : 'Keine News'}
            </Text>
            <Text style={styles.emptySubtext}>
              {activeTab === 'alerts' ? 'Alle Alarme werden hier angezeigt' : 
               activeTab === 'active' ? 'Aktiv bearbeitete Alarme erscheinen hier' :
               activeTab === 'users' ? 'Registrierte Benutzer werden hier angezeigt' : 'Klicken Sie "Neue Nachricht" um zu beginnen'}
            </Text>
          </View>
        }
      />

      {/* News Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={newsModalVisible}
        onRequestClose={() => setNewsModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.newsModalContent}>
            <View style={styles.modalHeader}>
              <TouchableOpacity onPress={() => setNewsModalVisible(false)}>
                <Text style={styles.cancelButton}>Abbrechen</Text>
              </TouchableOpacity>
              <Text style={styles.modalTitle}>
                {editingNews ? 'Nachricht bearbeiten' : 'Neue Nachricht'}
              </Text>
              <TouchableOpacity onPress={saveNews}>
                <Text style={styles.saveButton}>Speichern</Text>
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.newsForm} showsVerticalScrollIndicator={false}>
              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Titel *</Text>
                <TextInput
                  style={styles.textInput}
                  value={newsForm.title}
                  onChangeText={(text) => setNewsForm({ ...newsForm, title: text })}
                  placeholder="Geben Sie den Nachrichtentitel ein"
                  placeholderTextColor="#666"
                  maxLength={100}
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Inhalt *</Text>
                <TextInput
                  style={[styles.textInput, styles.textArea]}
                  value={newsForm.content}
                  onChangeText={(text) => setNewsForm({ ...newsForm, content: text })}
                  placeholder="Geben Sie den Nachrichteninhalt ein..."
                  placeholderTextColor="#666"
                  multiline
                  numberOfLines={8}
                  maxLength={1000}
                />
              </View>

              <Text style={styles.characterCount}>
                {newsForm.content.length}/1000 Zeichen
              </Text>
            </ScrollView>
          </View>
        </View>
      </Modal>

      {/* User Group Assignment Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={userGroupModalVisible}
        onRequestClose={() => setUserGroupModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.newsModalContent}>
            <View style={styles.modalHeader}>
              <TouchableOpacity onPress={() => setUserGroupModalVisible(false)}>
                <Text style={styles.cancelButton}>Abbrechen</Text>
              </TouchableOpacity>
              <Text style={styles.modalTitle}>
                Gruppen für {selectedUser?.full_name}
              </Text>
              <TouchableOpacity onPress={saveUserGroups}>
                <Text style={styles.saveButton}>Speichern</Text>
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.newsForm} showsVerticalScrollIndicator={false}>
              <Text style={styles.inputLabel}>Chat-Gruppen auswählen:</Text>
              {groups.map((group) => (
                <TouchableOpacity
                  key={group.id}
                  style={styles.groupItem}
                  onPress={() => toggleUserGroup(group.id)}
                >
                  <View style={styles.groupInfo}>
                    <Text style={styles.groupName}>{group.name}</Text>
                    {group.description && (
                      <Text style={styles.groupDescription}>{group.description}</Text>
                    )}
                    <Text style={styles.groupMembers}>
                      {group.members.length} Mitglieder
                    </Text>
                  </View>
                  <View style={[styles.checkbox, userGroups.includes(group.id) && styles.checkboxActive]}>
                    {userGroups.includes(group.id) && (
                      <Ionicons name="checkmark" size={16} color="#fff" />
                    )}
                  </View>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        </View>
      </Modal>

      {/* SOS Detail Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={sosDetailModalVisible}
        onRequestClose={() => setSosDetailModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.sosDetailModal}>
            <View style={styles.modalHeader}>
              <TouchableOpacity onPress={() => setSosDetailModalVisible(false)}>
                <Text style={styles.cancelButton}>Schließen</Text>
              </TouchableOpacity>
              <Text style={styles.modalTitle}>🚨 SOS-Alarm Details</Text>
              <TouchableOpacity 
                onPress={() => selectedSOS && activateSOS(selectedSOS._id || selectedSOS.id)}
                style={styles.activateButton}
              >
                <Text style={styles.activateButtonText}>AKTIVIEREN</Text>
              </TouchableOpacity>
            </View>

            {selectedSOS && (
              <ScrollView style={styles.sosDetailContent} showsVerticalScrollIndicator={false}>
                {/* Alert Type & Time */}
                <View style={styles.sosDetailSection}>
                  <Text style={styles.sosDetailLabel}>🚨 Alarm-Typ</Text>
                  <Text style={styles.sosDetailValue}>
                    {selectedSOS.alert_type.toUpperCase()}
                  </Text>
                  <Text style={styles.sosDetailTime}>
                    {new Date(selectedSOS.created_at).toLocaleString('de-DE', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit'
                    })}
                  </Text>
                </View>

                {/* User Information */}
                <View style={styles.sosDetailSection}>
                  <Text style={styles.sosDetailLabel}>👤 Benutzer-Informationen</Text>
                  <Text style={styles.sosDetailValue}>
                    {selectedSOS.user?.full_name || 'Name nicht verfügbar'}
                  </Text>
                  <Text style={styles.sosDetailSubValue}>
                    ID: {selectedSOS.user_id}
                  </Text>
                  {selectedSOS.user?.email && (
                    <Text style={styles.sosDetailSubValue}>
                      📧 {selectedSOS.user.email}
                    </Text>
                  )}
                </View>

                {/* GPS Location */}
                <View style={styles.sosDetailSection}>
                  <Text style={styles.sosDetailLabel}>📍 GPS-Position</Text>
                  {sosLocation ? (
                    <View>
                      <Text style={styles.sosDetailValue}>
                        Lat: {sosLocation.latitude.toFixed(6)}
                      </Text>
                      <Text style={styles.sosDetailValue}>
                        Lng: {sosLocation.longitude.toFixed(6)}
                      </Text>
                      <TouchableOpacity 
                        style={styles.mapButton}
                        onPress={() => {
                          const url = `https://www.google.com/maps?q=${sosLocation.latitude},${sosLocation.longitude}`;
                          // In a real app, you would use Linking.openURL(url)
                          Alert.alert('GPS-Position', `Lat: ${sosLocation.latitude}, Lng: ${sosLocation.longitude}\n\nGoogle Maps URL: ${url}`);
                        }}
                      >
                        <Text style={styles.mapButtonText}>🗺️ In Karte öffnen</Text>
                      </TouchableOpacity>
                    </View>
                  ) : (
                    <Text style={styles.sosDetailValue}>
                      {selectedSOS.location_address || 'Keine GPS-Daten verfügbar'}
                    </Text>
                  )}
                </View>

                {/* Message */}
                {selectedSOS.message && (
                  <View style={styles.sosDetailSection}>
                    <Text style={styles.sosDetailLabel}>💬 Nachricht</Text>
                    <Text style={styles.sosDetailValue}>
                      {selectedSOS.message}
                    </Text>
                  </View>
                )}

                {/* Status */}
                <View style={styles.sosDetailSection}>
                  <Text style={styles.sosDetailLabel}>📊 Status</Text>
                  <View style={[styles.statusChip, { backgroundColor: getStatusColor(selectedSOS.status) + '20' }]}>
                    <Text style={[styles.statusChipText, { color: getStatusColor(selectedSOS.status) }]}>
                      {selectedSOS.status.toUpperCase()}
                    </Text>
                  </View>
                </View>

                {/* Action Instructions */}
                <View style={styles.sosInstructionsBox}>
                  <Text style={styles.sosInstructionsTitle}>📋 Anweisungen</Text>
                  <Text style={styles.sosInstructionsText}>
                    • Auf "AKTIVIEREN" klicken, um den SOS-Alarm zu bearbeiten{'\n'}
                    • Der Alarm wird als AKTIV markiert{'\n'}
                    • Er verschwindet aus der SOS-Liste{'\n'}
                    • Einsatzkräfte werden benachrichtigt
                  </Text>
                </View>
              </ScrollView>
            )}
          </View>
        </View>
      </Modal>

      {/* Role Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={roleModalVisible}
        onRequestClose={() => setRoleModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.newsModalContent}>
            <View style={styles.modalHeader}>
              <TouchableOpacity onPress={() => setRoleModalVisible(false)}>
                <Text style={styles.cancelButton}>Abbrechen</Text>
              </TouchableOpacity>
              <Text style={styles.modalTitle}>
                Rolle für {selectedUser?.full_name}
              </Text>
              <TouchableOpacity onPress={updateUserRole}>
                <Text style={styles.saveButton}>Speichern</Text>
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.newsForm} showsVerticalScrollIndicator={false}>
              <Text style={styles.inputLabel}>Rolle auswählen:</Text>
              
              {(['user', 'team', 'admin', 'emergency'] as const).map((role) => (
                <TouchableOpacity
                  key={role}
                  style={styles.groupItem}
                  onPress={() => setSelectedRole(role)}
                >
                  <View style={styles.groupInfo}>
                    <Text style={styles.groupName}>{getRoleName(role)}</Text>
                    <Text style={styles.groupDescription}>
                      {role === 'admin' ? 'Vollzugriff auf alle Funktionen' :
                       role === 'team' ? 'Erweiterte Berechtigungen für Teamleiter' :
                       role === 'emergency' ? 'Notfall-Berechtigungen für Rettungsdienste' :
                       'Standardbenutzer mit Grundfunktionen'}
                    </Text>
                  </View>
                  <View style={[styles.checkbox, selectedRole === role && styles.checkboxActive]}>
                    {selectedRole === role && (
                      <Ionicons name="checkmark" size={16} color="#fff" />
                    )}
                  </View>
                </TouchableOpacity>
              ))}
            </ScrollView>
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
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  welcomeSection: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#2a2a2a',
  },
  welcomeText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  welcomeSubtext: {
    fontSize: 14,
    color: '#888',
    marginTop: 4,
  },
  statsContainer: {
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
  },
  statNumber: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  statLabel: {
    fontSize: 10,
    color: '#888',
    marginTop: 4,
    textAlign: 'center',
  },
  tabContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    backgroundColor: '#2a2a2a',
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#ff4444',
  },
  tabText: {
    fontSize: 14,
    color: '#888',
    marginLeft: 8,
  },
  activeTabText: {
    color: '#ff4444',
    fontWeight: '600',
  },
  listContainer: {
    padding: 20,
    flexGrow: 1,
  },
  alertCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  alertHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  alertInfo: {
    flex: 1,
  },
  alertTypeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  alertType: {
    fontSize: 14,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  alertDate: {
    fontSize: 12,
    color: '#888',
    marginBottom: 2,
  },
  userId: {
    fontSize: 12,
    color: '#666',
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  statusText: {
    fontSize: 10,
    fontWeight: 'bold',
  },
  alertMessage: {
    fontSize: 14,
    color: '#fff',
    marginBottom: 8,
  },
  locationContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  locationText: {
    fontSize: 12,
    color: '#888',
    marginLeft: 4,
    flex: 1,
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 8,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 6,
    alignItems: 'center',
  },
  resolveButton: {
    backgroundColor: '#4CAF50',
  },
  cancelButton: {
    backgroundColor: '#666',
  },
  deleteButton: {
    backgroundColor: '#ff4444',
  },
  activeButton: {
    backgroundColor: '#ff4444',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  userCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  inactiveUserCard: {
    opacity: 0.6,
  },
  userRoleContainer: {
    marginTop: 8,
  },
  roleChip: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    alignSelf: 'flex-start',
  },
  activateButton: {
    backgroundColor: '#4CAF50',
  },
  deactivateButton: {
    backgroundColor: '#ff4444',
  },
  userInfo: {
    flex: 1,
    marginBottom: 12,
  },
  userHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  userName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
    marginRight: 8,
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
  userEmail: {
    fontSize: 14,
    color: '#888',
    marginBottom: 2,
  },
  userUsername: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  userDate: {
    fontSize: 12,
    color: '#666',
    marginBottom: 8,
  },
  userGroupsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 4,
  },
  userGroupChip: {
    backgroundColor: '#ff4444',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 12,
  },
  userGroupText: {
    fontSize: 10,
    color: '#fff',
    fontWeight: '600',
  },

  userStatus: {
    alignItems: 'center',
  },
  statusIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginBottom: 4,
  },
  statusLabel: {
    fontSize: 12,
    fontWeight: '600',
  },
  userButtonsContainer: {
    flexDirection: 'column',
    gap: 4,
  },
  statusButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    minWidth: 80,
    alignItems: 'center',
  },
  statusButtonText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '600',
  },
  newsCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  newsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  newsTitle: {
    flex: 1,
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
    marginRight: 8,
  },
  newsActions: {
    flexDirection: 'row',
    gap: 8,
  },
  newsEditButton: {
    padding: 4,
  },
  newsDeleteButton: {
    padding: 4,
  },
  newsContent: {
    fontSize: 14,
    color: '#ccc',
    marginBottom: 12,
    lineHeight: 20,
  },
  newsFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#333',
    paddingTop: 8,
  },
  newsAuthor: {
    fontSize: 12,
    color: '#888',
    fontStyle: 'italic',
  },
  newsDate: {
    fontSize: 12,
    color: '#888',
  },
  newsHeaderContainer: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    backgroundColor: '#2a2a2a',
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  addNewsButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#ff4444',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  addNewsText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  newsModalContent: {
    backgroundColor: '#1a1a1a',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '90%',
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
  saveButton: {
    fontSize: 16,
    color: '#ff4444',
    fontWeight: '600',
  },
  newsForm: {
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
    height: 120,
    textAlignVertical: 'top',
  },
  characterCount: {
    fontSize: 12,
    color: '#888',
    textAlign: 'right',
    marginTop: -10,
    marginBottom: 20,
  },
  groupItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: '#2a2a2a',
    borderRadius: 8,
    marginBottom: 8,
  },
  groupInfo: {
    flex: 1,
  },
  groupName: {
    fontSize: 16,
    color: '#fff',
    fontWeight: '600',
  },
  groupDescription: {
    fontSize: 14,
    color: '#888',
    marginTop: 2,
  },
  groupMembers: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#666',
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxActive: {
    backgroundColor: '#ff4444',
    borderColor: '#ff4444',
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
  sosDetailModal: {
    backgroundColor: '#1a1a1a',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '95%',
    width: '100%',
  },
  sosDetailContent: {
    flex: 1,
    padding: 20,
  },
  sosDetailSection: {
    marginBottom: 20,
    padding: 16,
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
  },
  sosDetailLabel: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#ff4444',
    marginBottom: 8,
  },
  sosDetailValue: {
    fontSize: 16,
    color: '#fff',
    marginBottom: 4,
  },
  sosDetailSubValue: {
    fontSize: 14,
    color: '#888',
    marginBottom: 2,
  },
  sosDetailTime: {
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
    marginTop: 4,
  },
  statusChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    alignSelf: 'flex-start',
  },
  statusChipText: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  mapButton: {
    backgroundColor: '#2196F3',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    marginTop: 8,
    alignItems: 'center',
  },
  mapButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  sosInstructionsBox: {
    backgroundColor: '#333',
    padding: 16,
    borderRadius: 12,
    marginTop: 8,
  },
  sosInstructionsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ff4444',
    marginBottom: 8,
  },
  sosInstructionsText: {
    fontSize: 14,
    color: '#ccc',
    lineHeight: 20,
  },
  activateButton: {
    backgroundColor: '#ff4444',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  activateButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  actionHint: {
    backgroundColor: '#333',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    marginTop: 8,
    alignItems: 'center',
  },
  actionHintText: {
    fontSize: 12,
    color: '#888',
    fontStyle: 'italic',
  },
});