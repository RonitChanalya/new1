import React from 'react';
import Svg, { Path, Polyline } from 'react-native-svg';

interface IconProps {
  size?: number;
  color?: string;
}

export function CheckCircleIcon({ size = 24, color = 'currentColor' }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      <Path 
        d="M22 11.08V12a10 10 0 1 1-5.93-9.14" 
        fill="none" 
        stroke={color} 
        strokeWidth="2" 
        strokeLinecap="round" 
        strokeLinejoin="round"
      />
      <Polyline 
        points="22 4 12 14.01 9 11.01" 
        fill="none" 
        stroke={color} 
        strokeWidth="2" 
        strokeLinecap="round" 
        strokeLinejoin="round"
      />
    </Svg>
  );
}
