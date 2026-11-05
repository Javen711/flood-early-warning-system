import React, { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { colors, riskColor } from '../theme';

// Five bars that rise like phone signal bars: tap the fourth for "4 out of 5".
export function RatingBars({ value, onRate }) {
  return (
    <View style={styles.ratingRow}>
      <Text style={styles.ratingLabel}>Was this useful?</Text>
      <View style={styles.bars}>
        {[1, 2, 3, 4, 5].map((n) => (
          <Pressable
            key={n}
            onPress={() => onRate(n)}
            hitSlop={{ top: 12, bottom: 12, left: 4, right: 4 }}
            accessibilityRole="button"
            accessibilityLabel={`Rate ${n} out of 5`}
            accessibilityState={{ selected: n === value }}
          >
            <View style={[styles.bar, { height: 8 + n * 5, backgroundColor: n <= (value || 0) ? colors.waterDark : colors.line }]} />
          </Pressable>
        ))}
      </View>
    </View>
  );
}

export function Button({ title, onPress, loading = false, variant = 'primary', disabled = false }) {
  const isPrimary = variant === 'primary';
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      disabled={loading || disabled}
      style={({ pressed }) => [
        styles.button,
        isPrimary ? styles.buttonPrimary : styles.buttonGhost,
        (pressed || disabled) && { opacity: 0.7 },
      ]}
    >
      {loading
        ? <ActivityIndicator color={isPrimary ? colors.riverDeep : colors.river} />
        : <Text style={[styles.buttonText, !isPrimary && { color: colors.river }]}>{title}</Text>}
    </Pressable>
  );
}

export function Field({ label, error, secure = false, ...inputProps }) {
  const [hidden, setHidden] = useState(secure);
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <View style={[styles.inputWrap, error && { borderColor: colors.high }]}>
        <TextInput
          style={styles.input}
          placeholderTextColor={colors.muted}
          secureTextEntry={hidden}
          autoCapitalize="none"
          autoCorrect={false}
          {...inputProps}
        />
        {secure && (
          <Pressable onPress={() => setHidden(!hidden)} hitSlop={10} accessibilityRole="button">
            <Text style={styles.toggle}>{hidden ? 'Show' : 'Hide'}</Text>
          </Pressable>
        )}
      </View>
      {!!error && <Text style={styles.error}>{error}</Text>}
    </View>
  );
}

export function Banner({ text, kind = 'error' }) {
  if (!text) return null;
  const isError = kind === 'error';
  return (
    <View style={[styles.banner, { backgroundColor: isError ? colors.errorBg : colors.infoBg, borderLeftColor: isError ? colors.high : colors.water }]}>
      <Text style={{ color: isError ? colors.errorText : colors.infoText, fontSize: 14 }}>{text}</Text>
    </View>
  );
}

export function RiskPill({ level, label, large = false }) {
  return (
    <View style={[styles.pill, { backgroundColor: riskColor(level) }, large && styles.pillLarge]}>
      <Text style={[styles.pillText, large && { fontSize: 18 }]}>{label || 'No data'}</Text>
    </View>
  );
}

export function Card({ children, style }) {
  return <View style={[styles.card, style]}>{children}</View>;
}

const styles = StyleSheet.create({
  ratingRow: { flexDirection: 'row', alignItems: 'flex-end', marginTop: 10 },
  ratingLabel: { fontSize: 13, color: colors.muted, marginRight: 12, marginBottom: 1 },
  bars: { flexDirection: 'row', alignItems: 'flex-end', gap: 6 },
  bar: { width: 12, borderRadius: 3 },
  button: { minHeight: 50, borderRadius: 8, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 16 },
  buttonPrimary: { backgroundColor: colors.amber },
  buttonGhost: { backgroundColor: 'transparent', borderWidth: 1.5, borderColor: colors.river },
  buttonText: { fontSize: 16, fontWeight: '700', color: colors.riverDeep },
  field: { marginBottom: 14 },
  label: { fontSize: 14, fontWeight: '600', color: colors.ink, marginBottom: 6 },
  inputWrap: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: colors.white,
    borderWidth: 1.5, borderColor: colors.line, borderRadius: 8, paddingHorizontal: 12,
  },
  input: { flex: 1, minHeight: 48, fontSize: 16, color: colors.ink },
  toggle: { color: colors.water, fontWeight: '700', fontSize: 14, paddingLeft: 8 },
  error: { color: colors.errorText, fontSize: 13, marginTop: 4 },
  banner: { borderLeftWidth: 4, padding: 12, borderRadius: 4, marginBottom: 14 },
  pill: { alignSelf: 'flex-start', paddingHorizontal: 12, paddingVertical: 4, borderRadius: 999 },
  pillLarge: { paddingHorizontal: 18, paddingVertical: 8 },
  pillText: { color: colors.white, fontWeight: '700', fontSize: 13 },
  card: { backgroundColor: colors.white, borderRadius: 12, borderWidth: 1, borderColor: colors.line, padding: 16, marginBottom: 14 },
});
