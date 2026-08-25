const state = {
  info: null,
  terms: [],
  records: [],
  localFiles: [],
  activeTab: "overview",
  lastQuery: null,
};

const content = document.querySelector("#content");

async function loadApi() {
  state.info = await fetchJson("/api/pheno/info");
  const terms = await fetchJson("/api/pheno/filtering_terms");
  const records = await fetchJson("/api/pheno/records");
  state.terms = terms.filtering_terms;
  state.records = records.records;
  document.querySelector("#release").textContent =
    `${state.info.release.site_id} / ${state.info.release.release_id}`;
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
      <table>
        <thead><tr><th>Phenopacket</th><th>Phenotypes</th><th>Diseases</th><th>Genomic</th></tr></thead>
        <tbody>
          ${state.records.map((record) => `
            <tr>
              <td>${escapeHtml(record.phenopacket_id)}</td>
              <td>${record.phenotype_count}</td>
              <td>${record.disease_count}</td>
              <td>${record.has_genomic_interpretations}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </section>
  `;
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

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

document.querySelector("#run-query").addEventListener("click", runQuery);
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
