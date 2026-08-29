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
  document.getElementById('tabUpload')?.classList.toggle('active', tab === 'upload');
  document.getElementById('tabCamera')?.classList.toggle('active', tab === 'camera');
  const dz = document.getElementById('dropzoneContainer');
  if (dz) dz.style.display = tab === 'upload' ? 'block' : 'none';
  const cc = document.getElementById('cameraContent');
  if (cc) cc.style.display = tab === 'camera' ? 'block' : 'none';

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
  document.getElementById('dropzone')?.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) previewFile(file);
}

function handleDragOver(e) {
  e.preventDefault();
  document.getElementById('dropzone')?.classList.add('drag-over');
}

function handleDragLeave(e) {
  document.getElementById('dropzone')?.classList.remove('drag-over');
}

function previewFile(file) {
  const reader = new FileReader();
  reader.onload = (ev) => {
    currentImageData = ev.target.result;
    const pi = document.getElementById('previewImg');
    if (pi) pi.src = currentImageData;
    const pc = document.getElementById('previewContainer');
    if (pc) pc.style.display = 'block';
    const da = document.getElementById('dropzoneArea');
    if (da) da.style.display = 'none';
    updateDetectBtn();
  };
  reader.readAsDataURL(file);
}

function clearUpload() {
  currentImageData = null;
  const pc = document.getElementById('previewContainer');
  if (pc) pc.style.display = 'none';
  const da = document.getElementById('dropzoneArea');
  if (da) da.style.display = '';
  const fi = document.getElementById('fileInput');
  if (fi) fi.value = '';
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
    if (video) { video.srcObject = cameraStream; video.style.display = 'block'; }
    const ov = document.getElementById('cameraOverlay');
    if (ov) ov.style.display = 'flex';
    const cp = document.getElementById('cameraPlaceholder');
    if (cp) cp.style.display = 'none';
    const cc = document.getElementById('cameraCaptured');
    if (cc) cc.style.display = 'none';
    const bStart = document.getElementById('btnStartCam');
    if (bStart) bStart.style.display = 'none';
    const bCap = document.getElementById('btnCapture');
    if (bCap) bCap.style.display = 'inline-flex';
    const bStop = document.getElementById('btnStopCam');
    if (bStop) bStop.style.display = 'inline-flex';
  } catch (err) {
    alert('Tidak dapat mengakses kamera: ' + err.message);
  }
}

function capturePhoto() {
  const video  = document.getElementById('cameraVideo');
  const canvas = document.getElementById('cameraCanvas');
  if (!video || !canvas) return;
  canvas.width  = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);
  currentImageData = canvas.toDataURL('image/jpeg', 0.9);

  const ci = document.getElementById('capturedImg');
  if (ci) ci.src = currentImageData;
  video.style.display = 'none';
  const ov = document.getElementById('cameraOverlay');
  if (ov) ov.style.display = 'none';
  const cc = document.getElementById('cameraCaptured');
  if (cc) cc.style.display = 'block';
  const bCap = document.getElementById('btnCapture');
  if (bCap) bCap.style.display = 'none';
  const bStop = document.getElementById('btnStopCam');
  if (bStop) bStop.style.display = 'none';
  stopCamera(false);
  updateDetectBtn();
}

function retakePhoto() {
  currentImageData = null;
  const cc = document.getElementById('cameraCaptured');
  if (cc) cc.style.display = 'none';
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
  const btn = document.getElementById('btnDetect');
  if (btn) btn.disabled = !currentImageData;
}

// ────────────────────────────────────────────────
// DETECTION
// ────────────────────────────────────────────────
async function runDetection() {
  if (!currentImageData) return;

  showLoading();
  const btn = document.getElementById('btnDetect');
  if (btn) btn.disabled = true;

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
    if (btn) btn.disabled = !currentImageData;
  }
}

// ────────────────────────────────────────────────
// STATE MANAGERS (use display directly — more reliable)
// ────────────────────────────────────────────────
function setPanel(which) {
  const inputPanel = document.getElementById('inputPanel');
  const resultPanel = document.getElementById('resultPanel');
  const loadingState = document.getElementById('loadingState');
  const resultState = document.getElementById('resultState');

  if (inputPanel) inputPanel.style.display = which === 'empty' ? 'flex' : 'none';
  if (resultPanel) resultPanel.style.display = (which === 'loading' || which === 'result') ? 'flex' : 'none';

  if (loadingState) loadingState.style.display = which === 'loading' ? 'flex' : 'none';
  if (resultState) resultState.style.display  = which === 'result'  ? 'block' : 'none';
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
  if (img) {
    img.src = data.annotated_image;
    img.style.display = 'block';
  }

  // Summary header
  const s = data.summary;
  const statusColor = {
    sehat:'#22C55E', ringan:'#EAB308', berat:'#F97316', kritis:'#EF4444', error:'#888'
  };
  const col = statusColor[s.status] || '#888';
  const hdr = document.getElementById('resultHeader');
  if (hdr) {
    hdr.className = `result-header-light status-${s.status}`;
    hdr.innerHTML = `
      <div style="font-size:18px;font-weight:800;color:${col};margin-bottom:6px">${s.message}</div>
      <div style="font-size:13px;color:#334155">${s.recommendation}</div>
      <div style="margin-top:8px;font-size:12px;color:#94a3b8">🔍 ${data.total} objek terdeteksi · Mode: ${data.mode.toUpperCase()}</div>
    `;
  }

  // Detection cards
  const list = document.getElementById('detectionsList');
  if (!list) return;
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
// INIT
// ────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const uploadTab = document.getElementById('uploadTab');
  if (!uploadTab) return; // Exit if not on deteksi page

  showEmpty();
  uploadTab.style.display = 'block';
  const cameraTab = document.getElementById('cameraTab');
  if (cameraTab) cameraTab.style.display = 'none';

  const btnCap  = document.getElementById('btnCapture');
  const btnStop = document.getElementById('btnStopCam');
  if (btnCap)  btnCap.style.display  = 'none';
  if (btnStop) btnStop.style.display = 'none';
});
