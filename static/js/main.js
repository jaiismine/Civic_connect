// ── CivicConnect Main JS ──

// Update clock in topbar
function updateClock() {
  const el = document.getElementById('live-clock');
  if (el) {
    const now = new Date();
    el.textContent = now.toLocaleString('en-US', {
      weekday: 'short', month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  }
}
setInterval(updateClock, 1000);
updateClock();

// Auto-dismiss alerts
document.querySelectorAll('.alert').forEach(el => {
  setTimeout(() => { el.style.opacity = '0'; el.style.transition = 'opacity .5s'; setTimeout(()=> el.remove(), 500); }, 4500);
});

// Role toggle on login page
document.querySelectorAll('.role-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.role-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('roleInput').value = btn.dataset.role;
    const label = document.getElementById('portalLabel');
    if (label) label.textContent = btn.dataset.role === 'admin' ? 'Admin Portal' : 'Citizen Portal';
  });
});

// Image drop zone
const dropZone = document.querySelector('.image-drop-zone');
if (dropZone) {
  dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
  dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
  dropZone.addEventListener('drop', e => {
    e.preventDefault(); dropZone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) previewImage(file);
  });
  const fileInput = dropZone.querySelector('input[type="file"]');
  if (fileInput) fileInput.addEventListener('change', e => { if (e.target.files[0]) previewImage(e.target.files[0]); });
}

function previewImage(file) {
  const preview = document.getElementById('imagePreview');
  if (!preview) return;
  const reader = new FileReader();
  reader.onload = e => { preview.src = e.target.result; preview.style.display = 'block'; };
  reader.readAsDataURL(file);
}

// Get user location for report form
const locBtn = document.getElementById('getLocationBtn');
if (locBtn) {
  locBtn.addEventListener('click', () => {
    locBtn.disabled = true;
    locBtn.textContent = '📡 Detecting...';
    if (!navigator.geolocation) {
      alert('Geolocation not supported.'); locBtn.disabled = false; return;
    }
    navigator.geolocation.getCurrentPosition(pos => {
      const { latitude: lat, longitude: lng } = pos.coords;
      document.getElementById('latInput').value  = lat.toFixed(6);
      document.getElementById('lngInput').value  = lng.toFixed(6);
      document.getElementById('addrInput').value = `Lat: ${lat.toFixed(4)}, Lng: ${lng.toFixed(4)}`;
      locBtn.textContent = '✅ Location Captured';
      locBtn.style.background = '#16a34a';
      // Update preview map
      if (window.previewMap && window.previewMarker) {
        window.previewMap.setView([lat, lng], 15);
        window.previewMarker.setLatLng([lat, lng]);
      } else if (window.previewMap) {
        window.previewMap.setView([lat, lng], 15);
        window.previewMarker = L.marker([lat, lng]).addTo(window.previewMap)
          .bindPopup('Your location').openPopup();
      }
      // Reverse geocode (OpenStreetMap Nominatim)
      fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`)
        .then(r => r.json())
        .then(d => {
          if (d.display_name) document.getElementById('addrInput').value = d.display_name;
        }).catch(() => {});
    }, err => {
      alert('Could not get location: ' + err.message);
      locBtn.disabled = false;
      locBtn.textContent = '📍 Auto-Detect My Location';
    }, { enableHighAccuracy: true, timeout: 10000 });
  });
}

// Initialize preview map on report page
function initPreviewMap() {
  const el = document.getElementById('previewMap');
  if (!el || !window.L) return;
  window.previewMap = L.map('previewMap').setView([40.7128, -74.0060], 10);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(window.previewMap);
  // Allow manual pin drop
  window.previewMap.on('click', e => {
    const { lat, lng } = e.latlng;
    document.getElementById('latInput').value  = lat.toFixed(6);
    document.getElementById('lngInput').value  = lng.toFixed(6);
    fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`)
      .then(r => r.json())
      .then(d => { if (d.display_name) document.getElementById('addrInput').value = d.display_name; })
      .catch(() => {});
    if (window.previewMarker) window.previewMarker.setLatLng([lat, lng]);
    else window.previewMarker = L.marker([lat, lng]).addTo(window.previewMap).bindPopup('Report Location').openPopup();
  });
}
if (document.getElementById('previewMap')) {
  if (window.L) initPreviewMap();
  else window.addEventListener('load', initPreviewMap);
}

// Admin map (severity-colored markers)
function initAdminMap(reports) {
  const el = document.getElementById('reportMap');
  if (!el || !window.L) return;
  const map = L.map('reportMap').setView([40.7128, -74.0060], 11);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map);
  const colors = { Critical: '#dc2626', High: '#ea580c', Medium: '#ca8a04', Low: '#16a34a' };
  reports.forEach(r => {
    if (!r.latitude || !r.longitude) return;
    const color = colors[r.severity] || '#64748b';
    const icon = L.divIcon({
      html: `<div style="background:${color};width:16px;height:16px;border-radius:50%;border:2px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,.4)"></div>`,
      className: '', iconSize: [16, 16], iconAnchor: [8, 8]
    });
    L.marker([r.latitude, r.longitude], { icon })
      .addTo(map)
      .bindPopup(`
        <div style="min-width:200px">
          <div style="font-weight:700;font-size:.95rem;margin-bottom:6px">${r.title}</div>
          <div style="font-size:.82rem;color:#64748b">${r.category} • ${r.location_address || ''}</div>
          <div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap">
            <span style="background:${color};color:#fff;padding:2px 8px;border-radius:99px;font-size:.75rem;font-weight:600">${r.severity}</span>
            <span style="background:#e2e8f0;padding:2px 8px;border-radius:99px;font-size:.75rem">${r.status}</span>
          </div>
          <div style="font-size:.78rem;color:#94a3b8;margin-top:6px">${r.report_id}</div>
        </div>
      `);
  });
}

// Modal helpers
function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }
document.querySelectorAll('.modal-overlay').forEach(modal => {
  modal.addEventListener('click', e => { if (e.target === modal) modal.classList.remove('open'); });
});

// Support type selector
document.querySelectorAll('.support-option').forEach(card => {
  card.addEventListener('click', () => {
    document.querySelectorAll('.support-option').forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');
    const typeInput = document.getElementById('supportType');
    if (typeInput) typeInput.value = card.dataset.type;
    const formSection = document.getElementById('supportForm');
    if (formSection) { formSection.style.display = 'block'; formSection.scrollIntoView({ behavior: 'smooth' }); }
  });
});

// Sidebar active link
const path = window.location.pathname;
document.querySelectorAll('.nav-item').forEach(link => {
  if (link.getAttribute('href') === path) link.classList.add('active');
});
