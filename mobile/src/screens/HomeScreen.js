import React, { useCallback, useEffect, useState } from 'react';
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import GaugeHero from '../components/GaugeHero';
import TimelineEntry from '../components/Timeline';
import { Banner } from '../components/ui';
import { api, ApiError } from '../api';
import { formatEAT, timeAgo } from '../format';
import { colors, fonts } from '../theme';

const REFRESH_EVERY_MS = 60000;

export default function HomeScreen({ token, user, onUnauthorized, onSeeAlerts }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      setData(await api.myZone(token));
      setError('');
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) return onUnauthorized();
      setError(e instanceof ApiError ? e.message : 'Could not load your zone.');
    }
  }, [token, onUnauthorized]);

  useEffect(() => {
    load();
    const timer = setInterval(load, REFRESH_EVERY_MS);
    return () => clearInterval(timer);
  }, [load]);

  async function onRefresh() {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }

  const risk = data?.risk;
  const firstName = (user.full_name || user.username).split(' ')[0];

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: colors.mist }}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {data?.zone ? (
        <GaugeHero
          greeting={`Hello, ${firstName}`}
          zoneName={data.zone.zone_name}
          ward={data.zone.ward}
          risk={risk}
        />
      ) : (
        <View style={styles.plain}>
          <Text style={styles.greeting}>Hello, {firstName}</Text>
          {!data && !error && <Text style={styles.muted}>Loading your zone...</Text>}
          {data && !data.zone && <Text style={styles.body}>Your account isn't linked to a zone. Ask a disaster management officer to add you.</Text>}
        </View>
      )}

      <View style={styles.section}>
        <Banner text={error} />
        {data?.zone && risk && (
          <View style={{ marginBottom: 24 }}>
            <Text style={styles.muted}>Updated {timeAgo(risk.predicted_at)}</Text>
            <Text style={styles.muted}>{formatEAT(risk.predicted_at)}</Text>
          </View>
        )}

        {data?.zone && (
          <>
            <Text style={styles.heading}>Latest alerts</Text>
            {data.alerts.length === 0 && <Text style={styles.muted}>No alerts have been sent to your zone.</Text>}
            {data.alerts.map((alert, i) => (
              <TimelineEntry key={alert.id} alert={alert} timeText={timeAgo(alert.sent_at)} last={i === data.alerts.length - 1} />
            ))}
            {data.alerts.length > 0 && (
              <Pressable onPress={onSeeAlerts} accessibilityRole="button" style={styles.more}>
                <Text style={styles.moreText}>See all alerts and rate them</Text>
              </Pressable>
            )}
          </>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  plain: { padding: 24 },
  greeting: { fontFamily: fonts.display, fontSize: 34, color: colors.ink },
  section: { padding: 24, paddingTop: 20 },
  heading: { fontFamily: fonts.display, fontSize: 28, color: colors.ink, marginBottom: 12 },
  body: { fontSize: 15, lineHeight: 22, color: colors.ink, marginTop: 6 },
  muted: { fontSize: 13, color: colors.muted },
  more: { marginTop: 4, paddingVertical: 12 },
  moreText: { color: colors.waterDark, fontSize: 16, fontWeight: '700' },
});
