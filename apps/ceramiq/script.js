const screens = document.querySelectorAll(".screen");
const navItems = document.querySelectorAll(".nav-item");
const shotButtons = document.querySelectorAll(".shot");
const guideLabel = document.getElementById("guideLabel");
const photoInput = document.getElementById("photoInput");
const guideInput = document.getElementById("guideInput");
const runAnalysis = document.getElementById("runAnalysis");
const indexCase = document.getElementById("indexCase");
const engineNote = document.getElementById("engineNote");
const deltaBadge = document.getElementById("deltaBadge");
const analysisSummary = document.getElementById("analysisSummary");
const thirdStack = document.querySelector(".third-stack");
const recipeStack = document.querySelector(".recipe-stack");
const recipeHero = document.querySelector(".recipe-hero");
const validationList = document.getElementById("validationList");
const analysisMeta = document.getElementById("analysisMeta");
const ceramiqAnswer = document.getElementById("ceramiqAnswer");
const ceramicChatQuestion = document.getElementById("ceramicChatQuestion");
const askCeramicExpert = document.getElementById("askCeramicExpert");
const recordChatVoice = document.getElementById("recordChatVoice");
const toggleChatSpeech = document.getElementById("toggleChatSpeech");
const ceramicChatMessages = document.getElementById("ceramicChatMessages");
const ceramicChatStatus = document.getElementById("ceramicChatStatus");
const startCamera = document.getElementById("startCamera");
const takePhoto = document.getElementById("takePhoto");
const cameraPreview = document.getElementById("cameraPreview");
const cameraNote = document.getElementById("cameraNote");
const captureViewport = document.querySelector(".capture-viewport");
const caseDescription = document.getElementById("caseDescription");
const materialSystem = document.getElementById("materialSystem");
const customMaterial = document.getElementById("customMaterial");
const recordCaseAudio = document.getElementById("recordCaseAudio");
const caseAudioPreview = document.getElementById("caseAudioPreview");
const saveState = document.getElementById("saveState");
const savedCount = document.getElementById("savedCount");
const mediaGrid = document.getElementById("mediaGrid");
const clearCase = document.getElementById("clearCase");
const shots = ["Diente objetivo + guia", "Tarjeta gris BigColor Cera", "Foto polarizada", "Sustrato / munon", "Prueba / comparativa Delta"];
let currentShot = 0;
let cameraStream = null;
const completedShots = new Set();
let latestClinicalResult = null;
let savedPhotos = [];
let savedAudio = null;
let recorder = null;
let audioChunks = [];
let chatRecorder = null;
let chatAudioChunks = [];
let chatSpeechEnabled = false;
let chatRecognition = null;
const DB_NAME = "ceramiq-case-v1";
const STORE_NAME = "case-store";
const CASE_TEXT_KEY = "ceramiq.caseDescription";
const MATERIAL_KEY = "ceramiq.materialSystem";
const CUSTOM_MATERIAL_KEY = "ceramiq.customMaterial";

function openCaseDb() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(STORE_NAME, { keyPath: "id" });
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function readStore() {
  const db = await openCaseDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readonly");
    const request = tx.objectStore(STORE_NAME).getAll();
    request.onsuccess = () => resolve(request.result || []);
    request.onerror = () => reject(request.error);
  });
}

async function writeStore(item) {
  const db = await openCaseDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readwrite");
    tx.objectStore(STORE_NAME).put(item);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

async function clearStore() {
  const db = await openCaseDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readwrite");
    tx.objectStore(STORE_NAME).clear();
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

function setSavedState(text) {
  if (saveState) saveState.textContent = text;
}

function photoFileName(item, index) {
  return item.name || "ceramiq-foto-" + String(index + 1).padStart(2, "0") + ".jpg";
}

function photoRolePayload() {
  return savedPhotos.map((item, index) => ({
    name: photoFileName(item, index),
    role: item.shot || "Foto clinica",
  }));
}

async function loadSavedCase() {
  try {
    const items = await readStore();
    savedPhotos = items.filter((item) => item.type === "photo").sort((a, b) => a.createdAt - b.createdAt);
    savedAudio = items.find((item) => item.type === "audio") || null;
    syncCompletedShotsFromPhotos();
    if (caseDescription) caseDescription.value = localStorage.getItem(CASE_TEXT_KEY) || "";
    if (materialSystem) materialSystem.value = localStorage.getItem(MATERIAL_KEY) || "ips_emax_ceram";
    if (customMaterial) customMaterial.value = localStorage.getItem(CUSTOM_MATERIAL_KEY) || "";
    updateCustomMaterialVisibility();
    renderSavedMedia();
    setSavedState("Guardado local");
  } catch (error) {
    setSavedState("Sin guardado");
  }
}

function renderSavedMedia() {
  if (savedCount) savedCount.textContent = savedPhotos.length + (savedPhotos.length === 1 ? " foto" : " fotos");
  if (mediaGrid) {
    mediaGrid.innerHTML = "";
    savedPhotos.forEach((item, index) => {
      const card = document.createElement("article");
      card.className = "media-card";
      const button = document.createElement("button");
      button.className = "media-thumb";
      button.type = "button";
      button.setAttribute("aria-label", "Marcar foto " + (index + 1) + " como " + shots[currentShot]);
      const img = document.createElement("img");
      img.src = URL.createObjectURL(item.blob);
      img.alt = photoFileName(item, index);
      const label = document.createElement("span");
      label.className = "media-index";
      label.textContent = String(index + 1);
      const role = document.createElement("em");
      role.textContent = item.shot || "Sin rol";
      button.append(img, label, role);
      button.addEventListener("click", () => assignPhotoRole(index));
      card.append(button);
      mediaGrid.append(card);
    });
  }
  if (caseAudioPreview) {
    if (savedAudio && savedAudio.blob) {
      caseAudioPreview.src = URL.createObjectURL(savedAudio.blob);
      caseAudioPreview.style.display = "block";
    } else {
      caseAudioPreview.removeAttribute("src");
      caseAudioPreview.style.display = "none";
    }
  }
  if (cameraNote) cameraNote.textContent = savedPhotos.length ? savedPhotos.length + " fotos listas para Ceramic IQ." : "Cada foto entra al visor Ceramic IQ con rol de captura. Sin tarjeta gris, guia y polarizada, CIELAB y Delta E quedan estimados.";
}

function syncCompletedShotsFromPhotos() {
  completedShots.clear();
  savedPhotos.forEach((item) => {
    const index = shots.indexOf(item.shot);
    if (index >= 0) completedShots.add(index);
  });
}

async function assignPhotoRole(index) {
  const item = savedPhotos[index];
  if (!item) return;
  item.shot = shots[currentShot];
  await writeStore(item);
  syncCompletedShotsFromPhotos();
  updateShot(currentShot);
  renderSavedMedia();
  setSavedState("Foto " + (index + 1) + " marcada");
  if (cameraNote) {
    cameraNote.textContent = "Foto " + (index + 1) + " marcada como " + item.shot + ". Toca otra foto o cambia el tipo de captura arriba.";
  }
}

async function savePhotoBlob(blob, name, role) {
  const item = {
    id: "photo-" + Date.now() + "-" + Math.random().toString(16).slice(2),
    type: "photo",
    name,
    shot: role || shots[currentShot],
    blob,
    createdAt: Date.now(),
  };
  await writeStore(item);
  savedPhotos.push(item);
  syncCompletedShotsFromPhotos();
  renderSavedMedia();
  setSavedState("Guardado local");
}

function showScreen(name) {
  screens.forEach((screen) => screen.classList.toggle("active", screen.dataset.screen === name));
  navItems.forEach((item) => item.classList.toggle("active", item.dataset.go === name));
}
function updateShot(index) {
  currentShot = index;
  guideLabel.textContent = shots[index];
  shotButtons.forEach((button) => {
    const shotIndex = Number(button.dataset.shot);
    button.classList.toggle("active", shotIndex === index);
    button.classList.toggle("done", completedShots.has(shotIndex));
  });
}
function markShotDone() {
  completedShots.add(currentShot);
  updateShot(Math.min(currentShot + 1, shots.length - 1));
  cameraNote.textContent = completedShots.size + "/5 capturas registradas.";
}
function selectedMaterialPayload() {
  const value = materialSystem ? materialSystem.value : "ips_emax_ceram";
  const custom = customMaterial ? customMaterial.value.trim() : "";
  return { id: value, custom_name: custom };
}
function buildCaseFormData() {
  const data = new FormData();
  savedPhotos.forEach((item, index) => data.append("photos", item.blob, photoFileName(item, index)));
  data.append("photo_roles", JSON.stringify(photoRolePayload()));
  data.append("material_system", JSON.stringify(selectedMaterialPayload()));
  if (caseDescription) data.append("case_description", caseDescription.value.trim());
  if (savedAudio && savedAudio.blob) data.append("case_audio", savedAudio.blob, savedAudio.name || "ceramiq-brief.webm");
  data.append("engine", "Ceramic IQ");
  data.append("policy", "ceramiq_ceramic_only");
  return data;
}
async function indexCurrentCase() {
  if (!savedPhotos.length) {
    if (cameraNote) cameraNote.textContent = "Sube al menos una foto antes de guardar el caso.";
    showScreen("capture");
    return;
  }
  try {
    if (indexCase) indexCase.disabled = true;
    setSavedState("Indexando...");
    const response = await fetch("/api/ceramiq/index", { method: "POST", body: buildCaseFormData() });
    if (!response.ok) throw new Error("Index endpoint failed");
    const result = await response.json();
    setSavedState("Indexado");
    if (cameraNote) cameraNote.textContent = "Caso guardado: " + result.case_id + ". Ya puedes analizar fotos o vaciar el caso local.";
  } catch (error) {
    setSavedState("No indexado");
    if (cameraNote) cameraNote.textContent = "No se pudo guardar. Revisa que el servidor Ceramic IQ este abierto.";
  } finally {
    if (indexCase) indexCase.disabled = false;
  }
}
async function sendToClinicalHarness() {
  if (!savedPhotos.length) {
    if (cameraNote) cameraNote.textContent = "Sube al menos una foto antes de analizar. Para validar Delta E, sube objetivo y prueba.";
    showScreen("capture");
    return;
  }
  const data = buildCaseFormData();

  try {
    if (engineNote) engineNote.textContent = "Analizando fotos reales, calidad de captura, CIELAB por tercios y criterio ceramico...";
    const response = await fetch("/api/ceramiq/analyze", { method: "POST", body: data });
    if (!response.ok) throw new Error("Clinical endpoint failed");
    latestClinicalResult = await response.json();
    if (engineNote) engineNote.textContent = "Informe recibido desde Ceramic IQ. El caso queda trazado por fotos, roles y protocolo.";
    renderClinicalResult(latestClinicalResult);
    showScreen("analysis");
  } catch (error) {
    if (engineNote) engineNote.textContent = "No se pudo completar el analisis clinico. Revisa conexion y fotos subidas.";
  }
}
function updateCustomMaterialVisibility() {
  if (!customMaterial || !materialSystem) return;
  customMaterial.classList.toggle("active", materialSystem.value === "custom");
}

function fmtLab(lab) {
  if (!lab) return "L* -- a* -- b* --";
  return "L* " + lab.L + " a* " + lab.a + " b* " + lab.b;
}

function escapeHtml(value) {
  return String(value || "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[char]);
}

function appendChatBubble(kind, text) {
  if (!ceramicChatMessages) return;
  const article = document.createElement("article");
  article.className = "chat-bubble " + kind;
  article.textContent = text;
  ceramicChatMessages.append(article);
  ceramicChatMessages.scrollTop = ceramicChatMessages.scrollHeight;
}

async function askCeramicExpertQuestion(questionOverride) {
  const question = (questionOverride || (ceramicChatQuestion ? ceramicChatQuestion.value : "") || "").trim();
  if (!question) {
    if (ceramicChatStatus) ceramicChatStatus.textContent = "Escribe una pregunta concreta: material, cemento, receta, masa o coccion.";
    showScreen("chat");
    return;
  }
  appendChatBubble("user", question);
  if (ceramicChatQuestion && !questionOverride) ceramicChatQuestion.value = "";
  if (askCeramicExpert) askCeramicExpert.disabled = true;
  if (ceramicChatStatus) ceramicChatStatus.textContent = "Consultando Ceramic IQ Expert...";
  try {
    const response = await fetch("/api/ceramiq/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        case_context: caseDescription ? caseDescription.value.trim() : "",
        material_system: selectedMaterialPayload(),
      }),
    });
    if (!response.ok) throw new Error("Chat endpoint failed");
    const result = await response.json();
    if (result.ok === false) {
      appendChatBubble("assistant", result.error || "No se pudo consultar la pregunta.");
      return;
    }
    appendChatBubble("assistant", result.answer || "No hay respuesta tecnica disponible.");
    speakChatAnswer(result.answer || "");
    if (ceramicChatStatus) {
      ceramicChatStatus.textContent = (result.engine || "Ceramic IQ Expert") + " · " + (result.rag_source || "RAG ceramico") + " · " + (result.intent || "consulta");
    }
  } catch (error) {
    appendChatBubble("assistant", "No se pudo consultar el RAG ceramico ahora. Revisa conexion del servidor.");
    if (ceramicChatStatus) ceramicChatStatus.textContent = "Consulta no completada.";
  } finally {
    if (askCeramicExpert) askCeramicExpert.disabled = false;
  }
}

async function askCeramicExpertVoice(blob) {
  if (!blob || !blob.size) {
    if (ceramicChatStatus) ceramicChatStatus.textContent = "Audio vacio.";
    return;
  }
  if (askCeramicExpert) askCeramicExpert.disabled = true;
  if (recordChatVoice) recordChatVoice.disabled = true;
  if (ceramicChatStatus) ceramicChatStatus.textContent = "Transcribiendo voz...";
  try {
    const data = new FormData();
    data.append("chat_audio", blob, "ceramiq-chat.webm");
    data.append("case_context", caseDescription ? caseDescription.value.trim() : "");
    data.append("material_system", JSON.stringify(selectedMaterialPayload()));
    const response = await fetch("/api/ceramiq/chat", { method: "POST", body: data });
    if (!response.ok) throw new Error("Voice chat endpoint failed");
    const result = await response.json();
    if (result.question_transcript) appendChatBubble("user", result.question_transcript);
    if (result.ok === false) {
      appendChatBubble("assistant", result.error || "No se pudo transcribir la pregunta por voz.");
      if (ceramicChatStatus) ceramicChatStatus.textContent = "Voz no transcrita.";
      return;
    }
    appendChatBubble("assistant", result.answer || "No hay respuesta tecnica disponible.");
    speakChatAnswer(result.answer || "");
    if (ceramicChatStatus) {
      ceramicChatStatus.textContent = (result.engine || "Ceramic IQ Expert") + " · voz · " + (result.rag_source || "RAG ceramico") + " · " + (result.intent || "consulta");
    }
  } catch (error) {
    appendChatBubble("assistant", "No se pudo procesar la voz ahora. Prueba por texto o revisa micro/conexion.");
    if (ceramicChatStatus) ceramicChatStatus.textContent = "Consulta por voz no completada.";
  } finally {
    if (askCeramicExpert) askCeramicExpert.disabled = false;
    if (recordChatVoice) recordChatVoice.disabled = false;
  }
}

function speakChatAnswer(text) {
  if (!chatSpeechEnabled || !text || !window.speechSynthesis || !window.SpeechSynthesisUtterance) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "es-ES";
  utterance.rate = 0.98;
  utterance.pitch = 1;
  window.speechSynthesis.speak(utterance);
}

function renderClinicalResult(result) {
  if (deltaBadge) deltaBadge.textContent = result.delta_e === null ? "Delta E --" : "Delta E " + result.delta_e;
  if (analysisSummary) {
    analysisSummary.textContent = result.thirds && result.thirds.length
      ? result.thirds.map((third) => third.diagnosis).join(" ")
      : "Sube al menos una foto para calcular CIELAB por tercios.";
  }
  if (thirdStack && result.thirds) {
    thirdStack.innerHTML = "";
    result.thirds.forEach((third) => {
      const article = document.createElement("article");
      const comparisonLine = third.delta_e === null || third.delta_e === undefined
        ? "Resultado final pendiente"
        : "Actual " + fmtLab(third.current) + " · Delta E " + third.delta_e;
      article.innerHTML =
        "<div><strong>" + escapeHtml(third.name) + "</strong><span>Referencia " + escapeHtml(fmtLab(third.target)) + "</span></div>" +
        "<em>" + escapeHtml(comparisonLine) + "</em>" +
        "<p>" + escapeHtml(third.diagnosis) + "</p>";
      thirdStack.append(article);
    });
  }
  if (recipeHero && result.recipe && result.recipe.length) {
    const title = recipeHero.querySelector("h3");
    const body = recipeHero.querySelector("p");
    const pill = recipeHero.querySelector(".pill");
    if (pill) pill.textContent = result.calibration_status === "estimated_from_uploaded_pixels" ? "Analisis pixel real" : "Estimacion limitada";
    if (title) {
      title.textContent = result.case_phase === "final_result_delta_by_thirds"
        ? "Evaluacion final " + (result.material_system || "Ceramic IQ")
        : "Planificacion inicial " + (result.material_system || "Ceramic IQ");
    }
    if (body) {
      body.textContent = result.case_phase === "final_result_delta_by_thirds"
        ? result.warning
        : "Receta y criterio tecnico listos. Delta E final queda pendiente hasta recibir el resultado terminado del caso.";
    }
  }
  if (recipeStack && result.recipe) {
    recipeStack.innerHTML = "";
    result.recipe.forEach((block) => {
      const article = document.createElement("article");
      const items = block.masses.map((mass) =>
        "<li><b>" + mass.name + " - " + mass.percentage + "%</b><span>" + mass.function + ".</span></li>"
      ).join("");
      article.innerHTML =
        "<header><strong>Tercio " + block.third.toLowerCase() + "</strong><span>" + (block.material || "") + " · " + block.application_note + "</span></header>" +
        "<ul>" + items + "</ul>";
      recipeStack.append(article);
    });
  }
  renderValidation(result);
  renderCeramiqAnswer(result);
}

function renderCeramiqAnswer(result) {
  if (!ceramiqAnswer) return;
  const title = ceramiqAnswer.querySelector("h3");
  const body = ceramiqAnswer.querySelector("p:last-child");
  const checks = result.validation && result.validation.checks ? result.validation.checks : [];
  const missing = checks.filter((check) => !check.ok).map((check) => check.label.toLowerCase());
  const firstThird = result.thirds && result.thirds[0] ? result.thirds[0].diagnosis : "";
  const material = result.material_system || "el sistema seleccionado";
  if (title) title.textContent = "Ceramic IQ responde sobre " + material + ".";
  if (body) {
    body.textContent = firstThird
      ? firstThird + " Incluye criterio de material y receta con 4 masas por tercio cuando procede. " + (missing.length ? "Atencion: falta o queda debil " + missing.join(", ") + "; Ceramic IQ lo debe declarar como estimado." : "Protocolo completo para revision ceramica con guia, gris y polarizada.")
      : "No hay tercios calculados todavia. Sube fotos del caso y ejecuta Analizar caso.";
  }
}

function renderValidation(result) {
  if (validationList) {
    validationList.innerHTML = "";
    const checks = result.validation && result.validation.checks ? result.validation.checks : [];
    checks.forEach((check) => {
      const item = document.createElement("article");
      item.className = check.ok ? "ok" : "warn";
      item.innerHTML = "<strong>" + check.label + "</strong><span>" + check.detail + "</span>";
      validationList.append(item);
    });
  }
  if (analysisMeta) {
    const photos = result.input_photos ? result.input_photos.length : 0;
    const audio = result.case_audio_transcript ? "audio transcrito" : "sin audio";
    const score = result.validation ? result.validation.score : 0;
    analysisMeta.textContent = "Caso " + result.case_id + " · " + photos + " foto(s) · " + audio + " · validacion " + score + "% · " + result.calibration_status;
  }
}
document.querySelectorAll("[data-go]").forEach((button) => button.addEventListener("click", () => showScreen(button.dataset.go)));
if (runAnalysis) runAnalysis.addEventListener("click", sendToClinicalHarness);
if (indexCase) indexCase.addEventListener("click", indexCurrentCase);
if (askCeramicExpert) askCeramicExpert.addEventListener("click", () => askCeramicExpertQuestion());
if (toggleChatSpeech) toggleChatSpeech.addEventListener("click", () => {
  chatSpeechEnabled = !chatSpeechEnabled;
  toggleChatSpeech.setAttribute("aria-pressed", String(chatSpeechEnabled));
  toggleChatSpeech.textContent = chatSpeechEnabled ? "Oyendo" : "Escuchar";
  if (!chatSpeechEnabled && window.speechSynthesis) window.speechSynthesis.cancel();
});
if (recordChatVoice) recordChatVoice.addEventListener("click", async () => {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition) {
    if (chatRecognition) {
      chatRecognition.stop();
      chatRecognition = null;
      recordChatVoice.classList.remove("recording");
      recordChatVoice.querySelector("strong").textContent = "Voz";
      return;
    }
    chatRecognition = new SpeechRecognition();
    chatRecognition.lang = "es-ES";
    chatRecognition.interimResults = false;
    chatRecognition.maxAlternatives = 1;
    chatRecognition.onresult = (event) => {
      const transcript = Array.from(event.results || [])
        .map((result) => result[0] && result[0].transcript ? result[0].transcript : "")
        .join(" ")
        .trim();
      if (transcript) askCeramicExpertQuestion(transcript);
    };
    chatRecognition.onerror = () => {
      if (ceramicChatStatus) ceramicChatStatus.textContent = "No se pudo reconocer la voz.";
    };
    chatRecognition.onend = () => {
      chatRecognition = null;
      recordChatVoice.classList.remove("recording");
      recordChatVoice.querySelector("strong").textContent = "Voz";
    };
    recordChatVoice.classList.add("recording");
    recordChatVoice.querySelector("strong").textContent = "Parar";
    if (ceramicChatStatus) ceramicChatStatus.textContent = "Escuchando pregunta...";
    chatRecognition.start();
    return;
  }
  if (chatRecorder && chatRecorder.state === "recording") {
    chatRecorder.stop();
    recordChatVoice.classList.remove("recording");
    recordChatVoice.querySelector("strong").textContent = "Voz";
    return;
  }
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || !window.MediaRecorder) {
    if (ceramicChatStatus) ceramicChatStatus.textContent = "Micro no disponible en este navegador.";
    return;
  }
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
  chatAudioChunks = [];
  chatRecorder = new MediaRecorder(stream);
  chatRecorder.ondataavailable = (event) => {
    if (event.data.size) chatAudioChunks.push(event.data);
  };
  chatRecorder.onstop = async () => {
    stream.getTracks().forEach((track) => track.stop());
    const blob = new Blob(chatAudioChunks, { type: chatRecorder.mimeType || "audio/webm" });
    recordChatVoice.querySelector("strong").textContent = "Voz";
    await askCeramicExpertVoice(blob);
  };
  chatRecorder.start();
  recordChatVoice.classList.add("recording");
  recordChatVoice.querySelector("strong").textContent = "Parar";
  if (ceramicChatStatus) ceramicChatStatus.textContent = "Grabando pregunta...";
});
document.querySelectorAll("[data-chat-prompt]").forEach((button) => button.addEventListener("click", () => askCeramicExpertQuestion(button.dataset.chatPrompt)));
if (ceramicChatQuestion) ceramicChatQuestion.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") askCeramicExpertQuestion();
});
shotButtons.forEach((button) => button.addEventListener("click", () => updateShot(Number(button.dataset.shot))));
if (photoInput) photoInput.addEventListener("change", async () => {
  if (!photoInput.files.length) return;
  for (const file of Array.from(photoInput.files)) {
    await savePhotoBlob(file, file.name);
  }
  markShotDone();
  photoInput.value = "";
  if (cameraNote) cameraNote.textContent = savedPhotos.length + " foto(s) guardadas. Pulsa Guardar caso o Analizar fotos para generar informe.";
});
if (guideInput) guideInput.addEventListener("change", async () => {
  if (!guideInput.files.length) return;
  const file = guideInput.files[0];
  await savePhotoBlob(file, file.name || "guia-color.jpg", "Guia de color");
  const guideIndex = shots.indexOf("Diente objetivo + guia");
  if (guideIndex >= 0) completedShots.add(guideIndex);
  updateShot(currentShot);
  guideInput.value = "";
  if (cameraNote) cameraNote.textContent = "Guia de color guardada. Ahora sube tarjeta gris BigColor Cera y polarizada para que Ceramic IQ no lo marque como estimado.";
});
if (caseDescription) caseDescription.addEventListener("input", () => {
  localStorage.setItem(CASE_TEXT_KEY, caseDescription.value);
  setSavedState("Guardado local");
});
if (materialSystem) materialSystem.addEventListener("change", () => {
  localStorage.setItem(MATERIAL_KEY, materialSystem.value);
  updateCustomMaterialVisibility();
  setSavedState("Material guardado");
});
if (customMaterial) customMaterial.addEventListener("input", () => {
  localStorage.setItem(CUSTOM_MATERIAL_KEY, customMaterial.value);
  setSavedState("Material guardado");
});
async function openCamera() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    cameraNote.textContent = "Este navegador no permite camara directa. Usa galeria o abre en Safari/Chrome.";
    return;
  }
  try {
    if (cameraStream) cameraStream.getTracks().forEach((track) => track.stop());
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false });
    cameraPreview.srcObject = cameraStream;
    await cameraPreview.play();
    captureViewport.classList.add("live");
    cameraNote.textContent = "Camara activa. Manten guia, gris y diente dentro del encuadre.";
  } catch (error) {
    cameraNote.textContent = "No se pudo abrir la camara. Usa galeria o revisa permisos del navegador.";
  }
}
if (startCamera) startCamera.addEventListener("click", openCamera);
if (takePhoto) takePhoto.addEventListener("click", async () => {
  if (!cameraStream) {
    openCamera();
    return;
  }
  const canvas = document.createElement("canvas");
  canvas.width = cameraPreview.videoWidth || 1280;
  canvas.height = cameraPreview.videoHeight || 720;
  const context = canvas.getContext("2d");
  context.drawImage(cameraPreview, 0, 0, canvas.width, canvas.height);
  const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.92));
  if (blob) await savePhotoBlob(blob, "captura-" + (currentShot + 1) + ".jpg");
  markShotDone();
  if (cameraNote) cameraNote.textContent = "Captura guardada. Pulsa Guardar caso o Analizar fotos para generar informe.";
});
if (recordCaseAudio) recordCaseAudio.addEventListener("click", async () => {
  if (recorder && recorder.state === "recording") {
    recorder.stop();
    recordCaseAudio.classList.remove("recording");
    recordCaseAudio.querySelector("strong").textContent = "Grabar audio del caso";
    return;
  }
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || !window.MediaRecorder) {
    setSavedState("Audio no disponible");
    return;
  }
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
  audioChunks = [];
  recorder = new MediaRecorder(stream);
  recorder.ondataavailable = (event) => {
    if (event.data.size) audioChunks.push(event.data);
  };
  recorder.onstop = async () => {
    stream.getTracks().forEach((track) => track.stop());
    const blob = new Blob(audioChunks, { type: recorder.mimeType || "audio/webm" });
    const item = { id: "case-audio", type: "audio", name: "ceramiq-brief.webm", blob, createdAt: Date.now() };
    await writeStore(item);
    savedAudio = item;
    renderSavedMedia();
    setSavedState("Audio guardado");
  };
  recorder.start();
  recordCaseAudio.classList.add("recording");
  recordCaseAudio.querySelector("strong").textContent = "Detener grabacion";
  setSavedState("Grabando audio");
});
if (clearCase) clearCase.addEventListener("click", async () => {
  await clearStore();
  localStorage.removeItem(CASE_TEXT_KEY);
  savedPhotos = [];
  savedAudio = null;
  completedShots.clear();
  if (caseDescription) caseDescription.value = "";
  updateShot(0);
  renderSavedMedia();
  setSavedState("Caso vaciado");
});
updateShot(0);
loadSavedCase();
