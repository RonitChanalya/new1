// app/components/MessageBubble.tsx
import React, { useEffect, useRef, useState } from 'react';
import { Animated, Text, View, StyleSheet } from 'react-native';
export default function MessageBubble({ msg }: any) {
  const expiry = msg.expiry ?? 90; // 90 seconds default
  const [timeLeft, setTimeLeft] = useState<number>(expiry);
  const [visible, setVisible] = useState(true);
  const fade = useRef(new Animated.Value(1)).current;
  useEffect(() => {
    let interval = setInterval(() => setTimeLeft(t => t - 1), 1000);
    return () => clearInterval(interval);
  }, []);
  useEffect(() => {
    if (timeLeft <= 0 && visible) {
      Animated.timing(fade, { toValue: 0, duration: 600, useNativeDriver: true }).start(() => setVisible(false));
    }
  }, [timeLeft, visible]);
  if (!visible) return (<View style={{paddingVertical:6}}><Text style={{color:'#666', textAlign:'center'}}>💥 Message self-destructed</Text></View>);
  return (
    <Animated.View style={[styles.bubble, { opacity: fade }]}>
      <Text style={styles.sender}>{msg.sender}</Text>
      <Text style={styles.text}>{msg.message}</Text>
      <Text style={styles.timer}>⏱ {Math.max(0, timeLeft)}s left</Text>
    </Animated.View>
  );
}
const styles = StyleSheet.create({
  bubble:{ backgroundColor:'#1F2937', padding:10, borderRadius:8, marginVertical:6, alignSelf:'stretch' },
  sender:{ color:'#9BE8FF', fontWeight:'700', marginBottom:4 },
  text:{ color:'#fff', fontSize:15 },
  timer:{ color:'#999', fontSize:11, marginTop:6, textAlign:'right' }
});
