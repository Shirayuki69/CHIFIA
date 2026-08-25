/**
 * CHIFIA — Frontend Logic
 * Camera · Upload · Detection · Results
 */

// ────────────────────────────────────────────────
// MOBILE MENU
// ────────────────────────────────────────────────
function toggleMobileMenu() {
  const menu = document.getElementById('mobileMenu');
  const btn  = document.getElementById('navHamburger');
  if (menu) menu.classList.toggle('open');
  if (btn)  btn.classList.toggle('open');
}

// ────────────────────────────────────────────────
// STATE
// ────────────────────────────────────────────────
let currentImageData = null;
let cameraStream     = null;
let activeTab        = 'upload';

// ────────────────────────────────────────────────
// TAB SWITCHING
// ────────────────────────────────────────────────
function switchTab(tab) {
  activeTab = tab;
  document.getElementById('tabUpload').classList.toggle('active', tab === 'upload');
  document.getElementById('tabCamera').classList.toggle('active', tab === 'camera');
  document.getElementById('dropzoneContainer').style.display = tab === 'upload' ? 'block' : 'none';
  document.getElementById('cameraContent').style.display = tab === 'camera' ? 'block' : 'none';

  if (tab !== 'camera') stopCamera();
  currentImageData = null;
  updateDetectBtn();
}

// ────────────────────────────────────────────────
// FILE UPLOAD
// ────────────────────────────────────────────────
function handleFileSelect(e) {
  const file = e.target.files[0];
  if (!file) return;
  previewFile(file);
}

function handleDrop(e) {
  e.preventDefault();
  document.getElementById('dropzone').classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) previewFile(file);
}

function handleDragOver(e) {
  e.preventDefault();
  document.getElementById('dropzone').classList.add('drag-over');
}

function handleDragLeave(e) {
  document.getElementById('dropzone').classList.remove('drag-over');
}

function previewFile(file) {
  const reader = new FileReader();
  reader.onload = (ev) => {
    currentImageData = ev.target.result;
    document.getElementById('previewImg').src = currentImageData;
    document.getElementById('previewContainer').style.display = 'block';
    document.getElementById('dropzoneArea').style.display = 'none';
    updateDetectBtn();
  };
  reader.readAsDataURL(file);
}

function clearUpload() {
  currentImageData = null;
  document.getElementById('previewContainer').style.display = 'none';
  document.getElementById('dropzoneArea').style.display = '';
  document.getElementById('fileInput').value = '';
  updateDetectBtn();
  showEmpty();
}

// ────────────────────────────────────────────────
// CAMERA
// ────────────────────────────────────────────────
async function startCamera() {
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false
    });
    const video = document.getElementById('cameraVideo');
    video.srcObject = cameraStream;
    video.style.display = 'block';
    document.getElementById('cameraOverlay').style.display = 'flex';
    document.getElementById('cameraPlaceholder').style.display = 'none'; // Sembunyikan placeholder
    document.getElementById('cameraCaptured').style.display = 'none'; // Pastikan hasil foto disembunyikan
    document.getElementById('btnStartCam').style.display = 'none';
    document.getElementById('btnCapture').style.display = 'inline-flex';
    document.getElementById('btnStopCam').style.display = 'inline-flex';
  } catch (err) {
    alert('Tidak dapat mengakses kamera: ' + err.message);
  }
}

function capturePhoto() {
  const video  = document.getElementById('cameraVideo');
  const canvas = document.getElementById('cameraCanvas');
  canvas.width  = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);
  currentImageData = canvas.toDataURL('image/jpeg', 0.9);

  document.getElementById('capturedImg').src = currentImageData;
  document.getElementById('cameraVideo').style.display = 'none';
  document.getElementById('cameraOverlay').style.display = 'none';
  document.getElementById('cameraCaptured').style.display = 'block';
  document.getElementById('btnCapture').style.display = 'none';
  document.getElementById('btnStopCam').style.display = 'none';
  stopCamera(false);
  updateDetectBtn();
}

function retakePhoto() {
  currentImageData = null;
  document.getElementById('cameraCaptured').style.display = 'none';
  updateDetectBtn();
  startCamera();
}

function stopCamera(clearStream = true) {
  if (clearStream && cameraStream) {
    cameraStream.getTracks().forEach(t => t.stop());
    cameraStream = null;
  }
  const video = document.getElementById('cameraVideo');
  if (video) { video.srcObject = null; video.style.display = 'none'; }
  const overlay = document.getElementById('cameraOverlay');
  if (overlay) overlay.style.display = 'none';
  const placeholder = document.getElementById('cameraPlaceholder');
  if (placeholder) placeholder.style.display = currentImageData ? 'none' : 'flex';
  const btnStart = document.getElementById('btnStartCam');
  if (btnStart) btnStart.style.display = '';
  const btnCap = document.getElementById('btnCapture');
  if (btnCap) btnCap.style.display = 'none';
  const btnStop = document.getElementById('btnStopCam');
  if (btnStop) btnStop.style.display = 'none';
}

// ────────────────────────────────────────────────
// DETECT BUTTON STATE
// ────────────────────────────────────────────────
function updateDetectBtn() {
  document.getElementById('btnDetect').disabled = !currentImageData;
}

// ────────────────────────────────────────────────
// DETECTION
// ────────────────────────────────────────────────
async function runDetection() {
  if (!currentImageData) return;

  showLoading();
  const btn = document.getElementById('btnDetect');
  btn.disabled = true;

  try {
    const resp = await fetch('/detect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image: currentImageData }),
    });
    const data = await resp.json();
    if (!resp.ok || data.error) throw new Error(data.error || 'Detection failed');
    showResult(data);
  } catch (err) {
    showEmpty();
    alert('Gagal mendeteksi: ' + err.message);
  } finally {
    btn.disabled = !currentImageData;
  }
}

// ────────────────────────────────────────────────
// STATE MANAGERS (use display directly — more reliable)
// ────────────────────────────────────────────────
function setPanel(which) {
  // Panel toggles
  document.getElementById('inputPanel').style.display = which === 'empty' ? 'flex' : 'none';
  document.getElementById('resultPanel').style.display = (which === 'loading' || which === 'result') ? 'flex' : 'none';

  // Result content toggles
  document.getElementById('loadingState').style.display = which === 'loading' ? 'flex' : 'none';
  document.getElementById('resultState').style.display  = which === 'result'  ? 'block' : 'none';
}
function showEmpty()   { setPanel('empty'); }
function showLoading() { setPanel('loading'); }
function resetResult() {
  if (activeTab === 'upload') {
    clearUpload();
  } else if (activeTab === 'camera') {
    retakePhoto();
  }
  showEmpty();
}

// ────────────────────────────────────────────────
// RENDER RESULT
// ────────────────────────────────────────────────
function showResult(data) {
  setPanel('result');

  // Annotated image
  const img = document.getElementById('annotatedImg');
  img.src = data.annotated_image;
  img.style.display = 'block';

  // Summary header
  const s = data.summary;
  const statusColor = {
    sehat:'#22C55E', ringan:'#EAB308', berat:'#F97316', kritis:'#EF4444', error:'#888'
  };
  const col = statusColor[s.status] || '#888';
  const hdr = document.getElementById('resultHeader');
  hdr.className = `result-header-light status-${s.status}`;
  hdr.innerHTML = `
    <div style="font-size:18px;font-weight:800;color:${col};margin-bottom:6px">${s.message}</div>
    <div style="font-size:13px;color:#334155">${s.recommendation}</div>
    <div style="margin-top:8px;font-size:12px;color:#94a3b8">🔍 ${data.total} objek terdeteksi · Mode: ${data.mode.toUpperCase()}</div>
  `;

  // Detection cards
  const list = document.getElementById('detectionsList');
  list.innerHTML = '';

  if (!data.detections || data.detections.length === 0) {
    list.innerHTML = `
      <div class="det-card" style="display:flex;align-items:center;justify-content:center;min-height:280px;flex-direction:column;gap:12px;text-align:center;background:#f8fafc;border:1px dashed #cbd5e1">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
        <div style="font-family:'Outfit',sans-serif;font-size:16px;color:#1e293b;font-weight:600">Bebas Penyakit</div>
        <div style="font-size:13px;color:#64748b">Tidak ada penyakit daun cabai yang terdeteksi pada gambar ini.</div>
      </div>
    `;
    return;
  }

  data.detections.forEach((d, i) => {
    const isHealthy = d.class_name === 'healthy';
    const causeHtml = !isHealthy ? `
      <div class="det-section" style="border-left-color:#f97316">
        <div class="det-section-title">🔬 Penyebab</div>
        <div class="det-section-body">${d.cause}</div>
      </div>` : '';
    const treatHtml = `
      <div class="det-section" style="border-left-color:${d.color}">
        <div class="det-section-title">💊 Cara Mengatasi</div>
        <div class="det-section-body">${d.treatment}</div>
      </div>`;

    const pct = Math.round(d.confidence * 100);
    const card = document.createElement('div');
    card.className = 'det-card';
    card.style.animationDelay = `${i * 0.08}s`;
    card.innerHTML = `
      <div class="det-card-header">
        <span class="det-icon">${d.icon}</span>
        <div class="det-label-wrap">
          <div class="det-label" style="color:${d.color}">${d.label}</div>
        </div>
        <div class="det-conf-badge" style="color:${d.color};border-color:${d.color}">${pct}%</div>
      </div>
      <div style="margin:10px 0 14px">
        <div class="det-conf-bar-wrap">
          <div class="det-conf-bar" style="width:${pct}%;background:${d.color}"></div>
        </div>
        <div style="font-size:11px;color:#94a3b8;margin-top:4px">Akurasi Prediksi: ${pct}%</div>
      </div>
      ${causeHtml}
      ${treatHtml}
    `;
    list.appendChild(card);
  });
}

// ────────────────────────────────────────────────
// RESET
// ────────────────────────────────────────────────
function resetResult() {
  clearUpload();
  if (activeTab === 'camera') {
    const cap = document.getElementById('cameraCaptured');
    if (cap) cap.style.display = 'none';
  }
  currentImageData = null;
  updateDetectBtn();
  showEmpty();
}

// ────────────────────────────────────────────────
// INIT
// ────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  showEmpty();
  // Init tab display
  document.getElementById('uploadTab').style.display = 'block';
  document.getElementById('cameraTab').style.display = 'none';
  // Camera button visibility
  const btnCap  = document.getElementById('btnCapture');
  const btnStop = document.getElementById('btnStopCam');
  if (btnCap)  btnCap.style.display  = 'none';
  if (btnStop) btnStop.style.display = 'none';
});
