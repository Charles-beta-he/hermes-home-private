#!/usr/bin/env node
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';

const helperPath = '/Users/charles/Desktop/folder/work/uaec-react-h5/src/pages/ContractPage/ContractInterface/klineDataMerge.ts';
const interfacePath = '/Users/charles/Desktop/folder/work/uaec-react-h5/src/pages/ContractPage/ContractInterface/ContractInterface.tsx';
const { upsertKlineData } = await import(pathToFileURL(helperPath).href);

const existing = [
  { time: '100', close: '1' },
  { time: '200', close: '2', volume: '10' }
];

const replaced = upsertKlineData(existing, [{ time: 200, close: '3', volume: '11' }]);
assert.equal(replaced.length, 2, 'same bucket must not append');
assert.equal(replaced[1].close, '3', 'same bucket must replace stale candle');
assert.equal(replaced[1].volume, '11');

const appended = upsertKlineData(replaced, [{ timestamp: '300', close: '4' }]);
assert.equal(appended.length, 3, 'new bucket must append');
assert.equal(appended[2].close, '4');

const wsBatch = upsertKlineData(existing, [
  { timestamp: 200, close: '3' },
  { time: 300, close: '4' }
]);
assert.deepEqual(wsBatch.map((item) => item.close), ['1', '3', '4']);

assert.deepEqual(upsertKlineData(existing, null), existing);
assert.deepEqual(upsertKlineData(null, [{ time: 100, close: '1' }]), [{ time: 100, close: '1' }]);

const interfaceSource = await readFile(interfacePath, 'utf8');
assert.equal(
  interfaceSource.match(/return upsertKlineData\(/g)?.length,
  2,
  'HTTP/WS initial merge and incremental WS merge must share the upsert rule'
);

console.log(JSON.stringify({
  result: 'PASS',
  sameBucketLength: replaced.length,
  sameBucketClose: replaced[1].close,
  appendedLength: appended.length,
  normalizedNumericStringBucket: wsBatch[1].close,
  integratedMergePaths: 2
}));
