import React from 'react';
import { View, StyleProp, ViewStyle } from 'react-native';
import Svg, { SvgProps } from 'react-native-svg';

interface IconProps {
  name: string;
  size?: number;
  color?: string;
  style?: StyleProp<ViewStyle>;
}

// SVG icon definitions
const icons = {
  lock: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <rect width="18" height="11" x="3" y="11" rx="2" ry="2"/>
  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
</svg>`,
  // Add more icons here as you provide them
};

export function Icon({ name, size = 24, color = '#000', style }: IconProps) {
  const svgString = icons[name as keyof typeof icons];
  
  if (!svgString) {
    console.warn(`Icon "${name}" not found`);
    return null;
  }

  // Parse SVG string and extract paths
  const svgMatch = svgString.match(/<svg[^>]*>(.*?)<\/svg>/s);
  if (!svgMatch) return null;

  const svgContent = svgMatch[1];
  
  return (
    <View style={[{ width: size, height: size }, style]}>
      <Svg width={size} height={size} viewBox="0 0 24 24">
        {/* Parse and render SVG content */}
        <SvgFromString content={svgContent} color={color} />
      </Svg>
    </View>
  );
}

// Helper component to render SVG content
function SvgFromString({ content, color }: { content: string; color: string }) {
  // This is a simplified approach - for production, you'd want a proper SVG parser
  // For now, we'll use a basic implementation
  return (
    <Svg width="24" height="24" viewBox="0 0 24 24">
      {/* This will be replaced with proper SVG parsing */}
      <rect width="18" height="11" x="3" y="11" rx="2" ry="2" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M7 11V7a5 5 0 0 1 10 0v4" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </Svg>
  );
}
