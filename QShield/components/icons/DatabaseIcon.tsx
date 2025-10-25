import React from 'react';
import Svg, { Ellipse, Path } from 'react-native-svg';

interface IconProps {
  size?: number;
  color?: string;
}

export function DatabaseIcon({ size = 24, color = 'currentColor' }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      <Ellipse 
        cx="12" 
        cy="5" 
        rx="9" 
        ry="3" 
        fill="none" 
        stroke={color} 
        strokeWidth="2" 
        strokeLinecap="round" 
        strokeLinejoin="round"
      />
      <Path 
        d="M3 5V19A9 3 0 0 0 21 19V5" 
        fill="none" 
        stroke={color} 
        strokeWidth="2" 
        strokeLinecap="round" 
        strokeLinejoin="round"
      />
      <Path 
        d="M3 12A9 3 0 0 0 21 12" 
        fill="none" 
        stroke={color} 
        strokeWidth="2" 
        strokeLinecap="round" 
        strokeLinejoin="round"
      />
    </Svg>
  );
}
