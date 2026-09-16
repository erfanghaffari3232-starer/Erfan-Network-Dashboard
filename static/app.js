const $ = (id) => document.getElementById(id);
let devices = [];

async function loadInfo() {
  const res = await fetch('/api/network');
  const data = await res.json();
  $('localIp').textContent = data.local_ip;
  $('network').textContent = data.network;
  $('hostname').textContent = data.hostname;
}

function render() {
  const q = $('search').value.trim().toLowerCase();
  const list = devices.filter(d => `${d.ip} ${d.hostname}`.toLowerCase().includes(q));
  $('deviceCount').textContent = devices.length;
  $('devices').innerHTML = list.length ? list.map(d => `
    <tr><td>🖥️ ${escapeHtml(d.hostname)}</td><td><code>${d.ip}</code></td><td>${d.ping ? `${d.ping} ms` : '<1 ms'}</td><td><span class="online">● آنلاین</span></td></tr>
  `).join('') : '<tr><td colspan="4" class="empty">دستگاهی پیدا نشد.</td></tr>';
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
}

async function scan() {
  const btn = $('scanBtn');
  btn.disabled = true;
  btn.textContent = '⏳ در حال اسکن...';
  $('status').textContent = 'در حال بررسی دستگاه‌های شبکه محلی...';
  try {
    const res = await fetch('/api/scan');
    const data = await res.json();
    devices = data.devices;
    render();
    $('status').textContent = `اسکن تمام شد؛ ${devices.length} دستگاه آنلاین پیدا شد.`;
  } catch (e) {
    $('status').textContent = 'خطا در اسکن شبکه.';
  } finally {
    btn.disabled = false;
    btn.textContent = '🔄 اسکن شبکه';
  }
}

$('scanBtn').addEventListener('click', scan);
$('search').addEventListener('input', render);
loadInfo();
