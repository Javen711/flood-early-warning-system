import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { colors, fonts, riskColor } from '../theme';

// One alert on a vertical line, like a river running through time. The dot
// takes the risk colour, so you can scan the whole history at a glance.
export default function TimelineEntry({ alert, timeText, children, last = false }) {
  const color = riskColor(alert.risk_level);
  return (
    <View style={styles.row}>
      <View style={styles.rail}>
        <View style={[styles.line, last && { bottom: '60%' }]} />
        <View style={[styles.dot, { backgroundColor: color }]} />
      </View>
      <View style={styles.content}>
        <View style={styles.head}>
          <Text style={[styles.level, { color }]}>{alert.risk_label}</Text>
          <Text style={styles.time}>{timeText}</Text>
        </View>
        <Text style={styles.message}>{alert.message}</Text>
        {children}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row' },
  rail: { width: 28, alignItems: 'center' },
  line: { position: 'absolute', top: 0, bottom: 0, width: 2, backgroundColor: colors.line },
  dot: { width: 14, height: 14, borderRadius: 7, marginTop: 6, borderWidth: 3, borderColor: colors.mist },
  content: { flex: 1, paddingBottom: 22, paddingLeft: 4 },
  head: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' },
  level: { fontFamily: fonts.display, fontSize: 22 },
  time: { fontSize: 13, color: colors.muted },
  message: { fontSize: 15, lineHeight: 22, color: colors.ink, marginTop: 2 },
});
