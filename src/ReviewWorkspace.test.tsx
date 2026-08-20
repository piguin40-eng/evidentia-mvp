// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ReviewWorkspace } from './ReviewWorkspace'

const assessment = {
  assessment_id: 'ASM-SYNTHETIC-001',
  case_code: 'AIQ-DEMO-SYNTHETIC',
  decision_status: 'CANDIDATO_EXPERIMENTAL',
  requires_human_confirmation: true,
  clinical_decision: false,
  agent_output: {
    verdict: 'CORRECTA',
    probability_incorrect: 0.325332,
    probability_correct: 0.674668,
    abstention: false,
    limitations: ['Debe compararse con revisión humana.'],
  },
  technical_features: { faces: 209153, boundary_edges: 955, components: 1, watertight: 0 },
  training: { model_version: '2026-08-16-baseline-v1', balanced_accuracy: 0.576923, promotion_status: 'NO_PROMOTION' },
  rag: {
    status: 'EVIDENCIA_RECUPERADA',
    citations: [{ title: 'Congruence between scanbody meshes', text: 'La congruencia requiere CAD exacto.', confidence: 'UNVERIFIED', ordinal: 1 }],
  },
}

function jsonResponse(body: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } }))
}

const rectification = {
  review_id: 'REV-ORIGINAL', human_label: 'INCORRECTA', agent_was_correct: false,
  training_eligibility: 'REVALIDATION_EXISTING_HASH',
  new_training_sample: false, previous_system_output: { verdict: 'CORRECTA', probability_correct: 0.674668 },
}

describe('ReviewWorkspace', () => {
  afterEach(() => vi.restoreAllMocks())

  it('runs the supervised agent and shows model, technical and RAG evidence', async () => {
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/api/status')) return jsonResponse({ status: 'ok', rag: { documents: 263, chunks: 12528 } })
      if (url.includes('/api/training/status')) return jsonResponse({ meshes: 26, case_groups: 18, balanced_accuracy: 0.576923, human_reviews_received: 1, revalidations: 1, new_unique_training_samples: 0, next_candidate_gate: { ready: false, minimum_new_unique_samples: 6, reason: 'Faltan muestras' }, promotion: 'NO_PROMOTION' })
      if (url.includes('/api/reviews/latest')) return jsonResponse(rectification)
      if (url.includes('/api/agent/analyze-demo')) return jsonResponse(assessment)
      throw new Error(`URL inesperada ${url}`)
    }))

    render(<ReviewWorkspace />)
    fireEvent.change(screen.getByRole('combobox', { name: /función real/i }), { target: { value: 'implantologia_scanbody' } })
    fireEvent.click(screen.getByRole('button', { name: /analizar con agente/i }))

    expect(await screen.findByRole('heading', { name: 'CORRECTA' })).toBeInTheDocument()
    expect(screen.getByText(/67,5%/)).toBeInTheDocument()
    expect(screen.getByText('Congruence between scanbody meshes')).toBeInTheDocument()
    expect(screen.getByText(/209\.153 caras/i)).toBeInTheDocument()
    expect(screen.getByText(/263 documentos/i)).toBeInTheDocument()
  })

  it('requires an explicit human label and invalidates assessment when the visible mesh changes', async () => {
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/api/status')) return jsonResponse({ status: 'ok', rag: { documents: 1, chunks: 1 } })
      if (url.includes('/api/training/status')) return jsonResponse({ meshes: 0, case_groups: 0, balanced_accuracy: 0, human_reviews_received: 0, revalidations: 0, new_unique_training_samples: 0, next_candidate_gate: { ready: false, minimum_new_unique_samples: 6, reason: 'Faltan muestras' }, promotion: 'NO_PROMOTION' })
      if (url.includes('/api/reviews/latest')) return jsonResponse({}, 404)
      if (url.includes('/api/agent/analyze-demo')) return jsonResponse(assessment)
      throw new Error(`URL inesperada ${url}`)
    }))

    const { rerender } = render(<ReviewWorkspace meshRevisionKey="mesh-a" />)
    fireEvent.change(screen.getByRole('combobox', { name: /función real/i }), { target: { value: 'antagonista' } })
    fireEvent.click(screen.getByRole('button', { name: /analizar con agente/i }))
    expect(await screen.findByRole('heading', { name: 'CORRECTA' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /guardar revisión/i })).toBeDisabled()

    fireEvent.click(screen.getByRole('button', { name: 'correcta' }))
    expect(screen.getByRole('button', { name: /guardar revisión/i })).toBeEnabled()
    expect(screen.getByText(/revisor vinculado a la cuenta autenticada/i)).toBeInTheDocument()

    rerender(<ReviewWorkspace meshRevisionKey="mesh-b" />)
    expect(await screen.findByRole('heading', { name: 'SIN ANALIZAR' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /guardar revisión/i })).toBeDisabled()
  })

  it('discards a late review response after the visible mesh changes', async () => {
    let resolveReview!: (response: Response) => void
    const pendingReview = new Promise<Response>(resolve => { resolveReview = resolve })
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/api/status')) return jsonResponse({ status: 'ok', rag: { documents: 1, chunks: 1 } })
      if (url.includes('/api/training/status')) return jsonResponse({ meshes: 0, case_groups: 0, balanced_accuracy: 0, human_reviews_received: 0, revalidations: 0, new_unique_training_samples: 0, next_candidate_gate: { ready: false, minimum_new_unique_samples: 6, reason: 'Faltan muestras' }, promotion: 'NO_PROMOTION' })
      if (url.includes('/api/reviews/latest')) return jsonResponse({}, 404)
      if (url.includes('/api/agent/analyze-demo')) return jsonResponse(assessment)
      if (url.endsWith('/api/reviews')) return pendingReview
      throw new Error(`URL inesperada ${url}`)
    }))

    const { rerender } = render(<ReviewWorkspace meshRevisionKey="mesh-a" />)
    fireEvent.change(screen.getByRole('combobox', { name: /función real/i }), { target: { value: 'antagonista' } })
    fireEvent.click(screen.getByRole('button', { name: /analizar con agente/i }))
    await screen.findByRole('heading', { name: 'CORRECTA' })
    fireEvent.click(screen.getByRole('button', { name: 'correcta' }))
    fireEvent.click(screen.getByRole('button', { name: /guardar revisión/i }))

    rerender(<ReviewWorkspace meshRevisionKey="mesh-b" />)
    await act(async () => {
      resolveReview(new Response(JSON.stringify({
        review_id: 'REV-LATE', human_label: 'CORRECTA', agent_was_correct: true,
        training_eligibility: 'REVALIDATION_EXISTING_HASH', new_training_sample: false,
        previous_system_output: assessment.agent_output,
      }), { status: 201, headers: { 'Content-Type': 'application/json' } }))
      await pendingReview
      await Promise.resolve()
    })

    expect(screen.getByRole('heading', { name: 'SIN ANALIZAR' })).toBeInTheDocument()
    expect(screen.queryByText(/revisión guardada|corrección guardada/i)).not.toBeInTheDocument()
    expect(screen.queryByLabelText(/rectificación humana vigente/i)).not.toBeInTheDocument()
  })

  it('sends a correction without client-supplied reviewer identity and refreshes training status', async () => {
    let trainingReads = 0
    const fetchMock = vi.fn((input: RequestInfo | URL, _init?: RequestInit) => {
      const url = String(input)
      if (url.includes('/api/status')) return jsonResponse({ status: 'ok', rag: { documents: 263, chunks: 12528 } })
      if (url.includes('/api/training/status')) {
        trainingReads += 1
        return jsonResponse({ meshes: 26, case_groups: 18, balanced_accuracy: 0.576923, human_reviews_received: trainingReads > 1 ? 1 : 0, revalidations: trainingReads > 1 ? 1 : 0, new_unique_training_samples: 0, next_candidate_gate: { ready: false, minimum_new_unique_samples: 6, reason: 'SHA ya presente' }, promotion: 'NO_PROMOTION' })
      }
      if (url.includes('/api/agent/analyze-demo')) return jsonResponse(assessment)
      if (url.includes('/api/reviews/latest')) return jsonResponse({}, 404)
      if (url.endsWith('/api/reviews')) return jsonResponse({ review_id: 'REV-001', agent_was_correct: false, training_eligibility: 'REVALIDATION_EXISTING_HASH', new_training_sample: false, previous_system_output: assessment.agent_output, human_label: 'INCORRECTA', change_reason: 'Malla doble' }, 201)
      throw new Error(`URL inesperada ${url}`)
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<ReviewWorkspace />)
    fireEvent.change(screen.getByRole('combobox', { name: /función real/i }), { target: { value: 'implantologia_scanbody' } })
    fireEvent.click(screen.getByRole('button', { name: /analizar con agente/i }))
    await screen.findByText('CORRECTA')
    fireEvent.click(screen.getByRole('button', { name: 'incorrecta' }))
    fireEvent.change(screen.getByPlaceholderText(/escribe exactamente/i), { target: { value: 'Malla doble y scanbody defectuoso.' } })
    fireEvent.click(screen.getByRole('button', { name: /guardar revisión/i }))

    expect(await screen.findByText(/corrección guardada/i)).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText(/1 revalidación/i)).toBeInTheDocument())
    const reviewCall = fetchMock.mock.calls.find(call => String(call[0]).endsWith('/api/reviews'))
    expect(reviewCall).toBeTruthy()
    if (!reviewCall) throw new Error('No se envió la revisión')
    expect(JSON.parse(String(reviewCall[1]?.body)).judgment).toBe('INCORRECT')
    expect(JSON.parse(String(reviewCall[1]?.body))).not.toHaveProperty('reviewer')
  })

  it('analyzes the active daily case and exposes a clear human correction', async () => {
    const queueCase = {
      case_code: 'AIQ-E08F9059', daily_slot: 2, daily_total: 7,
      review_status: 'AWAITING_HUMAN_REVIEW',
      mesh_format: 'stl' as const, mesh_url: '/api/review-queue/AIQ-E08F9059/mesh', triangle_count: 346949,
    }
    const queueAssessment = { ...assessment, case_code: queueCase.case_code }
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/api/status')) return jsonResponse({ status: 'ok', rag: { documents: 263, chunks: 12528 } })
      if (url.includes('/api/training/status')) return jsonResponse({ meshes: 26, case_groups: 18, balanced_accuracy: 0.576923, human_reviews_received: 0, revalidations: 0, new_unique_training_samples: 0, next_candidate_gate: { ready: false, minimum_new_unique_samples: 6, reason: 'Faltan muestras' }, promotion: 'NO_PROMOTION' })
      if (url.includes('/api/reviews/latest')) return jsonResponse({}, 404)
      if (url.includes('/api/agent/analyze-queue/AIQ-E08F9059')) return jsonResponse(queueAssessment)
      if (url.endsWith('/api/reviews')) return jsonResponse({ ...rectification, previous_system_output: queueAssessment.agent_output }, 201)
      throw new Error(`URL inesperada ${url}`)
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<ReviewWorkspace queueCase={queueCase}/>)
    expect(await screen.findByText('Cola diaria 2/7')).toBeInTheDocument()
    fireEvent.change(screen.getByRole('combobox', { name: /función real/i }), { target: { value: 'antagonista' } })
    fireEvent.click(screen.getByRole('button', { name: /analizar con agente/i }))
    expect(await screen.findByRole('heading', { name: 'CORRECTA' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'incorrecta' }))
    fireEvent.change(screen.getByPlaceholderText(/escribe exactamente/i), { target: { value: 'Scanbody defectuoso.' } })
    fireEvent.click(screen.getByRole('button', { name: /guardar revisión/i }))

    expect(await screen.findByText(/el agente se equivocó/i)).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/agent/analyze-queue/AIQ-E08F9059',
      expect.objectContaining({ method: 'POST' }),
    )
  })

  it('loads the next continuous mesh only after an effective review', async () => {
    const queueCase = {
      case_code: 'AIQ-CURRENT', daily_slot: 4, daily_total: 0,
      review_status: 'COMPLETED',
      mesh_format: 'stl' as const, mesh_url: '/api/review-queue/AIQ-CURRENT/mesh', triangle_count: 100,
    }
    const nextCase = {
      case_code: 'AIQ-NEXT', daily_slot: 5, daily_total: 0,
      review_status: 'AWAITING_HUMAN_REVIEW',
      mesh_format: 'stl' as const, mesh_url: '/api/review-queue/AIQ-NEXT/mesh', triangle_count: 200,
    }
    const onQueueAdvanced = vi.fn()
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/api/status')) return jsonResponse({ status: 'ok', rag: { documents: 263, chunks: 12528 } })
      if (url.includes('/api/training/status')) return jsonResponse({ meshes: 26, case_groups: 18, balanced_accuracy: 0.576923, human_reviews_received: 4, revalidations: 0, new_unique_training_samples: 4, next_candidate_gate: { ready: false, minimum_new_unique_samples: 6, reason: 'Faltan muestras' }, promotion: 'NO_PROMOTION' })
      if (url.includes('/api/reviews/latest')) return jsonResponse(rectification)
      if (url.endsWith('/api/review-queue/next')) return jsonResponse({ case: nextCase }, 201)
      throw new Error(`URL inesperada ${url}`)
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<ReviewWorkspace queueCase={queueCase} onQueueAdvanced={onQueueAdvanced}/>)
    fireEvent.click(await screen.findByRole('button', { name: /siguiente malla/i }))

    await waitFor(() => expect(onQueueAdvanced).toHaveBeenCalledWith(nextCase))
    expect(fetchMock).toHaveBeenCalledWith('/api/review-queue/next', expect.objectContaining({ method: 'POST' }))
  })

  it('discards a late queue advance after the visible mesh changes', async () => {
    const queueCase = {
      case_code: 'AIQ-CURRENT', daily_slot: 4, daily_total: 0,
      review_status: 'COMPLETED', mesh_format: 'stl' as const,
      mesh_url: '/api/review-queue/AIQ-CURRENT/mesh', triangle_count: 100,
    }
    const nextCase = {
      case_code: 'AIQ-LATE', daily_slot: 5, daily_total: 0,
      review_status: 'AWAITING_HUMAN_REVIEW', mesh_format: 'stl' as const,
      mesh_url: '/api/review-queue/AIQ-LATE/mesh', triangle_count: 200,
    }
    let resolveAdvance!: (response: Response) => void
    const pendingAdvance = new Promise<Response>(resolve => { resolveAdvance = resolve })
    const onQueueAdvanced = vi.fn()
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/api/status')) return jsonResponse({ status: 'ok', rag: { documents: 1, chunks: 1 } })
      if (url.includes('/api/training/status')) return jsonResponse({ meshes: 0, case_groups: 0, balanced_accuracy: 0, human_reviews_received: 1, revalidations: 0, new_unique_training_samples: 1, next_candidate_gate: { ready: false, minimum_new_unique_samples: 6, reason: 'Faltan muestras' }, promotion: 'NO_PROMOTION' })
      if (url.includes('/api/reviews/latest')) return jsonResponse(rectification)
      if (url.endsWith('/api/review-queue/next')) return pendingAdvance
      throw new Error(`URL inesperada ${url}`)
    }))

    const { rerender } = render(<ReviewWorkspace queueCase={queueCase} onQueueAdvanced={onQueueAdvanced} meshRevisionKey="queue:current" />)
    fireEvent.click(await screen.findByRole('button', { name: /siguiente malla/i }))
    const localMesh = new File(['solid local\nendsolid local'], 'local.stl', { type: 'model/stl' })
    rerender(<ReviewWorkspace selectedMeshFile={localMesh} queueCase={null} onQueueAdvanced={onQueueAdvanced} meshRevisionKey="upload:1" />)
    await act(async () => {
      resolveAdvance(new Response(JSON.stringify({ case: nextCase }), {
        status: 201, headers: { 'Content-Type': 'application/json' },
      }))
      await pendingAdvance
      await Promise.resolve()
    })
    expect(onQueueAdvanced).not.toHaveBeenCalled()
  })

  it('invalidates a completed analysis when the visible RAG question changes', async () => {
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/api/status')) return jsonResponse({ status: 'ok', rag: { documents: 1, chunks: 1 } })
      if (url.includes('/api/training/status')) return jsonResponse({ meshes: 0, case_groups: 0, balanced_accuracy: 0, human_reviews_received: 0, revalidations: 0, new_unique_training_samples: 0, next_candidate_gate: { ready: false, minimum_new_unique_samples: 6, reason: 'Faltan muestras' }, promotion: 'NO_PROMOTION' })
      if (url.includes('/api/reviews/latest')) return jsonResponse({}, 404)
      if (url.includes('/api/agent/analyze-demo')) return jsonResponse(assessment)
      throw new Error(`URL inesperada ${url}`)
    }))
    render(<ReviewWorkspace />)
    fireEvent.change(screen.getByRole('combobox', { name: /función real/i }), { target: { value: 'antagonista' } })
    fireEvent.click(screen.getByRole('button', { name: /analizar con agente/i }))
    await screen.findByRole('heading', { name: 'CORRECTA' })
    fireEvent.change(screen.getByRole('textbox', { name: /consulta rag/i }), { target: { value: 'Consulta diferente' } })
    expect(screen.queryByRole('heading', { name: 'CORRECTA' })).not.toBeInTheDocument()
  })

  it('locks the visible decision while its review is being saved', async () => {
    const queueCase = { case_code: 'AIQ-LOCK', daily_slot: 1, daily_total: 0, review_status: 'AWAITING_HUMAN_REVIEW', mesh_format: 'stl' as const, mesh_url: '/mesh', triangle_count: 10 }
    let resolveSave!: (value: Response) => void
    const pendingSave = new Promise<Response>(resolve => { resolveSave = resolve })
    let reviewPosts = 0
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/api/status')) return jsonResponse({ status: 'ok', rag: { documents: 1, chunks: 1 } })
      if (url.includes('/api/training/status')) return jsonResponse({ meshes: 0, case_groups: 0, balanced_accuracy: 0, human_reviews_received: 0, revalidations: 0, new_unique_training_samples: 0, next_candidate_gate: { ready: false, minimum_new_unique_samples: 6, reason: 'Faltan muestras' }, promotion: 'NO_PROMOTION' })
      if (url.includes('/api/reviews/latest')) return jsonResponse({}, 404)
      if (url.includes('/api/agent/analyze-queue')) return jsonResponse({ ...assessment, case_code: 'AIQ-LOCK' })
      if (url.endsWith('/api/reviews')) {
        reviewPosts += 1
        return reviewPosts === 1
          ? pendingSave
          : jsonResponse({ ...rectification, case_code: 'AIQ-LOCK', human_label: 'INCORRECTA', agent_was_correct: false })
      }
      throw new Error(`URL inesperada ${url}`)
    }))
    render(<ReviewWorkspace queueCase={queueCase} onQueueAdvanced={vi.fn()} />)
    fireEvent.change(screen.getByRole('combobox', { name: /función real/i }), { target: { value: 'antagonista' } })
    fireEvent.click(screen.getByRole('button', { name: /analizar con agente/i }))
    await screen.findByRole('heading', { name: 'CORRECTA' })
    fireEvent.click(screen.getByRole('button', { name: 'correcta' }))
    fireEvent.click(screen.getByRole('button', { name: /guardar revisión/i }))
    expect(screen.getByRole('button', { name: 'incorrecta' })).toBeDisabled()
    expect(screen.getByPlaceholderText(/escribe exactamente/i)).toBeDisabled()
    const functionSelector = screen.getByRole('combobox', { name: /función real/i })
    expect(functionSelector).toBeDisabled()
    fireEvent.change(functionSelector, { target: { value: 'implantologia_scanbody' } })
    expect(functionSelector).toHaveValue('antagonista')
    const questionInput = screen.getByRole('textbox', { name: /consulta rag/i })
    const savedQuestion = questionInput.getAttribute('value') ?? (questionInput as HTMLTextAreaElement).value
    expect(questionInput).toBeDisabled()
    fireEvent.change(questionInput, { target: { value: 'Consulta intrusa' } })
    expect(questionInput).toHaveValue(savedQuestion)
    fireEvent.click(screen.getByRole('button', { name: 'incorrecta' }))
    expect(screen.getByRole('button', { name: 'correcta' })).toHaveClass('active')
    const notesInput = screen.getByPlaceholderText(/escribe exactamente/i)
    fireEvent.change(notesInput, { target: { value: 'Notas intrusas' } })
    expect(notesInput).toHaveValue('')
    await act(async () => {
      resolveSave(new Response(JSON.stringify({ ...rectification, case_code: 'AIQ-LOCK' }), { status: 201, headers: { 'Content-Type': 'application/json' } }))
      await pendingSave
    })
    expect(screen.getByRole('button', { name: 'correcta' })).toHaveClass('active')
    expect(screen.getByRole('button', { name: /siguiente malla/i })).toBeEnabled()
    fireEvent.click(screen.getByRole('button', { name: 'incorrecta' }))
    expect(screen.queryByRole('button', { name: /siguiente malla/i })).not.toBeInTheDocument()
    fireEvent.change(screen.getByPlaceholderText(/escribe exactamente/i), { target: { value: 'Nueva corrección persistible' } })
    fireEvent.click(screen.getByRole('button', { name: /guardar revisión/i }))
    expect(await screen.findByRole('button', { name: /siguiente malla/i })).toBeEnabled()
    fireEvent.change(screen.getByPlaceholderText(/escribe exactamente/i), { target: { value: 'Cambio posterior sin guardar' } })
    expect(screen.queryByRole('button', { name: /siguiente malla/i })).not.toBeInTheDocument()
  })
})
