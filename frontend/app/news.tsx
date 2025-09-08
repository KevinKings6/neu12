import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  StatusBar,
  RefreshControl,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons, MaterialIcons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useAuth } from '../contexts/AuthContext';
import Constants from 'expo-constants';

const BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface NewsArticle {
  id: string;
  title: string;
  content: string;
  author_name: string;
  created_at: string;
  updated_at: string;
}

export default function News() {
  const { user } = useAuth();
  const [news, setNews] = useState<NewsArticle[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedArticle, setSelectedArticle] = useState<NewsArticle | null>(null);

  useEffect(() => {
    loadNews();
  }, []);

  const loadNews = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/news`);
      if (response.ok) {
        const newsData = await response.json();
        setNews(newsData);
      }
    } catch (error) {
      console.error('Error loading news:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadNews();
    setRefreshing(false);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('de-DE') + ' ' + date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
  };

  const renderNewsItem = ({ item }: { item: NewsArticle }) => (
    <TouchableOpacity
      style={styles.newsCard}
      onPress={() => setSelectedArticle(item)}
    >
      <View style={styles.newsHeader}>
        <MaterialIcons name="announcement" size={24} color="#ff4444" />
        <View style={styles.newsInfo}>
          <Text style={styles.newsTitle} numberOfLines={2}>{item.title}</Text>
          <Text style={styles.newsDate}>{formatDate(item.created_at)}</Text>
        </View>
      </View>
      <Text style={styles.newsPreview} numberOfLines={3}>
        {item.content}
      </Text>
      <View style={styles.newsFooter}>
        <Text style={styles.newsAuthor}>Von: {item.author_name}</Text>
        <Ionicons name="chevron-forward" size={16} color="#888" />
      </View>
    </TouchableOpacity>
  );

  if (selectedArticle) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="light-content" backgroundColor="#1a1a1a" />
        
        {/* Article Header */}
        <View style={styles.articleHeader}>
          <TouchableOpacity onPress={() => setSelectedArticle(null)}>
            <Ionicons name="arrow-back" size={24} color="#fff" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Nachricht</Text>
          <View style={styles.placeholder} />
        </View>

        <ScrollView style={styles.articleContainer} showsVerticalScrollIndicator={false}>
          <View style={styles.articleContent}>
            <Text style={styles.articleTitle}>{selectedArticle.title}</Text>
            
            <View style={styles.articleMeta}>
              <Text style={styles.articleAuthor}>Von: {selectedArticle.author_name}</Text>
              <Text style={styles.articleDate}>{formatDate(selectedArticle.created_at)}</Text>
            </View>

            <Text style={styles.articleText}>{selectedArticle.content}</Text>
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a1a" />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Nachrichten</Text>
        <TouchableOpacity onPress={onRefresh}>
          <Ionicons name="refresh" size={24} color="#fff" />
        </TouchableOpacity>
      </View>

      {/* Welcome Section */}
      <View style={styles.welcomeSection}>
        <Text style={styles.welcomeText}>Willkommen, {user?.full_name}</Text>
        <Text style={styles.welcomeSubtext}>Aktuelle Nachrichten und Updates</Text>
      </View>

      {/* News List */}
      <FlatList
        data={news}
        renderItem={renderNewsItem}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContainer}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#ff4444" />
        }
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <MaterialIcons name="article" size={80} color="#666" />
            <Text style={styles.emptyText}>Keine Nachrichten verfügbar</Text>
            <Text style={styles.emptySubtext}>Ziehen Sie nach unten um zu aktualisieren</Text>
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
  placeholder: {
    width: 24,
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
  listContainer: {
    padding: 20,
    flexGrow: 1,
  },
  newsCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#ff4444',
  },
  newsHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  newsInfo: {
    flex: 1,
    marginLeft: 12,
  },
  newsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  newsDate: {
    fontSize: 12,
    color: '#888',
  },
  newsPreview: {
    fontSize: 14,
    color: '#ccc',
    lineHeight: 20,
    marginBottom: 12,
  },
  newsFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#333',
    paddingTop: 12,
  },
  newsAuthor: {
    fontSize: 12,
    color: '#888',
    fontStyle: 'italic',
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
  articleHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  articleContainer: {
    flex: 1,
  },
  articleContent: {
    padding: 20,
  },
  articleTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 16,
    lineHeight: 32,
  },
  articleMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  articleAuthor: {
    fontSize: 14,
    color: '#ff4444',
    fontWeight: '600',
  },
  articleDate: {
    fontSize: 14,
    color: '#888',
  },
  articleText: {
    fontSize: 16,
    color: '#ccc',
    lineHeight: 24,
  },
});