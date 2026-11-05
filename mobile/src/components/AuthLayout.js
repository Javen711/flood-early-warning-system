import React from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, View } from 'react-native';
import Svg, { Path } from 'react-native-svg';
import { colors, fonts } from '../theme';

// Shared frame for the sign-in and create-account screens: the river-coloured
// header ends in a wave, so the first screen already hints at water.
export default function AuthLayout({ title, subtitle, children }) {
  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView style={{ flex: 1, backgroundColor: colors.mist }} keyboardShouldPersistTaps="handled">
        <View style={styles.hero}>
          <Text style={styles.brand}>AFEWS</Text>
          <Text style={styles.tagline}>Know before the water reaches you.</Text>
          <Svg width="100%" height={26} viewBox="0 0 390 26" preserveAspectRatio="none" style={styles.wave}>
            <Path d="M0 14 C 40 0, 80 26, 130 14 S 220 0, 260 14 S 340 26, 390 10 L390 26 L0 26 Z" fill={colors.mist} />
          </Svg>
        </View>
        <View style={styles.body}>
          <Text style={styles.title}>{title}</Text>
          {!!subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
          {children}
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  hero: { backgroundColor: colors.river, paddingHorizontal: 24, paddingTop: 30, paddingBottom: 54 },
  brand: { color: colors.white, fontFamily: fonts.display, fontSize: 52, lineHeight: 54, letterSpacing: 1 },
  tagline: { color: '#a9c6ce', fontSize: 16, marginTop: 4 },
  wave: { position: 'absolute', left: 0, right: 0, bottom: -1 },
  body: { paddingHorizontal: 24, paddingBottom: 32 },
  title: { fontFamily: fonts.display, fontSize: 34, lineHeight: 38, color: colors.ink },
  subtitle: { fontSize: 15, color: colors.muted, marginTop: 4, marginBottom: 20, lineHeight: 21 },
});
