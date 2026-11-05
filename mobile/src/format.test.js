const test = require('node:test');
const assert = require('node:assert/strict');
const { formatEAT, timeAgo, firstError, mapRegisterErrors } = require('./format');

test('formatEAT shows Nairobi time (UTC+3)', () => {
  assert.equal(formatEAT('2026-11-04T16:49:01Z'), '04 Nov 2026, 19:49');
});

test('formatEAT rolls over midnight into the next day', () => {
  assert.equal(formatEAT('2026-12-31T22:30:00Z'), '01 Jan 2027, 01:30');
});

test('formatEAT handles empty or invalid input', () => {
  assert.equal(formatEAT(null), '');
  assert.equal(formatEAT('not a date'), '');
});

test('timeAgo picks a sensible unit', () => {
  const now = Date.parse('2026-11-04T12:00:00Z');
  assert.equal(timeAgo('2026-11-04T11:59:40Z', now), 'just now');
  assert.equal(timeAgo('2026-11-04T11:55:00Z', now), '5 min ago');
  assert.equal(timeAgo('2026-11-04T09:00:00Z', now), '3 h ago');
  assert.equal(timeAgo('2026-11-03T11:00:00Z', now), '1 day ago');
  assert.equal(timeAgo('2026-11-01T12:00:00Z', now), '3 days ago');
});

test('firstError returns the first message', () => {
  assert.equal(firstError({ phone_number: ['Bad number.'], zone: ['Required.'] }), 'Bad number.');
  assert.equal(firstError(null), '');
});

test('mapRegisterErrors renames password fields and form-level errors', () => {
  assert.deepEqual(
    mapRegisterErrors({ password2: ['Too common.'], __all__: ['Oops.'], username: ['Taken.'] }),
    { password: 'Too common.', form: 'Oops.', username: 'Taken.' },
  );
});
