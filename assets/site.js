'use strict';
const load = document.querySelector('#load');
load.addEventListener('input', () => {
  const value = Number(load.value);
  document.querySelector('#load-out').textContent = `${value}%`;
  document.querySelector('#cpu-value').textContent = `${value}%`;
  const bar = document.querySelector('#cpu-bar');
  bar.style.width = `${value}%`;
  bar.style.background = value >= 90 ? '#f28a6e' : 'var(--cyan)';
  document.querySelector('#demo-state').textContent = value >= 90 ? 'LIMIAR DE 90% ATINGIDO · DEMO' : 'CARGA ILUSTRATIVA NORMAL';
});
const commands = document.querySelector('#commands');
const commandText = (os) => [
  'git clone https://github.com/brunnojob/devpulse-usb.git',
  'cd devpulse-usb',
  `${os === 'windows' ? 'python' : 'python3'} -m venv .venv`,
  os === 'windows' ? '.venv\\Scripts\\Activate.ps1' : 'source .venv/bin/activate',
  'python -m pip install -r requirements.txt',
  'python agent.py --stdout'
].join('\n');
document.querySelectorAll('.os').forEach(button => {
  button.addEventListener('click', () => {
    document.querySelectorAll('.os').forEach(item => {
      item.classList.toggle('active', item === button);
      item.setAttribute('aria-pressed', String(item === button));
    });
    commands.textContent = commandText(button.dataset.os);
    document.querySelector('#copy-status').textContent = '';
  });
});
document.querySelector('#copy').addEventListener('click', async () => {
  const status = document.querySelector('#copy-status');
  try {
    await navigator.clipboard.writeText(commands.textContent);
    status.textContent = 'Comandos copiados.';
  } catch {
    status.textContent = 'Selecione e copie o texto acima.';
  }
});
