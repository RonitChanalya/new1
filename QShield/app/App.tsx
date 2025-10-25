import React, { useState } from 'react';
import { View, StyleSheet } from 'react-native';
import AuthPage from './AuthPage';
import MainLayout from './MainLayout';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const handleAuthenticated = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
  };

  return (
    <View style={styles.container}>
      {!isAuthenticated ? (
        <AuthPage onAuthenticated={handleAuthenticated} />
      ) : (
        <MainLayout onLogout={handleLogout} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1A202C',
  },
});
