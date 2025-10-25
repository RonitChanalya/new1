import React, { useState } from 'react';
import { View, Text, TouchableOpacity, ScrollView, StyleSheet } from 'react-native';
import { LockIcon, ShieldIcon, ActivityIcon, ClockIcon } from '../components/icons';

interface SettingItem {
  id: string;
  title: string;
  description: string;
  enabled: boolean;
  type: 'toggle' | 'dropdown';
  options?: string[];
  selectedOption?: string;
}

export default function SettingsPanel() {
  const [settings, setSettings] = useState<SettingItem[]>([
    // Encryption Section
    {
      id: 'force-e2e',
      title: 'Force E2E Encryption',
      description: 'Require encryption on all communications',
      enabled: true,
      type: 'toggle',
    },
    {
      id: 'metadata-protection',
      title: 'Metadata Protection',
      description: 'Strip metadata from all messages',
      enabled: true,
      type: 'toggle',
    },
    {
      id: 'encryption-protocol',
      title: 'Encryption Protocol',
      description: 'Select encryption standard',
      enabled: true,
      type: 'dropdown',
      options: ['AES-256', 'ChaCha20-Poly1305', 'XChaCha20-Poly1305'],
      selectedOption: 'AES-256',
    },
    // Message Controls Section
    {
      id: 'auto-destruct',
      title: 'Auto-Destruct Messages',
      description: 'Messages self-destruct after timer expires',
      enabled: true,
      type: 'toggle',
    },
    {
      id: 'destruct-timer',
      title: 'Default Destruct Timer',
      description: 'Time before auto-deletion',
      enabled: true,
      type: 'dropdown',
      options: ['15 seconds', '30 seconds', '1 minute', '5 minutes'],
      selectedOption: '30 seconds',
    },
    {
      id: 'history-retention',
      title: 'History Retention',
      description: 'How long to keep message history',
      enabled: true,
      type: 'dropdown',
      options: ['1 day', '3 days', '7 days', '30 days'],
      selectedOption: '7 days',
    },
    // Authentication Section
    {
      id: 'biometric-auth',
      title: 'Biometric Authentication',
      description: 'Use fingerprint or face recognition',
      enabled: true,
      type: 'toggle',
    },
    {
      id: 'two-factor',
      title: 'Two-Factor Authentication',
      description: 'Require 2FA token for login',
      enabled: true,
      type: 'toggle',
    },
    {
      id: 'session-timeout',
      title: 'Session Timeout',
      description: 'Auto-logout after inactivity',
      enabled: true,
      type: 'dropdown',
      options: ['5 minutes', '15 minutes', '30 minutes', '1 hour'],
      selectedOption: '15 minutes',
    },
    // AI & Monitoring Section
    {
      id: 'threat-analysis',
      title: 'Real-time Threat Analysis',
      description: 'AI-powered security monitoring',
      enabled: true,
      type: 'toggle',
    },
    {
      id: 'alert-notifications',
      title: 'Alert Notifications',
      description: 'Receive security alerts and warnings',
      enabled: true,
      type: 'toggle',
    },
    {
      id: 'alert-sensitivity',
      title: 'Alert Sensitivity',
      description: 'Threat detection threshold',
      enabled: true,
      type: 'dropdown',
      options: ['Low', 'Balanced', 'High', 'Maximum'],
      selectedOption: 'Balanced',
    },
  ]);

  const toggleSetting = (id: string) => {
    setSettings(prev => prev.map(setting => 
      setting.id === id ? { ...setting, enabled: !setting.enabled } : setting
    ));
  };

  const selectOption = (id: string, option: string) => {
    setSettings(prev => prev.map(setting => 
      setting.id === id ? { ...setting, selectedOption: option } : setting
    ));
  };

  const renderSettingItem = (setting: SettingItem) => {
    if (setting.type === 'toggle') {
      return (
        <TouchableOpacity
          key={setting.id}
          style={styles.settingItem}
          onPress={() => toggleSetting(setting.id)}
        >
          <View style={styles.settingContent}>
            <Text style={styles.settingTitle}>{setting.title}</Text>
            <Text style={styles.settingDescription}>{setting.description}</Text>
          </View>
          <View style={[styles.toggle, setting.enabled && styles.toggleActive]}>
            <View style={[styles.toggleThumb, setting.enabled && styles.toggleThumbActive]} />
          </View>
        </TouchableOpacity>
      );
    }

    return (
      <View key={setting.id} style={styles.settingItem}>
        <View style={styles.settingContent}>
          <Text style={styles.settingTitle}>{setting.title}</Text>
          <Text style={styles.settingDescription}>{setting.description}</Text>
        </View>
        <View style={styles.dropdown}>
          <Text style={styles.dropdownText}>{setting.selectedOption}</Text>
        </View>
      </View>
    );
  };

  const renderSection = (title: string, icon: React.ReactElement, subtitle: string, settingIds: string[]) => {
    const sectionSettings = settings.filter(setting => settingIds.includes(setting.id));
    
    return (
      <View key={title} style={styles.section}>
        <View style={styles.sectionHeader}>
          <View style={{ marginRight: 16 }}>
            {icon}
          </View>
          <View style={styles.sectionContent}>
            <Text style={styles.sectionTitle}>{title}</Text>
            <Text style={styles.sectionSubtitle}>{subtitle}</Text>
          </View>
        </View>
        <View style={styles.sectionSettings}>
          {sectionSettings.map(renderSettingItem)}
        </View>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollContainer}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Security Settings</Text>
          <Text style={styles.subtitle}>Configure encryption, authentication, and privacy controls.</Text>
        </View>

        {/* Settings Sections */}
        {renderSection(
          'Encryption',
          <LockIcon size={20} color="hsl(210, 40%, 98%)" />,
          'End-to-end encryption settings',
          ['force-e2e', 'metadata-protection', 'encryption-protocol']
        )}

        {renderSection(
          'Message Controls',
          <ClockIcon size={20} color="hsl(210, 40%, 98%)" />,
          'Auto-destruct and retention settings',
          ['auto-destruct', 'destruct-timer', 'history-retention']
        )}

        {renderSection(
          'Authentication',
          <ShieldIcon size={20} color="hsl(210, 40%, 98%)" />,
          'Security and access controls',
          ['biometric-auth', 'two-factor', 'session-timeout']
        )}

        {renderSection(
          'AI & Monitoring',
          <ActivityIcon size={20} color="hsl(210, 40%, 98%)" />,
          'Threat detection settings',
          ['threat-analysis', 'alert-notifications', 'alert-sensitivity']
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'hsl(217, 45%, 10%)', // --background
  },
  scrollContainer: {
    flex: 1,
    padding: 24,
  },
  header: {
    marginBottom: 40,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: 'hsl(180, 94%, 29%)', // --primary
    marginBottom: 12,
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 18,
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
    fontWeight: '400',
  },
  section: {
    marginBottom: 40,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  sectionContent: {
    flex: 1,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: 'hsl(180, 94%, 29%)', // --primary
    marginBottom: 6,
    letterSpacing: -0.25,
  },
  sectionSubtitle: {
    fontSize: 16,
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
    fontWeight: '400',
  },
  sectionSettings: {
    backgroundColor: 'hsl(220, 20%, 15%)', // --card
    borderRadius: 6, // --radius
    padding: 20,
    borderWidth: 1,
    borderColor: 'hsl(220, 15%, 25%)', // --border
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'hsl(220, 15%, 25%)', // --border
  },
  settingContent: {
    flex: 1,
  },
  settingTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: 'hsl(210, 40%, 98%)', // --foreground
    marginBottom: 6,
  },
  settingDescription: {
    fontSize: 16,
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
    lineHeight: 22,
  },
  toggle: {
    width: 48,
    height: 28,
    backgroundColor: 'hsl(220, 15%, 20%)', // --secondary
    borderRadius: 14,
    padding: 2,
    justifyContent: 'center',
  },
  toggleActive: {
    backgroundColor: 'hsl(180, 94%, 29%)', // --primary
  },
  toggleThumb: {
    width: 24,
    height: 24,
    backgroundColor: 'hsl(210, 40%, 98%)', // --foreground
    borderRadius: 12,
    alignSelf: 'flex-start',
  },
  toggleThumbActive: {
    alignSelf: 'flex-end',
  },
  dropdown: {
    backgroundColor: 'hsl(220, 15%, 20%)', // --secondary
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 6, // --radius
    minWidth: 140,
    borderWidth: 1,
    borderColor: 'hsl(220, 15%, 25%)', // --border
  },
  dropdownText: {
    color: 'hsl(210, 40%, 98%)', // --foreground
    fontSize: 14,
    fontWeight: '500',
  },
});
