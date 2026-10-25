import {
  MAX_FILE_BYTES,
  illustrativeSession,
  parseSession,
  points,
  summarize,
} from './session.mjs?v=0.2.0';

const $ = (selector) => document.querySelector(selector);
const slider = $('#sample');
let sessions = [];
let axisDuration = 1;
let importVersion = 0;
const pct = (value) => `${value.toFixed(1)}%`;
const seconds = (value) => `${value.toFixed(1)} s`;
const signed = (value, suffix) => `${value > 0 ? '+' : ''}${value.toFixed(1)}${suffix}`;

function cell(row, text) {
  const element = document.createElement('td');
  element.textContent = text;
  row.append(element);
  return element;
}

function renderRate(element, value) {
  const units = ['KiB/s', 'MiB/s', 'GiB/s', 'TiB/s', 'PiB/s'];
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  element.replaceChildren(document.createTextNode(value.toFixed(1)));
  const suffix = document.createElement('small');
  suffix.textContent = units[unit];
  element.append(suffix);
}

function renderReadout() {
  const samples = sessions[0].samples;
  const sample = samples[Number(slider.value)];
  const elapsed = sample.t - samples[0].t;
  $('#sample-time').textContent =
    `${seconds(elapsed)} · ${Number(slider.value) + 1}/${samples.length}`;
  $('#read-cpu').textContent = pct(sample.cpu);
  $('#read-ram').textContent = pct(sample.ram);
  renderRate($('#read-rx'), sample.rx);
  renderRate($('#read-tx'), sample.tx);
  $('#read-alert').textContent = sample.alert;
  $('#read-alert').style.color = sample.alert === 'OK' ? '#c1cdb8' : 'var(--trace)';
  const x = ((elapsed / axisDuration) * 900).toFixed(2);
  $('#cursor').setAttribute('x1', x);
  $('#cursor').setAttribute('x2', x);
}

function showSessions(next, illustrative = false) {
  sessions = next;
  const summaries = sessions.map((item) => summarize(item.samples));
  axisDuration = Math.max(...summaries.map((item) => item.duration), 1);
  $('#trace-a').setAttribute('points', points(sessions[0].samples, 'cpu', 900, 180, axisDuration));
  $('#trace-ram').setAttribute(
    'points',
    points(sessions[0].samples, 'ram', 900, 180, axisDuration)
  );
  $('#trace-b').setAttribute(
    'points',
    sessions[1] ? points(sessions[1].samples, 'cpu', 900, 180, axisDuration) : ''
  );
  $('#legend-b').hidden = !sessions[1];
  slider.max = sessions[0].samples.length - 1;
  slider.value = '0';
  $('#half-time').textContent = seconds(axisDuration / 2);
  $('#end-time').textContent = seconds(axisDuration);
  $('#source-label').textContent = illustrative ? 'EXEMPLO ILUSTRATIVO' : 'CAPTURA LOCAL';
  const message = $('#session-message');
  message.classList.remove('error');
  message.textContent = illustrative
    ? 'Dados sintéticos para explorar a interface. Nenhuma leitura do seu computador.'
    : sessions.map((item, i) => `${i ? 'B' : 'A'}: ${item.name}`).join(' / ') +
      ' — arquivo lido localmente.';
  $('#sample-count').textContent = sessions
    .map((item, i) => `${i ? 'B' : 'A'}: ${item.samples.length} amostras`)
    .join(' / ');
  const body = $('#session-summary');
  body.replaceChildren();
  summaries.forEach((summary, i) => {
    const row = document.createElement('tr');
    const title = cell(row, i ? 'B' : 'A');
    const name = document.createElement('span');
    name.className = 'session-name';
    name.textContent = sessions[i].name;
    title.append(name);
    cell(row, seconds(summary.duration));
    cell(row, pct(summary.meanCpu));
    cell(row, pct(summary.peakCpu));
    cell(row, pct(summary.peakRam));
    cell(row, String(summary.alertSamples));
    body.append(row);
  });
  if (summaries.length === 2) {
    const [a, b] = summaries;
    const row = document.createElement('tr');
    row.className = 'delta';
    cell(row, 'Δ B − A');
    cell(row, signed(b.duration - a.duration, ' s'));
    cell(row, signed(b.meanCpu - a.meanCpu, ' pp'));
    cell(row, signed(b.peakCpu - a.peakCpu, ' pp'));
    cell(row, signed(b.peakRam - a.peakRam, ' pp'));
    cell(row, String(b.alertSamples - a.alertSamples));
    body.append(row);
  }
  const gaps = summaries.reduce((total, summary) => total + summary.gaps, 0);
  $('#analysis-note').textContent =
    'Média de CPU por integração trapezoidal entre as amostras. ' +
    (gaps ? `${gaps} intervalo(s) acima de 3 s; há lacunas na captura. ` : '') +
    'Sessões alinhadas pela primeira leitura. Cargas diferentes não formam um benchmark controlado.';
  renderReadout();
}

function reportError(error) {
  const message = $('#session-message');
  message.classList.add('error');
  message.textContent = `${error.message} A sessão anterior foi mantida.`;
}

$('#session-file').addEventListener('change', async (event) => {
  const version = ++importVersion;
  const files = [...event.target.files];
  if (!files.length) return;
  try {
    if (files.length > 2) throw new Error('Selecione um ou dois arquivos.');
    const next = await Promise.all(
      files.map(async (file) => {
        if (file.size > MAX_FILE_BYTES) throw new Error('O limite é 4 MiB por arquivo.');
        return { name: file.name, samples: parseSession(await file.text()) };
      })
    );
    if (version === importVersion) showSessions(next);
  } catch (error) {
    if (version === importVersion) reportError(error);
  } finally {
    event.target.value = '';
  }
});

$('#example').addEventListener('click', () => {
  importVersion += 1;
  showSessions([{ name: 'Carga ilustrativa · 90 segundos', samples: illustrativeSession() }], true);
});
$('#paste-session').addEventListener('click', () => {
  importVersion += 1;
  try {
    showSessions([{ name: 'Captura colada', samples: parseSession($('#session-text').value) }]);
  } catch (error) {
    reportError(error);
  }
});
slider.addEventListener('input', renderReadout);

const commands = $('#commands');
function commandText(os) {
  return [
    'git clone https://github.com/brunnojob/devpulse-usb.git',
    'cd devpulse-usb',
    `${os === 'windows' ? 'python' : 'python3'} -m venv .venv`,
    os === 'windows' ? '.venv\\Scripts\\Activate.ps1' : 'source .venv/bin/activate',
    'python -m pip install -r requirements.txt',
    'python agent.py --record sessao.ndjson --duration 60',
  ].join('\n');
}
document.querySelectorAll('.os').forEach((button) => {
  button.addEventListener('click', () => {
    document.querySelectorAll('.os').forEach((item) => {
      item.classList.toggle('active', item === button);
      item.setAttribute('aria-pressed', String(item === button));
    });
    commands.textContent = commandText(button.dataset.os);
    $('#copy-status').textContent = '';
  });
});
$('#copy').addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(commands.textContent);
    $('#copy-status').textContent = 'Comandos copiados.';
  } catch {
    $('#copy-status').textContent = 'Selecione e copie o texto acima.';
  }
});
showSessions([{ name: 'Carga ilustrativa · 90 segundos', samples: illustrativeSession() }], true);
