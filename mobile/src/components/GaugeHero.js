import React, { useEffect, useRef, useState } from 'react';
import { AccessibilityInfo, Animated, Easing, StyleSheet, Text, View } from 'react-native';
import Svg, { G, Line, Path, Polygon, Rect } from 'react-native-svg';
import { colors, fonts, gaugeLevel } from '../theme';

const STAFF_W = 40;
const WAVE_H = 16;

// The memorable part of the app: a staff gauge with water rising to the zone's
// current risk level. The staff is striped with the three risk colours, the
// water climbs once when the screen opens, and the risk is written large.
export default function GaugeHero({ greeting, zoneName, ward, risk }) {
  const level = gaugeLevel(risk?.level);
  const [height, setHeight] = useState(0);
  const rise = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (!height) return undefined;
    let cancelled = false;
    AccessibilityInfo.isReduceMotionEnabled().then((reduce) => {
      if (cancelled) return;
      if (reduce) rise.setValue(level);
      else Animated.timing(rise, { toValue: level, duration: 1400, easing: Easing.out(Easing.cubic), useNativeDriver: true }).start();
    });
    return () => { cancelled = true; };
  }, [height, level, rise]);

  const translateY = rise.interpolate({ inputRange: [0, 1], outputRange: [height, 0] });
  const word = risk ? risk.label : 'No data';

  return (
    <View
      style={styles.panel}
      onLayout={(e) => setHeight(e.nativeEvent.layout.height)}
      accessible
      accessibilityLabel={risk ? `Flood risk ${risk.label}. ${risk.advice}` : 'No risk assessment yet'}
    >
      {!!height && (
        <Animated.View style={[styles.water, { height, transform: [{ translateY }] }]} pointerEvents="none">
          <Svg width="100%" height={WAVE_H} viewBox="0 0 390 16" preserveAspectRatio="none" style={styles.wave}>
            <Path d="M0 8 C 30 0, 60 16, 97 8 S 165 0, 195 8 S 260 16, 292 8 S 360 0, 390 8 L390 16 L0 16 Z" fill="rgba(63,178,204,0.42)" />
          </Svg>
          <View style={styles.waterBody} />
        </Animated.View>
      )}

      {!!height && <Staff height={height} level={level} />}

      <View style={styles.text}>
        {!!greeting && <Text style={styles.greeting}>{greeting}</Text>}
        <Text style={styles.zone} numberOfLines={2}>{zoneName}</Text>
        {!!ward && <Text style={styles.ward} numberOfLines={2}>{ward}</Text>}
        <Text style={[styles.word, !risk && { fontSize: 44, lineHeight: 50 }]} accessibilityElementsHidden>{word}</Text>
        {!!risk && <Text style={styles.advice}>{risk.advice}</Text>}
        {!risk && <Text style={styles.advice}>No risk assessment has been made for your zone yet. It will appear here after the first prediction.</Text>}
      </View>
    </View>
  );
}

// The painted staff on the left edge: green, amber and red bands with tick marks,
// and a pointer at the current water level.
function Staff({ height, level }) {
  const top = 14;
  const bottom = height - 14;
  const span = bottom - top;
  const bands = [
    { y: top, h: span * 0.3, color: colors.high },
    { y: top + span * 0.3, h: span * 0.35, color: colors.medium },
    { y: top + span * 0.65, h: span * 0.35, color: colors.low },
  ];
  const ticks = Array.from({ length: 11 }, (_, i) => top + (span * i) / 10);
  const pointerY = bottom - span * level;
  return (
    <Svg width={STAFF_W + 14} height={height} style={styles.staff} pointerEvents="none">
      {bands.map((b) => <Rect key={b.color} x={4} y={b.y} width={STAFF_W - 8} height={b.h} fill={b.color} opacity={0.95} />)}
      <G stroke="#ffffff" strokeWidth={1.5}>
        {ticks.map((y, i) => <Line key={i} x1={4} x2={i % 5 === 0 ? STAFF_W - 4 : STAFF_W - 18} y1={y} y2={y} />)}
      </G>
      <Polygon points={`${STAFF_W - 2},${pointerY} ${STAFF_W + 12},${pointerY - 8} ${STAFF_W + 12},${pointerY + 8}`} fill={colors.amber} />
    </Svg>
  );
}

const styles = StyleSheet.create({
  panel: { backgroundColor: colors.river, minHeight: 380, overflow: 'hidden', paddingVertical: 22, paddingRight: 22, paddingLeft: STAFF_W + 34 },
  staff: { position: 'absolute', left: 12, top: 0 },
  water: { position: 'absolute', left: 0, right: 0, bottom: 0 },
  wave: { position: 'absolute', top: -WAVE_H + 1, left: 0 },
  waterBody: { flex: 1, backgroundColor: 'rgba(63,178,204,0.42)', borderTopWidth: 2, borderTopColor: 'rgba(143,220,238,0.9)' },
  text: { flex: 1 },
  greeting: { color: '#a9c6ce', fontSize: 15, marginBottom: 2 },
  zone: { color: colors.white, fontFamily: fonts.display, fontSize: 30, lineHeight: 34 },
  ward: { color: '#a9c6ce', fontSize: 13, lineHeight: 18, marginTop: 2 },
  word: { color: colors.white, fontFamily: fonts.display, fontSize: 96, lineHeight: 100, letterSpacing: -1, marginTop: 18 },
  advice: { color: colors.white, fontSize: 17, lineHeight: 24, marginTop: 6 },
});
