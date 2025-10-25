import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Path } from 'react-native-svg';

interface QShieldLogoProps {
  size?: number;
  showText?: boolean;
  textColor?: string;
  shieldColor?: string;
  textSize?: number;
}

export function QShieldLogoComponent({ 
  size = 32, 
  showText = true, 
  textColor = 'hsl(210, 40%, 98%)',
  shieldColor = 'hsl(180, 94%, 29%)',
  textSize = 16
}: QShieldLogoProps) {
  return (
    <View style={styles.container}>
      <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={shieldColor} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <Path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      </Svg>
      {showText && (
        <Text style={[styles.text, { color: textColor, fontSize: textSize }]}>
          QShield
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  text: {
    fontWeight: '700',
    letterSpacing: 0.5,
    marginLeft: 6,
  },
});
