import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { useFonts, BarlowCondensed_600SemiBold, BarlowCondensed_700Bold } from '@expo-google-fonts/barlow-condensed';

import { api, ApiError } from './src/api';
import { clearToken, loadToken, saveToken } from './src/storage';
import { colors } from './src/theme';
import { Banner, Button } from './src/components/ui';
import LoginScreen from './src/screens/LoginScreen';
import RegisterScreen from './src/screens/RegisterScreen';
import HomeScreen from './src/screens/HomeScreen';
import AlertsScreen from './src/screens/AlertsScreen';
import AccountScreen from './src/screens/AccountScreen';

const TABS = [
  { key: 'home', label: 'My zone' },
  { key: 'alerts', label: 'Alerts' },
  { key: 'account', label: 'Account' },
];

export default function App() {
  const [fontsLoaded, fontError] = useFonts({ BarlowCondensed_600SemiBold, BarlowCondensed_700Bold });
  const [booting, setBooting] = useState(true);
  const [bootError, setBootError] = useState('');
  const [session, setSession] = useState(null); // { token, user } when signed in
  const [authScreen, setAuthScreen] = useState('login');
  const [tab, setTab] = useState('home');

  // On start, restore the saved sign-in (if any) and check it is still valid.
  const restore = useCallback(async () => {
    setBooting(true);
    setBootError('');
    try {
      const token = await loadToken();
      if (token) {
        const user = await api.me(token);
        if (user.role === 'RESIDENT') setSession({ token, user });
        else await clearToken();
      }
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) await clearToken();
      else setBootError(e instanceof ApiError ? e.message : 'Could not start the app.');
    } finally {
      setBooting(false);
    }
  }, []);
  useEffect(() => { restore(); }, [restore]);

  const onSignedIn = useCallback(async (token, user) => {
    await saveToken(token);
    setTab('home');
    setSession({ token, user });
  }, []);

  const onUnauthorized = useCallback(async () => {
    await clearToken();
    setSession(null);
    setAuthScreen('login');
  }, []);

  const onSignOut = useCallback(async () => {
    if (session) await api.logout(session.token).catch(() => {});
    await onUnauthorized();
  }, [session, onUnauthorized]);

  let content;
  if (booting || !(fontsLoaded || fontError)) {
    content = <View style={styles.center}><ActivityIndicator size="large" color={colors.river} /></View>;
  } else if (bootError) {
    content = (
      <View style={[styles.center, { padding: 24 }]}>
        <Banner text={bootError} />
        <View style={{ alignSelf: 'stretch' }}><Button title="Try again" onPress={restore} /></View>
      </View>
    );
  } else if (!session) {
    content = authScreen === 'login'
      ? <LoginScreen onSignedIn={onSignedIn} goRegister={() => setAuthScreen('register')} />
      : <RegisterScreen onSignedIn={onSignedIn} goLogin={() => setAuthScreen('login')} />;
  } else {
    content = (
      <View style={{ flex: 1 }}>
        <View style={{ flex: 1 }}>
          {tab === 'home' && <HomeScreen token={session.token} user={session.user} onUnauthorized={onUnauthorized} onSeeAlerts={() => setTab('alerts')} />}
          {tab === 'alerts' && <AlertsScreen token={session.token} onUnauthorized={onUnauthorized} />}
          {tab === 'account' && <AccountScreen user={session.user} onSignOut={onSignOut} />}
        </View>
        <View style={styles.tabBar}>
          {TABS.map((t) => (
            <Pressable key={t.key} style={styles.tab} onPress={() => setTab(t.key)} accessibilityRole="tab" accessibilityState={{ selected: tab === t.key }}>
              {tab === t.key && <View style={styles.tabBar_active} />}
              <Text style={[styles.tabText, tab === t.key && styles.tabTextActive]}>{t.label}</Text>
            </Pressable>
          ))}
        </View>
      </View>
    );
  }

  return (
    <SafeAreaProvider>
      <StatusBar style="light" backgroundColor={colors.river} />
      <SafeAreaView style={{ flex: 1, backgroundColor: colors.river }} edges={['top', 'bottom']}>
        <View style={{ flex: 1, backgroundColor: colors.mist }}>{content}</View>
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.mist },
  tabBar: { flexDirection: 'row', backgroundColor: colors.river },
  tab: { flex: 1, alignItems: 'center', paddingVertical: 14 },
  tabBar_active: { position: 'absolute', top: 0, left: 18, right: 18, height: 4, backgroundColor: colors.amber },
  tabText: { fontSize: 15, color: '#a9c6ce', fontWeight: '600' },
  tabTextActive: { color: colors.white },
});
