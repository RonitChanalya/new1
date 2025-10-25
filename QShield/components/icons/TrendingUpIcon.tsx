import React from 'react';
import Svg, { Polyline } from 'react-native-svg';

interface IconProps {
  size?: number;
  color?: string;
}

export function TrendingUpIcon({ size = 24, color = 'currentColor' }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      <Polyline 
        points="22 7 13.5 15.5 8.5 10.5 2 17" 
        fill="none" 
        stroke={color} 
        strokeWidth="2" 
        strokeLinecap="round" 
        strokeLinejoin="round"
      />
      <Polyline 
        points="16 7 22 7 22 13" 
        fill="none" 
        stroke={color} 
        strokeWidth="2" 
        strokeLinecap="round" 
        strokeLinejoin="round"
      />
    </Svg>
  );
}
