/* ============================================================
   Custom Demo v2 - frontend logic
   ============================================================ */

const API = `${window.location.origin}/api`;

let map, allZonesLayer, filterLayer;
let compLayers = { tp: null, fp: null, fn: null };
let gradientLayer = null;
let zonesGeoJSON = null;
let isRunning = false;
let lastRankedZones = [];
let lastPerfectCount = 0;

const OBS_PREVIEW_LEN = 500;

// ============================================================
// MAP
// ============================================================
function initMap() {
  map = L.map("map").setView([42.3601, -71.0589], 12);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
    attribution: "(C) OpenStreetMap (C) CARTO",
    maxZoom: 19,
  }).addTo(map);
}

async function loadZones() {
  try {
    const r = await fetch(`${API}/zones`);
    zonesGeoJSON = await r.json();
    allZonesLayer = L.geoJSON(zonesGeoJSON, {
      style: { fillColor: "#ccc", fillOpacity: 0.08, color: "#aaa", weight: 0.5 },
    }).addTo(map);
    showToast("Zones loaded");
  } catch (err) {
    console.error(err);
    showToast("Error loading zones", true);
  }
}

// ============================================================
// UI HELPERS
// ============================================================
function showToast(msg, isError = false) {
  const el = document.getElementById("status-toast");
  el.textContent = msg;
  el.style.borderColor = isError ? "rgba(224, 82, 82, 0.6)" : "rgba(29, 154, 108, 0.6)";
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2500);
}

function setStepStatus(stepKey, status, meta) {
  const el = document.querySelector(`[data-step="${stepKey}"]`);
  if (!el) return;
  el.classList.remove("pending", "running", "success", "error");
  el.classList.add(status);
  const metaEl = el.querySelector(".step-meta");
  if (metaEl) metaEl.textContent = meta || "";
}

function resetSteps() {
  setStepStatus("data", "pending", "Pending");
  setStepStatus("spec", "pending", "Pending");
  setStepStatus("run", "pending", "Pending");
}

function appendMessage(role, text) {
  const log = document.getElementById("chat-log");
  const item = document.createElement("div");
  item.className = `chat-bubble ${role}`;
  item.innerHTML = `
    <div class="chat-role">${role === "user" ? "User" : "System"}</div>
    <div>${escapeHtml(text)}</div>
  `;
  log.appendChild(item);
  log.scrollTop = log.scrollHeight;
}

function renderSpec(spec, validation) {
  const pre = document.getElementById("spec-json");
  pre.textContent = spec ? JSON.stringify(spec, null, 2) : "No spec generated.";

  const status = document.getElementById("spec-status");
  status.textContent = validation?.ok ? "Verified" : "Needs attention";
  status.className = `pill ${validation?.ok ? "pill-success" : "pill-danger"}`;

  const issues = document.getElementById("spec-issues");
  issues.innerHTML = "";
  if (!validation) return;

  if (validation.errors?.length) {
    validation.errors.forEach(err => {
      const item = document.createElement("div");
      item.className = "issue";
      item.textContent = err;
      issues.appendChild(item);
    });
  }

  if (validation.warnings?.length) {
    validation.warnings.forEach(warn => {
      const item = document.createElement("div");
      item.className = "issue warning";
      item.textContent = warn;
      issues.appendChild(item);
    });
  }

  if (!validation.errors?.length && !validation.warnings?.length) {
    const item = document.createElement("div");
    item.className = "issue warning";
    item.textContent = "Spec validated with no issues.";
    issues.appendChild(item);
  }
}

function resetResults() {
  renderSteps("gt-steps", []);
  renderSteps("llm-steps", []);
  renderSteps("compare-steps", []);
  document.getElementById("m-precision").textContent = "-";
  document.getElementById("m-recall").textContent = "-";
  document.getElementById("m-f1").textContent = "-";
  document.getElementById("llm-panel-title").textContent = "LLM output";
  document.getElementById("generated-code").textContent = "";
  document.getElementById("code-section").style.display = "none";
  document.getElementById("agent-section").style.display = "none";
  clearAgentTrace();
  clearLayers();
  resetRanked();
}

// ============================================================
// PIPELINE
// ============================================================
async function runPipeline() {
  if (isRunning) return;
  const prompt = document.getElementById("prompt-input").value.trim();
  if (!prompt) {
    showToast("Enter a prompt first", true);
    return;
  }

  isRunning = true;
  document.getElementById("btn-run").disabled = true;
  resetSteps();
  resetResults();

  appendMessage("user", prompt);

  try {
    setStepStatus("data", "running", "Checking data");
    const statusResp = await fetch(`${API}/status`);
    const statusData = await statusResp.json();

    if (!statusData.ok) {
      setStepStatus("data", "error", "Missing data");
      appendMessage("system", (statusData.errors || ["Data check failed"]).join("; "));
      showToast("Data check failed", true);
      return;
    }

    setStepStatus("data", "success", `${statusData.zones_count} zones`);
    appendMessage("system", `Data check passed. ${statusData.zones_count} zones loaded.`);

    setStepStatus("spec", "running", "Generating spec");
    const model = document.getElementById("model-select").value;
    const specResp = await fetch(`${API}/spec_from_nl`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nl_query: prompt, model }),
    });
    const specData = await specResp.json();

    if (specData.error) {
      setStepStatus("spec", "error", "Spec failed");
      appendMessage("system", specData.error);
      showToast("Spec generation failed", true);
      renderSpec(null, null);
      return;
    }

    renderSpec(specData.spec, specData.validation);

    if (!specData.validation?.ok) {
      setStepStatus("spec", "error", "Spec needs fixes");
      appendMessage("system", "Spec validation failed. Fix the prompt and retry.");
      showToast("Spec validation failed", true);
      return;
    }

    setStepStatus("spec", "success", "Spec verified");
    appendMessage("system", "Spec verified. Running evaluation.");

    setStepStatus("run", "running", "Evaluating");
    const strategy = document.getElementById("strategy-select").value;
    const evalResp = await fetch(`${API}/evaluate_prompt`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nl_query: prompt,
        model,
        strategy,
        spec: specData.spec,
      }),
    });
    const evalData = await evalResp.json();

    if (evalData.error) {
      setStepStatus("run", "error", "Evaluation failed");
      appendMessage("system", evalData.error);
      showToast("Evaluation failed", true);
      return;
    }

    await applyResults(evalData, strategy);
    setStepStatus("run", "success", `F1 ${Math.round(evalData.comparison.f1 * 100)}%`);
    appendMessage("system", `Evaluation complete. F1 ${Math.round(evalData.comparison.f1 * 100)}%.`);
    showToast("Evaluation complete");

  } catch (err) {
    console.error(err);
    setStepStatus("run", "error", "Error");
    showToast("Pipeline failed", true);
  } finally {
    isRunning = false;
    document.getElementById("btn-run").disabled = false;
  }
}

async function applyResults(data, strategy) {
  const llmTitles = {
    direct: "LLM output (direct)",
    react: "LLM output (react)",
    reflexion: "LLM output (reflexion)",
  };
  document.getElementById("llm-panel-title").textContent = llmTitles[strategy] || "LLM output";

  renderSteps("gt-steps", []);
  renderSteps("llm-steps", []);
  renderSteps("compare-steps", []);

  // Animate GT steps
  for (let i = 0; i < data.gt_steps.length; i++) {
    renderSteps("gt-steps", data.gt_steps, i);
    highlightZones(data.gt_steps[i].zones, "#227af6", 0.55);
    await sleep(900);
  }

  // Animate LLM steps
  if (data.llm_steps && data.llm_steps.length) {
    for (let i = 0; i < data.llm_steps.length; i++) {
      renderSteps("llm-steps", data.llm_steps, i);
      highlightZones(data.llm_steps[i].zones, "#8556ff", 0.5);
      await sleep(900);
    }
  } else {
    renderSteps("llm-steps", [{ description: data.codegen_error || "No LLM output", count: 0 }], 0);
  }

  const cmp = data.comparison;
  showComparison(cmp);

  renderSteps("compare-steps", [
    { description: "Ground truth zones", count: data.gt_count },
    { description: "LLM predicted zones", count: data.llm_count },
    { description: "True positives", count: cmp.tp_count },
    { description: "False positives", count: cmp.fp_count },
    { description: "False negatives", count: cmp.fn_count },
  ], 4);

  document.getElementById("m-precision").textContent = (cmp.precision * 100).toFixed(1) + "%";
  document.getElementById("m-recall").textContent = (cmp.recall * 100).toFixed(1) + "%";
  document.getElementById("m-f1").textContent = (cmp.f1 * 100).toFixed(1) + "%";

  if (data.strategy === "direct" && data.generated_code) {
    document.getElementById("generated-code").textContent = data.generated_code;
    document.getElementById("code-section").style.display = "flex";
  } else if (data.agent_trace) {
    renderAgentTrace(data.agent_trace, data.strategy);
    document.getElementById("agent-section").style.display = "flex";
  }

  // Ranked zones panel + gradient map — only when NO perfect matches
  if (data.gt_count === 0 && data.ranked_zones && data.ranked_zones.length > 0) {
    renderRankedZones(data.ranked_zones, 0);
    showGradientZones(data.ranked_zones);
  }
}

// ============================================================
// MAP HELPERS
// ============================================================
function clearLayers() {
  if (filterLayer) { map.removeLayer(filterLayer); filterLayer = null; }
  if (gradientLayer) { map.removeLayer(gradientLayer); gradientLayer = null; }
  Object.keys(compLayers).forEach(key => {
    if (compLayers[key]) { map.removeLayer(compLayers[key]); compLayers[key] = null; }
  });
}

function highlightZones(ids, color, opacity) {
  if (!zonesGeoJSON) return;
  const s = new Set(ids.map(String));
  const feats = zonesGeoJSON.features.filter(f => s.has(String(f.properties.zone_id)));
  if (filterLayer) map.removeLayer(filterLayer);
  filterLayer = L.geoJSON({ type: "FeatureCollection", features: feats }, {
    style: { fillColor: color, fillOpacity: opacity, color, weight: 2 },
  }).addTo(map);
}

function showComparison(cmp) {
  clearLayers();
  const make = (ids, color, op) => {
    const s = new Set(ids.map(String));
    const feats = zonesGeoJSON.features.filter(f => s.has(String(f.properties.zone_id)));
    return L.geoJSON({ type: "FeatureCollection", features: feats }, {
      style: { fillColor: color, fillOpacity: op, color, weight: 2 },
    });
  };
  if (cmp.fn.length) compLayers.fn = make(cmp.fn, "#264653", 0.6).addTo(map);
  if (cmp.fp.length) compLayers.fp = make(cmp.fp, "#e05252", 0.7).addTo(map);
  if (cmp.tp.length) compLayers.tp = make(cmp.tp, "#1d9a6c", 0.7).addTo(map);
}

// ============================================================
// RENDERING
// ============================================================
function renderSteps(containerId, steps, active = -1) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = steps.map((s, i) => `
    <div class="step-item ${i === active ? "active" : ""}">
      <span>${escapeHtml(s.description || "")}</span>
      <span class="step-count">${s.count ?? "-"}</span>
    </div>
  `).join("");
}

function clearAgentTrace() {
  document.getElementById("agent-meta").textContent = "No trace available.";
  document.getElementById("agent-status").textContent = "Not run";
  document.getElementById("agent-status").className = "pill pill-muted";
  document.getElementById("agent-trace-steps").innerHTML = "";
  document.getElementById("reflections-list").innerHTML = "";
  document.getElementById("reflections-wrap").style.display = "none";
}

function escapeHtml(str) {
  const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
  return String(str ?? "").replace(/[&<>"']/g, m => map[m]);
}

function renderObservation(value, idx) {
  const txt = String(value ?? "");
  const short = txt.length > OBS_PREVIEW_LEN;
  const preview = escapeHtml(short ? txt.slice(0, OBS_PREVIEW_LEN) + "..." : txt);
  const full = escapeHtml(txt);
  const bodyId = `obs-body-${idx}`;
  const fullId = `obs-full-${idx}`;

  if (!short) {
    return `<div class="trace-observation">${full}</div>`;
  }

  return `
    <div class="trace-observation" id="${bodyId}">${preview}</div>
    <span class="trace-toggle" onclick="toggleObservation('${bodyId}', '${fullId}')" id="${fullId}">Show more</span>
    <input type="hidden" data-full="${full.replace(/"/g, "&quot;")}" data-short="${preview.replace(/"/g, "&quot;")}">
  `;
}

function toggleObservation(bodyId, toggleId) {
  const body = document.getElementById(bodyId);
  const toggle = document.getElementById(toggleId);
  if (!body || !toggle) return;
  const hidden = toggle.nextElementSibling;
  if (!hidden) return;

  const full = hidden.getAttribute("data-full") || "";
  const short = hidden.getAttribute("data-short") || "";
  const expanded = toggle.getAttribute("data-expanded") === "1";

  if (expanded) {
    body.innerHTML = short;
    toggle.textContent = "Show more";
    toggle.setAttribute("data-expanded", "0");
  } else {
    body.innerHTML = full;
    toggle.textContent = "Show less";
    toggle.setAttribute("data-expanded", "1");
  }
}

function renderAgentTrace(trace, strategy) {
  const steps = Array.isArray(trace.steps) ? trace.steps : [];
  const success = !!trace.success;
  const attempts = trace.num_attempts || 1;
  const meta = `${strategy.toUpperCase()} | Steps: ${trace.num_steps || steps.length} | Attempts: ${attempts}`;

  document.getElementById("agent-meta").textContent = meta;
  const badge = document.getElementById("agent-status");
  badge.textContent = success ? "Success" : "Failed";
  badge.className = success ? "pill pill-success" : "pill pill-danger";

  const reflections = Array.isArray(trace.reflections) ? trace.reflections : [];
  const reflectionsWrap = document.getElementById("reflections-wrap");
  const reflectionsList = document.getElementById("reflections-list");
  reflectionsList.innerHTML = "";

  if (strategy === "reflexion" && reflections.length > 0) {
    reflections.forEach((r, i) => {
      const item = document.createElement("div");
      item.className = "reflection-item";
      item.innerHTML = `<strong>Attempt ${i + 1} Reflection:</strong><br>${escapeHtml(r)}`;
      reflectionsList.appendChild(item);
    });
    reflectionsWrap.style.display = "flex";
  } else {
    reflectionsWrap.style.display = "none";
  }

  const container = document.getElementById("agent-trace-steps");
  if (steps.length === 0) {
    container.innerHTML = '<div class="step-item">No tool trace returned.</div>';
    return;
  }

  container.innerHTML = steps.map((s, i) => `
    <details class="trace-step" ${i < 2 ? "open" : ""}>
      <summary>Step ${s.step || i + 1}</summary>
      <div class="trace-step-body">
        <div class="trace-thought">${escapeHtml(s.thought || "")}</div>
        <div class="trace-action">${escapeHtml(s.action || "(final answer / no action)")}</div>
        ${renderObservation(s.observation || "", i)}
      </div>
    </details>
  `).join("");
}

// ============================================================
// RANKING
// ============================================================
function getScoreColor(score) {
  if (score >= 1.0) return "#1d9a6c";
  if (score >= 0.75) return "#4ecb9e";
  if (score >= 0.50) return "#f4b06b";
  if (score >= 0.25) return "#f4a259";
  if (score > 0)    return "#f0a3a3";
  return "#e05252";
}

function showGradientZones(rankedZones) {
  if (!zonesGeoJSON) return;
  clearLayers();

  const scoreMap = {};
  rankedZones.forEach(z => { scoreMap[String(z.zone_id)] = z; });

  const scored = zonesGeoJSON.features.filter(f => scoreMap[String(f.properties.zone_id)]);

  gradientLayer = L.geoJSON({ type: "FeatureCollection", features: scored }, {
    style: (feature) => {
      const z = scoreMap[String(feature.properties.zone_id)];
      const color = getScoreColor(z ? z.score : 0);
      return { fillColor: color, fillOpacity: 0.72, color, weight: 1.5 };
    },
    onEachFeature: (feature, layer) => {
      const z = scoreMap[String(feature.properties.zone_id)];
      if (z) layer.bindPopup(buildZonePopup(z), { maxWidth: 280 });
    },
  }).addTo(map);

  document.getElementById("legend-standard").style.display = "none";
  document.getElementById("legend-ranked").style.display = "block";
}

function buildZonePopup(z) {
  const pct = Math.round(z.score * 100);
  const color = getScoreColor(z.score);
  const leaves = flattenBreakdown(z.breakdown);

  const rows = leaves.map(leaf => {
    const icon = leaf.satisfied ? "✓" : "✗";
    const cls = leaf.satisfied ? "popup-ok" : "popup-fail";
    return `<tr class="${cls}"><td>${icon}</td><td>${escapeHtml(leaf.label)}</td></tr>`;
  }).join("");

  return `
    <div class="zone-popup">
      <div class="popup-header">
        <strong>Zone ${escapeHtml(z.zone_id.slice(0, 12))}</strong>
        <span class="popup-score" style="color:${color}">${pct}%</span>
      </div>
      <div class="popup-summary">${escapeHtml(z.summary)}</div>
      <table class="popup-table">${rows}</table>
    </div>`;
}

function flattenBreakdown(node) {
  if (!node) return [];
  if (!node.children || node.children.length === 0) return [node];
  return node.children.flatMap(flattenBreakdown);
}

function getTopN(allZones) {
  const val = document.getElementById("topn-select").value;
  if (val === "75pct") return allZones.filter(z => z.score >= 0.75);
  return allZones.slice(0, parseInt(val, 10));
}

function renderRankedZones(rankedZones, perfectCount) {
  const section = document.getElementById("ranked-section");
  const list = document.getElementById("ranked-list");
  const subtitle = document.getElementById("ranked-subtitle");
  const pill = document.getElementById("ranked-count-pill");
  const banner = document.getElementById("no-gt-banner");
  const noGtMsg = document.getElementById("no-gt-msg");

  lastRankedZones = rankedZones;
  lastPerfectCount = perfectCount;
  section.style.display = "flex";

  const visible = getTopN(rankedZones);

  if (perfectCount > 0) {
    subtitle.textContent = `${perfectCount} perfect match${perfectCount > 1 ? "es" : ""} — showing ${visible.length} ranked`;
    banner.style.display = "none";
  } else {
    subtitle.textContent = `Showing ${visible.length} closest zones`;
    noGtMsg.textContent = `No zones satisfy all constraints. Showing closest partial matches below.`;
    banner.style.display = "flex";
  }
  pill.textContent = visible.length;

  list.innerHTML = visible.map((z, i) => {
    const pct = Math.round(z.score * 100);
    const color = getScoreColor(z.score);
    const leaves = flattenBreakdown(z.breakdown);
    const constraintRows = leaves.map(leaf => {
      const icon = leaf.satisfied ? "✓" : "✗";
      const cls = leaf.satisfied ? "detail-ok" : "detail-fail";
      return `<div class="detail-row ${cls}">${icon} ${escapeHtml(leaf.label)}</div>`;
    }).join("");

    return `
      <div class="ranked-item" data-zone-id="${escapeHtml(z.zone_id)}"
           onclick="toggleRankedItem(this, '${escapeHtml(z.zone_id)}')"
           title="Click to expand · double-click to fly to zone">
        <div class="ranked-rank" style="color:${color}">#${i + 1}</div>
        <div class="ranked-info">
          <div class="ranked-zone-id">${escapeHtml(z.zone_id.slice(0, 15))}</div>
          <div class="ranked-meta">${z.satisfied_count}/${z.total_constraints} met</div>
          <div class="ranked-details">${constraintRows}</div>
        </div>
        <div class="ranked-bar-wrap">
          <div class="ranked-pct" style="color:${color}">${pct}%</div>
          <div class="ranked-bar">
            <div class="ranked-bar-fill" style="width:${pct}%; background:${color}"></div>
          </div>
        </div>
      </div>`;
  }).join("");
}

function toggleRankedItem(el, zoneId) {
  // single click = expand/collapse details
  const wasExpanded = el.classList.contains("expanded");
  // collapse all others first
  document.querySelectorAll(".ranked-item.expanded").forEach(x => x.classList.remove("expanded"));
  if (!wasExpanded) el.classList.add("expanded");
  // double-click handled separately via dblclick event wired below
}

function flyToZone(zoneId) {
  if (!zonesGeoJSON || !gradientLayer) return;
  const feat = zonesGeoJSON.features.find(f => String(f.properties.zone_id) === String(zoneId));
  if (!feat) return;

  const layer = gradientLayer.getLayers().find(l => {
    return l.feature && String(l.feature.properties.zone_id) === String(zoneId);
  });
  if (!layer) return;

  const bounds = layer.getBounds ? layer.getBounds() : null;
  if (bounds) map.fitBounds(bounds, { maxZoom: 14 });
  layer.openPopup();
}

function resetRanked() {
  const section = document.getElementById("ranked-section");
  section.style.display = "none";
  document.getElementById("ranked-list").innerHTML = "";
  document.getElementById("ranked-count-pill").textContent = "—";
  document.getElementById("no-gt-banner").style.display = "none";
  document.getElementById("legend-standard").style.display = "block";
  document.getElementById("legend-ranked").style.display = "none";
  lastRankedZones = [];
  lastPerfectCount = 0;
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ============================================================
// THEME
// ============================================================
function initTheme() {
  const stored = localStorage.getItem("theme");
  const theme = stored || "dark";
  document.body.dataset.theme = theme;
}

function toggleTheme() {
  const next = document.body.dataset.theme === "dark" ? "light" : "dark";
  document.body.dataset.theme = next;
  localStorage.setItem("theme", next);
}

// ============================================================
// EVENTS
// ============================================================
document.getElementById("btn-run").addEventListener("click", runPipeline);
document.getElementById("btn-clear").addEventListener("click", () => {
  document.getElementById("prompt-input").value = "";
  document.getElementById("chat-log").innerHTML = "";
  renderSpec(null, null);
  resetSteps();
  resetResults();
});

document.getElementById("theme-toggle").addEventListener("click", toggleTheme);

document.getElementById("ranked-list").addEventListener("dblclick", (e) => {
  const item = e.target.closest(".ranked-item");
  if (item) flyToZone(item.dataset.zoneId);
});

document.getElementById("topn-select").addEventListener("change", () => {
  if (lastRankedZones.length > 0) {
    renderRankedZones(lastRankedZones, lastPerfectCount);
    if (lastPerfectCount === 0) showGradientZones(getTopN(lastRankedZones));
  }
});

document.getElementById("prompt-input").addEventListener("keydown", (event) => {
  if (event.ctrlKey && event.key === "Enter") {
    runPipeline();
  }
});

// ============================================================
// INIT
// ============================================================
async function init() {
  initTheme();
  initMap();
  await loadZones();
  resetSteps();
}

init();
