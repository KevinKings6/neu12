import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  StatusBar,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons, MaterialIcons } from '@expo/vector-icons';
import { router } from 'expo-router';
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

export default function History() {
  const [alerts, setAlerts] = useState<SOSAlert[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadAlerts();
  }, []);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/sos-alerts`);
      if (response.ok) {
        const alertsData = await response.json();
        setAlerts(alertsData);
      }
    } catch (error) {
      console.error('Error loading alerts:', error);
      Alert.alert('Error', 'Failed to load SOS history');
    } finally {
      setLoading(false);
    }
  };

  const updateAlertStatus = async (alertId: string, status: string) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/sos-alerts/${alertId}/status?status=${status}`, {
        method: 'PUT'
      });

      if (response.ok) {
        await loadAlerts();
      } else {
        Alert.alert('Error', 'Failed to update alert status');
      }
    } catch (error) {
      console.error('Error updating alert status:', error);
      Alert.alert('Error', 'Failed to update alert status');
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
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
    <View style={styles.alertCard}>
      <View style={styles.alertHeader}>
        <View style={styles.alertInfo}>
          <View style={styles.alertTypeContainer}>
            <Ionicons 
              name={getAlertIcon(item.alert_type)} 
              size={24} 
              color={getAlertColor(item.alert_type)} 
            />
            <Text style={[styles.alertType, { color: getAlertColor(item.alert_type) }]}>
              {item.alert_type.toUpperCase()}
            </Text>
          </View>
          <Text style={styles.alertDate}>{formatDate(item.created_at)}</Text>
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

      {item.contacts_notified.length > 0 && (
        <View style={styles.notifiedContainer}>
          <Ionicons name="people-outline" size={16} color="#888" />
          <Text style={styles.notifiedText}>
            {item.contacts_notified.length} contact(s) notified
          </Text>
        </View>
      )}

      {item.status === 'active' && (
        <View style={styles.actionButtons}>
          <TouchableOpacity
            style={[styles.actionButton, styles.resolveButton]}
            onPress={() => updateAlertStatus(item.id, 'resolved')}
          >
            <Text style={styles.actionButtonText}>Mark Resolved</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.actionButton, styles.cancelButton]}
            onPress={() => updateAlertStatus(item.id, 'cancelled')}
          >
            <Text style={styles.actionButtonText}>Cancel</Text>
          </TouchableOpacity>
        </View>
      )}
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
        <Text style={styles.headerTitle}>SOS History</Text>
        <TouchableOpacity onPress={loadAlerts}>
          <Ionicons name="refresh" size={24} color="#fff" />
        </TouchableOpacity>
      </View>

      {/* Summary Stats */}
      <View style={styles.statsContainer}>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>{alerts.length}</Text>
          <Text style={styles.statLabel}>Total Alerts</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>{alerts.filter(a => a.status === 'active').length}</Text>
          <Text style={styles.statLabel}>Active</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>{alerts.filter(a => a.status === 'resolved').length}</Text>
          <Text style={styles.statLabel}>Resolved</Text>
        </View>
      </View>

      {/* Alerts List */}
      <FlatList
        data={alerts}
        renderItem={renderAlert}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContainer}
        showsVerticalScrollIndicator={false}
        refreshing={loading}
        onRefresh={loadAlerts}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <MaterialIcons name="history" size={80} color="#666" />
            <Text style={styles.emptyText}>No SOS alerts yet</Text>
            <Text style={styles.emptySubtext}>Your emergency alerts will appear here</Text>
          </View>
        }
      />
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
    padding: 16,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  statLabel: {
    fontSize: 12,
    color: '#888',
    marginTop: 4,
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
    marginBottom: 12,
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
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  alertDate: {
    fontSize: 14,
    color: '#888',
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  statusText: {
    fontSize: 12,
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
    marginBottom: 4,
  },
  locationText: {
    fontSize: 14,
    color: '#888',
    marginLeft: 4,
    flex: 1,
  },
  notifiedContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  notifiedText: {
    fontSize: 14,
    color: '#888',
    marginLeft: 4,
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 8,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 6,
    alignItems: 'center',
  },
  resolveButton: {
    backgroundColor: '#4CAF50',
  },
  cancelButton: {
    backgroundColor: '#666',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 14,
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
});