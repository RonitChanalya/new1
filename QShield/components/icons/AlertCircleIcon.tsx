import React from 'react';
import Svg, { Circle, Line } from 'react-native-svg';

interface IconProps {
  size?: number;
  color?: string;
}

export function AlertCircleIcon({ size = 24, color = 'currentColor' }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      <Circle 
        cx="12" 
        cy="12" 
        r="10" 
        fill="none" 
        stroke={color} 
        strokeWidth="2" 
        strokeLinecap="round" 
        strokeLinejoin="round"
      />
      <Line 
        x1="12" 
        x2="12" 
        y1="8" 
        y2="12" 
        fill="none" 
        stroke={color} 
        strokeWidth="2" 
        strokeLinecap="round" 
        strokeLinejoin="round"
      />
      <Line 
        x1="12" 
        x2="12.01" 
        y1="16" 
        y2="16" 
        fill="none" 
        stroke={color} 
        strokeWidth="2" 
        strokeLinecap="round" 
        strokeLinejoin="round"
      />
    </Svg>
  );
}
