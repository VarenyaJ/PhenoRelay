const state = {
  info: null,
  terms: [],
  records: [],
  recordCount: 0,
  localFiles: [],
  activeTab: "overview",
  lastQuery: null,
  filters: {},
  selectedRecord: null,
  rawSource: null,
};

const content = document.querySelector("#content");

async function loadApi() {
  state.info = await fetchJson("/api/pheno/info");
  const terms = await fetchJson("/api/pheno/filtering_terms");
  state.terms = terms.filtering_terms;
  await loadRecords();
  document.querySelector("#release").textContent =
    `${state.info.release.site_id} / ${state.info.release.release_id}`;
  renderDatalists();
  render();
}

async function fetchJson(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) {
    throw new Error(`${path} returned ${response.status}`);
  }
  return response.json();
}

async function runQuery() {
  const request = {
    query_id: "browser-query",
    feature: document.querySelector("#feature").value,
    term: document.querySelector("#term").value,
    match_mode: "exact",
    presence: "present",
    requested_granularity: document.querySelector("#granularity").value,
  };
  state.lastQuery = await fetchJson("/api/pheno/query", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(request),
  });
  state.activeTab = "overview";
  render();
}

async function loadRecords() {
  const params = new URLSearchParams();
  Object.entries(state.filters).forEach(([key, value]) => {
    if (value) {
      params.set(key, value);
    }
  });
  const suffix = params.toString() ? `?${params.toString()}` : "";
  const records = await fetchJson(`/api/pheno/records${suffix}`);
  state.records = records.records;
  state.recordCount = records.record_count ?? records.records.length;
}

async function applyFilters() {
  state.filters = {
    cohort: document.querySelector("#filter-cohort").value,
    phenotype: document.querySelector("#filter-phenotype").value,
    phenotype_presence: document.querySelector("#filter-phenotype-presence").value,
    disease: document.querySelector("#filter-disease").value,
    gene: document.querySelector("#filter-gene").value,
    has_genomic_interpretations: document.querySelector("#filter-genomics").value,
    source_pmid: document.querySelector("#filter-pmid").value,
    text: document.querySelector("#filter-text").value,
  };
  await loadRecords();
  state.activeTab = "records";
  render();
}

async function clearFilters() {
  [
    "#filter-cohort",
    "#filter-phenotype",
    "#filter-phenotype-presence",
    "#filter-disease",
    "#filter-gene",
    "#filter-genomics",
    "#filter-pmid",
    "#filter-text",
  ].forEach((selector) => {
    document.querySelector(selector).value = "";
  });
  state.filters = {};
  await loadRecords();
  state.activeTab = "records";
  render();
}

async function showRecordDetail(phenopacketId) {
  const detail = await fetchJson(`/api/pheno/records/${encodeURIComponent(phenopacketId)}`);
  state.selectedRecord = detail.record;
  state.rawSource = null;
  state.activeTab = "records";
  render();
}

async function loadRawSource(phenopacketId) {
  try {
    const source = await fetchJson(
      `/api/pheno/records/${encodeURIComponent(phenopacketId)}/source`
    );
    state.rawSource = source;
  } catch (error) {
    state.rawSource = {error: error.message};
  }
  render();
}

function render() {
  document.querySelectorAll(".tabs button").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === state.activeTab);
  });
  if (state.activeTab === "overview") {
    renderOverview();
  } else if (state.activeTab === "terms") {
    renderTerms();
  } else if (state.activeTab === "records") {
    renderRecords();
  } else {
    renderLocalFiles();
  }
}

function renderOverview() {
  const release = state.info?.release || {};
  content.innerHTML = `
    <section class="card">
      <h2>Release</h2>
      <p>${release.site_id || ""} / ${release.release_id || ""}</p>
      <p>${release.record_count || 0} records</p>
    </section>
    <section class="card">
      <h2>Filtered records</h2>
      <p>${state.recordCount} records match the active filters.</p>
    </section>
    <section class="card">
      <h2>Last query</h2>
      <pre>${JSON.stringify(state.lastQuery || {status: "not_run"}, null, 2)}</pre>
    </section>
  `;
}

function renderTerms() {
  content.innerHTML = `
    <section class="card">
      <h2>Filtering terms</h2>
      <table>
        <thead><tr><th>Feature</th><th>Term</th><th>Label</th><th>Presence</th><th>Count</th></tr></thead>
        <tbody>
          ${state.terms.map((term) => `
            <tr>
              <td>${escapeHtml(term.feature)}</td>
              <td>${escapeHtml(term.term)}</td>
              <td>${escapeHtml(term.label || "")}</td>
              <td>${escapeHtml(term.presence || "")}</td>
              <td>${term.count}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </section>
  `;
}

function renderRecords() {
  content.innerHTML = `
    <section class="card">
      <h2>Individuals</h2>
      <p>${state.recordCount} records match the active filters.</p>
      <table>
        <thead>
          <tr>
            <th>Phenopacket</th>
            <th>Cohort</th>
            <th>Source file</th>
            <th>Phenotypes</th>
            <th>Diseases</th>
            <th>Genes</th>
            <th>Genomic</th>
          </tr>
        </thead>
        <tbody>
          ${state.records.map((record) => `
            <tr>
              <td>
                <button class="link-button" data-record-id="${escapeHtml(record.phenopacket_id)}">
                  ${escapeHtml(record.phenopacket_id)}
                </button>
              </td>
              <td>${escapeHtml(record.source_cohort || "")}</td>
              <td>${escapeHtml(record.source_filename || "")}</td>
              <td>${record.phenotype_count}</td>
              <td>${record.disease_count}</td>
              <td>${record.gene_count}</td>
              <td>${record.has_genomic_interpretations ? "yes" : "no"}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </section>
    ${renderSelectedRecord()}
  `;
  document.querySelectorAll("[data-record-id]").forEach((button) => {
    button.addEventListener("click", () => showRecordDetail(button.dataset.recordId));
  });
  document.querySelectorAll("[data-raw-source-id]").forEach((button) => {
    button.addEventListener("click", () => loadRawSource(button.dataset.rawSourceId));
  });
}

function renderLocalFiles() {
  content.innerHTML = `
    <section class="card">
      <h2>Local files</h2>
      <p>${state.localFiles.length} files loaded in this browser.</p>
      <pre>${JSON.stringify(state.localFiles, null, 2)}</pre>
    </section>
  `;
}

function renderDatalists() {
  renderDatalist("cohort-options", "cohort");
  renderDatalist("phenotype-options", "phenotype");
  renderDatalist("disease-options", "disease");
  renderDatalist("gene-options", "gene");
  renderDatalist("pmid-options", "source_pmid");
}

function renderSelectedRecord() {
  const record = state.selectedRecord;
  if (!record) {
    return "";
  }
  return `
    <section class="card">
      <h2>Record detail</h2>
      <dl class="detail-list">
        <dt>Phenopacket</dt><dd>${escapeHtml(record.phenopacket_id)}</dd>
        <dt>Cohort</dt><dd>${escapeHtml(record.source_cohort || "")}</dd>
        <dt>Source file</dt><dd>${escapeHtml(record.source_filename || "")}</dd>
        <dt>PMIDs</dt><dd>${escapeHtml((record.source_pmids || []).join(", "))}</dd>
        <dt>Genes</dt><dd>${escapeHtml((record.genes || []).join(", "))}</dd>
        <dt>Variants</dt><dd>${escapeHtml((record.variant_descriptors || []).join(", "))}</dd>
      </dl>
      <div class="detail-grid">
        ${renderTermList("Present phenotypes", record.phenotypes, "present")}
        ${renderTermList("Excluded phenotypes", record.phenotypes, "excluded")}
        ${renderTermList("Diseases", record.diseases)}
      </div>
      <button data-raw-source-id="${escapeHtml(record.phenopacket_id)}">Load raw public source</button>
      ${renderRawSource()}
    </section>
  `;
}

function renderTermList(title, terms, presence) {
  const filtered = presence ? terms.filter((term) => term.presence === presence) : terms;
  return `
    <section class="detail-section">
      <h3>${escapeHtml(title)}</h3>
      <ul>
        ${filtered.map((term) => `
          <li><code>${escapeHtml(term.term)}</code> ${escapeHtml(term.label || "")}</li>
        `).join("")}
      </ul>
    </section>
  `;
}

function renderRawSource() {
  if (!state.rawSource) {
    return "";
  }
  return `<pre>${escapeHtml(JSON.stringify(state.rawSource, null, 2))}</pre>`;
}

function renderDatalist(id, feature) {
  const options = state.terms
    .filter((term) => term.feature === feature)
    .map((term) => {
      const label = term.label ? ` - ${term.label}` : "";
      return `<option value="${escapeHtml(term.term)}">${escapeHtml(term.term + label)}</option>`;
    })
    .join("");
  document.querySelector(`#${id}`).innerHTML = options;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

document.querySelector("#run-query").addEventListener("click", runQuery);
document.querySelector("#apply-filters").addEventListener("click", applyFilters);
document.querySelector("#clear-filters").addEventListener("click", clearFilters);
document.querySelectorAll(".tabs button").forEach((button) => {
  button.addEventListener("click", () => {
    state.activeTab = button.dataset.tab;
    render();
  });
});
document.querySelector("#file-input").addEventListener("change", async (event) => {
  state.localFiles = await Promise.all(
    Array.from(event.target.files).map(async (file) => {
      const text = await file.text();
      const parsed = JSON.parse(text);
      return {
        name: file.name,
        phenopacket_id: parsed.id || null,
        phenotype_count: (parsed.phenotypicFeatures || []).length,
        disease_count: (parsed.diseases || []).length,
      };
    })
  );
  state.activeTab = "local";
  render();
});

loadApi().catch((error) => {
  content.innerHTML = `<section class="card"><h2>Load failed</h2><pre>${escapeHtml(error.message)}</pre></section>`;
});
