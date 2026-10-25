import test from 'node:test';
import assert from 'node:assert/strict';
import { parseSession, summarize, points, MAX_FILE_BYTES } from '../assets/session.mjs';

const row = (t, cpu = 10) => ({ v: 1, t, cpu, ram: 50, disk: 20, rx: 0, tx: 0, alert: 'OK' });
const lines = (...rows) => rows.map((value) => JSON.stringify(value)).join('\n');

test('reads CRLF sessions and ignores empty lines', () => {
  assert.equal(parseSession(lines(row(1), row(2)).replaceAll('\n', '\r\n') + '\n\n').length, 2);
});
test('rejects malformed, nonnumeric, out-of-order and incompatible records', () => {
  for (const text of [
    '{',
    'null',
    '[]',
    lines({ ...row(1), v: 2 }),
    lines({ ...row(1), cpu: true }),
    lines({ ...row(1), ram: 101 }),
    lines({ ...row(1), t: undefined }),
    lines(row(2), row(1)),
    lines(row(1), row(1)),
    lines({ ...row(1), alert: '<script>' }),
  ]) {
    assert.throws(() => parseSession(text));
  }
});
test('enforces file and sample limits', () => {
  assert.throws(() => parseSession(' '.repeat(MAX_FILE_BYTES + 1)));
  assert.throws(() =>
    parseSession(Array.from({ length: 20001 }, (_, i) => JSON.stringify(row(i))).join('\n'))
  );
});
test('uses elapsed time for CPU mean with irregular sampling', () => {
  const result = summarize([row(0, 0), row(1, 100), row(10, 100)]);
  assert.equal(result.meanCpu, 95);
  assert.equal(result.peakCpu, 100);
  assert.equal(result.duration, 10);
  assert.equal(result.gaps, 1);
});
test('one-sample session has a meaningful zero-duration summary', () => {
  const result = summarize([row(10, 37)]);
  assert.equal(result.meanCpu, 37);
  assert.equal(result.duration, 0);
  assert.equal(points([row(10, 50)], 'cpu'), '450.00,90.00');
});
test('chart coordinates use elapsed time and share a scale when comparing sessions', () => {
  assert.equal(points([row(0, 0), row(2, 100)], 'cpu', 100, 100, 10), '0.00,100.00 20.00,0.00');
  assert.equal(
    points([row(0, 0), row(1, 50), row(10, 100)], 'cpu', 100, 100),
    '0.00,100.00 10.00,50.00 100.00,0.00'
  );
});
