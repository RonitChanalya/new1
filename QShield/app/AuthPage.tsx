import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { QShieldLogo, KeyRoundIcon, FingerprintIcon, ShieldIcon, AlertTriangleIcon, QShieldLogoComponent } from '../components/icons';

interface AuthPageProps {
  onAuthenticated: () => void;
}

export default function AuthPage({ onAuthenticated }: AuthPageProps) {
  const [authMethod, setAuthMethod] = useState<'passphrase' | 'biometric' | '2fa'>('passphrase');
  const [passphrase, setPassphrase] = useState('');

  const handleAuthenticate = () => {
    if (authMethod === 'passphrase' && passphrase.trim()) {
      // For demo purposes, accept any passphrase
      onAuthenticated();
    } else {
      Alert.alert('Authentication Required', 'Please enter a valid passphrase');
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={{ marginBottom: 14 }}>
          <QShieldLogoComponent size={48} textSize={36.56448} />
        </View>
        <Text style={styles.subtitle}>Secure Military Communications</Text>
      </View>

      {/* Authentication Card */}
      <View style={styles.authCard}>
        <Text style={styles.cardTitle}>Authenticate</Text>
        
        {/* Auth Method Selection */}
        <View style={styles.methodGrid}>
          <TouchableOpacity
            style={[styles.methodButton, authMethod === 'passphrase' && styles.activeMethodButton]}
            onPress={() => setAuthMethod('passphrase')}
          >
            <KeyRoundIcon size={24} color="hsl(210, 40%, 98%)" />
            <Text style={[styles.methodText, authMethod === 'passphrase' && styles.activeMethodText]}>Passphrase</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.methodButton, authMethod === 'biometric' && styles.activeMethodButton]}
            onPress={() => setAuthMethod('biometric')}
          >
            <FingerprintIcon size={24} color="hsl(210, 40%, 98%)" />
            <Text style={[styles.methodText, authMethod === 'biometric' && styles.activeMethodText]}>Biometric</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.methodButton, authMethod === '2fa' && styles.activeMethodButton]}
            onPress={() => setAuthMethod('2fa')}
          >
            <ShieldIcon size={24} color="hsl(210, 40%, 98%)" />
            <Text style={[styles.methodText, authMethod === '2fa' && styles.activeMethodText]}>2FA Token</Text>
          </TouchableOpacity>
        </View>

        {/* Auth Forms */}
        {authMethod === 'passphrase' && (
          <View style={styles.formContainer}>
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Secure Passphrase</Text>
              <TextInput
                style={styles.input}
                placeholder="Enter any text (demo mode)"
                placeholderTextColor="hsl(215, 20%, 65%)"
                value={passphrase}
                onChangeText={setPassphrase}
                autoComplete="off"
                autoCorrect={false}
                spellCheck={false}
                onSubmitEditing={handleAuthenticate}
                returnKeyType="done"
              />
            </View>
            <TouchableOpacity style={styles.authButton} onPress={handleAuthenticate}>
              <Text style={styles.authButtonText}>Authenticate</Text>
            </TouchableOpacity>
          </View>
        )}

        {authMethod === 'biometric' && (
          <View style={styles.formContainer}>
            <View style={styles.biometricContainer}>
              <FingerprintIcon size={20} color="hsl(210, 40%, 98%)" />
              <Text style={styles.biometricText}>Place finger on scanner to authenticate</Text>
            </View>
            <TouchableOpacity style={styles.authButton} onPress={handleAuthenticate}>
              <Text style={styles.authButtonText}>Simulate Biometric Scan</Text>
            </TouchableOpacity>
          </View>
        )}

        {authMethod === '2fa' && (
          <View style={styles.formContainer}>
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>2FA Token</Text>
              <TextInput
                style={[styles.input, styles.tokenInput]}
                placeholder="000000"
                placeholderTextColor="hsl(215, 20%, 65%)"
                value={passphrase}
                onChangeText={setPassphrase}
                keyboardType="numeric"
                maxLength={6}
                onSubmitEditing={handleAuthenticate}
                returnKeyType="done"
              />
            </View>
            <TouchableOpacity style={styles.authButton} onPress={handleAuthenticate}>
              <Text style={styles.authButtonText}>Verify Token</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Security Notice */}
        <View style={styles.securityNotice}>
          <AlertTriangleIcon size={16} color="#F59E0B" />
          <Text style={styles.securityText}>End-to-end encrypted. All communications are secure.</Text>
        </View>
      </View>

      {/* Footer */}
      <Text style={styles.footer}>Authorized Personnel Only • v2.1.0</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'hsl(217, 45%, 10%)', // --background
    justifyContent: 'center',
    alignItems: 'center',
    padding: 28, // Reduced from 32
  },
  header: {
    alignItems: 'center',
    marginBottom: 42, // Reduced from 48
  },
  title: {
    fontSize: 28, // Reduced from 32
    fontWeight: '700',
    color: 'hsl(210, 40%, 98%)', // --foreground
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 16, // Reduced from 18
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
    fontWeight: '400',
  },
  authCard: {
    backgroundColor: 'hsl(220, 20%, 15%)', // --card
    borderRadius: 6, // --radius
    padding: 28, // Reduced from 32
    width: '100%',
    maxWidth: 430, // Reduced from 480
    shadowColor: 'hsl(220, 25%, 8%)',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.8,
    shadowRadius: 16,
    elevation: 8,
  },
  cardTitle: {
    fontSize: 22, // Reduced from 24
    fontWeight: '700',
    color: 'hsl(210, 40%, 98%)', // --card-foreground
    textAlign: 'center',
    marginBottom: 28, // Reduced from 32
    letterSpacing: -0.25,
  },
  methodGrid: {
    flexDirection: 'row',
    marginBottom: 22, // Reduced from 24
    gap: 7, // Reduced from 8
  },
  methodButton: {
    flex: 1,
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10, // Reduced from 12
    paddingHorizontal: 7, // Reduced from 8
    borderRadius: 6, // --radius
    backgroundColor: 'hsl(220, 15%, 20%)', // --secondary
    borderWidth: 1,
    borderColor: 'hsl(220, 15%, 25%)', // --border
  },
  activeMethodButton: {
    backgroundColor: 'hsl(180, 94%, 29%)', // --primary
    borderColor: 'hsl(180, 94%, 29%)', // --primary
  },
  methodIcon: {
    fontSize: 20,
    marginBottom: 4,
  },
  methodText: {
    fontSize: 12,
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
    fontWeight: '500',
  },
  activeMethodText: {
    color: 'hsl(210, 40%, 98%)', // --primary-foreground
  },
  formContainer: {
    marginBottom: 22, // Reduced from 24
  },
  inputGroup: {
    marginBottom: 14, // Reduced from 16
  },
  biometricContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 28, // Reduced from 32
    marginBottom: 14, // Reduced from 16
  },
  biometricIcon: {
    fontSize: 56, // Reduced from 64
    marginBottom: 14, // Reduced from 16
  },
  biometricText: {
    fontSize: 13, // Reduced from 14
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
    textAlign: 'center',
    marginBottom: 22, // Reduced from 24
  },
  tokenInput: {
    textAlign: 'center',
    fontSize: 16, // Reduced from 18
    letterSpacing: 3, // Reduced from 4
  },
  inputLabel: {
    fontSize: 15, // Reduced from 16
    color: 'hsl(210, 40%, 98%)', // --foreground
    marginBottom: 10, // Reduced from 12
    fontWeight: '500',
  },
  input: {
    backgroundColor: 'hsl(220, 15%, 22%)', // --input
    borderRadius: 6, // --radius
    padding: 14, // Reduced from 16
    fontSize: 15, // Reduced from 16
    color: 'hsl(210, 40%, 98%)', // --foreground
    marginBottom: 28, // Reduced from 32
    borderWidth: 1,
    borderColor: 'hsl(220, 15%, 25%)', // --border
  },
  authButton: {
    backgroundColor: 'hsl(180, 94%, 29%)', // --primary
    borderRadius: 6, // --radius
    padding: 14, // Reduced from 16
    alignItems: 'center',
    marginBottom: 18, // Reduced from 20
  },
  authButtonText: {
    color: 'hsl(210, 40%, 98%)', // --primary-foreground
    fontSize: 15, // Reduced from 16
    fontWeight: '600',
  },
  securityNotice: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: 'hsl(30, 95%, 44%, 0.1)', // --warning with opacity
    borderWidth: 1,
    borderColor: 'hsl(30, 95%, 44%, 0.3)', // --warning with opacity
    padding: 12,
    borderRadius: 6, // --radius
  },
  securityIcon: {
    fontSize: 16,
    marginRight: 8,
  },
  securityText: {
    color: 'hsl(30, 95%, 44%)', // --warning
    fontSize: 12,
    flex: 1,
    fontWeight: '500',
  },
  footer: {
    position: 'absolute',
    bottom: 28, // Reduced from 32
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
    fontSize: 13, // Reduced from 14
    fontWeight: '400',
  },
});
