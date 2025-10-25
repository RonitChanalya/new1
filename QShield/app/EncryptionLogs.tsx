import React from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import { LockIcon, CheckCircleIcon, ActivityIcon, ClockIcon } from '../components/icons';

interface LogEntry {
  id: string;
  type: string;
  entity: string;
  description: string;
  timestamp: string;
}

export default function EncryptionLogs() {
  const logEntries: LogEntry[] = [
    {
      id: '1',
      type: 'Key Exchange',
      entity: 'Alpha Team',
      description: 'AES-256 key rotation completed',
      timestamp: '14:34:12',
    },
    {
      id: '2',
      type: 'Message Encrypted',
      entity: 'Command HQ',
      description: 'E2E encryption verified',
      timestamp: '14:32:45',
    },
    {
      id: '3',
      type: 'Channel Created',
      entity: 'Bravo Squad',
      description: 'New secure channel established',
      timestamp: '14:28:03',
    },
    {
      id: '4',
      type: 'Authentication',
      entity: 'System',
      description: 'Biometric verification completed',
      timestamp: '14:15:22',
    },
    {
      id: '5',
      type: 'Auto-Destruct',
      entity: 'Alpha Team',
      description: 'Message self-destructed after 30s',
      timestamp: '14:10:51',
    },
  ];

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerContent}>
          <Text style={styles.title}>Encryption Logs</Text>
          <Text style={styles.subtitle}>Complete audit trail of all encryption operations</Text>
        </View>
        <View style={styles.statusTag}>
          <LockIcon size={16} color="hsl(210, 40%, 98%)" />
          <Text style={styles.statusText}>AES-256 Active</Text>
        </View>
      </View>

      {/* Summary Statistics */}
      <View style={styles.statsContainer}>
        <View style={styles.statCard}>
          <View style={[styles.statIconContainer, { backgroundColor: 'hsl(150, 70%, 40%, 0.2)' }]}>
            <CheckCircleIcon size={20} color="hsl(150, 70%, 40%)" />
          </View>
          <View style={styles.statContent}>
            <Text style={styles.statTitle}>Operations Today</Text>
            <Text style={styles.statValue}>247</Text>
          </View>
        </View>

        <View style={styles.statCard}>
          <View style={[styles.statIconContainer, { backgroundColor: 'hsl(180, 94%, 29%, 0.2)' }]}>
            <LockIcon size={20} color="hsl(180, 94%, 29%)" />
          </View>
          <View style={styles.statContent}>
            <Text style={styles.statTitle}>Messages Encrypted</Text>
            <Text style={styles.statValue}>1,429</Text>
          </View>
        </View>

        <View style={styles.statCard}>
          <View style={[styles.statIconContainer, { backgroundColor: 'hsl(180, 94%, 29%, 0.2)' }]}>
            <ClockIcon size={20} color="hsl(180, 94%, 29%)" />
          </View>
          <View style={styles.statContent}>
            <Text style={styles.statTitle}>Avg. Processing</Text>
            <Text style={styles.statValue}>12ms</Text>
          </View>
        </View>
      </View>

      {/* Recent Activity */}
      <View style={styles.activityContainer}>
        <Text style={styles.sectionTitle}>Recent Activity</Text>
        
        <ScrollView style={styles.activityList}>
          {logEntries.map((entry) => (
            <View key={entry.id} style={styles.activityItem}>
              <View style={styles.activityIconContainer}>
                <ActivityIcon size={16} color="hsl(150, 70%, 40%)" />
              </View>
              
              <View style={styles.activityContent}>
                <View style={styles.activityHeader}>
                  <Text style={styles.activityType}>{entry.type}</Text>
                  <View style={styles.entityTag}>
                    <Text style={styles.entityText}>{entry.entity}</Text>
                  </View>
                </View>
                <Text style={styles.activityDescription}>{entry.description}</Text>
              </View>
              
              <Text style={styles.activityTimestamp}>{entry.timestamp}</Text>
            </View>
          ))}
        </ScrollView>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'hsl(217, 45%, 10%)', // --background
    padding: 24,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 32,
  },
  headerContent: {
    flex: 1,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: 'hsl(210, 40%, 98%)', // --foreground
    marginBottom: 8,
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 18,
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
    fontWeight: '400',
  },
  statusTag: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'hsl(220, 15%, 20%)', // --secondary
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 6, // --radius
  },
  statusIcon: {
    fontSize: 14,
    marginRight: 8,
  },
  statusText: {
    color: 'hsl(210, 40%, 98%)', // --secondary-foreground
    fontSize: 14,
    fontWeight: '600',
  },
  statsContainer: {
    flexDirection: 'row',
    marginBottom: 24,
    gap: 16,
  },
  statCard: {
    flex: 1,
    backgroundColor: 'hsl(220, 20%, 15%)', // --card
    padding: 16,
    borderRadius: 6, // --radius
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  statIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 6,
    alignItems: 'center',
    justifyContent: 'center',
  },
  statIcon: {
    fontSize: 20,
  },
  statContent: {
    flex: 1,
  },
  statTitle: {
    fontSize: 12,
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
    marginBottom: 4,
    fontWeight: '500',
  },
  statValue: {
    fontSize: 18,
    fontWeight: '700',
    color: 'hsl(210, 40%, 98%)', // --foreground
    letterSpacing: -0.25,
  },
  activityContainer: {
    flex: 1,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: 'hsl(210, 40%, 98%)', // --foreground
    marginBottom: 20,
    letterSpacing: -0.25,
  },
  activityList: {
    flex: 1,
  },
  activityItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: 'hsl(220, 20%, 15%)', // --card
    padding: 16,
    borderRadius: 6, // --radius
    marginBottom: 0,
    borderBottomWidth: 1,
    borderBottomColor: 'hsl(220, 15%, 25%)', // --border
  },
  activityIconContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'hsl(150, 70%, 40%, 0.2)', // --success with opacity
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
    marginTop: 4,
  },
  activityIcon: {
    fontSize: 16,
    color: 'hsl(150, 70%, 40%)', // --success
  },
  activityContent: {
    flex: 1,
  },
  activityHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  activityType: {
    fontSize: 14,
    fontWeight: '600',
    color: 'hsl(210, 40%, 98%)', // --foreground
    flex: 1,
  },
  entityTag: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: 'hsl(220, 15%, 25%)', // --border
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  entityText: {
    color: 'hsl(210, 40%, 98%)', // --foreground
    fontSize: 12,
    fontWeight: '500',
  },
  activityDescription: {
    fontSize: 14,
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
    lineHeight: 20,
  },
  activityTimestamp: {
    fontSize: 12,
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
    marginLeft: 16,
    fontWeight: '500',
  },
});
