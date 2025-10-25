// app/index.tsx
import React from 'react';
import { View, Text, Button, StyleSheet } from 'react-native';
import { Link } from 'expo-router';

export default function Home() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>🔰 QShield</Text>
      <Text style={styles.subtitle}>AI-Powered Secure Messaging</Text>
      <Link href="/chat" style={styles.button}><Text style={{color:'#00E0FF'}}>Enter Secure Chat</Text></Link>
    </View>
  );
}

const styles = StyleSheet.create({
  container:{ flex:1, justifyContent:'center', alignItems:'center', backgroundColor:'#0A0F16' },
  title:{ color:'#00E0FF', fontSize:28, fontWeight:'700' },
  subtitle:{ color:'#CCC', marginTop:8, marginBottom:16 },
  button:{ padding:12, borderRadius:8, borderWidth:1, borderColor:'#00E0FF' }
});
