const STORAGE_KEY = "evidentia_records_v2";
const HERO_VIDEO_VERSION = "20260618-reference-video";
const BRAND_WORD = 'EVID&#398;NTIA';
const ALL_VIEWS = ["intake", "entities", "graph", "chat", "intelligence", "query", "pack", "connectors", "cases", "consent", "storage"];
const VECTOR_CLUSTERS = [
  { name: "Conocimiento", color: "#f0de40", cx: 0.58, cy: -0.12, cz: 0.18 },
  { name: "Casos clinicos", color: "#56d4ff", cx: -0.34, cy: 0.22, cz: -0.18 },
  { name: "Pacientes", color: "#ff7a58", cx: 0.16, cy: 0.42, cz: 0.28 },
  { name: "Datos", color: "#70ffaf", cx: 0.04, cy: -0.48, cz: -0.22 }
];
const VECTOR_POINTS = buildVectorPoints();

const entityRules = [
  { type: "discipline", label: "Ortodoncia", pattern: /ortodoncia|alineador|bracket|oclusion|oclusión|maloclusion|maloclusión/i },
  { type: "discipline", label: "Rehabilitacion", pattern: /rehabilitacion|rehabilitación|protesis|prótesis|implante|implantologia|implantología/i },
  { type: "discipline", label: "Estetica dental", pattern: /estetica|estética|sonrisa|carilla|veneer|mockup|mocap/i },
  { type: "discipline", label: "Periodoncia", pattern: /periodoncia|encia|encía|periodontal|gingival/i },
  { type: "knowledge", label: "Nota de conocimiento", pattern: /nota|transcripcion|transcripción|decision|decisión|criterio|observacion|observación/i },
  { type: "knowledge", label: "Protocolo o aprendizaje", pattern: /protocolo|aprendizaje|leccion|lección|recordar|conocimiento/i },
  { type: "measurement", label: "CIELAB", pattern: /cielab|l\*|a\*|b\*|delta e|de00/i },
  { type: "measurement", label: "Medicion", pattern: /medicion|medición|medida|espesor|grosor|\d+(?:[.,]\d+)?\s*mm/i },
  { type: "outcome", label: "Resultado o seguimiento", pattern: /resultado|exito|éxito|fracaso|estable|seguimiento|dolor|problema|revision|revisión/i },
  { type: "pattern", label: "Patron odontologico", pattern: /patron|patrón|recurrencia|repetido|similar|similares|tendencia/i },
  { type: "clinical_focus", label: "Seguimiento oclusal", pattern: /oclusal|oclusion|oclusión|mordida|contactos|guia anterior|guía anterior|desoclusion|desoclusión/i }
];

const state = {
  records: loadRecords(),
  activeRecordId: null,
  activeView: "intake",
  activeEntityKey: null,
  activeGraphNodeId: "root",
  apiOnline: false,
  ragStats: null,
  aiProvider: null,
  chatMessages: [
    {
      role: "assistant",
      text: "Soy el chat de tu espejo de conocimiento. Preguntame por casos, proyectos, resultados, protocolos, fotos, fracasos, exitos o criterios que hayas guardado.",
      sources: []
    }
  ],
  installPrompt: null,
  agentLog: ["Sistema iniciado", "Esperando ingesta o seleccion de caso"]
};

const el = {
  body: document.body,
  work: document.querySelector("#work"),
  context: document.querySelector("#context"),
  contextBody: document.querySelector("#contextBody"),
  caseName: document.querySelector("#caseName"),
  traceCount: document.querySelector("#traceCount"),
  storageStatus: document.querySelector("#storageStatus"),
  consentBadge: document.querySelector("#consentBadge"),
  aiStatus: document.querySelector("#aiStatus"),
  search: document.querySelector("#globalSearch"),
  agentLogBtn: document.querySelector("#agentLogBtn"),
  installApp: document.querySelector("#installApp"),
  toast: document.querySelector("#toast")
};

document.querySelectorAll(".rail-item").forEach((button) => {
  button.addEventListener("click", () => setView(button.dataset.view));
});
el.search.addEventListener("input", () => {
  if (state.activeView !== "query") setView("query", false);
  render();
});
document.querySelector("#casePill").addEventListener("click", () => setView(state.activeRecordId ? "cases" : "intake"));
el.agentLogBtn.addEventListener("click", () => showToast(state.agentLog.slice(0, 4).join(" · ") || "Sin actividad registrada"));
el.installApp.addEventListener("click", installApp);
document.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    el.search.focus();
  }
});
window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  state.installPrompt = event;
  el.installApp.classList.add("available");
});
window.addEventListener("appinstalled", () => {
  state.installPrompt = null;
  showToast("Evidentia instalada en el dispositivo.");
});

bootstrap();

async function bootstrap() {
  await loadFromApi();
  await loadRagStats();
  await loadAiProvider();
  if (state.records[0]) state.activeRecordId = state.records[0].id;
  const hashView = window.location.hash.replace("#", "");
  if (hashView && ALL_VIEWS.includes(hashView)) {
    state.activeView = hashView;
  }
  document.querySelectorAll(".rail-item").forEach((button) => button.classList.toggle("active", button.dataset.view === state.activeView));
  render();
  requestAnimationFrame(drawCube);
}

function setView(view, clearSearch = true) {
  state.activeView = view;
  if (view !== "entities") state.activeEntityKey = null;
  if (window.location.hash !== "#" + view) history.replaceState(null, "", "#" + view);
  if (clearSearch && view !== "query") el.search.value = "";
  document.querySelectorAll(".rail-item").forEach((button) => button.classList.toggle("active", button.dataset.view === view));
  render();
}

function loadRecords() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || []; } catch { return []; }
}

function saveRecords() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state.records));
}

async function loadFromApi() {
  try {
    const response = await fetch("/api/records", { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error("API offline");
    const payload = await response.json();
    state.records = payload.records || [];
    state.apiOnline = true;
    saveRecords();
  } catch {
    state.apiOnline = false;
  }
}

async function loadRagStats() {
  try {
    const response = await fetch("/api/rag/stats", { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error("RAG offline");
    state.ragStats = await response.json();
  } catch {
    state.ragStats = null;
  }
}

async function loadAiProvider() {
  try {
    const response = await fetch("/api/ai/status", { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error("AI offline");
    state.aiProvider = await response.json();
    setAiState(state.aiProvider.active ? "working" : "idle", aiStatusLabel());
  } catch {
    state.aiProvider = null;
    setAiState("idle", aiStatusLabel());
  }
}

async function persistRecord(record) {
  setAiState("working", "IA procesando");
  try {
    const response = await fetch("/api/records", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(record)
    });
    if (!response.ok) {
      let detail = "API offline";
      try {
        const errorPayload = await response.json();
        detail = errorPayload.error || detail;
      } catch {}
      throw new Error(detail);
    }
    const payload = await response.json();
    state.apiOnline = true;
    state.agentLog.unshift("Registro guardado en SQLite: " + record.patientCode);
    showToast("Registro guardado e indexado.");
    return payload.record || record;
  } catch (error) {
    state.apiOnline = false;
    state.agentLog.unshift("Registro guardado en fallback local: " + record.patientCode + " · " + error.message);
    showToast("Guardado solo en este navegador. Servidor: " + error.message);
    return record;
  } finally {
    setAiState(state.aiProvider && state.aiProvider.active ? "working" : "idle", aiStatusLabel());
  }
}

function aiStatusLabel() {
  if (state.aiProvider && state.aiProvider.active) return "IA activa";
  return "Verificable local";
}

function setAiState(stateName, label) {
  el.aiStatus.dataset.state = stateName;
  el.aiStatus.querySelector("span:last-child").textContent = label;
}

function showToast(message) {
  if (!el.toast) return;
  el.toast.textContent = message;
  el.toast.classList.add("show");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => el.toast.classList.remove("show"), 4200);
}

async function installApp() {
  if (state.installPrompt) {
    state.installPrompt.prompt();
    await state.installPrompt.userChoice.catch(() => null);
    state.installPrompt = null;
    return;
  }
  const isiOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
  showToast(isiOS ? "En iPhone: Safari > compartir > Añadir a pantalla de inicio." : "En Chrome: menú de tres puntos > Instalar app o Añadir a pantalla de inicio.");
}

function render() {
  const active = activeRecord();
  el.body.dataset.case = active ? active.id : "";
  el.caseName.textContent = active ? active.patientCode : "Sin caso activo";
  el.traceCount.textContent = totalEvidence();
  const ragLabel = state.ragStats && state.ragStats.backend === "chroma" ? " · " + state.ragStats.chunks + " fragmentos" : "";
  el.storageStatus.textContent = (state.apiOnline ? "Datos activos" : "Modo local") + ragLabel;
  renderContext(active);
  renderWork();
}

function renderContext(record) {
  const title = document.querySelector(".context-head h2");
  title.textContent = record ? record.patientCode : "Sin caso seleccionado";
  if (!record) {
    el.contextBody.innerHTML = '<p class="muted">Crea un caso desde Ingesta o selecciona uno del vault.</p>';
    return;
  }
  el.contextBody.innerHTML = [
    metric("Area", record.domain),
    metric("Tipo", record.recordType),
    metric("Responsable", record.operator || "Sin responsable"),
    metric("Entidades", record.entities.length),
    metric("Evidencias", record.files.length),
    '<div class="card compact"><h3>Resumen operativo</h3><p>' + escapeHtml(record.notes.slice(0, 520)) + (record.notes.length > 520 ? "..." : "") + '</p></div>',
    '<div class="card compact"><h3>Estado</h3><span class="chip ok">Datos sensibles separados</span><span class="chip warn">Revision humana</span></div>'
  ].join("");
}

function renderWork() {
  const views = {
    intake: renderIntake,
    entities: renderEntities,
    graph: renderGraph,
    chat: renderChat,
    intelligence: renderIntelligence,
    query: renderQuery,
    pack: renderPack,
    connectors: renderConnectors,
    cases: renderCases,
    consent: renderConsent,
    storage: renderStorage
  };
  el.work.innerHTML = views[state.activeView]();
  bindViewEvents();
  primeHeroVideo();
}

function primeHeroVideo() {
  const video = document.querySelector(".hero-video");
  if (!video) return;
  video.muted = true;
  video.defaultMuted = true;
  video.playsInline = true;
  const playAttempt = video.play();
  if (playAttempt && typeof playAttempt.catch === "function") playAttempt.catch(function () {});
}

function bindViewEvents() {
  const form = document.querySelector("#caseForm");
  if (form) form.addEventListener("submit", saveCaseFromForm);
  const dictation = document.querySelector("#startDictation");
  if (dictation) dictation.addEventListener("click", startDictation);
  const sample = document.querySelector("#loadSample");
  if (sample) sample.addEventListener("click", loadSampleRecord);
  document.querySelectorAll("[data-jump-consent]").forEach((button) => {
    button.addEventListener("click", () => setView("consent"));
  });
  document.querySelectorAll("[data-set-view]").forEach((button) => {
    button.addEventListener("click", () => setView(button.dataset.setView));
  });
  document.querySelectorAll("[data-open-entity]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeEntityKey = button.dataset.openEntity;
      render();
      const detail = document.querySelector(".entity-detail:not(.empty)");
      if (detail) detail.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
  });
  document.querySelectorAll("[data-entity-search]").forEach((button) => {
    button.addEventListener("click", () => {
      el.search.value = button.dataset.entitySearch;
      setView("query", false);
    });
  });
  document.querySelectorAll("[data-entity-chat]").forEach((button) => {
    button.addEventListener("click", () => {
      const prompt = "Que conocimiento tengo conectado con " + button.dataset.entityChat + "?";
      setView("chat");
      requestAnimationFrame(() => {
        const input = document.querySelector("#knowledgeChatInput");
        if (input) {
          input.value = prompt;
          input.focus();
        }
      });
    });
  });
  document.querySelectorAll("[data-focus-notes]").forEach((button) => {
    button.addEventListener("click", () => {
      const notes = document.querySelector("#notes");
      if (notes) {
        notes.scrollIntoView({ behavior: "smooth", block: "center" });
        notes.focus();
      }
    });
  });
  document.querySelectorAll("[data-select-case]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeRecordId = button.dataset.selectCase;
      setView("entities");
    });
  });
  document.querySelectorAll("[data-map-node]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeGraphNodeId = button.dataset.mapNode || "root";
      render();
    });
  });
  document.querySelectorAll("[data-map-case]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeRecordId = button.dataset.mapCase;
      state.activeGraphNodeId = "case:" + button.dataset.mapCase;
      render();
    });
  });
  const consentInputs = document.querySelectorAll("[data-consent-input]");
  consentInputs.forEach((input) => input.addEventListener("input", updateConsentPreview));
  document.querySelectorAll("[data-download-consent]").forEach((button) => {
    button.addEventListener("click", downloadConsentDocument);
  });
  const chatForm = document.querySelector("#knowledgeChatForm");
  if (chatForm) chatForm.addEventListener("submit", submitKnowledgeChat);
  const exportPack = document.querySelector("#exportPack");
  if (exportPack) exportPack.addEventListener("click", downloadPackDocument);
  const exportKnowledge = document.querySelector("#exportKnowledgeBundle");
  if (exportKnowledge) exportKnowledge.addEventListener("click", downloadKnowledgeBundle);
  const copyEndpoint = document.querySelector("#copyConnectorEndpoint");
  if (copyEndpoint) copyEndpoint.addEventListener("click", copyConnectorEndpoint);
  document.querySelectorAll("[data-chat-prompt]").forEach((button) => {
    button.addEventListener("click", () => {
      const input = document.querySelector("#knowledgeChatInput");
      if (input) {
        input.value = button.dataset.chatPrompt;
        const form = document.querySelector("#knowledgeChatForm");
        if (form && form.requestSubmit) form.requestSubmit();
        else input.focus();
      }
    });
  });
  if (consentInputs.length) updateConsentPreview();
}

function renderIntake() {
  const rag = state.ragStats || { chunks: 0, sqliteChunks: 0, backend: "local" };
  const chunks = rag.chunks || rag.sqliteChunks || 0;
  const aiActive = Boolean(state.aiProvider && state.aiProvider.active);
  return '<section class="evidentia-home">' +
    '<article class="evidentia-hero">' +
    '<div class="hero-copy"><span class="eyebrow">Evidentia Local Node</span><h1 class="brand-word hero-brand-word">' + BRAND_WORD + '</h1><p class="hero-claim">Memoria privada.<br>Fuentes visibles.<br>Decision humana.</p><p class="hero-subclaim">Mirror consultable con trazabilidad para notas, fotos, audio, video, PDFs y criterio del equipo. No diagnostica: prepara decisiones revisables.</p>' +
    '<div class="hero-actions"><button class="primary" data-focus-notes type="button">Capturar conocimiento</button><button class="secondary" data-set-view="chat" type="button">Preguntar al mirror</button><button class="secondary" data-set-view="connectors" type="button">Conectar agentes</button><button class="secondary" data-download-consent type="button">Consentimiento</button></div></div>' +
    '<div class="hero-visual" aria-label="Evidentia en funcionamiento">' +
    '<video class="hero-video" autoplay muted loop playsinline disablepictureinpicture preload="metadata" poster="./assets/evidentia/evidentia-reference-hero-poster.jpg?v=' + HERO_VIDEO_VERSION + '"><source src="./assets/evidentia/evidentia-reference-hero.mp4?v=' + HERO_VIDEO_VERSION + '" type="video/mp4"></video>' +
    '<canvas class="cube-canvas hero-cube-canvas" width="300" height="220" aria-hidden="true"></canvas>' +
    '<div class="hero-video-brand"><strong class="brand-word">' + BRAND_WORD + '</strong><span>Knowledge OS</span></div>' +
    '<div class="hero-video-metrics"><span>' + state.records.length + ' registros</span><span>' + chunks + ' chunks</span><span>' + (aiActive ? "IA opt-in" : "Sin salida externa") + '</span></div>' +
    '</div></article>' +
    renderCommandDeck() +
    '<div class="value-strip">' +
    '<button class="value-card" data-focus-notes type="button"><strong>Registros</strong><span>Casos, proyectos, reuniones, clases y protocolos.</span></button>' +
    '<button class="value-card" data-set-view="pack" type="button"><strong>Archivos</strong><span>Audio, v&iacute;deo, fotos, PDF y notas.</span></button>' +
    '<button class="value-card" data-set-view="chat" type="button"><strong>Consulta</strong><span>Preguntas directas sobre lo guardado.</span></button>' +
    '</div>' +
    renderKnowledgeRoutingBand() +
    '<section class="video-memory-band" aria-label="Evidentia Video Memory">' +
    '<div><span class="eyebrow">Audio y v&iacute;deo</span><h2>Sube un archivo y preg&uacute;ntale despu&eacute;s.</h2><p>Notas de voz, clases, reuniones y v&iacute;deos propios.</p></div>' +
    '<ol><li>Subir</li><li>Guardar</li><li>Consultar</li><li>Revisar fuente</li></ol>' +
    '</section>' +
    '<section class="work-grid">' +
    '<article class="card intake-card">' +
    '<div class="section-head"><div><span class="eyebrow">Nuevo registro</span><h1>Guardar</h1></div><button class="secondary" id="startDictation" type="button">Dictar</button></div>' +
    '<form id="caseForm">' +
    '<div class="field-row"><label>Area libre<select id="domain"><option>Conocimiento general del centro</option><option>Operacion / procesos</option><option>Equipo / formacion</option><option>Docencia / investigacion</option><option>Odontologia general</option><option>Ortodoncia</option><option>Estetica y rehabilitacion</option><option>Implantes</option><option>Periodoncia</option><option>Laboratorio</option><option>Otro conocimiento</option></select></label><label>Tipo de entrada<select id="recordType"><option>Registro de conocimiento</option><option>Transcripcion</option><option>Articulo de conocimiento</option><option>Caso de exito</option><option>Caso de no exito</option><option>Archivo de conocimiento</option><option>Nota de conocimiento</option><option>Protocolo</option><option>Seguimiento</option><option>Idea o aprendizaje</option></select></label></div>' +
    '<div class="field-row"><label>Persona, caso, proyecto o referencia<input id="patient" autocomplete="off" placeholder="Iniciales, numero de caso, proyecto o referencia interna"></label><label>Responsable<input id="operator" autocomplete="off" placeholder="Profesional, tecnico, responsable, direccion o equipo"></label></div>' +
    '<label>Nota<textarea id="notes" rows="11" placeholder="Escribe o pega aqui el contenido importante."></textarea></label>' +
    '<div class="field-row"><label>Archivos<input id="files" type="file" multiple accept="image/*,video/*,audio/*,.pdf,.txt,.md,.csv,.json,.html,.xml"><small class="field-hint">Audio y video quedan listos para consulta al guardar.</small></label><label>Fecha<input id="captureDate" type="date" value="' + new Date().toISOString().slice(0, 10) + '"></label></div>' +
    '<div class="actions"><button class="primary" type="submit">Guardar</button><button class="secondary" id="loadSample" type="button">Usar plantilla</button><button class="secondary" data-set-view="cases" type="button">Ver registros</button></div>' +
    '</form></article>' +
    '<article class="card pipeline-card"><canvas class="cube-canvas pipeline-cube-canvas" width="330" height="300" aria-hidden="true"></canvas>' +
    renderPipelineSteps("intake") +
    '<div class="trust-stack"><span>Guardado</span><span>Consultable</span><span>Revisable</span></div></article>' +
    '</section></section>';
}

function renderCommandDeck() {
  const rag = state.ragStats || { chunks: 0, sqliteChunks: 0, backend: "local" };
  const chunks = rag.chunks || rag.sqliteChunks || 0;
  const aiActive = Boolean(state.aiProvider && state.aiProvider.active);
  const provider = aiActive && state.aiProvider.provider ? state.aiProvider.provider : "apagada";
  return '<section class="command-deck" aria-label="Panel operativo Evidentia">' +
    '<div class="command-copy">' +
    '<span class="eyebrow">Command deck</span>' +
    '<h2>El estado del mirror debe verse antes de tocar nada.</h2>' +
    '<p>Esta es la capa de control: que hay dentro, que fuente se recupera, que sale del nodo y donde debe intervenir una persona.</p>' +
    '</div>' +
    '<div class="command-grid">' +
    commandTile("Nodo", state.apiOnline ? "SQLite activo" : "Demo local", state.apiOnline ? "Datos persistidos en servidor local." : "Fallback de navegador, util solo para demo.", state.apiOnline ? "ok" : "warn", "storage") +
    commandTile("RAG", chunks + " chunks", chunks ? "Fuentes recuperables para preguntas." : "Faltan registros para memoria real.", chunks ? "ok" : "warn", "graph") +
    commandTile("Modo verificable", aiActive ? provider : "sin salida externa", aiActive ? "Proveedor conectado por opt-in." : "Busqueda local con fuentes, sin enviar datos fuera del nodo.", aiActive ? "warn" : "ok", "chat") +
    commandTile("Gate humano", "obligatorio", "Build, adjust o stop antes de prometer valor.", "warn", "pack") +
    '</div>' +
    '</section>';
}

function commandTile(label, valueText, detail, tone, view) {
  return '<button class="command-tile ' + escapeHtml(tone) + '" data-set-view="' + escapeHtml(view) + '" type="button">' +
    '<span>' + escapeHtml(label) + '</span>' +
    '<strong>' + escapeHtml(String(valueText)) + '</strong>' +
    '<small>' + escapeHtml(detail) + '</small>' +
    '</button>';
}

function renderKnowledgeRoutingBand() {
  const rag = state.ragStats || { chunks: 0, sqliteChunks: 0 };
  const chunks = rag.chunks || rag.sqliteChunks || 0;
  const recordCount = rag.records || state.records.length;
  return '<section class="knowledge-routing-band" aria-label="Conexion del conocimiento RAG">' +
    '<div class="routing-copy"><span class="eyebrow">RAG conectado</span><h2>El conocimiento no se queda en un chat: alimenta agentes, projects y decisiones.</h2><p>Evidentia convierte registros, pacientes, casos clinicos y datos en un bundle trazable. Ese bundle se entrega a agentes autorizados, Claude/ChatGPT Projects o automatizaciones internas con fuentes y permiso.</p></div>' +
    '<div class="routing-flow">' +
    routingNode("01", "Conocimiento", recordCount + " registros", "Notas, protocolos, decisiones y contexto del equipo.") +
    routingNode("02", "Vector RAG", chunks + " fragmentos", "Busqueda semantica local con fuentes recuperables.") +
    routingNode("03", "Agentes", "Pedro / Faki / Yolito", "Roles que consultan sin inventar y citan origen.") +
    routingNode("04", "Projects", "Claude / ChatGPT", "Memoria exportable para trabajo por proyecto.") +
    routingNode("05", "Control", "Consentimiento", "Permisos, limites y revision humana antes de uso externo.") +
    '</div>' +
    '<div class="actions"><button class="primary" data-set-view="connectors" type="button">Configurar conexion</button><button class="secondary" data-set-view="graph" type="button">Ver mapa RAG</button><button class="secondary" data-download-consent type="button">Descargar consentimiento</button></div>' +
    '</section>';
}

function routingNode(step, title, valueText, detail) {
  return '<article class="routing-node"><span>' + escapeHtml(step) + '</span><strong>' + escapeHtml(title) + '</strong><em>' + escapeHtml(valueText) + '</em><small>' + escapeHtml(detail) + '</small></article>';
}

function renderEntities() {
  const record = activeRecord();
  if (!record) return emptyPipeline("Selecciona un caso para ver entidades.");
  const entities = knowledgeEntities(record);
  const activeEntity = activeEntityFor(record);
  return '<section class="card"><div class="section-head"><div><span class="eyebrow">Extra&iacute;do</span><h1>Entidades</h1></div><span class="score">' + entities.length + ' entidades · ' + (record.files || []).length + ' archivos</span></div>' +
    '<div class="entity-grid">' + (entities.length ? entities.map((entity) => renderEntityCard(entity)).join("") : '<article class="empty-state"><strong>Sin entidades todav&iacute;a</strong><p>A&ntilde;ade una nota o archivo.</p></article>') + '</div>' +
    renderEntityPanel(record, activeEntity) +
    renderEvidencePanel(record) +
    '</section>';
}

function renderEntityCard(entity) {
  const key = entityKey(entity);
  const active = state.activeEntityKey === key;
  return '<button class="entity-card' + (active ? " active" : "") + '" data-open-entity="' + escapeHtml(key) + '" type="button" aria-pressed="' + (active ? "true" : "false") + '">' +
    '<span class="type">' + escapeHtml(entity.type) + '</span><strong>' + escapeHtml(entity.label) + '</strong><small>confianza ' + Math.round((entity.confidence || 0.7) * 100) + '%</small></button>';
}

function activeEntityFor(record) {
  const entities = knowledgeEntities(record);
  if (!entities.length) return null;
  return entities.find((entity) => entityKey(entity) === state.activeEntityKey) || null;
}

function knowledgeEntities(record) {
  return (record.entities || []).filter((entity) => !["asset", "evidence"].includes(entity.type));
}

function entityKey(entity) {
  return normalizeText(entity.type + "::" + entity.label).replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

function renderEntityPanel(record, entity) {
  if (!entity) {
    return '<article class="entity-detail empty"><strong>Toca una entidad para abrirla.</strong><p>Veras su relacion con el caso, evidencias asociadas y accesos directos al mapa, chat, busqueda o pack.</p></article>';
  }
  const files = filesForEntity(record, entity);
  const fileHtml = files.length
    ? files.map((file) => '<li><strong>' + escapeHtml(file.name || "Archivo") + '</strong><span>' + escapeHtml(file.type || "tipo no indicado") + ' · ' + formatBytes(file.size || 0) + '</span></li>').join("")
    : '<li><strong>Sin archivo directo</strong><span>A&ntilde;ade evidencia si hace falta.</span></li>';
  const relation = relationFor(entity.type);
  return '<article class="entity-detail">' +
    '<div><span class="eyebrow">Entidad abierta</span><h2>' + escapeHtml(entity.label) + '</h2><p>' + escapeHtml(record.patientCode) + ' -- ' + escapeHtml(relation) + ' -- ' + escapeHtml(entity.label) + '</p></div>' +
    '<ul class="entity-files">' + fileHtml + '</ul>' +
    '<div class="actions">' +
    '<button class="secondary" data-set-view="graph" type="button">Ver en mapa</button>' +
    '<button class="secondary" data-entity-search="' + escapeHtml(entity.label) + '" type="button">Buscar similares</button>' +
    '<button class="secondary" data-entity-chat="' + escapeHtml(entity.label) + '" type="button">Preguntar</button>' +
    '<button class="secondary" data-set-view="' + (files.length ? "pack" : "intake") + '" type="button">' + (files.length ? "Abrir pack" : "Anadir evidencia") + '</button>' +
    '</div></article>';
}

function filesForEntity(record, entity) {
  const label = normalizeText(entity.label);
  const type = normalizeText(entity.type);
  return (record.files || []).filter((file) => {
    const name = normalizeText(file.name || "");
    const mime = normalizeText(file.type || "");
    if (type === "evidence") return true;
    if (label.includes("foto")) return mime.includes("image") || /foto|image|jpg|jpeg|png|webp/.test(name);
    if (label.includes("video")) return mime.includes("video") || /video|mp4|mov|webm/.test(name);
    if (label.includes("pdf") || label.includes("documento")) return mime.includes("pdf") || /pdf|doc|documento|informe/.test(name);
    if (label.includes("3d") || label.includes("escaneo")) return /stl|obj|ply|dicom|dcm|scan|escaneo|intraoral/.test(name + " " + mime);
    return name.includes(label);
  });
}

function evidenceKind(file) {
  const name = normalizeText(file.name || "");
  const mime = normalizeText(file.type || "");
  if (mime.includes("image") || /jpg|jpeg|png|webp|tif|foto|imagen/.test(name)) return "Fotografia / imagen";
  if (mime.includes("video") || /mp4|mov|webm|video/.test(name)) return "Video";
  if (mime.includes("pdf") || /pdf/.test(name)) return "PDF / documento";
  if (/stl|obj|ply|dicom|dcm|scan|escaneo|intraoral/.test(name + " " + mime)) return "3D / escaneo";
  return "Archivo asociado";
}

function renderEvidencePanel(record) {
  const files = record.files || [];
  const rows = files.length
    ? files.map((file) => '<li><strong>' + escapeHtml(evidenceKind(file)) + '</strong><span>' + escapeHtml(file.name || "Archivo") + ' · ' + escapeHtml(file.type || "tipo no indicado") + ' · ' + formatBytes(file.size || 0) + '</span></li>').join("")
    : '<li><strong>Sin evidencias adjuntas</strong><span>Fotos, videos, JPG, PDF, STL y otros archivos se muestran aqui, separados de las entidades clinicas.</span></li>';
  return '<article class="entity-detail"><div><span class="eyebrow">Archivos</span><h2>Material asociado</h2></div><ul class="entity-files">' + rows + '</ul></article>';
}

function renderGraph() {
  const map = buildKnowledgeMap();
  const selected = map.nodes.find((node) => node.id === state.activeGraphNodeId) || map.nodes[0];
  const fileCount = map.nodes.filter((node) => node.kind === "file").length;
  const edgeHtml = map.edges.map((edge) => {
    const from = map.nodeById[edge.from];
    const to = map.nodeById[edge.to];
    if (!from || !to) return "";
    const active = selected && (selected.id === from.id || selected.id === to.id);
    return '<line class="' + (active ? "active" : "") + '" x1="' + from.x + '%" y1="' + from.y + '%" x2="' + to.x + '%" y2="' + to.y + '%"></line>';
  }).join("");
  const nodeHtml = map.nodes.map((node) => {
    const selectedClass = selected && selected.id === node.id ? " selected" : "";
    return '<button class="map-node map-node-' + escapeHtml(node.kind) + selectedClass + '" data-map-node="' + escapeHtml(node.id) + '" type="button" style="--x:' + node.x + '%;--y:' + node.y + '%;--s:' + node.size + 'px" aria-pressed="' + (selectedClass ? "true" : "false") + '">' +
      '<span></span><strong>' + escapeHtml(node.label) + '</strong><small>' + escapeHtml(node.meta) + '</small></button>';
  }).join("");
  return '<section class="card knowledge-map-shell"><div class="section-head"><div><span class="eyebrow">Mapa de archivos</span><h1>Tu conocimiento visible</h1><p class="lead">Vista tipo mapa: archivos, casos, notas y entidades conectados para entender donde vive cada fuente.</p></div><span class="score">' + fileCount + ' archivos · ' + map.edges.length + ' enlaces</span></div>' +
    '<div class="knowledge-map-layout">' +
    '<aside class="knowledge-map-sidebar"><div><span class="eyebrow">Vault</span><h3>Fuentes</h3></div>' + renderMapFileTree(map) + '</aside>' +
    '<div class="knowledge-map-stage" aria-label="Mapa visual de archivos Evidentia"><svg class="knowledge-map-links" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">' + edgeHtml + '</svg>' + nodeHtml + '</div>' +
    '<aside class="knowledge-map-detail">' + renderMapDetail(selected) + '</aside>' +
    '</div>' +
    '<div class="map-toolbar"><button class="secondary" data-map-node="root" type="button">Centrar mapa</button><button class="secondary" data-set-view="intake" type="button">Subir archivos</button><button class="secondary" data-set-view="chat" type="button">Preguntar al mirror</button></div>' +
    '</section>';
}

function graphDisplayNodes(record) {
  return (record.graph || []).slice(1).filter((node) => {
    if (node.type === "asset") return false;
    if (node.type === "evidence" && normalizeText(node.label || "") === "evidencia asociada") return false;
    return true;
  });
}

function buildKnowledgeMap() {
  const records = state.records || [];
  const active = activeRecord();
  const orderedRecords = active ? [active].concat(records.filter((record) => record.id !== active.id)) : records.slice();
  const nodes = [{
    id: "root",
    kind: "root",
    label: "Evidentia",
    meta: "mirror local",
    detail: "Centro del mapa. Desde aqui se conectan casos, archivos, notas, entidades y conocimiento recuperable.",
    x: 50,
    y: 50,
    size: 58
  }];
  const edges = [];
  const clusterNodes = [
    { id: "cluster:files", kind: "cluster", label: "Archivos", meta: "evidencias", detail: "Fotos, videos, PDFs, audios y documentos guardados.", x: 24, y: 22, size: 44 },
    { id: "cluster:cases", kind: "cluster", label: "Casos", meta: "expedientes", detail: "Registros clinicos o de proyecto que agrupan fuentes.", x: 77, y: 28, size: 46 },
    { id: "cluster:notes", kind: "cluster", label: "Notas", meta: "criterio", detail: "Observaciones, decisiones y aprendizaje humano.", x: 29, y: 78, size: 40 },
    { id: "cluster:entities", kind: "cluster", label: "Entidades", meta: "conceptos", detail: "Temas detectados en notas y archivos.", x: 76, y: 74, size: 40 }
  ];
  clusterNodes.forEach((node) => {
    nodes.push(node);
    edges.push({ from: "root", to: node.id });
  });

  const recordsToShow = orderedRecords.slice(0, 9);
  recordsToShow.forEach((record, index) => {
    const point = mapPoint(index, Math.max(recordsToShow.length, 1), 33, 21, -0.35);
    const caseId = "case:" + record.id;
    nodes.push({
      id: caseId,
      kind: "case",
      label: record.patientCode || "Caso",
      meta: (record.files || []).length + " archivos",
      detail: record.notes || record.recordType || "Registro sin resumen.",
      recordId: record.id,
      x: point.x,
      y: point.y,
      size: active && active.id === record.id ? 50 : 38
    });
    edges.push({ from: "cluster:cases", to: caseId });

    const fileLimit = active && active.id === record.id ? 12 : 4;
    (record.files || []).slice(0, fileLimit).forEach((file, fileIndex) => {
      const filePoint = mapPoint(index * fileLimit + fileIndex, Math.max(recordsToShow.length * fileLimit, 8), 42, 31, 0.25);
      const fileId = "file:" + record.id + ":" + fileIndex;
      nodes.push({
        id: fileId,
        kind: "file",
        label: file.name || "Archivo",
        meta: evidenceKind(file),
        detail: (file.type || "tipo no indicado") + " · " + formatBytes(file.size || 0),
        recordId: record.id,
        x: filePoint.x,
        y: filePoint.y,
        size: fileNodeSize(file)
      });
      edges.push({ from: caseId, to: fileId });
      edges.push({ from: "cluster:files", to: fileId });
    });

    knowledgeEntities(record).slice(0, 3).forEach((entity, entityIndex) => {
      const entityPoint = mapPoint(index * 3 + entityIndex, Math.max(recordsToShow.length * 3, 6), 28, 34, 1.65);
      const entityId = "entity:" + record.id + ":" + entityKey(entity);
      if (nodes.some((node) => node.id === entityId)) return;
      nodes.push({
        id: entityId,
        kind: "entity",
        label: entity.label,
        meta: entity.type,
        detail: "Concepto conectado con " + (record.patientCode || "el caso") + ".",
        recordId: record.id,
        x: entityPoint.x,
        y: entityPoint.y,
        size: 30
      });
      edges.push({ from: caseId, to: entityId });
      edges.push({ from: "cluster:entities", to: entityId });
    });
  });

  if (!records.length) {
    [
      { id: "demo:pdf", kind: "file", label: "PDF clinico", meta: "documento", detail: "Cuando subas un PDF aparecera como nodo conectado.", x: 19, y: 42, size: 34 },
      { id: "demo:video", kind: "file", label: "Video caso", meta: "video", detail: "Los videos se conectan al caso y al chat recuperable.", x: 43, y: 22, size: 38 },
      { id: "demo:audio", kind: "file", label: "Nota de voz", meta: "audio", detail: "Las notas de voz se transcriben y quedan consultables.", x: 62, y: 80, size: 32 }
    ].forEach((node) => {
      nodes.push(node);
      edges.push({ from: "cluster:files", to: node.id });
      edges.push({ from: "root", to: node.id });
    });
  }

  const nodeById = Object.fromEntries(nodes.map((node) => [node.id, node]));
  return { nodes, edges, nodeById, records: recordsToShow };
}

function mapPoint(index, total, rx, ry, offset) {
  const angle = offset + (Math.PI * 2 * index) / Math.max(total, 1);
  return {
    x: Math.round((50 + Math.cos(angle) * rx) * 10) / 10,
    y: Math.round((50 + Math.sin(angle) * ry) * 10) / 10
  };
}

function fileNodeSize(file) {
  const kind = evidenceKind(file).toLowerCase();
  if (kind.includes("video")) return 42;
  if (kind.includes("imagen")) return 38;
  if (kind.includes("pdf")) return 36;
  return 32;
}

function renderMapFileTree(map) {
  const records = map.records || [];
  if (!records.length) {
    return '<div class="map-empty"><strong>Aun no hay vault real</strong><p>Sube PDF, fotos, audio o video y el mapa se llenara automaticamente.</p></div>';
  }
  return '<div class="map-file-tree">' + records.map((record) => {
    const files = record.files || [];
    const fileRows = files.length
      ? files.slice(0, 8).map((file, index) => '<button data-map-node="file:' + escapeHtml(record.id) + ':' + index + '" type="button"><strong>' + escapeHtml(file.name || "Archivo") + '</strong><span>' + escapeHtml(evidenceKind(file)) + ' · ' + formatBytes(file.size || 0) + '</span></button>').join("")
      : '<p>Sin archivos adjuntos.</p>';
    return '<article><button class="map-tree-case" data-map-case="' + escapeHtml(record.id) + '" type="button"><strong>' + escapeHtml(record.patientCode || "Caso") + '</strong><span>' + files.length + ' fuentes</span></button>' + fileRows + '</article>';
  }).join("") + '</div>';
}

function renderMapDetail(node) {
  if (!node) return "";
  const record = node.recordId ? state.records.find((item) => item.id === node.recordId) : null;
  const action = record
    ? '<button class="secondary" data-map-case="' + escapeHtml(record.id) + '" type="button">Abrir caso</button>'
    : '<button class="secondary" data-set-view="intake" type="button">Capturar fuente</button>';
  return '<span class="eyebrow">Nodo seleccionado</span><h3>' + escapeHtml(node.label) + '</h3><p>' + escapeHtml(node.detail || node.meta || "") + '</p>' +
    '<dl><div><dt>Tipo</dt><dd>' + escapeHtml(node.kind) + '</dd></div><div><dt>Relacion</dt><dd>' + escapeHtml(node.meta || "conectado") + '</dd></div></dl>' +
    '<div class="actions">' + action + '<button class="secondary" data-set-view="chat" type="button">Preguntar</button></div>';
}

function renderQuery() {
  const query = el.search.value.trim().toLowerCase();
  const matches = query ? state.records.filter((record) => recordHaystack(record).includes(query)) : state.records.slice(0, 8);
  return '<section class="card"><div class="section-head"><div><span class="eyebrow">Buscar</span><h1>Resultados</h1></div><span class="score">' + matches.length + ' resultados</span></div>' +
    '<div class="result-list">' + (matches.length ? matches.map(resultCard).join("") : '<div class="empty-state"><strong>Sin coincidencias claras</strong><p>Prueba con palabras usadas al guardar el caso o registra nuevo conocimiento.</p><button class="secondary" data-set-view="intake" type="button">Guardar conocimiento</button></div>') + '</div></section>';
}

function renderChat() {
  const localPanel = renderLocalFirstPanel();
  return '<section class="card chat-shell">' +
    '<div class="section-head"><div><span class="eyebrow">Chat</span><h1>Pregunta</h1></div><span class="score">' + state.records.length + ' registros</span></div>' +
    '<div class="chat-layout">' +
    '<div class="chat-thread" id="knowledgeChatThread">' + state.chatMessages.map(chatBubble).join("") + '</div>' +
    '<aside class="chat-prompts">' + localPanel + '<h3>Preguntas utiles</h3>' +
    chatPrompt("Que casos tuvieron buen resultado?") +
    chatPrompt("Que fracasos o problemas he registrado?") +
    chatPrompt("Que protocolos o procesos he usado?") +
    chatPrompt("Que casos se parecen a este?") +
    chatPrompt("Que conocimiento tengo sobre este tema?") +
    '</aside></div>' +
    '<form class="chat-form" id="knowledgeChatForm">' +
    '<input id="knowledgeChatInput" autocomplete="off" placeholder="Ej: que casos, proyectos o aprendizajes parecidos tengo guardados?">' +
    '<button class="primary" type="submit">Preguntar</button>' +
    '</form></section>';
}

function renderLocalFirstPanel() {
  const aiActive = Boolean(state.aiProvider && state.aiProvider.active);
  const provider = state.aiProvider && state.aiProvider.provider ? state.aiProvider.provider : "sin proveedor externo";
  const rag = state.ragStats || { chunks: 0, sqliteChunks: 0 };
  const chunks = rag.chunks || rag.sqliteChunks || 0;
  const sourceProof = chunks ? chunks + ' fragmentos citables' : 'pendiente de indexar';
  return '<div class="local-first-panel" aria-label="Control local">' +
    '<span class="eyebrow">Prueba local-first</span>' +
    '<strong>' + (aiActive ? "IA externa opt-in: verificar permiso" : "Sin salida externa activa") + '</strong>' +
    '<ul>' +
    '<li><span>Datos</span><b>' + (state.apiOnline ? "SQLite local" : "Navegador local") + '</b></li>' +
    '<li><span>Fuentes</span><b>' + sourceProof + '</b></li>' +
    '<li><span>Salida externa</span><b>' + escapeHtml(aiActive ? provider : "ninguna") + '</b></li>' +
    '<li><span>Decision</span><b>humana, no clinica automatica</b></li>' +
    '</ul>' +
    '<p>Modo de demo recomendado: mostrar respuesta, abrir fuentes y descargar bundle. Si no hay evidencia suficiente, no se vende como respuesta clinica.</p>' +
    '<div class="local-proof-actions"><button class="secondary" id="exportKnowledgeBundle" type="button">Descargar prueba JSON</button><button class="secondary" data-set-view="connectors" type="button">Ver trazabilidad</button></div>' +
    '</div>';
}

function renderIntelligence() {
  const intel = intelligenceSnapshot();
  const contradictionHtml = intel.contradictions.length
    ? intel.contradictions.map((item) => '<span class="chip warn">' + escapeHtml(item) + '</span>').join("")
    : '<span class="chip ok">Sin contradicciones criticas detectadas todavia</span>';
  const expertHtml = intel.experts.length
    ? intel.experts.map((expert) => '<article class="case-card"><button type="button"><strong>' + escapeHtml(expert.name) + '</strong><span>Memoria de experto · ' + expert.records + ' registros</span><p>' + escapeHtml(expert.summary) + '</p><small>' + expert.files + ' fuentes · ' + expert.domains + ' areas</small></button></article>').join("")
    : '<div class="empty-state"><strong>Sin datos suficientes</strong><p>A&ntilde;ade m&aacute;s registros.</p></div>';
  const similarHtml = intel.similar.length
    ? intel.similar.map((item) => '<span class="chip ok">' + escapeHtml(item) + '</span>').join("")
    : '<span class="chip warn">Aun faltan registros comparables para similitud fuerte</span>';

  return '<section class="card"><div class="section-head"><div><span class="eyebrow">Intel</span><h1>Se&ntilde;ales</h1></div><span class="score">' + intel.confidence + '</span></div>' +
    '<div class="intel-grid">' +
    intelligenceBox("Tiempo recuperado", intel.hoursSaved + " h/mes", "Estimacion por revisar pacientes, proyectos y buscar patrones") +
    intelligenceBox("Busquedas evitadas", intel.searchesAvoided, "Consultas recuperables desde casos, archivos y mapa") +
    intelligenceBox("Casos similares", intel.similarCount, "Coincidencias por area y entidades") +
    intelligenceBox("Conocimiento disperso", intel.riskLevel, intel.riskReason) +
    '</div>' +
    '<div class="work-grid intelligence-work">' +
    '<article class="card compact"><h3>Expertos</h3><div class="case-list">' + expertHtml + '</div></article>' +
    '<article class="card compact"><h3>Contradicciones</h3><div class="actions">' + contradictionHtml + '</div><h3>Casos conectados</h3><div class="actions">' + similarHtml + '</div></article>' +
    '</div>' +
    '<div class="value-strip intelligence-strip"><article><strong>Expertos</strong><span>Criterio por persona.</span></article><article><strong>Formaci&oacute;n</strong><span>Tests y casos.</span></article><article><strong>Patrones</strong><span>Repeticiones detectadas.</span></article></div>' +
    '</section>';
}

function intelligenceBox(label, valueText, detail) {
  return '<div><span>' + escapeHtml(label) + '</span><strong>' + escapeHtml(String(valueText)) + '</strong><small>' + escapeHtml(detail) + '</small></div>';
}

function renderPack() {
  const record = activeRecord();
  if (!record) return emptyPipeline("Selecciona un caso para generar pack.");
  const missing = [];
  if (!record.files.length) missing.push("Adjuntar evidencia visual/documental");
  if (!record.files.length) missing.push("Adjuntar fotos, videos, PDF o documentos del caso");
  if (!record.entities.some((e) => e.type === "knowledge")) missing.push("Añadir criterio, decision o aprendizaje del equipo");
  if (!record.entities.some((e) => e.type === "outcome")) missing.push("Registrar evolucion, resultado o seguimiento si existe");
  return '<section class="card"><div class="section-head"><div><span class="eyebrow">Evidence-to-Outcome Pack</span><h1>Paquete operativo del caso</h1></div><button class="primary" id="exportPack" type="button">Exportar pack</button></div>' +
    '<div class="pack-grid">' + 
    metric("Caso", record.patientCode) + metric("Completitud", Math.max(20, 100 - missing.length * 22) + "%") + metric("Fuentes", record.files.length) + metric("Relaciones", record.graph.length) +
    '</div><div class="card compact"><h3>Siguiente acci&oacute;n</h3><p>' + (missing[0] || "Listo para consulta y revisi&oacute;n.") + '</p></div>' +
    '<div class="card compact"><h3>Faltantes</h3>' + (missing.length ? missing.map((item) => '<span class="chip warn">' + escapeHtml(item) + '</span>').join("") : '<span class="chip ok">Sin faltantes criticos</span>') + '</div></section>';
}

function renderConnectors() {
  const rag = state.ragStats || { chunks: 0, sqliteChunks: 0, backend: "local" };
  const endpoint = location.origin + "/api/connectors/export";
  const connectorCount = state.records.length ? "Listo" : "Sin datos";
  return '<section class="card connectors-shell">' +
    '<div class="section-head"><div><span class="eyebrow">Conectores de conocimiento</span><h1>RAG hacia agentes y Projects</h1><p class="lead">El mapa vectorial de Evidentia se exporta como conocimiento gobernado: registros, fuentes, chunks, permisos y trazabilidad para agentes, Claude Projects, ChatGPT Projects o automatizaciones internas.</p></div><span class="score">' + connectorCount + '</span></div>' +
    '<div class="connector-bridge" aria-label="Flujo de conexion">' +
    '<span>Registros</span><i></i><span>Chunks RAG</span><i></i><span>Knowledge bundle</span><i></i><span>Agentes</span><i></i><span>Projects</span><i></i><span>Revision humana</span>' +
    '</div>' +
    '<div class="pack-grid connector-metrics">' +
    metric("Registros", String(state.records.length)) +
    metric("Fragmentos RAG", String(rag.chunks || rag.sqliteChunks || 0)) +
    metric("Destino v1", "Agente / proyecto") +
    metric("Formato", "JSON trazable") +
    '</div>' +
    '<div class="connector-grid">' +
    connectorCard("Paquete para agente", "Descarga un JSON con registros, fuentes, entidades, chunks y reglas para que Pedro, Faki, Yolito u otro agente trabajen con memoria verificable.", '<button class="primary" id="exportKnowledgeBundle" type="button">Descargar knowledge bundle</button>') +
    connectorCard("Claude / ChatGPT Projects", "Carga el bundle en un Project para que el contexto no sea una conversacion suelta: queda organizado por fuentes, casos y limites.", '<button class="secondary" id="copyConnectorEndpoint" type="button">Copiar endpoint local</button><code id="connectorEndpoint">' + escapeHtml(endpoint) + '</code>') +
    connectorCard("Gobierno de datos", "Antes de conectar datos sensibles: definir destino, responsable, base juridica, consentimiento, minimizacion y si hay transferencia externa.", '<button class="secondary" data-set-view="consent" type="button">Preparar consentimiento</button><span class="chip warn">No enviar fuera sin permiso</span>') +
    '</div>' +
    '<article class="entity-detail connector-plan"><div><span class="eyebrow">Plan de conexion</span><h2>Evolucion del conector</h2></div>' +
    '<ul class="entity-files">' +
    '<li><strong>v1 local</strong><span>Export JSON y endpoint local para agente/proyecto controlado por el cliente.</span></li>' +
    '<li><strong>v2 permisos</strong><span>API keys, responsable por conexion, logs de acceso, consentimiento y alcance por workspace.</span></li>' +
    '<li><strong>v3 orquestacion</strong><span>Pedro revisa construccion, Faki web/conversion, Yolito conocimiento dental y otros agentes consumen solo lo autorizado.</span></li>' +
    '<li><strong>v4 marketplace</strong><span>Conectores certificados para ChatGPT Projects, Claude Projects, Make, n8n, Notion, Drive y CRMs.</span></li>' +
    '</ul></article>' +
    '</section>';
}

function connectorCard(title, text, actionHtml) {
  return '<article class="connector-card"><h3>' + escapeHtml(title) + '</h3><p>' + escapeHtml(text) + '</p><div class="actions">' + actionHtml + '</div></article>';
}

function renderCases() {
  const groups = groupedCases();
  return '<section class="card"><div class="section-head"><div><span class="eyebrow">Vault</span><h1>Casos estructurados</h1><p class="lead">Cada caso agrupa sus entradas. Yolito, notas, fotos y PDFs se guardan dentro del conocimiento; no como paginas nuevas.</p></div><span class="score">' + groups.length + ' casos · ' + state.records.length + ' entradas</span></div>' +
    '<div class="case-list">' + (groups.length ? groups.map(caseGroupCard).join("") : '<p class="muted">Todavia no hay conocimiento guardado.</p>') + '</div></section>';
}

function groupedCases() {
  const groups = new Map();
  state.records.forEach((record) => {
    const key = record.patientCode || "KNOWLEDGE-BASE";
    if (!groups.has(key)) groups.set(key, { key, records: [], files: 0, entities: 0, latestAt: "" });
    const group = groups.get(key);
    group.records.push(record);
    group.files += (record.files || []).length;
    group.entities += knowledgeEntities(record).length;
    if (!group.latestAt || String(record.createdAt || "") > group.latestAt) group.latestAt = String(record.createdAt || "");
  });
  return Array.from(groups.values()).map((group) => {
    group.records.sort((a, b) => String(b.createdAt || "").localeCompare(String(a.createdAt || "")));
    group.latest = group.records[0];
    return group;
  }).sort((a, b) => String(b.latestAt || "").localeCompare(String(a.latestAt || "")));
}

function caseGroupCard(group) {
  const latest = group.latest;
  const label = group.key === "KNOWLEDGE-BASE" ? "Base de conocimiento" : group.key;
  const recent = group.records.slice(0, 3).map((record) => escapeHtml(record.recordType) + " · " + escapeHtml(record.domain)).join(" / ");
  return '<article class="case-card"><button data-select-case="' + escapeHtml(latest.id) + '" type="button">' +
    '<strong>' + escapeHtml(label) + '</strong>' +
    '<span>' + group.records.length + ' entradas guardadas · ultima: ' + escapeHtml(latest.recordType) + '</span>' +
    '<p>' + escapeHtml(latest.notes.slice(0, 220)) + (latest.notes.length > 220 ? "..." : "") + '</p>' +
    '<small>' + group.entities + ' entidades · ' + group.files + ' evidencias · ' + recent + '</small>' +
    '</button></article>';
}

function renderConsent() {
  return '<section class="card consent-hero"><div class="section-head"><div><span class="eyebrow">Proteccion de datos</span><h1>Consentimiento del paciente</h1><p class="lead">Plantilla para autorizar tratamiento de datos, imagen, audio, video, RAG y agentes. En produccion debe revisarla el asesor RGPD del centro.</p></div><button class="primary" data-download-consent type="button">Descargar consentimiento</button></div>' +
    '<div class="consent-status-panel"><strong>Estado recomendado:</strong><span class="chip warn">No tratar datos sanitarios identificables sin base juridica y documento firmado</span><span class="chip ok">Incluye imagen, audio, video, PDF, transcripcion, RAG y agentes</span><span class="chip warn">IA externa solo con autorizacion expresa</span></div>' +
    '<div class="consent-layout"><div class="consent-form">' +
    consentInput("Centro responsable del tratamiento", "consentClinic", "Nombre fiscal/comercial del centro") +
    consentInput("Responsable / delegado o contacto RGPD", "consentDoctor", "Profesional, direccion, email o contacto") +
    consentInput("Persona interesada", "consentPatient", "Nombre y apellidos si aplica") +
    consentInput("DNI / identificador", "consentPatientId", "Documento o ID interno") +
    consentInput("Caso, proyecto o area", "consentCase", "Ej: caso, proyecto, area, proceso o expediente") +
    '<label>Fecha<input data-consent-input id="consentDate" type="date" value="' + new Date().toISOString().slice(0, 10) + '"></label>' +
    '<label>Finalidad<textarea data-consent-input id="consentPurpose" rows="5">Documentar el caso, ordenar archivos clinicos y administrativos, transcribir audio/video autorizado, indexar el contenido en una base vectorial privada y permitir consultas RAG con fuentes para apoyar la revision humana del equipo profesional.</textarea></label>' +
    '<label class="checkbox-line"><input data-consent-input id="consentSensitiveHealth" type="checkbox" checked> Autoriza el tratamiento de datos de salud, imagen intra/extraoral, documentos y archivos necesarios para el caso.</label>' +
    '<label class="checkbox-line"><input data-consent-input id="consentAgentsProjects" type="checkbox"> Autoriza conectar el conocimiento seudonimizado a agentes o Projects internos del centro bajo control del responsable.</label>' +
    '<label class="checkbox-line"><input data-consent-input id="consentExternalAi" type="checkbox"> Autoriza proveedores/modelos externos de IA si fueran necesarios y bajo medidas de seguridad aplicables.</label>' +
    '<label class="checkbox-line"><input data-consent-input id="consentAnonymizedLearning" type="checkbox"> Autoriza uso anonimizado/agregado no identificable para mejorar plantillas, flujos y calidad del sistema.</label>' +
    '<p class="legal-note">Plantilla operativa. Validar con asesor legal/RGPD antes de uso real.</p></div><article class="consent-preview" id="consentPreview"></article></div></section>';
}

function renderStorage() {
  const rag = state.ragStats || { backend: "sin conexion", chunks: 0, sqliteChunks: 0, path: "data/rag/chroma/" };
  const aiActive = Boolean(state.aiProvider && state.aiProvider.active);
  const provider = aiActive && state.aiProvider.provider ? state.aiProvider.provider : "sin proveedor externo activo";
  const chunks = rag.chunks || rag.sqliteChunks || 0;
  const recordCount = rag.records || state.records.length;
  return '<section class="card"><div class="section-head"><div><span class="eyebrow">Datos</span><h1>Estado</h1></div><span class="score">Local</span></div>' +
    '<div class="pack-grid">' + metric("Estado", state.apiOnline ? "Activo" : "Local") + metric("Fragmentos", String(chunks)) + metric("Registros", String(recordCount)) + metric("IA externa", aiActive ? "Opt-in" : "Apagada") + '</div>' +
    '<div class="local-proof-band">' +
    '<span class="chip ok">Nodo privado local-first</span>' +
    '<span class="chip warn">IA externa solo con permiso/API del cliente</span>' +
    '<span class="chip warn">Apoyo documental: no diagnostico ni decision automatica</span>' +
    '<p>Proveedor IA actual: ' + escapeHtml(provider) + '. Antes de conectar datos sensibles fuera del nodo hay que documentar destino, responsable, base juridica y consentimiento.</p>' +
    '</div>' +
    '<div class="storage-map">' +
    storageRow("Registros", "data/evidentia.sqlite", "Casos, proyectos y notas guardadas.") +
    storageRow("Archivos", "data/uploads/", "Fotos, videos, audio, PDF y documentos.") +
    storageRow("Transcripciones", "data/derived/transcripts/", "Texto recuperable de audios y videos.") +
    storageRow("Vector RAG", rag.path || "data/rag/chroma/", "Fragmentos semanticos guardados en el nodo.") +
    storageRow("Packs", "data/exports/", "Documentos descargables.") +
    '</div>' +
    '</section>';
}

function storageRow(title, path, detail) {
  return '<article class="storage-row"><strong>' + escapeHtml(title) + '</strong><code>' + escapeHtml(path) + '</code><p>' + escapeHtml(detail) + '</p></article>';
}

function consentInput(label, id, placeholder) {
  return '<label>' + label + '<input data-consent-input id="' + id + '" autocomplete="off" placeholder="' + placeholder + '"></label>';
}

async function saveCaseFromForm(event) {
  event.preventDefault();
  const record = await buildRecordFromForm();
  const saved = await persistRecord(record);
  state.records = [saved].concat(state.records.filter((item) => item.id !== saved.id));
  state.activeRecordId = saved.id;
  saveRecords();
  await loadRagStats();
  render();
  showToast("Guardado en el conocimiento. No se ha abierto ninguna pagina nueva.");
}

async function buildRecordFromForm() {
  const explicitNotes = value("#notes");
  const fileNotes = await textFromSelectedFiles();
  const notes = [explicitNotes, fileNotes].filter(Boolean).join("\n\n---\n\n");
  const patient = value("#patient");
  const files = await uploadSelectedFiles();
  const entities = extractEntities(notes);
  const patientCode = anonymize(patient);
  return {
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString(),
    date: value("#captureDate") || new Date().toISOString().slice(0, 10),
    domain: value("#domain"),
    recordType: value("#recordType"),
    patientCode,
    hasPrivateIdentity: Boolean(patient),
    operator: value("#operator") || "Sin responsable",
    notes,
    files,
    entities,
    graph: buildGraph(patientCode, entities, files)
  };
}

async function textFromSelectedFiles() {
  const input = document.querySelector("#files");
  const selected = Array.from(input.files || []);
  const readable = selected.filter((file) => isReadableTextFile(file) && file.size <= 2_000_000);
  if (!readable.length) return "";
  const chunks = [];
  for (const file of readable) {
    try {
      const text = (await file.text()).trim();
      if (text) chunks.push("Contenido extraido de " + file.name + ":\n" + text);
    } catch {
      state.agentLog.unshift("No se pudo leer el texto local de " + file.name);
    }
  }
  if (chunks.length) state.agentLog.unshift("TXT/markdown incorporado a la nota: " + chunks.length);
  return chunks.join("\n\n");
}

function isReadableTextFile(file) {
  const name = (file.name || "").toLowerCase();
  const type = (file.type || "").toLowerCase();
  return type.startsWith("text/") || /\.(txt|md|csv|json|html|htm|xml)$/i.test(name);
}

async function uploadSelectedFiles() {
  const input = document.querySelector("#files");
  const selected = Array.from(input.files || []);
  if (!selected.length) return [];
  const fallback = selected.map((file) => ({ name: file.name, type: file.type || "unknown", size: file.size }));
  try {
    const formData = new FormData();
    selected.forEach((file) => formData.append("files", file));
    const response = await fetch("/api/uploads", { method: "POST", body: formData });
    if (!response.ok) throw new Error("upload failed");
    const payload = await response.json();
    state.agentLog.unshift("Archivos guardados en data/uploads: " + (payload.files || []).length);
    return payload.files || fallback;
  } catch {
    state.agentLog.unshift("Archivos guardados como metadatos; servidor de uploads no disponible");
    return fallback;
  }
}

function value(selector) {
  return document.querySelector(selector).value.trim();
}

function extractEntities(text) {
  const entities = [];
  entityRules.forEach((rule) => {
    if (rule.pattern.test(text)) entities.push({ type: rule.type, label: rule.label, confidence: 0.74, source: "client" });
  });
  (text.match(/\b(?:A|B|C|D)[1-4]\b|\bBL[1-4]\b|\bND[1-9]\b/gi) || []).forEach((shade) => {
    entities.push({ type: "measurement", label: "Color " + shade.toUpperCase(), confidence: 0.82, source: "regex" });
  });
  return dedupe(entities);
}

function dedupe(entities) {
  const seen = new Set();
  return entities.filter((entity) => {
    const key = entity.type + ":" + entity.label;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function buildGraph(patientCode, entities, files) {
  const graph = [{ type: "identity", label: patientCode, relation: "caso_anonimizado" }];
  entities.filter((entity) => !["asset", "evidence"].includes(entity.type)).forEach((entity) => graph.push({ type: entity.type, label: entity.label, relation: relationFor(entity.type) }));
  files.forEach((file) => graph.push({ type: "evidence", label: file.name, relation: "evidencia_asociada" }));
  return graph;
}

function relationFor(type) {
  return {
    discipline: "clasifica_area",
    asset: "incluye_activo",
    knowledge: "contiene_conocimiento",
    material: "usa_o_menciona_material",
    treatment: "describe_tratamiento",
    measurement: "contiene_medicion",
    outcome: "aporta_resultado",
    evidence: "aporta_evidencia"
  }[type] || "relacionado_con";
}

function anonymize(raw) {
  if (!raw) return "KNOWLEDGE-BASE";
  let hash = 0;
  for (let index = 0; index < raw.length; index += 1) {
    hash = (hash << 5) - hash + raw.charCodeAt(index);
    hash |= 0;
  }
  return "PAT-" + Math.abs(hash).toString(36).toUpperCase();
}

function loadSampleRecord() {
  const notes = "Plantilla de conocimiento: el equipo documenta una decision importante, adjunta fotografias, video, PDF de planificacion y notas internas. Se registra criterio aplicado, resultado esperado, dudas pendientes y aprendizaje para reutilizarlo en futuras consultas.";
  const patientCode = "REF-PLANTILLA";
  const entities = extractEntities(notes);
  const record = {
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString(),
    date: new Date().toISOString().slice(0, 10),
    domain: "Ortodoncia",
    recordType: "Caso completo",
    patientCode,
    hasPrivateIdentity: true,
    operator: "Equipo",
    notes,
    files: [
      { name: "fotografias-referencia.jpg", type: "image/jpeg", size: 240000 },
      { name: "video-referencia.mp4", type: "video/mp4", size: 1240000 },
      { name: "planificacion-referencia.pdf", type: "application/pdf", size: 380000 }
    ],
    entities,
    graph: buildGraph(patientCode, entities, [
      { name: "fotografias-referencia.jpg" },
      { name: "video-referencia.mp4" },
      { name: "planificacion-referencia.pdf" }
    ])
  };
  state.records.unshift(record);
  state.activeRecordId = record.id;
  saveRecords();
  render();
  showToast("Plantilla guardada como conocimiento.");
}

function activeRecord() {
  return state.records.find((record) => record.id === state.activeRecordId) || null;
}

function totalEvidence() {
  return state.records.reduce((sum, record) => sum + (record.files ? record.files.length : 0), 0);
}

function intelligenceSnapshot() {
  const records = state.records;
  const evidence = totalEvidence();
  const searchesAvoided = Math.max(0, records.length * 6 + evidence * 2);
  const hoursSaved = records.length ? Math.max(10, Math.round((searchesAvoided * 10) / 60)) : 0;
  const similar = similarCaseSignals(records);
  const contradictions = contradictionSignals(records);
  const experts = expertMemories(records);
  const lonelyExperts = experts.filter((expert) => expert.records === 1).length;
  const weakEvidence = records.filter((record) => !record.files.length).length;
  const riskScore = lonelyExperts + weakEvidence + (contradictions.length ? 2 : 0);
  const riskLevel = riskScore >= 4 ? "ALTO" : riskScore >= 2 ? "MEDIO" : "BAJO";
  const riskReason = riskLevel === "ALTO"
    ? "Demasiado criterio en memoria personal o sin fuentes cruzadas"
    : riskLevel === "MEDIO"
      ? "Faltan fuentes, responsables o seguimiento cruzado"
      : "Base pequena, pero trazable y consultable";
  const confidence = records.length >= 10 ? "confianza media" : records.length >= 3 ? "confianza inicial" : "datos insuficientes";
  return {
    searchesAvoided,
    hoursSaved,
    similar,
    similarCount: similar.length,
    contradictions,
    experts,
    riskLevel,
    riskReason,
    confidence
  };
}

function expertMemories(records) {
  const groups = new Map();
  records.forEach((record) => {
    const name = record.operator || "Sin responsable";
    if (!groups.has(name)) groups.set(name, []);
    groups.get(name).push(record);
  });
  return Array.from(groups.entries())
    .map(([name, items]) => {
      const domains = Array.from(new Set(items.map((item) => item.domain).filter(Boolean)));
      const concepts = Array.from(new Set(items.flatMap((item) => knowledgeEntities(item).map((entity) => entity.label)))).slice(0, 4);
      return {
        name,
        records: items.length,
        files: items.reduce((sum, item) => sum + item.files.length, 0),
        domains: domains.length,
        summary: concepts.length
          ? "Criterios detectados: " + concepts.join(", ") + "."
          : "Aun faltan entidades repetidas para perfilar criterios propios."
      };
    })
    .sort((a, b) => b.records - a.records)
    .slice(0, 4);
}

function similarCaseSignals(records) {
  const signals = [];
  for (let a = 0; a < records.length; a += 1) {
    for (let b = a + 1; b < records.length; b += 1) {
      const left = records[a];
      const right = records[b];
      const sharedEntities = knowledgeEntities(left)
        .map((entity) => entity.label)
        .filter((label) => knowledgeEntities(right).some((entity) => entity.label === label));
      if (left.domain === right.domain || sharedEntities.length >= 2) {
        signals.push(left.patientCode + " parecido a " + right.patientCode);
      }
    }
  }
  return signals.slice(0, 6);
}

function contradictionSignals(records) {
  const signals = [];
  const protocolValues = new Map();
  records.forEach((record) => {
    const text = normalizeText(record.notes || "");
    const matches = Array.from(text.matchAll(/\b(hf|grabado|acido|cemento|coccion|arenado|pulido|glaseado)\D{0,32}(\d{1,3})\s*(segundos|seg|s|minutos|min|mm|%)\b/g));
    matches.forEach((match) => {
      const key = match[1] + ":" + match[3];
      const value = match[2];
      if (!protocolValues.has(key)) protocolValues.set(key, new Map());
      if (!protocolValues.get(key).has(value)) protocolValues.get(key).set(value, []);
      protocolValues.get(key).get(value).push(record.patientCode);
    });
  });
  protocolValues.forEach((values, key) => {
    if (values.size > 1) {
      const readable = Array.from(values.entries()).map(([value, cases]) => value + " en " + cases.join("/")).join(" vs ");
      signals.push(key.replace(":", " ") + ": " + readable);
    }
  });
  const byDomain = new Map();
  records.forEach((record) => {
    const key = record.domain || "general";
    if (!byDomain.has(key)) byDomain.set(key, []);
    byDomain.get(key).push(record);
  });
  byDomain.forEach((items, domain) => {
    const hasSuccess = items.some((record) => /exito|éxito|estable|buen resultado/i.test(record.notes));
    const hasFailure = items.some((record) => /fracaso|problema|complicacion|complicación|dolor|fallo/i.test(record.notes));
    if (hasSuccess && hasFailure) signals.push("Resultados opuestos en " + domain + ": revisar contexto antes de convertirlo en protocolo");
  });
  return signals.slice(0, 5);
}

function recordHaystack(record) {
  return normalizeText([record.domain, record.recordType, record.patientCode, record.operator, record.notes]
    .concat(record.entities.map((entity) => entity.label))
    .concat(record.files.map((file) => file.name))
    .join(" "));
}

function resultCard(record) {
  return '<article class="case-card"><button data-select-case="' + record.id + '" type="button"><strong>' + escapeHtml(record.patientCode) + '</strong><span>' + escapeHtml(record.recordType) + ' · ' + escapeHtml(record.domain) + '</span><p>' + escapeHtml(record.notes.slice(0, 220)) + (record.notes.length > 220 ? "..." : "") + '</p><small>' + knowledgeEntities(record).length + ' entidades · ' + record.files.length + ' evidencias</small></button></article>';
}

function chatPrompt(text) {
  return '<button class="prompt-chip" data-chat-prompt="' + escapeHtml(text) + '" type="button">' + escapeHtml(text) + '</button>';
}

function chatBubble(message) {
  const sourceHtml = message.sources && message.sources.length
    ? '<div class="chat-sources">' + message.sources.map((record) => '<button data-select-case="' + escapeHtml(record.id) + '" type="button"><strong>' + escapeHtml(record.patientCode) + '</strong><span>' + escapeHtml(record.recordType) + ' · ' + escapeHtml(record.domain) + '</span></button>').join("") + '</div>'
    : "";
  return '<article class="chat-bubble ' + escapeHtml(message.role) + '"><p>' + escapeHtml(message.text).replaceAll("\n", "<br>") + '</p>' + sourceHtml + '</article>';
}

async function submitKnowledgeChat(event) {
  event.preventDefault();
  const input = document.querySelector("#knowledgeChatInput");
  const question = input.value.trim();
  if (!question) return;
  input.value = "";
  state.chatMessages.push({ role: "user", text: question, sources: [] });
  render();
  const answer = await answerFromKnowledgeMap(question);
  state.chatMessages.push(answer);
  state.agentLog.unshift("Chat consulto el mapa: " + question);
  render();
  requestAnimationFrame(() => {
    const thread = document.querySelector("#knowledgeChatThread");
    if (thread) thread.scrollTop = thread.scrollHeight;
  });
}

async function answerFromKnowledgeMap(question) {
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ question })
    });
    if (response.ok) {
      const payload = await response.json();
      if (payload.answer) {
        state.apiOnline = true;
        return {
          role: "assistant",
          text: payload.answer,
          sources: payload.sources || []
        };
      }
    }
  } catch {
    state.apiOnline = false;
  }

  if (!state.records.length) {
    return {
      role: "assistant",
      text: "Todavia no hay conocimiento guardado. Primero mete una transcripcion, fotos, PDF, videos o notas; despues podre buscar en ese mapa.",
      sources: []
    };
  }

  const matches = rankedKnowledgeMatches(question).slice(0, 5);
  if (!matches.length) {
    return {
      role: "assistant",
      text: "No encuentro nada claro en el mapa con esa pregunta. Prueba con terminos que hayas usado al guardar el caso, como area, tratamiento, resultado, protocolo, material, problema o nombre interno.",
      sources: []
    };
  }

  const best = matches[0].record;
  const sourceLines = matches.slice(0, 3).map((match, index) => {
    const record = match.record;
    const labels = record.entities.slice(0, 4).map((entity) => entity.label).join(", ") || "sin entidades marcadas";
    return (index + 1) + ". " + record.patientCode + " · " + record.domain + " · " + labels;
  });
  const answerText = [
    "He encontrado " + matches.length + " coincidencia" + (matches.length === 1 ? "" : "s") + " en tu mapa.",
    "",
    "La fuente mas cercana es " + best.patientCode + ": " + best.notes.slice(0, 360) + (best.notes.length > 360 ? "..." : ""),
    "",
    "Fuentes usadas:",
    sourceLines.join("\n"),
    "",
    "Confianza: " + confidenceLabel(matches[0].score) + ". Es recuperacion sobre conocimiento guardado; no es una conclusion nueva ni sustituye criterio humano."
  ].join("\n");

  return { role: "assistant", text: answerText, sources: matches.map((match) => match.record) };
}

function rankedKnowledgeMatches(question) {
  const terms = tokenize(question);
  const phrase = question.trim().toLowerCase();
  return state.records.map((record) => {
    const haystack = recordHaystack(record);
    let score = 0;
    terms.forEach((term) => {
      if (haystack.includes(term)) score += term.length > 4 ? 3 : 1;
    });
    if (phrase && haystack.includes(phrase)) score += 8;
    record.entities.forEach((entity) => {
      const label = entity.label.toLowerCase();
      terms.forEach((term) => {
        if (label.includes(term)) score += 2;
      });
    });
    return { record, score };
  }).filter((item) => item.score > 0).sort((a, b) => b.score - a.score);
}

function tokenize(text) {
  const stop = new Set(["como", "para", "sobre", "donde", "cuando", "cual", "cuales", "que", "este", "esta", "estos", "estas", "caso", "casos", "tengo", "tuve", "he", "han", "con", "sin", "del", "las", "los", "una", "unos", "unas"]);
  return normalizeText(text).match(/[a-z0-9*]+/g)?.filter((term) => term.length > 2 && !stop.has(term)) || [];
}

function normalizeText(text) {
  return String(text).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

function confidenceLabel(score) {
  if (score >= 12) return "alta";
  if (score >= 6) return "media";
  return "baja";
}

function metric(label, valueText) {
  return '<div class="metric"><span>' + escapeHtml(label) + '</span><strong>' + escapeHtml(valueText) + '</strong></div>';
}

function emptyPipeline(text) {
  return '<section class="empty-pipeline card"><canvas class="cube-canvas pipeline-cube-canvas" width="330" height="300"></canvas>' + renderPipelineSteps(state.activeView) + '<div class="empty-state elevated"><strong>' + escapeHtml(text) + '</strong><p>Guarda un registro o abre un caso existente para activar esta vista.</p><div class="actions"><button class="primary" data-set-view="intake" type="button">Guardar conocimiento</button><button class="secondary" data-set-view="cases" type="button">Ver casos</button></div></div></section>';
}

function renderPipelineSteps(activeView) {
  const steps = [
    { label: "Captura", view: "intake" },
    { label: "Extrae", view: "entities" },
    { label: "Mapa", view: "graph" },
    { label: "Busca", view: "query" },
    { label: "Aprende", view: "chat" },
    { label: "Conecta", view: "connectors" }
  ];
  return '<nav class="pipeline-steps" aria-label="Flujo de conocimiento">' + steps.map((step) => {
    const active = step.view === activeView;
    return '<button class="' + (active ? "active" : "") + '" data-set-view="' + step.view + '" type="button" aria-current="' + (active ? "page" : "false") + '">' + step.label + '</button>';
  }).join("") + '</nav>';
}

function startDictation() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    showToast("Este navegador no expone dictado. Pega la transcripcion o usa Chrome.");
    return;
  }
  if (!window.isSecureContext) {
    showToast("El dictado necesita HTTPS. Abre el enlace seguro de Evidentia.");
    return;
  }
  const dictationButton = document.querySelector("#startDictation");
  const recognition = new SpeechRecognition();
  recognition.lang = "es-ES";
  recognition.interimResults = false;
  recognition.continuous = false;
  recognition.onstart = () => {
    if (dictationButton) dictationButton.textContent = "Escuchando...";
    showToast("Dictado activo. Acepta el permiso de microfono si aparece.");
  };
  recognition.onresult = (event) => {
    const notes = document.querySelector("#notes");
    notes.value = (notes.value + "\n" + event.results[0][0].transcript).trim();
    showToast("Dictado anadido a la nota.");
  };
  recognition.onerror = (event) => {
    const code = event && event.error ? event.error : "error";
    const messages = {
      "not-allowed": "Microfono bloqueado. Activalo en permisos del navegador para esta web.",
      "service-not-allowed": "El navegador ha bloqueado el servicio de dictado. Prueba Chrome o revisa permisos.",
      "no-speech": "No he detectado voz. Pulsa Dictar de nuevo y habla cerca del microfono.",
      "audio-capture": "No hay microfono disponible o el sistema lo tiene bloqueado.",
      "network": "El dictado del navegador no responde por red. Pega la transcripcion o reintenta."
    };
    showToast(messages[code] || ("Dictado no disponible: " + code));
  };
  recognition.onend = () => {
    if (dictationButton) dictationButton.textContent = "Dictar";
  };
  try {
    recognition.start();
  } catch {
    if (dictationButton) dictationButton.textContent = "Dictar";
    showToast("El dictado ya estaba activo o el navegador lo ha bloqueado.");
  }
}

function consentValues() {
  return {
    clinic: valueOr("consentClinic", "Centro, empresa o equipo responsable"),
    doctor: valueOr("consentDoctor", "Responsable"),
    patient: valueOr("consentPatient", "Persona interesada"),
    patientId: valueOr("consentPatientId", "Documento no indicado"),
    caseName: valueOr("consentCase", "Caso, proyecto o expediente"),
    date: valueOr("consentDate", new Date().toISOString().slice(0, 10)),
    purpose: valueOr("consentPurpose", "Organizar informacion y conocimiento profesional con apoyo de inteligencia artificial agentica bajo supervision humana."),
    sensitiveHealth: !document.querySelector("#consentSensitiveHealth") || document.querySelector("#consentSensitiveHealth").checked,
    agentsProjects: Boolean(document.querySelector("#consentAgentsProjects") && document.querySelector("#consentAgentsProjects").checked),
    externalAi: Boolean(document.querySelector("#consentExternalAi") && document.querySelector("#consentExternalAi").checked),
    anonymizedLearning: Boolean(document.querySelector("#consentAnonymizedLearning") && document.querySelector("#consentAnonymizedLearning").checked)
  };
}

function valueOr(id, fallback) {
  const input = document.querySelector("#" + id);
  return input && input.value.trim() ? input.value.trim() : fallback;
}

function consentBodyHtml(values) {
  return '<h1>Consentimiento informado para tratamiento de datos, imagen y conocimiento con Evidentia</h1>' +
    '<p><strong>Centro responsable:</strong> ' + escapeHtml(values.clinic) + '</p>' +
    '<p><strong>Responsable / contacto RGPD:</strong> ' + escapeHtml(values.doctor) + '</p>' +
    '<p><strong>Persona interesada:</strong> ' + escapeHtml(values.patient) + '</p>' +
    '<p><strong>DNI / identificador:</strong> ' + escapeHtml(values.patientId) + '</p>' +
    '<p><strong>Caso, proyecto o expediente:</strong> ' + escapeHtml(values.caseName) + '</p>' +
    '<p><strong>Fecha:</strong> ' + escapeHtml(values.date) + '</p>' +
    '<h2>1. Responsable y marco normativo</h2><p>El responsable del tratamiento sera el centro indicado. Esta plantilla se redacta para un uso compatible con RGPD y LOPDGDD, y debe adaptarse por el responsable antes de su uso real.</p>' +
    '<h2>2. Finalidad</h2><p>' + escapeHtml(values.purpose) + '</p>' +
    '<h2>3. Base juridica orientativa</h2><p>La base juridica podra incluir consentimiento de la persona interesada, prestacion de servicios sanitarios/asistenciales, gestion documental, interes legitimo interno cuando proceda y tratamiento de categorias especiales de datos bajo las excepciones aplicables del articulo 9 RGPD. El centro debe confirmar la base juridica exacta para su caso.</p>' +
    '<h2>4. Datos tratados</h2><p>Podran tratarse datos identificativos, datos de contacto si fueran necesarios, datos de salud, fotografias intraorales y extraorales, videos, audio, escaneos, PDF, transcripciones, notas, mediciones, planes, resultados, consentimientos, facturas o documentos administrativos vinculados al caso.</p><p>Tratamiento de datos de salud e imagen: <strong>' + (values.sensitiveHealth ? "autorizado para la finalidad indicada" : "no autorizado") + '</strong>.</p>' +
    '<h2>5. Evidentia, RAG y agentes</h2><p>Evidentia puede guardar informacion, separar identidad y conocimiento reutilizable, generar transcripciones, crear fragmentos semanticos, indexarlos en una base vectorial privada y recuperar respuestas con fuentes. Tambien puede conectar conocimiento seudonimizado a agentes o Projects internos si el responsable lo permite.</p><p>Conexion a agentes o Projects internos: <strong>' + (values.agentsProjects ? "autorizada" : "no autorizada salvo nueva autorizacion") + '</strong>.</p>' +
    '<h2>6. Proveedores y modelos externos</h2><p>Uso de proveedores/modelos externos de IA: <strong>' + (values.externalAi ? "autorizado bajo medidas de seguridad, contrato y configuracion aplicables" : "no autorizado salvo nueva autorizacion expresa") + '</strong>. Si se usan proveedores externos, el centro debera informar de proveedor, finalidad, ubicacion/region, retencion, seguridad y posible transferencia internacional.</p>' +
    '<h2>7. Aprendizaje anonimizado</h2><p>Uso anonimizado o agregado para mejorar plantillas, flujos y calidad del sistema: <strong>' + (values.anonymizedLearning ? "autorizado" : "no autorizado") + '</strong>. Este uso no debera incluir datos identificables de pacientes, profesionales, centros, equipos, clientes o casos.</p>' +
    '<h2>8. Limitaciones de la IA</h2><p>La persona interesada entiende que la IA puede cometer errores, generar transcripciones incompletas, clasificar informacion de forma imperfecta o recuperar fuentes no concluyentes. Evidentia se usa como apoyo documental y de recuperacion de conocimiento; no sustituye diagnostico, criterio clinico, criterio legal ni decisiones profesionales humanas.</p>' +
    '<h2>9. Seguridad, minimizacion y acceso</h2><p>El centro aplicara medidas razonables de minimizacion, control de acceso, trazabilidad, copias de seguridad, seudonimizacion o anonimizacion cuando sea posible, separando identidad/datos sensibles y conocimiento reutilizable. Solo accederan personas autorizadas por el responsable.</p>' +
    '<h2>10. Lugar de almacenamiento</h2><p>Cuando Evidentia funcione en modo local, los datos, archivos y RAG podran almacenarse en el ordenador, NAS o servidor del centro. Si se activa modalidad cloud o hibrida, el centro debera informar de proveedores, ubicacion, medidas de seguridad y condiciones aplicables.</p>' +
    '<h2>11. Conservacion</h2><p>Los datos se conservaran durante el tiempo necesario para la finalidad asistencial, documental, legal, tecnica o de mejora interna indicada por el centro, salvo solicitud valida de supresion o limitacion cuando proceda.</p>' +
    '<h2>12. Derechos</h2><p>La persona interesada podra solicitar informacion, acceso, rectificacion, limitacion, oposicion, portabilidad o supresion en los terminos previstos por la normativa aplicable. Tambien podra retirar esta autorizacion cuando proceda, sin afectar al tratamiento realizado previamente de forma licita.</p>' +
    '<h2>13. Consentimiento</h2><p>Declaro haber recibido informacion suficiente, haber podido formular preguntas y autorizar el tratamiento descrito en este documento para la finalidad indicada.</p>' +
    '<div class="signature-grid"><div><span>Firma de la persona interesada</span></div><div><span>Firma del responsable/centro</span></div></div>' +
    '<p class="fine-print">Plantilla operativa. Validar con asesor legal/RGPD antes de uso real.</p>';
}

function updateConsentPreview() {
  const preview = document.querySelector("#consentPreview");
  if (preview) preview.innerHTML = consentBodyHtml(consentValues());
}

async function downloadKnowledgeBundle() {
  let bundle = null;
  try {
    const response = await fetch("/api/connectors/export", { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error("export endpoint offline");
    bundle = await response.json();
    state.agentLog.unshift("Knowledge bundle descargado desde API local");
  } catch {
    bundle = buildLocalKnowledgeBundle();
    state.agentLog.unshift("Knowledge bundle generado desde navegador");
  }
  const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "evidentia-knowledge-bundle-" + new Date().toISOString().slice(0, 10) + ".json";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
  showToast("Knowledge bundle listo para agente o proyecto.");
}

function buildLocalKnowledgeBundle() {
  return {
    schema: "evidentia.knowledge_bundle.v1",
    generatedAt: new Date().toISOString(),
    source: "browser-local",
    policy: {
      allowedUse: "Conectar conocimiento validado a agentes, proyectos o automatizaciones bajo permiso del propietario.",
      humanReviewRequired: true,
      medicalOrLegalDecision: false
    },
    stats: {
      records: state.records.length,
      files: totalEvidence(),
      ragBackend: state.ragStats ? state.ragStats.backend : "browser"
    },
    records: state.records.map((record) => ({
      id: record.id,
      date: record.date,
      domain: record.domain,
      recordType: record.recordType,
      reference: record.patientCode,
      operator: record.operator,
      notes: record.notes,
      entities: knowledgeEntities(record),
      files: record.files || [],
      graph: record.graph || []
    })),
    chunks: []
  };
}

async function copyConnectorEndpoint() {
  const endpoint = location.origin + "/api/connectors/export";
  try {
    await navigator.clipboard.writeText(endpoint);
    showToast("Endpoint copiado.");
  } catch {
    showToast(endpoint);
  }
}

function downloadConsentDocument() {
  const values = consentValues();
  const html = '<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Consentimiento Evidentia</title><style>body{font-family:Arial,sans-serif;max-width:860px;margin:40px auto;color:#17201d;line-height:1.5;padding:0 24px}h1{font-size:24px}h2{font-size:17px;margin-top:24px}p{font-size:13px}.signature-grid{display:grid;grid-template-columns:1fr 1fr;gap:32px;margin-top:48px}.signature-grid div{height:96px;border-top:1px solid #17201d;padding-top:10px}.fine-print{margin-top:32px;color:#66736e;font-size:11px}</style></head><body>' + consentBodyHtml(values) + '</body></html>';
  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "consentimiento-evidentia.html";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
  el.consentBadge.textContent = "Consentimiento generado";
  el.consentBadge.dataset.state = "granted";
}

function downloadPackDocument() {
  const record = activeRecord();
  if (!record) {
    showToast("Selecciona un caso antes de exportar.");
    return;
  }
  const packEntities = knowledgeEntities(record);
  const entityRows = packEntities.length
    ? packEntities.map((entity) => '<li><strong>' + escapeHtml(entity.type) + ':</strong> ' + escapeHtml(entity.label) + '</li>').join("")
    : '<li>Sin entidades detectadas.</li>';
  const relationRows = record.graph.length
    ? record.graph.map((item) => '<li>' + escapeHtml(item.from) + ' -- ' + escapeHtml(item.relation) + ' -- ' + escapeHtml(item.to) + '</li>').join("")
    : '<li>Sin relaciones generadas.</li>';
  const fileRows = record.files.length
    ? record.files.map((file) => '<li>' + escapeHtml(file.name || file.filename || "Archivo") + ' · ' + escapeHtml(file.type || file.mimeType || "tipo no indicado") + '</li>').join("")
    : '<li>Sin archivos asociados.</li>';
  const html = '<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Pack Evidentia - ' + escapeHtml(record.patientCode) + '</title><style>body{font-family:Arial,sans-serif;max-width:900px;margin:40px auto;color:#17201d;line-height:1.5;padding:0 24px}h1{font-size:28px;margin-bottom:4px}h2{font-size:18px;margin-top:28px;border-bottom:1px solid #d9dfdd;padding-bottom:8px}p,li{font-size:13px}code{background:#eef2f1;padding:2px 5px;border-radius:4px}.meta{color:#66736e}.box{border:1px solid #d9dfdd;border-radius:8px;padding:14px;margin:12px 0}.fine-print{margin-top:32px;color:#66736e;font-size:11px}</style></head><body>' +
    '<h1>EVIDENTIA</h1><p class="meta">Evidence-to-Outcome Pack · ' + escapeHtml(record.patientCode) + '</p>' +
    '<div class="box"><p><strong>Area:</strong> ' + escapeHtml(record.domain) + '</p><p><strong>Tipo:</strong> ' + escapeHtml(record.recordType) + '</p><p><strong>Responsable:</strong> ' + escapeHtml(record.operator || "Sin responsable") + '</p><p><strong>Fecha:</strong> ' + escapeHtml(record.date || record.createdAt || "") + '</p></div>' +
    '<h2>Conocimiento registrado</h2><p>' + escapeHtml(record.notes || "Sin notas.") + '</p>' +
    '<h2>Entidades detectadas</h2><ul>' + entityRows + '</ul>' +
    '<h2>Relaciones del mapa</h2><ul>' + relationRows + '</ul>' +
    '<h2>Archivos asociados</h2><ul>' + fileRows + '</ul>' +
    '<p class="fine-print">Documento operativo generado por Evidentia. No sustituye revision legal, tecnica, profesional ni, cuando aplique, clinica humana.</p>' +
    '</body></html>';
  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "pack-evidentia-" + record.patientCode.toLowerCase().replace(/[^a-z0-9]+/g, "-") + ".html";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
  state.agentLog.unshift("Pack exportado: " + record.patientCode);
  showToast("Pack exportado: " + record.patientCode);
}

function buildVectorPoints() {
  const points = [];
  VECTOR_CLUSTERS.forEach((cluster, clusterIndex) => {
    for (let i = 0; i < 18; i += 1) {
      const seed = (clusterIndex + 1) * 37 + i * 11;
      const angle = seed * 0.77;
      const radius = 0.11 + ((seed % 7) * 0.018);
      points.push({
        cluster: clusterIndex,
        x: cluster.cx + Math.cos(angle) * radius + Math.sin(seed) * 0.035,
        y: cluster.cy + Math.sin(angle * 1.13) * radius + Math.cos(seed * 0.3) * 0.035,
        z: cluster.cz + Math.cos(angle * 0.7) * radius
      });
    }
  });
  return points;
}

function drawCube(time = 0) {
  document.querySelectorAll(".cube-canvas").forEach((canvas) => {
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    const cx = w / 2;
    const cy = h / 2;
    const isHero = canvas.classList.contains("hero-cube-canvas");
    if (isHero) {
      drawHeroCube(ctx, w, h, time);
      return;
    }
    const angle = time * 0.00042;
    const tilt = Math.sin(time * 0.00025) * 0.22;
    const radius = Math.min(w, h) * (isHero ? 0.42 : 0.40);
    const projected = VECTOR_POINTS.map((point) => {
      const cos = Math.cos(angle);
      const sin = Math.sin(angle);
      const rx = point.x * cos - point.z * sin;
      const rz = point.x * sin + point.z * cos;
      const ry = point.y * Math.cos(tilt) - rz * Math.sin(tilt);
      const depth = 1.35 + rz * 0.62;
      return {
        x: cx + (rx * radius) / depth,
        y: cy + (ry * radius) / depth,
        z: rz,
        cluster: point.cluster,
        depth
      };
    });

    ctx.save();
    ctx.globalCompositeOperation = "screen";
    ctx.lineWidth = isHero ? 0.85 : 1.05;
    projected.forEach((point, index) => {
      for (let i = index + 1; i < projected.length; i += 1) {
        const other = projected[i];
        if (other.cluster !== point.cluster) continue;
        const dist = Math.hypot(point.x - other.x, point.y - other.y);
        const max = isHero ? 42 : 56;
        if (dist > max) continue;
        const alpha = (1 - dist / max) * (isHero ? 0.42 : 0.55);
        ctx.strokeStyle = hexToRgba(VECTOR_CLUSTERS[point.cluster].color, alpha);
        ctx.beginPath();
        ctx.moveTo(point.x, point.y);
        ctx.lineTo(other.x, other.y);
        ctx.stroke();
      }
    });

    const sweep = (time * 0.00018) % 1;
    ctx.strokeStyle = "rgba(150,242,202,.38)";
    ctx.lineWidth = isHero ? 1.2 : 1.5;
    ctx.beginPath();
    ctx.arc(cx, cy, radius * 0.98, sweep * Math.PI * 2, sweep * Math.PI * 2 + Math.PI * 0.64);
    ctx.stroke();

    projected
      .sort((a, b) => a.depth - b.depth)
      .forEach((point) => {
        const color = VECTOR_CLUSTERS[point.cluster].color;
        const dot = Math.max(isHero ? 1.8 : 2.3, (isHero ? 3.8 : 4.5) / point.depth);
        ctx.shadowColor = color;
        ctx.shadowBlur = isHero ? 8 : 10;
        ctx.fillStyle = hexToRgba(color, Math.min(0.95, 0.58 + point.z * 0.3));
        ctx.beginPath();
        ctx.arc(point.x, point.y, dot, 0, Math.PI * 2);
        ctx.fill();
      });

    if (!isHero) {
      ctx.shadowBlur = 0;
      ctx.font = "700 11px Inter, system-ui, sans-serif";
      VECTOR_CLUSTERS.forEach((cluster, index) => {
        const clusterPoints = projected.filter((point) => point.cluster === index);
        const x = clusterPoints.reduce((sum, point) => sum + point.x, 0) / clusterPoints.length;
        const y = clusterPoints.reduce((sum, point) => sum + point.y, 0) / clusterPoints.length;
        ctx.fillStyle = hexToRgba(cluster.color, 0.84);
        ctx.fillText(cluster.name, x + 7, y - 7);
      });
    }
    ctx.restore();
  });
  requestAnimationFrame(drawCube);
}

function drawHeroCube(ctx, w, h, time) {
  const cx = w / 2;
  const cy = h / 2;
  const size = 86;
  const a = time * 0.001;
  const points = [
    [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
    [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]
  ].map(([x, y, z]) => {
    const rx = x * Math.cos(a) - z * Math.sin(a);
    const rz = x * Math.sin(a) + z * Math.cos(a);
    const scale = size / (2.8 + rz);
    return [cx + rx * scale, cy + y * scale, rz];
  });
  ctx.strokeStyle = "rgba(150,242,202,.92)";
  ctx.shadowColor = "rgba(94,224,201,.72)";
  ctx.shadowBlur = 12;
  ctx.lineWidth = 1.55;
  [[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]].forEach(([i, j]) => {
    ctx.beginPath();
    ctx.moveTo(points[i][0], points[i][1]);
    ctx.lineTo(points[j][0], points[j][1]);
    ctx.stroke();
  });
  ctx.shadowBlur = 8;
  ctx.fillStyle = "rgba(248,251,255,.96)";
  points.forEach((point) => {
    ctx.beginPath();
    ctx.arc(point[0], point[1], 2.5, 0, Math.PI * 2);
    ctx.fill();
  });
  ctx.shadowBlur = 0;
}

function hexToRgba(hex, alpha) {
  const clean = hex.replace("#", "");
  const r = parseInt(clean.slice(0, 2), 16);
  const g = parseInt(clean.slice(2, 4), 16);
  const b = parseInt(clean.slice(4, 6), 16);
  return "rgba(" + r + "," + g + "," + b + "," + alpha + ")";
}

function formatBytes(bytes) {
  if (!bytes) return "tamano no indicado";
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return Math.round(bytes / 1024) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
