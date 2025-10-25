const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// Add resolver configuration to handle Node.js modules
config.resolver.alias = {
  ...config.resolver.alias,
  crypto: 'react-native-crypto',
  stream: 'readable-stream',
  buffer: '@craftzdog/react-native-buffer',
  'crypto-js': 'crypto-js',
};

// Add platform extensions
config.resolver.platforms = ['ios', 'android', 'native', 'web'];

// Add source extensions
config.resolver.sourceExts = [...config.resolver.sourceExts, 'cjs'];

module.exports = config;
