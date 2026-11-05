import React, { useCallback, useEffect, useState } from 'react';
import { FlatList, Modal, Pressable, StyleSheet, Text, View } from 'react-native';
import AuthLayout from '../components/AuthLayout';
import { Banner, Button, Field } from '../components/ui';
import { api, ApiError } from '../api';
import { mapRegisterErrors } from '../format';
import { colors, fonts } from '../theme';

export default function RegisterScreen({ onSignedIn, goLogin }) {
  const [form, setForm] = useState({ fullName: '', phone: '', username: '', password: '', confirm: '' });
  const [zones, setZones] = useState([]);
  const [zone, setZone] = useState(null);
  const [zonesError, setZonesError] = useState('');
  const [pickerOpen, setPickerOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [errors, setErrors] = useState({});

  const set = (key) => (value) => setForm((f) => ({ ...f, [key]: value }));

  const loadZones = useCallback(async () => {
    setZonesError('');
    try {
      setZones(await api.zones());
    } catch (e) {
      setZonesError(e instanceof ApiError ? e.message : 'Could not load the zone list.');
    }
  }, []);
  useEffect(() => { loadZones(); }, [loadZones]);

  async function submit() {
    const problems = {};
    if (!form.fullName.trim()) problems.full_name = 'Enter your full name.';
    if (!form.phone.trim()) problems.phone_number = 'Enter your phone number.';
    if (!zone) problems.zone = 'Choose your zone.';
    if (!form.username.trim()) problems.username = 'Choose a username.';
    if (!form.password) problems.password = 'Choose a password.';
    else if (form.password !== form.confirm) problems.confirm = 'The two passwords do not match.';
    setErrors(problems);
    if (Object.keys(problems).length) return;

    setBusy(true);
    try {
      const { token, user } = await api.register({
        full_name: form.fullName.trim(),
        phone_number: form.phone.trim(),
        zone: zone.id,
        username: form.username.trim(),
        password: form.password,
      });
      await onSignedIn(token, user);
    } catch (e) {
      if (e instanceof ApiError && e.errors) setErrors(mapRegisterErrors(e.errors));
      else setErrors({ form: e instanceof ApiError ? e.message : 'Something went wrong. Try again.' });
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthLayout title="Create an account" subtitle="Your phone number is where flood alerts will be sent.">
      <Banner text={errors.form} />
      <Field label="Full name" value={form.fullName} onChangeText={set('fullName')} autoCapitalize="words" error={errors.full_name} />
      <Field label="Phone number" value={form.phone} onChangeText={set('phone')} keyboardType="phone-pad" placeholder="0712 345 678" error={errors.phone_number} />

      <View style={{ marginBottom: 14 }}>
        <Text style={styles.label}>Your zone</Text>
        <Pressable
          onPress={() => setPickerOpen(true)}
          accessibilityRole="button"
          style={[styles.picker, errors.zone && { borderColor: colors.high }]}
        >
          <Text style={{ fontSize: 16, color: zone ? colors.ink : colors.muted }}>{zone ? zone.zone_name : 'Choose your area'}</Text>
          <Text style={{ color: colors.water, fontWeight: '700' }}>Change</Text>
        </Pressable>
        {!!errors.zone && <Text style={styles.error}>{errors.zone}</Text>}
        {!!zonesError && (
          <Pressable onPress={loadZones}><Text style={styles.error}>{zonesError} Tap to try again.</Text></Pressable>
        )}
      </View>

      <Field label="Username" value={form.username} onChangeText={set('username')} error={errors.username} />
      <Field label="Password" value={form.password} onChangeText={set('password')} secure error={errors.password} />
      <Field label="Confirm password" value={form.confirm} onChangeText={set('confirm')} secure error={errors.confirm} onSubmitEditing={submit} />
      <Button title="Create account" onPress={submit} loading={busy} />
      <View style={{ flexDirection: 'row', justifyContent: 'center', marginTop: 20 }}>
        <Text style={{ color: colors.ink, fontSize: 15 }}>Already registered? </Text>
        <Pressable onPress={goLogin} accessibilityRole="link">
          <Text style={{ color: colors.water, fontWeight: '700', fontSize: 15 }}>Sign in</Text>
        </Pressable>
      </View>

      <Modal visible={pickerOpen} animationType="slide" onRequestClose={() => setPickerOpen(false)}>
        <View style={{ flex: 1, backgroundColor: colors.mist, paddingTop: 48 }}>
          <Text style={styles.modalTitle}>Choose your zone</Text>
          <FlatList
            data={zones}
            keyExtractor={(z) => String(z.id)}
            ListEmptyComponent={<Text style={{ padding: 24, color: colors.muted }}>No zones to show yet.</Text>}
            renderItem={({ item }) => (
              <Pressable
                onPress={() => { setZone(item); setPickerOpen(false); }}
                style={[styles.zoneRow, zone?.id === item.id && { backgroundColor: colors.white }]}
                accessibilityRole="button"
              >
                <Text style={{ fontSize: 16, fontWeight: '600', color: colors.ink }}>{item.zone_name}</Text>
                {!!item.ward && <Text style={{ fontSize: 13, color: colors.muted, marginTop: 2 }}>{item.ward}</Text>}
              </Pressable>
            )}
          />
          <View style={{ padding: 16 }}>
            <Button title="Cancel" variant="ghost" onPress={() => setPickerOpen(false)} />
          </View>
        </View>
      </Modal>
    </AuthLayout>
  );
}

const styles = StyleSheet.create({
  label: { fontSize: 14, fontWeight: '600', color: colors.ink, marginBottom: 6 },
  picker: {
    minHeight: 48, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    backgroundColor: colors.white, borderWidth: 1.5, borderColor: colors.line, borderRadius: 8, paddingHorizontal: 12,
  },
  error: { color: colors.errorText, fontSize: 13, marginTop: 4 },
  modalTitle: { fontFamily: fonts.display, fontSize: 32, color: colors.ink, paddingHorizontal: 20, paddingBottom: 12 },
  zoneRow: { paddingHorizontal: 20, paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: colors.line },
});
