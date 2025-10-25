import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { MessageSquareIcon, ScrollTextIcon, SettingsIcon, ActivityIcon, LockIcon, UsersIcon, ClockIcon, QShieldLogoComponent } from '../components/icons';
import ChatView from './ChatView';
import ThreatMonitor from './ThreatMonitor';
import EncryptionLogs from './EncryptionLogs';
import SettingsPanel from './SettingsPanel';

type ActiveView = 'chats' | 'threat-monitor' | 'encryption-logs' | 'settings';

interface MainLayoutProps {
  onLogout: () => void;
}

export default function MainLayout({ onLogout }: MainLayoutProps) {
  const [activeView, setActiveView] = useState<ActiveView>('chats');

  const renderActiveView = () => {
    switch (activeView) {
      case 'chats':
        return <ChatView />;
      case 'threat-monitor':
        return <ThreatMonitor />;
      case 'encryption-logs':
        return <EncryptionLogs />;
      case 'settings':
        return <SettingsPanel />;
      default:
        return <ChatView />;
    }
  };

  return (
    <View style={styles.container}>
      {/* Sidebar */}
      <View style={styles.sidebar}>
        {/* Logo */}
        <View style={{ marginBottom: 24 }}>
          <QShieldLogoComponent size={32} />
        </View>

        {/* Navigation */}
        <View style={styles.navigation}>
          <TouchableOpacity
            style={[styles.navItem, activeView === 'chats' && styles.activeNavItem]}
            onPress={() => setActiveView('chats')}
          >
            <MessageSquareIcon size={20} color={activeView === 'chats' ? 'hsl(210, 40%, 98%)' : 'hsl(210, 40%, 50%)'} />
            <Text style={[styles.navText, activeView === 'chats' && styles.activeNavText]}>Chats</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.navItem, activeView === 'threat-monitor' && styles.activeNavItem]}
            onPress={() => setActiveView('threat-monitor')}
          >
            <ActivityIcon size={20} color={activeView === 'threat-monitor' ? 'hsl(210, 40%, 98%)' : 'hsl(210, 40%, 50%)'} />
            <Text style={[styles.navText, activeView === 'threat-monitor' && styles.activeNavText]}>Threat Monitor</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.navItem, activeView === 'encryption-logs' && styles.activeNavItem]}
            onPress={() => setActiveView('encryption-logs')}
          >
            <ScrollTextIcon size={20} color={activeView === 'encryption-logs' ? 'hsl(210, 40%, 98%)' : 'hsl(210, 40%, 50%)'} />
            <Text style={[styles.navText, activeView === 'encryption-logs' && styles.activeNavText]}>Encryption Logs</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.navItem, activeView === 'settings' && styles.activeNavItem]}
            onPress={() => setActiveView('settings')}
          >
            <SettingsIcon size={20} color={activeView === 'settings' ? 'hsl(210, 40%, 98%)' : 'hsl(210, 40%, 50%)'} />
            <Text style={[styles.navText, activeView === 'settings' && styles.activeNavText]}>Settings</Text>
          </TouchableOpacity>
        </View>

        {/* Bottom Icons */}
        <View style={styles.bottomIcons}>
          <LockIcon size={20} color="hsl(210, 40%, 50%)" />
          <UsersIcon size={20} color="hsl(210, 40%, 50%)" />
          <ClockIcon size={20} color="hsl(210, 40%, 50%)" />
        </View>
      </View>

      {/* Main Content */}
      <View style={styles.mainContent}>
        {renderActiveView()}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    flexDirection: 'row',
    backgroundColor: 'hsl(217, 45%, 10%)', // --background
  },
  sidebar: {
    width: 115, // 100 * 1.15 (additional 15% increase)
    backgroundColor: 'hsl(220, 25%, 12%)', // --sidebar-background
    alignItems: 'center',
    paddingVertical: 24,
    borderRightWidth: 1,
    borderRightColor: 'hsl(220, 15%, 25%)', // --sidebar-border
  },
  navigation: {
    flex: 1,
    width: '100%',
    paddingHorizontal: 8,
  },
  navItem: {
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 8,
    marginBottom: 4,
    borderRadius: 6, // --radius
    gap: 4,
  },
  activeNavItem: {
    backgroundColor: 'hsl(220, 15%, 20%)', // --sidebar-accent
  },
  navIcon: {
    fontSize: 20,
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
  },
  activeNavIcon: {
    color: 'hsl(180, 94%, 29%)', // --sidebar-primary
  },
  navText: {
    fontSize: 10,
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
    fontWeight: '500',
  },
  activeNavText: {
    color: 'hsl(180, 94%, 29%)', // --sidebar-primary
    fontWeight: '600',
  },
  bottomIcons: {
    alignItems: 'center',
    gap: 12,
    marginTop: 24,
  },
  bottomIcon: {
    fontSize: 16,
    color: 'hsl(150, 70%, 40%)', // --success
  },
  mainContent: {
    flex: 1,
    backgroundColor: 'hsl(217, 45%, 10%)', // --background
  },
});
