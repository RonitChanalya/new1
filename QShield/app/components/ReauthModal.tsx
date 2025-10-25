// app/components/ReauthModal.tsx
import React, {useState} from 'react';
import { Modal, View, Text, Button, TextInput, StyleSheet } from 'react-native';
export default function ReauthModal({ visible, onCancel, onSuccess }: any) {
  const [code, setCode] = useState('');
  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View style={styles.overlay}>
        <View style={styles.box}>
          <Text style={styles.title}>Re-authentication Required</Text>
          <Text style={{color:'#ddd'}}>Enter MFA code (demo)</Text>
          <TextInput 
            placeholder="123456" 
            value={code} 
            onChangeText={setCode} 
            style={styles.input} 
            keyboardType="number-pad"
            onSubmitEditing={() => onSuccess(code)}
            returnKeyType="done"
          />
          <View style={{flexDirection:'row', justifyContent:'space-between', marginTop:12}}>
            <Button title="Cancel" onPress={onCancel}/>
            <Button title="Confirm" onPress={() => onSuccess(code)}/>
          </View>
        </View>
      </View>
    </Modal>
  );
}
const styles = StyleSheet.create({
  overlay:{ flex:1, backgroundColor:'rgba(0,0,0,0.6)', justifyContent:'center', alignItems:'center' },
  box:{ width:'86%', padding:16, backgroundColor:'#0b1020', borderRadius:8 },
  title:{ color:'#00E0FF', fontSize:18, marginBottom:8 },
  input:{ backgroundColor:'#111827', color:'#fff', padding:8, borderRadius:6, marginTop:8 }
});
