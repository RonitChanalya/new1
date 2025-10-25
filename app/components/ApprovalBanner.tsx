// app/components/ApprovalBanner.tsx
import React from 'react';
import { View, Text, Button, StyleSheet } from 'react-native';
export default function ApprovalBanner({ requestId, onPoll }: any) {
  return (
    <View style={styles.box}>
      <Text style={{color:'#fff'}}>Pending approval (request {requestId})</Text>
      <Button title="Check Approval" onPress={onPoll}/>
    </View>
  );
}
const styles = StyleSheet.create({
  box:{ backgroundColor:'#1f2937', padding:10, borderRadius:6, margin:8 }
});
