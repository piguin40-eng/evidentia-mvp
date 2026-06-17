const STORAGE_KEY = "evidentia_records_v2";
const HERO_VIDEO_VERSION = "20260617-roi-intel";
const BRAND_WORD = 'EVID&#398;NTIA';

const entityRules = [
  { type: "discipline", label: "Ortodoncia", pattern: /ortodoncia|alineador|bracket|oclusion|oclusión|maloclusion|maloclusión/i },
  { type: "discipline", label: "Rehabilitacion", pattern: /rehabilitacion|rehabilitación|protesis|prótesis|implante|implantologia|implantología/i },
  { type: "discipline", label: "Estetica dental", pattern: /estetica|estética|sonrisa|carilla|veneer|mockup|mocap/i },
  { type: "discipline", label: "Periodoncia", pattern: /periodoncia|encia|encía|periodontal|gingival/i },
  { type: "asset", label: "Fotografias", pattern: /foto|fotografia|fotografía|imagen|polarizada/i },
  { type: "asset", label: "Video", pattern: /video|vídeo|grabacion|grabación/i },
  { type: "asset", label: "PDF o documento", pattern: /pdf|documento|informe|consentimiento/i },
  { type: "asset", label: "Escaneo o archivo 3D", pattern: /stl|scan|escaneo|intraoral|cbct|dicom/i },
  { type: "knowledge", label: "Nota de conocimiento", pattern: /nota|transcripcion|transcripción|decision|decisión|criterio|observacion|observación/i },
  { type: "knowledge", label: "Protocolo o aprendizaje", pattern: /protocolo|aprendizaje|leccion|lección|recordar|conocimiento/i },
  { type: "measurement", label: "CIELAB", pattern: /cielab|l\*|a\*|b\*|delta e|de00/i },
  { type: "measurement", label: "Medicion", pattern: /medicion|medición|medida|espesor|grosor|\d+(?:[.,]\d+)?\s*mm/i },
  { type: "outcome", label: "Resultado o seguimiento", pattern: /resultado|exito|éxito|fracaso|estable|seguimiento|dolor|problema|revision|revisión/i },
  { type: "evidence", label: "Evidencia asociada", pattern: /evidencia|radiografia|radiografía|scan|pdf|documento|foto|video/i }
];

const state = {
  records: loadRecords(),
  activeRecordId: null,
  activeView: "intake",
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
  if (hashView && ["intake", "entities", "graph", "chat", "intelligence", "query", "pack", "cases", "consent", "storage"].includes(hashView)) {
    state.activeView = hashView;
  }
  render();
  requestAnimationFrame(drawCube);
}

function setView(view, clearSearch = true) {
  state.activeView = view;
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
    setAiState("working", "IA activa");
  } catch {
    state.aiProvider = null;
    setAiState("working", "IA activa");
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
    if (!response.ok) throw new Error("API offline");
    const payload = await response.json();
    state.apiOnline = true;
    state.agentLog.unshift("Registro guardado en SQLite: " + record.patientCode);
    return payload.record || record;
  } catch {
    state.apiOnline = false;
    state.agentLog.unshift("Registro guardado en fallback local: " + record.patientCode);
    return record;
  } finally {
    setAiState("working", "IA activa");
  }
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
  const ragLabel = state.ragStats && state.ragStats.backend === "chroma" ? " · Chroma " + state.ragStats.chunks + " chunks" : "";
  el.storageStatus.textContent = (state.apiOnline ? "SQLite activo" : "Modo local") + ragLabel;
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
  const focusNotes = document.querySelector("[data-focus-notes]");
  if (focusNotes) {
    focusNotes.addEventListener("click", () => {
      const notes = document.querySelector("#notes");
      if (notes) notes.focus();
    });
  }
  document.querySelectorAll("[data-select-case]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeRecordId = button.dataset.selectCase;
      setView("entities");
    });
  });
  const consentInputs = document.querySelectorAll("[data-consent-input]");
  consentInputs.forEach((input) => input.addEventListener("input", updateConsentPreview));
  const download = document.querySelector("#downloadConsent");
  if (download) download.addEventListener("click", downloadConsentDocument);
  const chatForm = document.querySelector("#knowledgeChatForm");
  if (chatForm) chatForm.addEventListener("submit", submitKnowledgeChat);
  const exportPack = document.querySelector("#exportPack");
  if (exportPack) exportPack.addEventListener("click", downloadPackDocument);
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
  return '<section class="evidentia-home">' +
    '<article class="evidentia-hero">' +
    '<div class="hero-copy"><span class="eyebrow">Base vectorial de conocimiento</span><h1 class="brand-word hero-brand-word">' + BRAND_WORD + '</h1><p class="hero-claim">Tu conocimiento vectorizado. Tu inteligencia amplificada.</p><p class="hero-subclaim">De la memoria dispersa al criterio propio. Del contexto a la acci&oacute;n.</p>' +
    '<div class="hero-actions"><button class="primary" data-focus-notes type="button">Guardar conocimiento</button><button class="secondary" data-set-view="chat" type="button">Hablar con el mapa</button><button class="secondary" data-jump-consent type="button">Permisos</button></div></div>' +
    '<div class="hero-visual" aria-label="Evidentia en funcionamiento">' +
    '<video class="hero-video" autoplay muted loop playsinline disablepictureinpicture preload="auto" poster="./assets/evidentia/evidentia-hero-poster.jpg?v=' + HERO_VIDEO_VERSION + '"><source src="./assets/evidentia/evidentia-hero.mp4?v=' + HERO_VIDEO_VERSION + '" type="video/mp4"></video>' +
    '<div class="hero-video-brand"><strong class="brand-word">' + BRAND_WORD + '</strong><span>Vector Knowledge Mirror</span></div>' +
    '<div class="hero-video-metrics"><span>' + state.records.length + ' registros</span><span>' + (state.ragStats ? state.ragStats.chunks || 0 : 0) + ' vectores</span><span>' + totalEvidence() + ' fuentes</span></div>' +
    '</div></article>' +
    '<div class="value-strip"><article><strong>Para personas, equipos y centros</strong><span>Profesionales, direcci&oacute;n, operaciones, docencia, colaboradores y equipos especializados.</span></article><article><strong>Conocimiento propio</strong><span>Casos, proyectos, protocolos, fotos, v&iacute;deos, PDF, decisiones, errores y aprendizajes.</span></article><article><strong>Contexto accionable</strong><span>Consulta lo guardado con fuentes, similitud, trazabilidad y criterio humano.</span></article></div>' +
    '<section class="work-grid">' +
    '<article class="card intake-card">' +
    '<div class="section-head"><div><span class="eyebrow">Ingesta inteligente</span><h1>Guardar conocimiento real</h1><p class="lead">Mete texto, audios transcritos, fotos, v&iacute;deos, PDF, protocolos o aprendizajes. Evidentia lo estructura, lo indexa y lo conecta.</p></div><button class="secondary" id="startDictation" type="button">Dictar</button></div>' +
    '<form id="caseForm">' +
    '<div class="field-row"><label>Area libre<select id="domain"><option>Conocimiento general del centro</option><option>Operacion / procesos</option><option>Equipo / formacion</option><option>Docencia / investigacion</option><option>Odontologia general</option><option>Ortodoncia</option><option>Estetica y rehabilitacion</option><option>Implantes</option><option>Periodoncia</option><option>Laboratorio</option><option>Otro conocimiento</option></select></label><label>Tipo de entrada<select id="recordType"><option>Registro de conocimiento</option><option>Transcripcion</option><option>Articulo de conocimiento</option><option>Caso de exito</option><option>Caso de no exito</option><option>Archivo de conocimiento</option><option>Nota de conocimiento</option><option>Protocolo</option><option>Seguimiento</option><option>Idea o aprendizaje</option></select></label></div>' +
    '<div class="field-row"><label>Persona, caso, proyecto o referencia<input id="patient" autocomplete="off" placeholder="Iniciales, numero de caso, proyecto o referencia interna"></label><label>Responsable<input id="operator" autocomplete="off" placeholder="Profesional, tecnico, responsable, direccion o equipo"></label></div>' +
    '<label>Conocimiento libre<textarea id="notes" rows="11" placeholder="Pega una transcripcion, explica que se hizo, sube fotos o videos, resume el resultado, registra si fue exito o fracaso, guarda criterios del equipo, protocolos, decisiones y aprendizajes. Sin estructura obligatoria."></textarea></label>' +
    '<div class="field-row"><label>Fotos, videos, PDF, TXT o archivos asociados<input id="files" type="file" multiple></label><label>Fecha<input id="captureDate" type="date" value="' + new Date().toISOString().slice(0, 10) + '"></label></div>' +
    '<div class="actions"><button class="primary" type="submit">Guardar en el mapa</button><button class="secondary" id="loadSample" type="button">Caso ejemplo</button><button class="secondary" data-set-view="cases" type="button">Ver casos</button></div>' +
    '</form></article>' +
    '<article class="card pipeline-card"><canvas id="cube" width="330" height="300" aria-hidden="true"></canvas>' +
    renderPipelineSteps("intake") +
    '<div class="trust-stack"><span>Sin ataduras</span><span>Fuente guardada</span><span>Conocimiento propio</span></div></article>' +
    '</section></section>';
}

function renderEntities() {
  const record = activeRecord();
  if (!record) return emptyPipeline("Selecciona un caso para ver entidades.");
  return '<section class="card"><div class="section-head"><div><span class="eyebrow">Extraccion</span><h1>Entidades detectadas</h1></div><span class="score">' + record.entities.length + ' entidades</span></div>' +
    '<div class="entity-grid">' + record.entities.map((entity) => '<article class="entity-card"><span class="type">' + escapeHtml(entity.type) + '</span><strong>' + escapeHtml(entity.label) + '</strong><small>confianza ' + Math.round((entity.confidence || 0.7) * 100) + '%</small></article>').join("") + '</div></section>';
}

function renderGraph() {
  const record = activeRecord();
  if (!record) return emptyPipeline("Selecciona un caso para ver el mapa.");
  return '<section class="card"><div class="section-head"><div><span class="eyebrow">Mapa de conocimiento</span><h1>Lo que Evidentia ha conectado</h1><p class="lead">No obliga al equipo a pensar en bases de datos. Solo muestra como queda conectado lo que ha guardado.</p></div><span class="score">' + record.graph.length + ' puntos</span></div>' +
    '<div class="graph-canvas"><div class="graph-root">' + escapeHtml(record.patientCode) + '</div>' + record.graph.slice(1).map((node, index) => '<article class="graph-node node-' + escapeHtml(node.type) + '" style="--i:' + index + '"><strong>' + escapeHtml(node.label) + '</strong><span>' + escapeHtml(node.relation) + '</span></article>').join("") + '</div></section>';
}

function renderQuery() {
  const query = el.search.value.trim().toLowerCase();
  const matches = query ? state.records.filter((record) => recordHaystack(record).includes(query)) : state.records.slice(0, 8);
  return '<section class="card"><div class="section-head"><div><span class="eyebrow">Busqueda vectorial</span><h1>Pregunta sobre todo lo guardado</h1><p class="lead">Usa la barra superior para buscar por caso, area, resultado, archivo, protocolo o criterio.</p></div><span class="score">' + matches.length + ' resultados</span></div>' +
    '<div class="result-list">' + (matches.length ? matches.map(resultCard).join("") : '<div class="empty-state"><strong>Sin coincidencias claras</strong><p>Prueba con palabras usadas al guardar el caso o registra nuevo conocimiento.</p><button class="secondary" data-set-view="intake" type="button">Guardar conocimiento</button></div>') + '</div></section>';
}

function renderChat() {
  return '<section class="card chat-shell">' +
    '<div class="section-head"><div><span class="eyebrow">Chat con el mapa</span><h1>Habla con tu conocimiento guardado</h1><p class="lead">Pregunta en lenguaje normal. Evidentia busca en tus casos, proyectos, notas, archivos y entidades, y responde con fuentes.</p></div><span class="score">' + state.records.length + ' registros</span></div>' +
    '<div class="chat-layout">' +
    '<div class="chat-thread" id="knowledgeChatThread">' + state.chatMessages.map(chatBubble).join("") + '</div>' +
    '<aside class="chat-prompts"><h3>Preguntas utiles</h3>' +
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

function renderIntelligence() {
  const intel = intelligenceSnapshot();
  const contradictionHtml = intel.contradictions.length
    ? intel.contradictions.map((item) => '<span class="chip warn">' + escapeHtml(item) + '</span>').join("")
    : '<span class="chip ok">Sin contradicciones criticas detectadas todavia</span>';
  const expertHtml = intel.experts.length
    ? intel.experts.map((expert) => '<article class="case-card"><button type="button"><strong>' + escapeHtml(expert.name) + '</strong><span>Memoria de experto · ' + expert.records + ' registros</span><p>' + escapeHtml(expert.summary) + '</p><small>' + expert.files + ' fuentes · ' + expert.domains + ' areas</small></button></article>').join("")
    : '<div class="empty-state"><strong>Sin memoria de experto suficiente</strong><p>Cuando un responsable acumule registros, Evidentia podra responder: que haria esta persona, que protocolo sigue y que criterios repite.</p></div>';
  const similarHtml = intel.similar.length
    ? intel.similar.map((item) => '<span class="chip ok">' + escapeHtml(item) + '</span>').join("")
    : '<span class="chip warn">Aun faltan registros comparables para similitud fuerte</span>';

  return '<section class="card"><div class="section-head"><div><span class="eyebrow">Inteligencia operativa</span><h1>ROI, expertos, riesgo y patrones</h1><p class="lead">Esto convierte Evidentia en algo vendible: no solo guarda conocimiento, detecta valor operativo y riesgo de perdida.</p></div><span class="score">' + intel.confidence + '</span></div>' +
    '<div class="intel-grid">' +
    intelligenceBox("Horas ahorradas", intel.hoursSaved + " h/mes", "Estimacion por busquedas manuales evitadas") +
    intelligenceBox("Busquedas evitadas", intel.searchesAvoided, "Consultas recuperables desde el mapa") +
    intelligenceBox("Casos similares", intel.similarCount, "Coincidencias por area y entidades") +
    intelligenceBox("Riesgo conocimiento", intel.riskLevel, intel.riskReason) +
    '</div>' +
    '<div class="work-grid intelligence-work">' +
    '<article class="card compact"><h3>Memoria de empleados / expertos</h3><p class="muted">Permite vender frases como: pregunta que haria Miguel Arroyo, Paula o cualquier experto interno segun su historial real.</p><div class="case-list">' + expertHtml + '</div></article>' +
    '<article class="card compact"><h3>Contradicciones detectadas</h3><p class="muted">Busca protocolos incompatibles, tiempos distintos, criterios opuestos o cambios sin trazabilidad.</p><div class="actions">' + contradictionHtml + '</div><h3>Casos conectados</h3><div class="actions">' + similarHtml + '</div></article>' +
    '</div>' +
    '<div class="value-strip intelligence-strip"><article><strong>Modo Preguntale al experto</strong><span>Proxima capa: responder desde la memoria de una persona concreta, citando registros y limites.</span></article><article><strong>Modo formacion</strong><span>Generar cursos, tests, evaluaciones y casos de entrenamiento desde el conocimiento indexado.</span></article><article><strong>Descubrimiento de patrones</strong><span>Detectar conclusiones que nadie escribio explicitamente, solo cuando haya evidencia repetida suficiente.</span></article></div>' +
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
    '</div><div class="card compact"><h3>Siguiente accion recomendada</h3><p>' + (missing[0] || "Caso suficientemente estructurado para consulta y revision profesional.") + '</p></div>' +
    '<div class="card compact"><h3>Faltantes</h3>' + (missing.length ? missing.map((item) => '<span class="chip warn">' + escapeHtml(item) + '</span>').join("") : '<span class="chip ok">Sin faltantes criticos</span>') + '</div></section>';
}

function renderCases() {
  return '<section class="card"><div class="section-head"><div><span class="eyebrow">Vault</span><h1>Casos estructurados</h1></div><span class="score">' + state.records.length + ' registros</span></div>' +
    '<div class="case-list">' + (state.records.length ? state.records.map(resultCard).join("") : '<p class="muted">Todavia no hay registros.</p>') + '</div></section>';
}

function renderConsent() {
  return '<section class="card consent-hero"><div class="section-head"><div><span class="eyebrow">Permiso descargable</span><h1>Autorizacion para datos sensibles</h1><p class="lead">Documento base para poder guardar fotos, videos, audios, PDF y datos del caso cuando el conocimiento incluya informacion identificable o sensible.</p></div><button class="primary" id="downloadConsent" type="button">Descargar documento firmable</button></div>' +
    '<div class="consent-status-panel"><strong>Estado recomendado:</strong><span class="chip warn">No iniciar tratamiento IA con datos identificables sin consentimiento firmado</span><span class="chip ok">Permite trabajo con texto, fotos, videos, PDF y transcripciones del caso</span></div>' +
    '<div class="consent-layout"><div class="consent-form">' +
    consentInput("Centro, empresa o equipo", "consentClinic", "Nombre del centro responsable") +
    consentInput("Responsable", "consentDoctor", "Profesional, tecnico, direccion o responsable") +
    consentInput("Persona interesada", "consentPatient", "Nombre y apellidos si aplica") +
    consentInput("DNI / identificador", "consentPatientId", "Documento o ID interno") +
    consentInput("Caso, proyecto o area", "consentCase", "Ej: caso, proyecto, area, proceso o expediente") +
    '<label>Fecha<input data-consent-input id="consentDate" type="date" value="' + new Date().toISOString().slice(0, 10) + '"></label>' +
    '<label>Finalidad<textarea data-consent-input id="consentPurpose" rows="5">Guardar, ordenar, vectorizar y consultar el conocimiento generado durante el caso, proyecto o actividad profesional, incluyendo archivos y notas, para que el equipo pueda recuperar informacion y aprender de su propia experiencia bajo supervision humana.</textarea></label>' +
    '<label class="checkbox-line"><input data-consent-input id="consentExternalAi" type="checkbox"> Autoriza proveedores/modelos externos de IA si fueran necesarios y bajo medidas de seguridad aplicables.</label>' +
    '<label class="checkbox-line"><input data-consent-input id="consentAnonymizedLearning" type="checkbox"> Autoriza uso anonimizado/agregado no identificable para mejorar plantillas, flujos y calidad del sistema.</label>' +
    '<p class="legal-note">Plantilla operativa. Validar con asesor legal/RGPD antes de uso real.</p></div><article class="consent-preview" id="consentPreview"></article></div></section>';
}

function renderStorage() {
  const rag = state.ragStats || { backend: "sin conexion", chunks: 0, sqliteChunks: 0, path: "data/rag/chroma/" };
  return '<section class="card"><div class="section-head"><div><span class="eyebrow">Mapa tecnico explicable</span><h1>Dónde se guarda cada cosa</h1><p class="lead">Arquitectura local-first para MVP. En cloud se conserva la misma separacion logica, cambiando SQLite/Chroma local por servicios gestionados.</p></div><span class="score">MVP local</span></div>' +
    '<div class="pack-grid">' + metric("Vector DB", rag.backend) + metric("Chunks Chroma", String(rag.chunks || 0)) + metric("Chunks SQLite", String(rag.sqliteChunks || 0)) + '</div>' +
    '<div class="storage-map">' +
    storageRow("Aplicacion", "/Users/piguin/.openclaw/workspace/evidentia-mvp", "Frontend, backend local y documentos del producto.") +
    storageRow("Base estructurada", "data/evidentia.sqlite", "Casos, entidades, relaciones, evidencias y busqueda FTS. Es SQLite dentro de la propia app local.") +
    storageRow("Archivos del caso", "data/uploads/", "Carpeta local donde se guardan fotos, videos, PDF, STL, CBCT/DICOM u otros adjuntos subidos desde la app.") +
    storageRow("RAG vectorial local", rag.path || "data/rag/chroma/", "ChromaDB persistente. Cada registro guardado indexa notas y texto extraido de archivos en chunks semanticos dentro del ordenador/servidor del cliente.") +
    storageRow("Exportaciones", "data/exports/", "Consentimientos, packs de evidencia, informes y documentos descargables.") +
    storageRow("Instalacion cliente", "Evidentia Local Node", "Opcion recomendada para equipos con conocimiento sensible: se instala en el ordenador/servidor del cliente y el RAG vive ahi dentro.") +
    storageRow("Aprendizaje global", "Opt-in anonimizado", "Evidentia no se queda con casos privados por defecto. Solo aprende con patrones anonimizados o contenido que el cliente autorice compartir.") +
    storageRow("Cloud v1", "Postgres + pgvector + object storage", "En produccion: base por organizacion, archivos en S3/R2, embeddings en pgvector o Qdrant, auditoria y permisos.") +
    '</div>' +
    '<div class="card compact"><h3>Modelo recomendado</h3><p>Para la primera version vendible: instalacion local o hibrida. El cliente compra Evidentia, se instala un nodo local en su ordenador/servidor, los datos y el RAG quedan dentro de su entorno, y solo se conectan servicios externos si el cliente lo autoriza.</p></div>' +
    '<div class="card compact"><h3>Aprendizaje entre clientes</h3><p>No debemos apropiarnos silenciosamente del conocimiento de cada cliente. La capa global solo debe usar estadistica anonima, mejoras tecnicas y bibliotecas compartidas con permiso explicito.</p></div>' +
    '<div class="card compact"><h3>Explicacion corta para venderlo</h3><p>En el MVP, todo vive dentro de la carpeta de la aplicacion en este Mac: SQLite para datos estructurados y una carpeta RAG preparada para Chroma local. En version cloud, el mismo modelo pasa a Postgres/pgvector y almacenamiento seguro por cliente u organizacion.</p></div></section>';
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
  setView("entities");
}

async function buildRecordFromForm() {
  const notes = value("#notes");
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
  entities.forEach((entity) => graph.push({ type: entity.type, label: entity.label, relation: relationFor(entity.type) }));
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
  if (!raw) return "CASE-" + Math.random().toString(36).slice(2, 8).toUpperCase();
  let hash = 0;
  for (let index = 0; index < raw.length; index += 1) {
    hash = (hash << 5) - hash + raw.charCodeAt(index);
    hash |= 0;
  }
  return "PAT-" + Math.abs(hash).toString(36).toUpperCase();
}

function loadSampleRecord() {
  const notes = "Registro demo de conocimiento: el equipo documenta una decision importante, adjunta fotografias, video, PDF de planificacion y notas internas. Se registra criterio aplicado, resultado esperado, dudas pendientes y aprendizaje para reutilizarlo en futuras consultas internas.";
  const patientCode = "PAT-DEMO";
  const entities = extractEntities(notes);
  const record = {
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString(),
    date: new Date().toISOString().slice(0, 10),
    domain: "Ortodoncia",
    recordType: "Caso completo",
    patientCode,
    hasPrivateIdentity: true,
    operator: "Demo Evidentia",
    notes,
    files: [
      { name: "fotografias-intraorales-demo.jpg", type: "image/jpeg", size: 240000 },
      { name: "video-mordida-demo.mp4", type: "video/mp4", size: 1240000 },
      { name: "planificacion-demo.pdf", type: "application/pdf", size: 380000 }
    ],
    entities,
    graph: buildGraph(patientCode, entities, [
      { name: "fotografias-intraorales-demo.jpg" },
      { name: "video-mordida-demo.mp4" },
      { name: "planificacion-demo.pdf" }
    ])
  };
  state.records.unshift(record);
  state.activeRecordId = record.id;
  saveRecords();
  setView("entities");
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
  const searchesAvoided = Math.max(0, records.length * 4 + evidence * 2);
  const hoursSaved = Math.max(0, Math.round((searchesAvoided * 7) / 60));
  const similar = similarCaseSignals(records);
  const contradictions = contradictionSignals(records);
  const experts = expertMemories(records);
  const lonelyExperts = experts.filter((expert) => expert.records === 1).length;
  const weakEvidence = records.filter((record) => !record.files.length).length;
  const riskScore = lonelyExperts + weakEvidence + (contradictions.length ? 2 : 0);
  const riskLevel = riskScore >= 4 ? "ALTO" : riskScore >= 2 ? "MEDIO" : "BAJO";
  const riskReason = riskLevel === "ALTO"
    ? "Conocimiento poco redundante o con contradicciones"
    : riskLevel === "MEDIO"
      ? "Faltan mas fuentes o validacion cruzada"
      : "Base pequena pero trazable";
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
      const concepts = Array.from(new Set(items.flatMap((item) => item.entities.map((entity) => entity.label)))).slice(0, 4);
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
      const sharedEntities = left.entities
        .map((entity) => entity.label)
        .filter((label) => right.entities.some((entity) => entity.label === label));
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
  return '<article class="case-card"><button data-select-case="' + record.id + '" type="button"><strong>' + escapeHtml(record.patientCode) + '</strong><span>' + escapeHtml(record.recordType) + ' · ' + escapeHtml(record.domain) + '</span><p>' + escapeHtml(record.notes.slice(0, 220)) + (record.notes.length > 220 ? "..." : "") + '</p><small>' + record.entities.length + ' entidades · ' + record.files.length + ' evidencias</small></button></article>';
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
  return '<section class="empty-pipeline card"><canvas id="cube" width="330" height="300"></canvas>' + renderPipelineSteps(state.activeView) + '<div class="empty-state elevated"><strong>' + escapeHtml(text) + '</strong><p>Guarda un registro o abre un caso existente para activar esta vista.</p><div class="actions"><button class="primary" data-set-view="intake" type="button">Guardar conocimiento</button><button class="secondary" data-set-view="cases" type="button">Ver casos</button></div></div></section>';
}

function renderPipelineSteps(activeView) {
  const steps = [
    { label: "Captura", view: "intake" },
    { label: "Vectoriza", view: "entities" },
    { label: "Mapa", view: "graph" },
    { label: "Busca", view: "query" },
    { label: "Aprende", view: "chat" }
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
  const recognition = new SpeechRecognition();
  recognition.lang = "es-ES";
  recognition.interimResults = false;
  recognition.onresult = (event) => {
    const notes = document.querySelector("#notes");
    notes.value = (notes.value + "\n" + event.results[0][0].transcript).trim();
  };
  recognition.start();
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
    externalAi: Boolean(document.querySelector("#consentExternalAi") && document.querySelector("#consentExternalAi").checked),
    anonymizedLearning: Boolean(document.querySelector("#consentAnonymizedLearning") && document.querySelector("#consentAnonymizedLearning").checked)
  };
}

function valueOr(id, fallback) {
  const input = document.querySelector("#" + id);
  return input && input.value.trim() ? input.value.trim() : fallback;
}

function consentBodyHtml(values) {
  return '<h1>Autorizacion para tratamiento de datos y conocimiento con sistemas de inteligencia artificial agentica</h1>' +
    '<p><strong>Centro responsable:</strong> ' + escapeHtml(values.clinic) + '</p>' +
    '<p><strong>Responsable:</strong> ' + escapeHtml(values.doctor) + '</p>' +
    '<p><strong>Persona interesada:</strong> ' + escapeHtml(values.patient) + '</p>' +
    '<p><strong>DNI / identificador:</strong> ' + escapeHtml(values.patientId) + '</p>' +
    '<p><strong>Caso, proyecto o expediente:</strong> ' + escapeHtml(values.caseName) + '</p>' +
    '<p><strong>Fecha:</strong> ' + escapeHtml(values.date) + '</p>' +
    '<h2>1. Finalidad</h2><p>' + escapeHtml(values.purpose) + '</p>' +
    '<h2>2. Datos tratados</h2><p>Podran tratarse datos identificativos, datos de contacto si fueran necesarios, fotografias, videos, escaneos, PDF, audios, transcripciones, notas, mediciones, planes, resultados, documentos administrativos y conocimiento aportado por el profesional o equipo relacionado con el caso, proyecto o expediente.</p>' +
    '<h2>3. Uso de inteligencia artificial</h2><p>El centro podra utilizar sistemas de IA, incluidos agentes, para transcribir, ordenar, vectorizar, buscar y conectar informacion guardada por el equipo profesional.</p><p>Estos sistemas no sustituyen el criterio humano ni toman decisiones autonomas. Toda decision profesional, economica, sanitaria o tecnica debera ser revisada y validada por personas cualificadas.</p>' +
    '<h2>4. Lugar de tratamiento y almacenamiento</h2><p>Cuando Evidentia funcione en modo local, los datos, archivos y RAG podran almacenarse en el ordenador, NAS o servidor del centro. Si se activa modalidad cloud o hibrida, el centro debera informar de los proveedores, ubicacion, medidas de seguridad y condiciones aplicables.</p>' +
    '<h2>5. Proveedores y modelos externos</h2><p>Uso de proveedores/modelos externos de IA: <strong>' + (values.externalAi ? "autorizado" : "no autorizado salvo nueva autorizacion expresa") + '</strong>.</p>' +
    '<h2>6. Aprendizaje anonimizado</h2><p>Uso anonimizado o agregado para mejorar plantillas, flujos y calidad del sistema: <strong>' + (values.anonymizedLearning ? "autorizado" : "no autorizado") + '</strong>. Este uso no debera incluir datos identificables de personas, equipos, clientes o casos.</p>' +
    '<h2>7. Riesgos y limitaciones</h2><p>La persona interesada entiende que la IA puede cometer errores, generar transcripciones incompletas o clasificar informacion de forma imperfecta. Por ello, el sistema se utiliza como apoyo para guardar y recuperar conocimiento, no como sustituto del criterio profesional humano.</p>' +
    '<h2>8. Seguridad y confidencialidad</h2><p>El centro aplicara medidas razonables de minimizacion, control de acceso, trazabilidad, seudonimizacion o anonimizacion cuando sea posible, separando identidad/datos sensibles y conocimiento reutilizable.</p>' +
    '<h2>9. Conservacion</h2><p>Los datos se conservaran durante el tiempo necesario para la finalidad asistencial, documental, legal, tecnica o de mejora interna indicada por el centro, salvo solicitud valida de supresion o limitacion cuando proceda.</p>' +
    '<h2>10. Derechos</h2><p>La persona interesada podra solicitar informacion, acceso, rectificacion, limitacion, oposicion o supresion en los terminos previstos por la normativa aplicable. Tambien podra retirar esta autorizacion cuando proceda, sin afectar al tratamiento realizado previamente de forma licita.</p>' +
    '<h2>11. Consentimiento</h2><p>Declaro haber recibido informacion suficiente, haber podido formular preguntas y autorizar el tratamiento descrito en este documento.</p>' +
    '<div class="signature-grid"><div><span>Firma de la persona interesada</span></div><div><span>Firma del responsable/centro</span></div></div>' +
    '<p class="fine-print">Plantilla operativa. Validar con asesor legal/RGPD antes de uso real.</p>';
}

function updateConsentPreview() {
  const preview = document.querySelector("#consentPreview");
  if (preview) preview.innerHTML = consentBodyHtml(consentValues());
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
  const entityRows = record.entities.length
    ? record.entities.map((entity) => '<li><strong>' + escapeHtml(entity.type) + ':</strong> ' + escapeHtml(entity.label) + '</li>').join("")
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

function drawCube(time = 0) {
  const canvas = document.querySelector("#cube");
  if (canvas) {
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    const cx = w / 2;
    const cy = h / 2;
    const size = 76;
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
    ctx.strokeStyle = "rgba(122,162,255,.85)";
    ctx.lineWidth = 1.5;
    [[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]].forEach(([i,j]) => {
      ctx.beginPath();
      ctx.moveTo(points[i][0], points[i][1]);
      ctx.lineTo(points[j][0], points[j][1]);
      ctx.stroke();
    });
    ctx.fillStyle = "rgba(94,224,201,.95)";
    points.forEach((p) => {
      ctx.beginPath();
      ctx.arc(p[0], p[1], 3, 0, Math.PI * 2);
      ctx.fill();
    });
  }
  requestAnimationFrame(drawCube);
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
