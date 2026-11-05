import React, { useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { Button } from '../components/ui';
import { API_URL } from '../config';
import { colors, fonts } from '../theme';

function Row({ label, value }) {
  return (
    <View style={styles.row}>
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.value}>{value || '—'}</Text>
    </View>
  );
}

export default function AccountScreen({ user, onSignOut }) {
  const [busy, setBusy] = useState(false);
  return (
    <ScrollView style={{ flex: 1, backgroundColor: colors.mist }} contentContainerStyle={{ padding: 24 }}>
      <Text style={styles.title}>Your account</Text>
      <Row label="Name" value={user.full_name} />
      <Row label="Username" value={user.username} />
      <Row label="Alerts are sent to" value={user.phone_number} />
      <Row label="Zone" value={user.zone ? user.zone.zone_name : ''} />
      <View style={{ marginTop: 28 }}>
        <Button title="Sign out" variant="ghost" loading={busy} onPress={async () => { setBusy(true); await onSignOut(); }} />
      </View>
      <Text style={styles.server}>Server: {API_URL}</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  title: { fontFamily: fonts.display, fontSize: 34, lineHeight: 38, color: colors.ink, marginBottom: 12 },
  row: { paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: colors.line },
  label: { fontSize: 13, color: colors.muted },
  value: { fontSize: 18, color: colors.ink, marginTop: 2 },
  server: { fontSize: 12, color: colors.muted, textAlign: 'center', marginTop: 28 },
});
