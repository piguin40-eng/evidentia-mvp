import { useCallback, useEffect, useRef, useState } from 'react'
import { AlertTriangle, ArrowRight, BrainCircuit, Check, Database, History, LoaderCircle, LockKeyhole, RefreshCw, Search, ShieldCheck } from 'lucide-react'
import { gate23Metrics } from './domain'
import type { QueueCase } from './App'

type Assessment = {
  assessment_id: string
  case_code: string
  decision_status: string
  requires_human_confirmation: boolean
  clinical_decision: boolean
  agent_output: {
    verdict: 'CORRECTA' | 'INCORRECTA'
    probability_incorrect: number
    probability_correct: number
    abstention: boolean
    limitations: string[]
  }
  technical_features: Record<string, number>
  training: { model_version: string; balanced_accuracy: number; promotion_status: string }
  rag: { status: string; citations: Array<{ title: string; text: string; confidence: string; ordinal?: number }> }
}

type HumanReview = {
  review_id: string
  human_label: string
  agent_was_correct: boolean
  training_eligibility: string
  new_training_sample: boolean
  previous_system_output: { verdict: string; probability_correct?: number }
}

type TrainingStatus = {
  meshes: number
  case_groups: number
  balanced_accuracy: number
  human_reviews_received: number
  revalidations: number
  new_unique_training_samples: number
  candidate_records?: number
  pending_group_assignment?: number
  ready_grouped_candidates?: number
  next_candidate_gate: { ready: boolean; minimum_new_unique_samples: number; reason: string }
  promotion: string
}

type SystemStatus = { status: string; rag: { documents: number; chunks: number } }

const humanLabel: Record<string, string> = {
  correcta: 'CORRECTA',
  condicional: 'CONDICIONAL',
  incorrecta: 'INCORRECTA',
}

async function readJson(response: Response) {
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = payload.detail
    const message = typeof detail === 'string'
      ? detail
      : detail && typeof detail.message === 'string' ? detail.message : `Error HTTP ${response.status}`
    throw new Error(message)
  }
  return payload
}

export function ReviewWorkspace({ selectedMeshFile, queueCase, onQueueAdvanced, meshRevisionKey }: {
  selectedMeshFile?: File | null
  queueCase?: QueueCase | null
  onQueueAdvanced?: (nextCase: QueueCase) => void
  meshRevisionKey?: string
}) {
  const metrics = gate23Metrics()
  const effectiveMeshKey = meshRevisionKey ?? (selectedMeshFile
    ? `upload:${selectedMeshFile.name}:${selectedMeshFile.size}:${selectedMeshFile.lastModified}`
    : queueCase ? `queue:${queueCase.case_code}` : 'demo:synthetic')
  const requestGeneration = useRef(0)
  const [functionalClass, setFunctionalClass] = useState('')
  const [verdict, setVerdict] = useState('')
  const [notes, setNotes] = useState('')

  const [question, setQuestion] = useState('¿La malla es técnicamente correcta y qué evidencia hay sobre scanbody?')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [assessment, setAssessment] = useState<Assessment | null>(null)
  const [latestReview, setLatestReview] = useState<HumanReview | null>(null)
  const [training, setTraining] = useState<TrainingStatus | null>(null)
  const [system, setSystem] = useState<SystemStatus | null>(null)

  const loadTraining = useCallback(async () => {
    try { setTraining(await readJson(await fetch('/api/training/status')) as TrainingStatus) }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'No se pudo leer el entrenamiento') }
  }, [])

  const loadLatestReview = useCallback(async (caseCode: string, expectedGeneration?: number) => {
    const response = await fetch(`/api/reviews/latest?case_code=${encodeURIComponent(caseCode)}`)
    if (expectedGeneration !== undefined && expectedGeneration !== requestGeneration.current) return
    if (response.status === 404) { setLatestReview(null); return }
    const review = await readJson(response) as HumanReview
    if (expectedGeneration !== undefined && expectedGeneration !== requestGeneration.current) return
    setLatestReview(review)
  }, [])

  useEffect(() => {
    void loadTraining()
    void fetch('/api/status').then(readJson).then(data => setSystem(data as SystemStatus)).catch(reason => setError(String(reason)))
  }, [loadTraining])

  useEffect(() => {
    requestGeneration.current += 1
    const generation = requestGeneration.current
    setLoading(false)
    setFunctionalClass('')
    setAssessment(null)
    setLatestReview(null)
    setVerdict('')
    setNotes('')
    setMessage('')
    setError('')
    if (queueCase?.case_code) {
      void loadLatestReview(queueCase.case_code, generation).catch(reason => setError(String(reason)))
    }
  }, [effectiveMeshKey, loadLatestReview, queueCase?.case_code])

  const changeFunctionalClass = (value: string) => {
    if (loading) return
    requestGeneration.current += 1
    setLoading(false)
    setFunctionalClass(value)
    setAssessment(null)
    setVerdict('')
    setNotes('')
    setMessage('')
    setError('')
  }

  const changeQuestion = (value: string) => {
    if (loading) return
    requestGeneration.current += 1
    setLoading(false)
    setQuestion(value)
    setAssessment(null)
    setVerdict('')
    setNotes('')
    setLatestReview(null)
    setMessage('')
    setError('')
  }

  const analyze = async () => {
    if (!functionalClass) { setError('Selecciona primero la función real de la malla'); return }
    const generation = ++requestGeneration.current
    const requestedFunction = functionalClass
    const requestedFile = selectedMeshFile
    const requestedCase = queueCase
    setLoading(true); setError(''); setMessage(''); setAssessment(null); setVerdict('')
    try {
      let response: Response
      if (requestedFile) {
        const form = new FormData()
        form.append('file', requestedFile)
        form.append('functional_class', requestedFunction)
        form.append('question', question)
        response = await fetch('/api/agent/analyze-upload', { method: 'POST', body: form })
      } else if (requestedCase) {
        response = await fetch(`/api/agent/analyze-queue/${encodeURIComponent(requestedCase.case_code)}`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ functional_class: requestedFunction, question }),
        })
      } else {
        response = await fetch('/api/agent/analyze-demo', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ functional_class: requestedFunction, question }),
        })
      }
      const result = await readJson(response) as Assessment
      if (generation !== requestGeneration.current) return
      await loadLatestReview(result.case_code, generation)
      if (generation !== requestGeneration.current) return
      setAssessment(result)
      setMessage('Análisis completado · pendiente de validación humana explícita')
    } catch (reason) {
      if (generation === requestGeneration.current) {
        setError(reason instanceof Error ? reason.message : 'No se pudo ejecutar el agente')
      }
    } finally {
      if (generation === requestGeneration.current) setLoading(false)
    }
  }

  const saveReview = async () => {
    if (!assessment) { setError('Ejecuta primero el análisis del agente'); return }
    if (!verdict) { setError('Selecciona explícitamente la validación humana'); return }
    const generation = requestGeneration.current
    const assessmentId = assessment.assessment_id
    const requestedFunction = functionalClass
    const selectedLabel = humanLabel[verdict]
    const judgment = selectedLabel === assessment.agent_output.verdict ? 'CORRECT' : 'INCORRECT'

    if (judgment === 'INCORRECT' && !notes.trim()) { setError('Explica qué observas para corregir al agente'); return }
    setLoading(true); setError(''); setMessage('')
    try {
      const review = await readJson(await fetch('/api/reviews', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          assessment_id: assessmentId,

          human_label: selectedLabel,
          judgment,
          notes,
          functional_class: requestedFunction,
        }),
      })) as HumanReview
      if (generation !== requestGeneration.current) return
      setLatestReview(review)
      setMessage(review.agent_was_correct
        ? 'Revisión guardada · confirmaste el resultado del agente'
        : `Corrección guardada · ${review.training_eligibility === 'REVALIDATION_EXISTING_HASH' ? 'revalidación de origen existente' : 'nueva muestra candidata'}`)
      await loadTraining()
    } catch (reason) {
      if (generation === requestGeneration.current) {
        setError(reason instanceof Error ? reason.message : 'No se pudo guardar la revisión')
      }
    } finally {
      if (generation === requestGeneration.current) setLoading(false)
    }
  }

  const changeVerdict = (value: string) => {
    if (loading) return
    setVerdict(value)
    if (latestReview) {
      setLatestReview(null)
      setMessage('Cambios pendientes · vuelve a guardar la revisión antes de avanzar')
    }
  }

  const changeNotes = (value: string) => {
    if (loading) return
    setNotes(value)
    if (latestReview) {
      setLatestReview(null)
      setMessage('Cambios pendientes · vuelve a guardar la revisión antes de avanzar')
    }
  }

  const advanceToNextMesh = async () => {
    if (!queueCase || !latestReview || !onQueueAdvanced) return
    const generation = requestGeneration.current
    const requestedCaseCode = queueCase.case_code
    setLoading(true); setError(''); setMessage('')
    try {
      const payload = await readJson(await fetch('/api/review-queue/next', { method: 'POST' })) as { case: QueueCase }
      if (generation !== requestGeneration.current || queueCase.case_code !== requestedCaseCode) return
      setAssessment(null)
      setLatestReview(null)
      setFunctionalClass('')
      setVerdict('')
      setNotes('')
      onQueueAdvanced(payload.case)
    } catch (reason) {
      if (generation === requestGeneration.current) {
        setError(reason instanceof Error ? reason.message : 'No se pudo preparar la siguiente malla')
      }
    } finally {
      if (generation === requestGeneration.current) setLoading(false)
    }
  }

  const queueProgress = queueCase
    ? queueCase.daily_total > 0 ? `diaria ${queueCase.daily_slot}/${queueCase.daily_total}` : `continua · revisión ${queueCase.daily_slot}`
    : ''
  const probability = assessment
    ? (assessment.agent_output.verdict === 'CORRECTA' ? assessment.agent_output.probability_correct : assessment.agent_output.probability_incorrect)
    : 0

  return <aside className="inspector" aria-label="Panel de revisión" id="agente">
    <div className="inspector-heading">
      <div><span>AGENTE SUPERVISADO</span><h2>{assessment?.agent_output.verdict ?? 'SIN ANALIZAR'}</h2></div>
      <span className="candidate-only"><LockKeyhole size={13}/> CANDIDATO EXPERIMENTAL</span>
    </div>

    <section className="agent-controls">
      <div className="section-head"><span>PREGUNTA AL AGENTE</span><em>{selectedMeshFile ? 'Malla cargada' : queueCase ? `Cola ${queueProgress}` : 'Demo sintética'}</em></div>
      <label>Función real de la malla<select aria-label="Función real de la malla" value={functionalClass} disabled={loading} onChange={event => changeFunctionalClass(event.target.value)}>
        <option value="" disabled>Selecciona la función real…</option>
        <option value="implantologia_scanbody">Implantología con scanbody</option>
        <option value="encia">Encía</option><option value="antagonista">Antagonista</option>
        <option value="encerado_mockup">Encerado / mock-up</option><option value="preparaciones_fijas">Preparaciones fijas</option>
        <option value="complementaria">Complementaria</option><option value="modelo_trabajo">Modelo de trabajo</option><option value="no_evaluable">No evaluable</option>
      </select></label>
      <label>Consulta RAG<textarea value={question} onChange={event => changeQuestion(event.target.value)} disabled={loading} /></label>
      <button className="save-review" onClick={analyze} disabled={loading || !functionalClass} title={!functionalClass ? 'Selecciona primero la función real de la malla' : undefined}>
        {loading ? <LoaderCircle className="spin" size={16}/> : <BrainCircuit size={16}/>} Analizar con agente
      </button>
      {system && <div className="training-line"><Database size={15}/><span>RAG conectado · {system.rag.documents} documentos · {system.rag.chunks.toLocaleString('es-ES')} fragmentos</span></div>}
    </section>

    {latestReview && <section className="human-rectification" aria-label="Rectificación humana vigente">
      <div className="section-head"><span>RECTIFICACIÓN HUMANA VIGENTE</span><em>IDENTIDAD PRIVADA</em></div>
      <div className="rectification-flow">
        <div><span>Predicción original del agente</span><strong>{latestReview.previous_system_output.verdict}</strong></div>
        <div><span>Rectificación humana</span><strong>{latestReview.human_label}</strong></div>
      </div>
      <h3>{latestReview.agent_was_correct ? 'El agente acertó' : 'El agente se equivocó'}</h3>
      <p>La observación técnica completa permanece en el registro privado.</p>
      <small>{latestReview.new_training_sample ? 'Nueva muestra candidata' : 'Revalidación de origen existente · no duplica la malla · modelo estable sin cambios'}</small>
      {queueCase && onQueueAdvanced && <button className="save-review" type="button" onClick={() => void advanceToNextMesh()} disabled={loading}>
        {loading ? <LoaderCircle className="spin" size={16}/> : <ArrowRight size={16}/>} Siguiente malla
      </button>}
    </section>}

    {assessment ? <>
      <div className="abstention-note"><AlertTriangle size={17}/><div>
        <strong>Resultado experimental: {assessment.agent_output.verdict} · {(probability * 100).toLocaleString('es-ES', { maximumFractionDigits: 1 })}%</strong>
        <span>No es decisión clínica. Balanced accuracy del candidato: {(assessment.training.balanced_accuracy * 100).toLocaleString('es-ES', { maximumFractionDigits: 1 })}%.</span>
      </div></div>

      <section>
        <div className="section-head"><span>OBSERVACIÓN TÉCNICA</span><b>MALLA ANALIZADA</b></div>
        <div className="technical-summary">
          <strong>{Number(assessment.technical_features.faces).toLocaleString('es-ES')} caras</strong>
          <span>{Number(assessment.technical_features.components).toLocaleString('es-ES')} componente · {Number(assessment.technical_features.boundary_edges).toLocaleString('es-ES')} bordes abiertos · watertight {assessment.technical_features.watertight ? 'sí' : 'no'}</span>
        </div>
      </section>

      <section id="rag">
        <div className="section-head"><span>EVIDENCIA RAG RECUPERADA</span><b>{assessment.rag.citations.length}</b></div>
        <div className="rag-list">{assessment.rag.citations.map((citation, index) => <article key={`${citation.ordinal ?? index}-${citation.title}`}>
          <Search size={14}/><div><strong>{citation.title}</strong><p>{citation.text}</p><small>{citation.confidence} · evidencia {citation.ordinal ?? index + 1}</small></div>
        </article>)}</div>
      </section>
    </> : <div className="abstention-note"><BrainCircuit size={17}/><div><strong>Agente preparado</strong><span>Ejecuta el análisis para obtener una predicción, rasgos técnicos y evidencia RAG.</span></div></div>}

    <section className="review-form" id="revision">
      <div className="section-head"><span>VALIDACIÓN HUMANA</span><em>{training?.human_reviews_received ?? 0} registros append-only</em></div>
      <div className="training-line"><LockKeyhole size={15}/><span>Revisor vinculado a la cuenta autenticada</span></div>
      <div className="verdict-row">
        {['correcta', 'condicional', 'incorrecta'].map(value => <button key={value} type="button" disabled={loading} className={verdict === value ? 'active' : ''} onClick={() => changeVerdict(value)}>{value}</button>)}
      </div>
      <label>Observación<textarea disabled={loading} value={notes} onChange={event => changeNotes(event.target.value)} placeholder="Escribe exactamente lo que observas…"/></label>
      <button className="save-review" onClick={saveReview} disabled={loading || !assessment || !verdict} title={!verdict ? 'Selecciona explícitamente la validación humana' : undefined}><Check size={16}/> Guardar revisión</button>
      {message && <div className="saved-message"><ShieldCheck size={15}/>{message}</div>}
      {error && <div className="saved-message error"><AlertTriangle size={15}/>{error}</div>}
    </section>

    <section className="training-card" id="entrenamiento">
      <div className="section-head"><span>ENTRENAMIENTO LOCAL ENLAZADO</span><span className="version">candidate only</span></div>
      <div className="training-stats"><div><span>MALLAS</span><strong>{training?.meshes ?? '—'}</strong></div><div><span>CASOS</span><strong>{training?.case_groups ?? '—'}</strong></div><div><span>MEJOR BA</span><strong>{training ? `${(training.balanced_accuracy * 100).toLocaleString('es-ES', { maximumFractionDigits: 1 })}%` : '—'}</strong></div></div>
      <div className="training-line"><Database size={15}/><span>{training?.new_unique_training_samples ?? 0} nuevas muestras únicas · {training?.revalidations ?? 0} {training?.revalidations === 1 ? 'revalidación' : 'revalidaciones'}</span></div>
      <div className="training-line"><ShieldCheck size={15}/><span>{training?.candidate_records ?? 0} candidatos · {training?.pending_group_assignment ?? 0} pendientes de grupo · {training?.ready_grouped_candidates ?? 0} listos para evaluación</span></div>
      <div className="training-line muted"><History size={15}/><span>{training?.next_candidate_gate.reason ?? 'Leyendo gate…'}</span></div>
      <button className="secondary-action" onClick={() => void loadTraining()}><RefreshCw size={14}/> Actualizar gate de entrenamiento</button>
      <div className="training-line muted"><LockKeyhole size={15}/><span>Modelo estable: sin cambios · promoción bloqueada</span></div>
    </section>

    <section className="gate23-card">
      <div className="section-head"><span>GATE 2.3 · EVALUACIÓN HONESTA</span></div>
      <div className="gate23-bars"><div><span>Decididos</span><b>{metrics.decided}/{metrics.total}</b></div><div><span>Ambiguos</span><b>{metrics.ambiguous}/{metrics.total}</b></div><div><span>Rechazos</span><b>{metrics.rejected}/{metrics.total}</b></div></div>
      <p>{metrics.accuracyDecided}% solo sobre decididos · {metrics.coverage}% de cobertura · {metrics.confidentErrors} error confiado preservado.</p>
    </section>
  </aside>
}
