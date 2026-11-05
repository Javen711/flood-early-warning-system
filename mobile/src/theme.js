// Colours match the AFEWS website. The three risk colours are the ones painted
// on the gauge, so a resident learns one colour language across the whole app.
export const colors = {
  river: '#0a3441',
  riverDeep: '#062530',
  water: '#2a9bb5',
  waterDark: '#1b7f9e',
  mist: '#eaf1f3',
  white: '#ffffff',
  ink: '#0d1f26',
  muted: '#5a6f78',
  line: '#cfdce1',
  amber: '#f2a33a',
  low: '#2f7d51',
  medium: '#d98200',
  high: '#b82a35',
  unknown: '#6b7280',
  errorBg: '#fbe9eb',
  errorText: '#8c1f34',
  infoBg: '#e8f1fb',
  infoText: '#234876',
};

// Barlow Condensed is loaded in App.js. It is the lettering of road signs and
// gauge boards: narrow, heavy and readable from a distance. Body text stays in
// the phone's own font, which is the most legible on small, low-end screens.
export const fonts = {
  display: 'BarlowCondensed_700Bold',
  displaySemi: 'BarlowCondensed_600SemiBold',
};

export const riskColor = (level) => ({
  LOW: colors.low,
  MEDIUM: colors.medium,
  HIGH: colors.high,
}[level] || colors.unknown);

// How high the water stands on the gauge for each risk level (0 = empty, 1 = full).
export const gaugeLevel = (level) => ({ LOW: 0.22, MEDIUM: 0.55, HIGH: 0.86 }[level] ?? 0.08);
