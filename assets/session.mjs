export const MAX_FILE_BYTES = 4 * 1024 * 1024;
export const MAX_SAMPLES = 20000;
const alerts = new Set(['OK', 'CPU', 'RAM', 'CPU+RAM']);

export function parseSession(text) {
  if (new TextEncoder().encode(text).length > MAX_FILE_BYTES) {
    throw new Error('O limite é 4 MiB por sessão. Grave um período menor.');
  }
  const samples = [];
  let lineNumber = 0;
  for (const line of text.split('\n')) {
    lineNumber += 1;
    if (!line.trim()) continue;
    if (samples.length >= MAX_SAMPLES) throw new Error('O limite é 20.000 amostras.');
    let row;
    try {
      row = JSON.parse(line);
    } catch {
      throw new Error(`JSON inválido na linha ${lineNumber}.`);
    }
    if (!row || typeof row !== 'object' || Array.isArray(row) || row.v !== 1) {
      throw new Error(`Protocolo incompatível na linha ${lineNumber}. Esperado v1.`);
    }
    for (const key of ['cpu', 'ram', 'disk', 'rx', 'tx', 't']) {
      const upper = ['cpu', 'ram', 'disk'].includes(key) ? 100 : 1e12;
      if (
        typeof row[key] !== 'number' ||
        !Number.isFinite(row[key]) ||
        row[key] < 0 ||
        row[key] > upper
      ) {
        throw new Error(`Campo ${key} inválido na linha ${lineNumber}.`);
      }
    }
    if (!alerts.has(row.alert)) throw new Error(`Alerta inválido na linha ${lineNumber}.`);
    if (samples.length && row.t <= samples[samples.length - 1].t) {
      throw new Error(`Tempo fora de ordem na linha ${lineNumber}. Use uma única sessão.`);
    }
    samples.push({
      v: 1,
      t: row.t,
      cpu: row.cpu,
      ram: row.ram,
      disk: row.disk,
      rx: row.rx,
      tx: row.tx,
      alert: row.alert,
    });
  }
  if (!samples.length) throw new Error('O arquivo não contém amostras.');
  return samples;
}

export function summarize(samples) {
  const duration = samples.at(-1).t - samples[0].t;
  let cpuArea = 0;
  let peakCpu = 0;
  let peakRam = 0;
  let gaps = 0;
  let alertSamples = 0;
  samples.forEach((sample, index) => {
    peakCpu = Math.max(peakCpu, sample.cpu);
    peakRam = Math.max(peakRam, sample.ram);
    if (sample.alert !== 'OK') alertSamples += 1;
    if (index) {
      const previous = samples[index - 1];
      const elapsed = sample.t - previous.t;
      cpuArea += (elapsed * (sample.cpu + previous.cpu)) / 2;
      if (elapsed > 3) gaps += 1;
    }
  });
  return {
    duration,
    peakCpu,
    peakRam,
    meanCpu: duration ? cpuArea / duration : samples[0].cpu,
    gaps,
    alertSamples,
  };
}

export function points(samples, key, width = 900, height = 180, span = null) {
  const start = samples[0].t;
  const duration = span ?? samples.at(-1).t - start;
  return samples
    .map((sample) => {
      const x = duration ? ((sample.t - start) / duration) * width : width / 2;
      const y = height - (sample[key] / 100) * height;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(' ');
}

export function illustrativeSession() {
  return Array.from({ length: 91 }, (_, index) => {
    const cpu =
      index < 15
        ? 13 + Math.sin(index) * 4
        : index < 62
          ? 92 + Math.sin(index / 3) * 5
          : 25 + Math.sin(index / 5) * 10;
    return {
      v: 1,
      t: index,
      cpu,
      ram: 42 + (index < 62 ? index * 0.65 : (90 - index) * 1.1),
      disk: 44,
      rx: 11 + Math.abs(Math.sin(index)) * 20,
      tx: 3 + Math.abs(Math.cos(index)) * 5,
      alert: index >= 25 && index < 62 ? 'CPU' : 'OK',
    };
  });
}
