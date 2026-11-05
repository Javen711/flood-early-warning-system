import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, RefreshControl, StyleSheet, Text, View } from 'react-native';
import TimelineEntry from '../components/Timeline';
import { Banner, RatingBars } from '../components/ui';
import { api, ApiError } from '../api';
import { formatEAT } from '../format';
import { colors, fonts } from '../theme';

export default function AlertsScreen({ token, onUnauthorized }) {
  const [items, setItems] = useState([]);
  const [nextUrl, setNextUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const handle = useCallback((e, fallback) => {
    if (e instanceof ApiError && e.status === 401) return onUnauthorized();
    setError(e instanceof ApiError ? e.message : fallback);
  }, [onUnauthorized]);

  const loadFirst = useCallback(async () => {
    try {
      const page = await api.alerts(token);
      setItems(page.results);
      setNextUrl(page.next);
      setError('');
    } catch (e) {
      handle(e, 'Could not load alerts.');
    } finally {
      setLoading(false);
    }
  }, [token, handle]);

  useEffect(() => { loadFirst(); }, [loadFirst]);

  async function loadMore() {
    if (!nextUrl || loadingMore) return;
    setLoadingMore(true);
    try {
      const page = await api.alerts(token, nextUrl);
      setItems((current) => [...current, ...page.results]);
      setNextUrl(page.next);
    } catch (e) {
      handle(e, 'Could not load more alerts.');
    } finally {
      setLoadingMore(false);
    }
  }

  async function onRefresh() {
    setRefreshing(true);
    await loadFirst();
    setRefreshing(false);
  }

  async function rate(alert, rating) {
    const previous = alert.feedback_rating;
    const update = (value) => setItems((current) => current.map((a) => (a.id === alert.id ? { ...a, feedback_rating: value } : a)));
    update(rating); // show the bars straight away, undo if the server says no
    try {
      await api.sendFeedback(token, alert.id, rating);
      setError('');
    } catch (e) {
      update(previous);
      handle(e, 'Could not save your rating.');
    }
  }

  if (loading) return <View style={styles.center}><ActivityIndicator color={colors.river} /></View>;

  return (
    <FlatList
      style={{ flex: 1, backgroundColor: colors.mist }}
      contentContainerStyle={{ padding: 24 }}
      data={items}
      keyExtractor={(a) => String(a.id)}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      onEndReached={loadMore}
      onEndReachedThreshold={0.4}
      ListHeaderComponent={<><Text style={styles.title}>Alerts for your zone</Text><Banner text={error} /></>}
      ListEmptyComponent={<Text style={styles.muted}>No alerts have been sent to your zone.</Text>}
      ListFooterComponent={loadingMore ? <ActivityIndicator color={colors.river} style={{ margin: 12 }} /> : null}
      renderItem={({ item, index }) => (
        <TimelineEntry alert={item} timeText={formatEAT(item.sent_at)} last={index === items.length - 1 && !nextUrl}>
          <RatingBars value={item.feedback_rating} onRate={(n) => rate(item, n)} />
        </TimelineEntry>
      )}
    />
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.mist },
  title: { fontFamily: fonts.display, fontSize: 34, lineHeight: 38, color: colors.ink, marginBottom: 16 },
  muted: { fontSize: 14, color: colors.muted },
});
