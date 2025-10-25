// app/index.tsx
import React from 'react';
import { View, Text, Button, StyleSheet } from 'react-native';
import { Link } from 'expo-router';
import { QShieldLogoComponent } from '../components/icons';

export default function Home() {
  return (
    <View style={styles.container}>
      <View style={{ marginBottom: 8 }}>
        <QShieldLogoComponent size={48} />
      </View>
      <Text style={styles.subtitle}>AI-Powered Secure Messaging</Text>
      <Link href="/chat" style={styles.button}><Text style={{color:'#00E0FF'}}>Enter Secure Chat</Text></Link>
    </View>
  );
}

const styles = StyleSheet.create({
  container:{ flex:1, justifyContent:'center', alignItems:'center', backgroundColor:'#0A0F16' },
  subtitle:{ color:'#CCC', marginTop:8, marginBottom:16 },
  button:{ padding:12, borderRadius:8, borderWidth:1, borderColor:'#00E0FF' }
});
