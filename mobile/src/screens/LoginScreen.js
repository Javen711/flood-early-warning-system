import React, { useState } from 'react';
import { Pressable, Text, View } from 'react-native';
import AuthLayout from '../components/AuthLayout';
import { Banner, Button, Field } from '../components/ui';
import { api, ApiError } from '../api';
import { colors } from '../theme';

export default function LoginScreen({ onSignedIn, goRegister }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function submit() {
    if (!username.trim() || !password) {
      setError('Enter your username and password.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      const { token, user } = await api.login(username.trim(), password);
      if (user.role !== 'RESIDENT') {
        // Officers use the website. Don't keep a token for an account this app can't use.
        await api.logout(token).catch(() => {});
        setError('This app is for residents. Officers and administrators should use the website.');
        return;
      }
      await onSignedIn(token, user);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Something went wrong. Try again.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthLayout title="Sign in" subtitle="See your zone's flood risk and the alerts sent to you.">
      <Banner text={error} />
      <Field label="Username" value={username} onChangeText={setUsername} autoComplete="username" textContentType="username" />
      <Field label="Password" value={password} onChangeText={setPassword} secure autoComplete="password" textContentType="password" onSubmitEditing={submit} />
      <Button title="Sign in" onPress={submit} loading={busy} />
      <View style={{ flexDirection: 'row', justifyContent: 'center', marginTop: 20 }}>
        <Text style={{ color: colors.ink, fontSize: 15 }}>New here? </Text>
        <Pressable onPress={goRegister} accessibilityRole="link">
          <Text style={{ color: colors.water, fontWeight: '700', fontSize: 15 }}>Create an account</Text>
        </Pressable>
      </View>
    </AuthLayout>
  );
}
