import Constants from 'expo-constants';
import { Platform } from 'react-native';

// Where the Django server is.
//
// Normally you do NOT need to change anything: when you run the app with
// `npx expo start`, Expo knows your laptop's address on the Wi-Fi and the app
// reuses it, assuming Django is running on port 8000 of the same laptop.
//
// If the app says it "can't reach the server" and you have checked the Wi-Fi,
// type the address by hand between the quotes, for example:
//   const MANUAL_API_URL = 'http://192.168.1.50:8000/api';
const MANUAL_API_URL = '';

const DJANGO_PORT = 8000;

function detectHost() {
  const hostUri = Constants.expoConfig?.hostUri || Constants.expoGoConfig?.debuggerHost;
  if (hostUri) return hostUri.split(':')[0];
  if (Platform.OS === 'web' && typeof window !== 'undefined') return window.location.hostname;
  return 'localhost';
}

export const API_URL = MANUAL_API_URL || `http://${detectHost()}:${DJANGO_PORT}/api`;
