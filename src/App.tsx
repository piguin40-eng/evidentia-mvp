import { useEffect, useState } from 'react'
import { Activity, BrainCircuit, ChevronRight, Database, FileCheck2, FolderOpen, History, Shield, Upload } from 'lucide-react'
import { MeshViewer } from './MeshViewer'
import { ReviewWorkspace } from './ReviewWorkspace'

const scrollTo = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
const openMeshPicker = () => document.getElementById('mesh-file-input')?.click()

export type QueueCase = {
  case_code: string
  daily_slot: number
  daily_total: number
  review_status: string
  mesh_format: 'stl' | 'ply'
  mesh_url: string
  triangle_count: number
}

export default function App() {
  const [selectedMeshFile, setSelectedMeshFile] = useState<File | null>(null)
  const [uploadRevision, setUploadRevision] = useState(0)
  const [queueCases, setQueueCases] = useState<QueueCase[]>([])
  useEffect(() => {
    let active = true
    void fetch('/api/review-queue')
      .then(async response => {
        if (!response.ok) throw new Error(`Error HTTP ${response.status}`)
        return response.json() as Promise<{ cases: QueueCase[] }>
      })
      .then(payload => { if (active) setQueueCases(payload.cases) })
      .catch(() => { if (active) setQueueCases([]) })
    return () => { active = false }
  }, [])
  const queueCase = selectedMeshFile
    ? null
    : [...queueCases].reverse().find(item => item.review_status !== 'COMPLETED') ?? queueCases.at(-1) ?? null
  const meshRevisionKey = selectedMeshFile
    ? `upload:${uploadRevision}`
    : queueCase ? `queue:${queueCase.case_code}` : 'demo:synthetic'
  const handleMeshSelected = (file: File) => {
    setUploadRevision(revision => revision + 1)
    setSelectedMeshFile(file)
  }
  const isUploaded = Boolean(selectedMeshFile)
  const activeCaseCode = isUploaded ? 'MALLA LOCAL' : queueCase?.case_code ?? 'AIQ-DEMO-SYNTHETIC'
  const queueProgress = queueCase
    ? queueCase.daily_total > 0 ? `Cola diaria · ${queueCase.daily_slot}/${queueCase.daily_total}` : `Sesión continua · revisión ${queueCase.daily_slot}`
    : ''
  const handleQueueAdvanced = (nextCase: QueueCase) => {
    setSelectedMeshFile(null)
    setQueueCases([nextCase])
    scrollTo('visor')
  }

  return <div className="app-shell">
    <header className="topbar">
      <button className="brand" type="button" onClick={() => scrollTo('visor')} aria-label="Ir al visor">
        <span className="brand-mark">A</span><span><strong>AbutmentIQ</strong><small>SUPERVISED MESH INTELLIGENCE</small></span>
      </button>
      <nav aria-label="Navegación principal">
        <button type="button" onClick={() => scrollTo('visor')} className="active">Visor</button>
        <button type="button" onClick={() => scrollTo('agente')}>Agente</button>
        <button type="button" onClick={() => scrollTo('rag')}>RAG</button>
        <button type="button" onClick={() => scrollTo('entrenamiento')}>Entrenamiento</button>
        <button type="button" onClick={() => scrollTo('revision')}>Revisión</button>
      </nav>
      <div className="system-status"><span className="status-dot"/><span><b>SISTEMA LOCAL</b><small>Supervisión humana activa</small></span><Shield size={17}/></div>
    </header>

    <aside className="case-rail" aria-label="Cola de casos">
      <div className="rail-title"><span>COLA DE REVISIÓN</span><b>{String(queueCases.length || 1).padStart(2, '0')}</b></div>
      <button type="button" className="case-row active" onClick={() => scrollTo('visor')}>
        <i/><div><strong>{activeCaseCode}</strong><span>{isUploaded ? selectedMeshFile?.name : queueCase ? queueProgress : 'Implante · scanbody · preparaciones'}</span></div><ChevronRight size={16}/>
      </button>
      <div className="rail-empty"><FileCheck2 size={22}/><span>{queueCase ? 'Caso diario activo' : 'Una malla activa'}</span><small>{queueCase ? 'Corrige al agente dentro de la app' : 'Carga otra para sustituirla'}</small></div>
      <button type="button" className="next-case" onClick={openMeshPicker}><Upload size={15}/> Cargar otra malla</button>
      <div className="rail-policy"><Shield size={15}/><span><b>NEVER_REPEAT</b><small>Identidad por SHA-256</small></span></div>
    </aside>

    <main className="viewer-area" id="visor">
      <div className="case-heading">
        <div><span>{isUploaded ? 'MALLA LOCAL · PENDIENTE DE ANÁLISIS' : queueCase ? queueProgress.toUpperCase() : 'DEMOSTRACIÓN SINTÉTICA · SIN DATOS CLÍNICOS'}</span><h1>{isUploaded ? selectedMeshFile?.name : activeCaseCode}</h1><p>El agente analiza, recupera evidencia y espera tu corrección</p></div>
        <div className="case-meta"><span>CÓDIGO DE CASO</span><code>{activeCaseCode}</code></div>
      </div>
      <MeshViewer
        onFileSelected={handleMeshSelected}
        source={queueCase ? { url: queueCase.mesh_url, kind: queueCase.mesh_format, name: `${queueCase.case_code} · cola diaria` } : undefined}
      />
      <div className="component-strip">
        <div><span>FUNCIÓN</span><strong>{isUploaded || queueCase ? 'Pendiente de confirmar' : 'Implante / scanbody'}</strong></div>
        <div><span>AGENTE</span><strong><BrainCircuit size={14}/> Candidato experimental</strong></div>
        <div><span>RAG</span><strong><Database size={14}/> 263 documentos</strong></div>
        <div><span>ESTADO</span><strong className="ambiguous"><Activity size={14}/> Pendiente de validar</strong></div>
      </div>
    </main>

    <ReviewWorkspace selectedMeshFile={selectedMeshFile} queueCase={queueCase} onQueueAdvanced={handleQueueAdvanced} meshRevisionKey={meshRevisionKey}/>

    <nav className="mobile-nav" aria-label="Navegación móvil">
      <button type="button" className="active" onClick={() => scrollTo('visor')}><FolderOpen size={18}/><span>Visor</span></button>
      <button type="button" onClick={() => scrollTo('agente')}><BrainCircuit size={18}/><span>Agente</span></button>
      <button type="button" onClick={() => scrollTo('rag')}><Database size={18}/><span>RAG</span></button>
      <button type="button" onClick={() => scrollTo('entrenamiento')}><History size={18}/><span>Entrenamiento</span></button>
      <button type="button" onClick={() => scrollTo('revision')}><FileCheck2 size={18}/><span>Revisión</span></button>
    </nav>
  </div>
}
