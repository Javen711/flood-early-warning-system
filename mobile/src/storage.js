import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

// The sign-in token lives in the phone's secure storage, so you stay signed in
// when you close the app. (The browser version uses localStorage instead.)
const KEY = 'afews_token';

export async function saveToken(token) {
  if (Platform.OS === 'web') {
    try { window.localStorage.setItem(KEY, token); } catch (e) { /* ignore */ }
    return;
  }
  await SecureStore.setItemAsync(KEY, token);
}

export async function loadToken() {
  if (Platform.OS === 'web') {
    try { return window.localStorage.getItem(KEY); } catch (e) { return null; }
  }
  return SecureStore.getItemAsync(KEY);
}

export async function clearToken() {
  if (Platform.OS === 'web') {
    try { window.localStorage.removeItem(KEY); } catch (e) { /* ignore */ }
    return;
  }
  await SecureStore.deleteItemAsync(KEY);
}
