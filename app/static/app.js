const SAMPLE_TOKENS = [
  { id: "t1", text: "TAX INVOICE #INV-2026-881", bbox: [0.08, 0.06, 0.88, 0.11] },
  { id: "t2", text: "Vendor: Acme Cloud Systems", bbox: [0.08, 0.14, 0.58, 0.18] },
  { id: "t3", text: "Service Item", bbox: [0.08, 0.28, 0.45, 0.32] },
  { id: "t4", text: "Amount", bbox: [0.70, 0.28, 0.90, 0.32] },
  { id: "t5", text: "Enterprise Support", bbox: [0.08, 0.36, 0.45, 0.40] },
  { id: "t6", text: "$1,200.00", bbox: [0.70, 0.36, 0.90, 0.40] },
  { id: "t7", text: "Total Amount: $1,200.00", bbox: [0.48, 0.62, 0.90, 0.67] }
];

document.getElementById("tokens-input").value = JSON.stringify(SAMPLE_TOKENS, null, 2);

async function checkSystemInfo() {
  try {
    const res = await fetch("/api/v1/system/info");
    const data = await res.json();
    document.getElementById("system-status").textContent =
      `Online • Phases 1-${data.completed_phases} (${data.env})`;
  } catch {
    document.getElementById("system-status").textContent = "API Offline";
  }
}

function drawBoundingBoxes(tokens, groundedFields = []) {
  const canvas = document.getElementById("bbox-canvas");
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;

  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, w, h);

  // Draw raw OCR/PDF tokens in soft blue
  tokens.forEach((tok) => {
    const [x0, y0, x1, y1] = tok.bbox;
    ctx.strokeStyle = "#94a3b8";
    ctx.lineWidth = 1;
    ctx.strokeRect(x0 * w, y0 * h, (x1 - x0) * w, (y1 - y0) * h);
    ctx.fillStyle = "#1e293b";
    ctx.font = "11px sans-serif";
    ctx.fillText(tok.text, x0 * w + 3, y0 * h + 13);
  });

  // Highlight grounded fields in emerald green or red if ungrounded
  groundedFields.forEach((f) => {
    if (!f.bbox || f.bbox.length !== 4) return;
    const [x0, y0, x1, y1] = f.bbox;
    ctx.strokeStyle = f.grounded ? "#16a34a" : "#dc2626";
    ctx.lineWidth = 2.5;
    ctx.strokeRect(x0 * w, y0 * h, (x1 - x0) * w, (y1 - y0) * h);
    ctx.fillStyle = f.grounded ? "rgba(22, 163, 74, 0.12)" : "rgba(220, 38, 38, 0.12)";
    ctx.fillRect(x0 * w, y0 * h, (x1 - x0) * w, (y1 - y0) * h);
  });
}

document.getElementById("btn-load-sample").addEventListener("click", () => {
  document.getElementById("tokens-input").value = JSON.stringify(SAMPLE_TOKENS, null, 2);
  drawBoundingBoxes(SAMPLE_TOKENS);
});

document.getElementById("btn-run-pipeline").addEventListener("click", async () => {
  const docId = document.getElementById("doc-id").value.trim() || "demo-invoice-001";
  const tenantId = document.getElementById("tenant-id").value.trim() || "default-tenant";
  let tokens = [];
  try {
    tokens = JSON.parse(document.getElementById("tokens-input").value);
  } catch (err) {
    document.getElementById("pipeline-output").textContent = "Invalid JSON in tokens: " + err.message;
    return;
  }

  const res = await fetch(`/api/v1/documents/${encodeURIComponent(docId)}/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      pages: [{ page_no: 1, tokens }],
      config: { tenant_id: tenantId, enable_rag_indexing: true }
    })
  });
  const data = await res.json();
  document.getElementById("pipeline-output").textContent = JSON.stringify(data, null, 2);
  document.getElementById("pipeline-verdict").textContent =
    `${data.doc_type.toUpperCase()} • ${data.approval_decision}`;

  const fieldsRes = await fetch(`/api/v1/documents/${encodeURIComponent(docId)}/fields`);
  const fields = fieldsRes.ok ? await fieldsRes.json() : [];
  drawBoundingBoxes(tokens, fields);
  refreshReviews();
  refreshMetrics();
});

document.getElementById("btn-rag-query").addEventListener("click", async () => {
  const query = document.getElementById("rag-query").value.trim();
  const tenantId = document.getElementById("tenant-id").value.trim() || "default-tenant";
  const res = await fetch("/api/v1/rag/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, tenant_id: tenantId, top_k: 3 })
  });
  const data = await res.json();
  document.getElementById("rag-output").textContent = JSON.stringify(data, null, 2);
});

async function refreshReviews() {
  const res = await fetch("/api/v1/reviews?task_status=pending");
  const data = await res.json();
  const container = document.getElementById("reviews-list");
  if (!data.items || data.items.length === 0) {
    container.innerHTML = '<div class="muted">No pending review tasks.</div>';
    return;
  }
  container.innerHTML = data.items
    .map(
      (t) => `
      <div class="review-item">
        <div><strong>${t.field_path}</strong> (Doc: ${t.document_id})</div>
        <div class="muted">Original: ${JSON.stringify(t.original_value)} • Reason: ${t.reason}</div>
        <div class="row">
          <input id="corr-${t.task_id}" placeholder="Corrected value..." style="flex:1;" />
          <button onclick="resolveTask('${t.task_id}')">Approve &amp; Resolve</button>
        </div>
      </div>`
    )
    .join("");
}

window.resolveTask = async function (taskId) {
  const val = document.getElementById(`corr-${taskId}`).value;
  await fetch(`/api/v1/reviews/${taskId}/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ corrected_value: val, reviewer: "ui-operator" })
  });
  refreshReviews();
};

async function refreshMetrics() {
  const res = await fetch("/api/v1/metrics");
  const data = await res.json();
  document.getElementById("metrics-output").textContent = JSON.stringify(data, null, 2);
}

document.getElementById("btn-refresh-reviews").addEventListener("click", refreshReviews);
document.getElementById("btn-refresh-metrics").addEventListener("click", refreshMetrics);

checkSystemInfo();
drawBoundingBoxes(SAMPLE_TOKENS);
refreshReviews();
refreshMetrics();
