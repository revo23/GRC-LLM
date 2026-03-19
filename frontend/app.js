const API = '/api';

// ─── TAB NAVIGATION ──────────────────────────────────────────────────────────

document.querySelectorAll('nav.tabs button').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('nav.tabs button').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');

    if (btn.dataset.tab === 'assess') { loadDocumentsIntoSelect(); loadFrameworks(); }
    if (btn.dataset.tab === 'results') { loadAssessmentList(); }
  });
});

// ─── HELPERS ─────────────────────────────────────────────────────────────────

function showAlert(containerId, message, type = 'error') {
  const el = document.getElementById(containerId);
  el.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
  setTimeout(() => { el.innerHTML = ''; }, 6000);
}

function scoreColor(score) {
  const colors = ['#ef4444','#f97316','#f59e0b','#84cc16','#22c55e','#10b981'];
  return colors[Math.max(0, Math.min(5, Math.round(score)))] || '#8892a4';
}

function scoreLabel(score) {
  const labels = ['Not Implemented','Initial','Developing','Defined','Managed','Optimized'];
  return labels[Math.max(0, Math.min(5, Math.round(score)))] || 'Unknown';
}

function formatBytes(b) {
  if (b < 1024) return b + ' B';
  if (b < 1024 * 1024) return (b / 1024).toFixed(1) + ' KB';
  return (b / 1024 / 1024).toFixed(1) + ' MB';
}

function formatDate(iso) {
  if (!iso) return '—';
  try { return new Date(iso + 'Z').toLocaleString(); } catch { return iso; }
}

// ─── UPLOAD ───────────────────────────────────────────────────────────────────

const uploadZone = document.getElementById('upload-zone');
const fileInput = document.getElementById('file-input');

uploadZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) uploadFile(fileInput.files[0]);
});

uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.classList.add('drag-over'); });
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
uploadZone.addEventListener('drop', e => {
  e.preventDefault();
  uploadZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) uploadFile(file);
});

async function uploadFile(file) {
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    showAlert('upload-alerts', 'Only PDF files are supported.'); return;
  }
  if (file.size > 50 * 1024 * 1024) {
    showAlert('upload-alerts', 'File exceeds 50MB limit.'); return;
  }

  const progressWrap = document.getElementById('upload-progress');
  const bar = document.getElementById('upload-progress-bar');
  const label = document.getElementById('upload-progress-label');
  progressWrap.style.display = 'block';
  bar.style.width = '10%';
  label.textContent = `Uploading ${file.name}...`;

  const formData = new FormData();
  formData.append('file', file);

  try {
    bar.style.width = '40%';
    const resp = await fetch(`${API}/documents/upload`, { method: 'POST', body: formData });
    bar.style.width = '80%';

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || 'Upload failed');
    }

    const doc = await resp.json();
    bar.style.width = '100%';
    label.textContent = `Done! ${doc.chunk_count} chunks indexed.`;
    showAlert('upload-alerts', `✓ "${doc.name}" uploaded — ${doc.page_count} pages, ${doc.chunk_count} chunks indexed.`, 'success');
    setTimeout(() => { progressWrap.style.display = 'none'; bar.style.width = '0%'; }, 2000);
    loadDocuments();
  } catch (e) {
    bar.style.width = '0%';
    progressWrap.style.display = 'none';
    showAlert('upload-alerts', `Upload failed: ${e.message}`);
  }
}

async function loadDocuments() {
  const list = document.getElementById('doc-list');
  try {
    const resp = await fetch(`${API}/documents`);
    const docs = await resp.json();

    if (!docs.length) {
      list.innerHTML = `<div class="empty-state"><span class="empty-icon">📂</span><p>No documents uploaded yet</p></div>`;
      return;
    }

    list.innerHTML = docs.map(d => `
      <div class="doc-item">
        <div>
          <div class="doc-name">📄 ${d.name}</div>
          <div class="doc-meta">${d.page_count} pages · ${d.chunk_count} chunks · ${formatBytes(d.size_bytes)} · ${formatDate(d.upload_time)}</div>
        </div>
        <button class="btn btn-danger" onclick="deleteDocument('${d.document_id}', '${d.name.replace(/'/g,'\\\'')}')" title="Delete">✕</button>
      </div>
    `).join('');
  } catch (e) {
    list.innerHTML = `<div class="alert alert-error">Failed to load documents: ${e.message}</div>`;
  }
}

async function deleteDocument(docId, name) {
  if (!confirm(`Delete "${name}"? This will also remove its index.`)) return;
  try {
    const resp = await fetch(`${API}/documents/${docId}`, { method: 'DELETE' });
    if (!resp.ok) throw new Error('Delete failed');
    showAlert('upload-alerts', `✓ Deleted "${name}"`, 'success');
    loadDocuments();
  } catch (e) {
    showAlert('upload-alerts', `Delete failed: ${e.message}`);
  }
}

// Initialize upload tab
loadDocuments();

// ─── ASSESS ───────────────────────────────────────────────────────────────────

let frameworks = [];

async function loadDocumentsIntoSelect() {
  const sel = document.getElementById('assess-doc-select');
  try {
    const resp = await fetch(`${API}/documents`);
    const docs = await resp.json();
    sel.innerHTML = '<option value="">— choose a document —</option>' +
      docs.map(d => `<option value="${d.document_id}">${d.name}</option>`).join('');
  } catch { /* ignore */ }
}

async function loadFrameworks() {
  const grid = document.getElementById('framework-grid');
  try {
    const resp = await fetch(`${API}/frameworks`);
    frameworks = await resp.json();
    grid.innerHTML = frameworks.map(fw => `
      <label class="fw-checkbox">
        <input type="checkbox" name="framework" value="${fw.id}" />
        <div>
          <div class="fw-name">${fw.name}</div>
          <div class="fw-count">${fw.control_count} controls · v${fw.version}</div>
        </div>
      </label>
    `).join('');
  } catch (e) {
    grid.innerHTML = `<div class="alert alert-error">Failed to load frameworks: ${e.message}</div>`;
  }
}

function selectAllFrameworks() {
  document.querySelectorAll('input[name="framework"]').forEach(cb => cb.checked = true);
}

function clearFrameworks() {
  document.querySelectorAll('input[name="framework"]').forEach(cb => cb.checked = false);
}

let pollInterval = null;

async function runAssessment() {
  const docId = document.getElementById('assess-doc-select').value;
  const frameworkIds = [...document.querySelectorAll('input[name="framework"]:checked')].map(cb => cb.value);

  if (!docId) { showAlert('assess-alerts', 'Please select a document.'); return; }
  if (!frameworkIds.length) { showAlert('assess-alerts', 'Please select at least one framework.'); return; }

  const btn = document.getElementById('run-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Starting...';

  try {
    const resp = await fetch(`${API}/assessments/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_id: docId, framework_ids: frameworkIds }),
    });

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || 'Failed to start assessment');
    }

    const { assessment_id } = await resp.json();
    showAssessmentStatus(assessment_id, frameworkIds);
    pollAssessment(assessment_id, btn);
  } catch (e) {
    showAlert('assess-alerts', `Failed: ${e.message}`);
    btn.disabled = false;
    btn.innerHTML = '▶ Run Assessment';
  }
}

function showAssessmentStatus(assessmentId, frameworkIds) {
  const card = document.getElementById('assess-status-card');
  const content = document.getElementById('assess-status-content');
  card.style.display = 'block';
  content.innerHTML = `
    <div style="margin-bottom:12px; font-size:13px; color:var(--text-muted)">
      Assessment ID: <code style="color:var(--text)">${assessmentId}</code>
    </div>
    <div class="progress-bar-wrap"><div class="progress-bar" id="assess-progress-bar" style="width:5%"></div></div>
    <div class="progress-label" id="assess-progress-label">Initializing assessment for ${frameworkIds.length} framework(s)...</div>
    <div id="assess-log" style="margin-top:12px; font-size:12px; color:var(--text-muted);"></div>
  `;
}

function pollAssessment(assessmentId, btn) {
  if (pollInterval) clearInterval(pollInterval);
  let elapsed = 0;

  pollInterval = setInterval(async () => {
    elapsed += 3;
    try {
      const resp = await fetch(`${API}/assessments/${assessmentId}`);
      if (!resp.ok) return;
      const data = await resp.json();

      const bar = document.getElementById('assess-progress-bar');
      const label = document.getElementById('assess-progress-label');
      const log = document.getElementById('assess-log');

      if (data.status === 'completed') {
        clearInterval(pollInterval);
        if (bar) bar.style.width = '100%';
        if (label) label.textContent = `✓ Completed! Overall score: ${data.overall_posture_score.toFixed(2)} / 5`;
        if (log) log.innerHTML = `<span style="color:var(--success)">Assessment complete. Switch to <strong>Results</strong> tab to view.</span>`;
        btn.disabled = false;
        btn.innerHTML = '▶ Run Assessment';
        return;
      }

      if (data.status === 'failed') {
        clearInterval(pollInterval);
        if (label) label.textContent = '✗ Assessment failed';
        btn.disabled = false;
        btn.innerHTML = '▶ Run Assessment';
        return;
      }

      const pct = Math.min(5 + elapsed * 1.5, 90);
      if (bar) bar.style.width = pct + '%';
      if (label) label.textContent = `Running... (${elapsed}s elapsed)`;
    } catch { /* ignore */ }
  }, 3000);
}

// ─── RESULTS ─────────────────────────────────────────────────────────────────

async function loadAssessmentList() {
  const sel = document.getElementById('results-assessment-select');
  try {
    const resp = await fetch(`${API}/assessments`);
    const assessments = await resp.json();
    sel.innerHTML = '<option value="">— select an assessment —</option>' +
      assessments.map(a => {
        const label = `${a.document_name} | ${a.frameworks_assessed.join(', ')} | Score: ${a.overall_posture_score.toFixed(2)} | ${a.status}`;
        return `<option value="${a.assessment_id}">${label}</option>`;
      }).join('');
  } catch { /* ignore */ }
}

async function loadAssessmentResult() {
  const assessmentId = document.getElementById('results-assessment-select').value;
  if (!assessmentId) return;

  const container = document.getElementById('results-content');
  container.innerHTML = '<div style="text-align:center; padding:32px;"><span class="spinner"></span></div>';

  try {
    const resp = await fetch(`${API}/assessments/${assessmentId}`);
    if (!resp.ok) throw new Error('Failed to load assessment');
    const data = await resp.json();

    if (data.status !== 'completed') {
      container.innerHTML = `<div class="alert alert-info">Assessment status: <strong>${data.status}</strong>. Refresh when complete.</div>`;
      return;
    }

    renderResults(data, container);
  } catch (e) {
    container.innerHTML = `<div class="alert alert-error">Failed to load results: ${e.message}</div>`;
  }
}

function renderResults(data, container) {
  const overallColor = scoreColor(data.overall_posture_score);
  const overallLabel = scoreLabel(data.overall_posture_score);
  const pct = (data.overall_posture_score / 5 * 100).toFixed(0);

  // Gauge SVG
  const radius = 80;
  const cx = 110, cy = 110;
  const startAngle = -210, endAngle = 30; // 240 degree arc
  const totalDeg = 240;
  const scoreDeg = (data.overall_posture_score / 5) * totalDeg;

  function polarToXY(angle, r) {
    const rad = (angle - 90) * Math.PI / 180;
    return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
  }

  function arcPath(startDeg, endDeg, r) {
    const s = polarToXY(startDeg, r);
    const e = polarToXY(endDeg, r);
    const large = (endDeg - startDeg) > 180 ? 1 : 0;
    return `M ${s.x} ${s.y} A ${r} ${r} 0 ${large} 1 ${e.x} ${e.y}`;
  }

  const bgPath = arcPath(startAngle, endAngle, radius);
  const scorePath = arcPath(startAngle, startAngle + scoreDeg, radius);

  const gaugeSVG = `
    <svg class="gauge-svg" width="220" height="160" viewBox="0 0 220 145">
      <path d="${bgPath}" fill="none" stroke="var(--border)" stroke-width="14" stroke-linecap="round"/>
      <path d="${scorePath}" fill="none" stroke="${overallColor}" stroke-width="14" stroke-linecap="round"/>
      <text x="${cx}" y="${cy - 8}" fill="${overallColor}" class="gauge-value" style="font-size:42px; font-weight:700;">${data.overall_posture_score.toFixed(2)}</text>
      <text x="${cx}" y="${cy + 26}" fill="var(--text-muted)" class="gauge-label" style="font-size:13px;">${overallLabel}</text>
      <text x="${cx}" y="${cy + 44}" fill="var(--text-muted)" class="gauge-label" style="font-size:11px;">out of 5.00</text>
    </svg>
  `;

  // Framework score cards
  const fwCards = data.framework_results.map(fr => {
    const c = scoreColor(fr.overall_score);
    const w = (fr.overall_score / 5 * 100).toFixed(0);
    return `
      <div class="fw-score-card">
        <div class="fw-score-name">${fr.framework_name}</div>
        <div class="fw-score-value" style="color:${c}">${fr.overall_score.toFixed(2)}</div>
        <div style="font-size:12px; color:var(--text-muted)">${scoreLabel(fr.overall_score)}</div>
        <div class="fw-score-bar"><div class="fw-score-bar-fill" style="width:${w}%; background:${c}"></div></div>
      </div>
    `;
  }).join('');

  // Family heatmap table
  let heatmapRows = '';
  for (const fr of data.framework_results) {
    for (const fs of fr.family_scores) {
      const c = scoreColor(fs.average_score);
      heatmapRows += `
        <tr>
          <td>${fr.framework_name}</td>
          <td>${fs.family}</td>
          <td>${fs.control_count}</td>
          <td><span class="score-pill" style="background:${c}22; color:${c}">${fs.average_score.toFixed(1)}</span></td>
        </tr>
      `;
    }
  }

  // Gap table (all controls)
  let gapRows = '';
  let rowIdx = 0;
  for (const fr of data.framework_results) {
    for (const cr of fr.control_results) {
      const c = scoreColor(cr.maturity_score);
      const idx = rowIdx++;
      const hasDetail = (cr.gaps?.length || cr.recommendations?.length || cr.evidence?.length);

      gapRows += `
        <tr class="${hasDetail ? 'expandable' : ''}" onclick="${hasDetail ? `toggleGapRow(${idx})` : ''}">
          <td><code style="font-size:11px">${cr.control_id}</code></td>
          <td>${cr.control_name}</td>
          <td>${cr.family}</td>
          <td><span class="score-pill" style="background:${c}22; color:${c}">${cr.maturity_score}</span></td>
          <td style="color:var(--text-muted); font-size:12px; max-width:300px;">${cr.score_rationale || '—'}</td>
          <td>${hasDetail ? '<span style="color:var(--accent)">▼</span>' : ''}</td>
        </tr>
        <tr class="gap-detail-row hidden" id="gap-detail-${idx}">
          <td colspan="6">
            ${cr.evidence?.length ? `<div style="margin-bottom:8px"><strong style="font-size:12px">Evidence:</strong><div class="tag-list" style="margin-top:4px">${cr.evidence.map(e => `<span class="tag tag-evidence" title="${escapeHtml(e)}">${escapeHtml(e.substring(0,100))}${e.length > 100 ? '…' : ''}</span>`).join('')}</div></div>` : ''}
            ${cr.gaps?.length ? `<div style="margin-bottom:8px"><strong style="font-size:12px">Gaps:</strong><div class="tag-list" style="margin-top:4px">${cr.gaps.map(g => `<span class="tag tag-gap">${escapeHtml(g)}</span>`).join('')}</div></div>` : ''}
            ${cr.recommendations?.length ? `<div><strong style="font-size:12px">Recommendations:</strong><div class="tag-list" style="margin-top:4px">${cr.recommendations.map(r => `<span class="tag tag-rec">${escapeHtml(r)}</span>`).join('')}</div></div>` : ''}
          </td>
        </tr>
      `;
    }
  }

  container.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
      <div>
        <div style="font-size:18px; font-weight:600;">${data.document_name}</div>
        <div style="font-size:12px; color:var(--text-muted)">
          ${data.frameworks_assessed.length} framework(s) · ${formatDate(data.created_at)}
        </div>
      </div>
      <button class="btn btn-secondary" onclick="downloadReport('${data.assessment_id}')">⬇ Download JSON</button>
    </div>

    <div class="overview-grid">
      <div class="card" style="display:flex; flex-direction:column; align-items:center; justify-content:center;">
        <div style="font-size:13px; color:var(--text-muted); margin-bottom:8px; font-weight:500; text-transform:uppercase; letter-spacing:0.5px;">Overall Posture Score</div>
        ${gaugeSVG}
      </div>
      <div class="card">
        <div class="card-title">Framework Scores</div>
        <div class="fw-score-grid">${fwCards}</div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">Control Family Heatmap</div>
      <div class="scroll-x">
        <table class="heatmap-table">
          <thead><tr><th>Framework</th><th>Family</th><th>Controls</th><th>Score</th></tr></thead>
          <tbody>${heatmapRows}</tbody>
        </table>
      </div>
    </div>

    <div class="card">
      <div class="section-header">
        <div class="section-title">Control Assessment Details</div>
        <div style="font-size:12px; color:var(--text-muted)">Click rows to expand gaps &amp; recommendations</div>
      </div>
      <div class="scroll-x">
        <table class="gap-table">
          <thead><tr><th>ID</th><th>Control</th><th>Family</th><th>Score</th><th>Rationale</th><th></th></tr></thead>
          <tbody>${gapRows}</tbody>
        </table>
      </div>
    </div>
  `;
}

function toggleGapRow(idx) {
  const row = document.getElementById(`gap-detail-${idx}`);
  if (row) row.classList.toggle('hidden');
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

async function downloadReport(assessmentId) {
  window.location.href = `${API}/reports/${assessmentId}/download`;
}
