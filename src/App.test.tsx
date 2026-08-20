// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest'
import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('./MeshViewer', () => ({ MeshViewer: ({ source }: { source?: { url: string } }) => <div data-testid="mesh-viewer" data-source-url={source?.url}>Visor 3D real</div> }))
vi.mock('./ReviewWorkspace', () => ({ ReviewWorkspace: ({ queueCase }: { queueCase?: { case_code: string } }) => <div data-testid="review-workspace">{queueCase?.case_code ?? 'demo'}</div> }))
import App from './App'

function jsonResponse(body: unknown) {
  return Promise.resolve(new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } }))
}

describe('App shell', () => {
  afterEach(() => vi.restoreAllMocks())
  it('shows a synthetic non-clinical demo and local-first safeguards', () => {
    render(<App/>)
    expect(screen.getByText('AbutmentIQ')).toBeInTheDocument()
    expect(screen.getAllByText('AIQ-DEMO-SYNTHETIC')).toHaveLength(3)
    expect(screen.getByText('DEMOSTRACIÓN SINTÉTICA · SIN DATOS CLÍNICOS')).toBeInTheDocument()
    expect(screen.queryByText(/SHA-256 FUENTE/i)).not.toBeInTheDocument()
    expect(screen.getByText('SISTEMA LOCAL')).toBeInTheDocument()
    expect(screen.getByText('NEVER_REPEAT')).toBeInTheDocument()
    expect(screen.getByTestId('mesh-viewer')).toBeInTheDocument()
  })

  it('shows the daily queue case in the main viewer', async () => {
    const queueCase = {
      case_code: 'AIQ-E08F9059', daily_slot: 2, daily_total: 7,
      review_status: 'AWAITING_HUMAN_REVIEW',
      mesh_format: 'stl', mesh_url: '/api/review-queue/AIQ-E08F9059/mesh', triangle_count: 346949,
    }
    vi.stubGlobal('fetch', vi.fn(() => jsonResponse({ cases: [queueCase] })))

    render(<App/>)

    expect((await screen.findAllByText('AIQ-E08F9059')).length).toBeGreaterThanOrEqual(2)
    expect(screen.getByText('COLA DIARIA · 2/7')).toBeInTheDocument()
    expect(screen.getByTestId('mesh-viewer')).toHaveAttribute('data-source-url', queueCase.mesh_url)
    expect(screen.getByTestId('review-workspace')).toHaveTextContent('AIQ-E08F9059')
  })

  it('selects the newest pending case instead of a completed first case', async () => {
    const completed = {
      case_code: 'AIQ-FIRST', daily_slot: 1, daily_total: 0, review_status: 'COMPLETED',
      mesh_format: 'stl', mesh_url: '/api/review-queue/AIQ-FIRST/mesh', triangle_count: 100,
    }
    const pending = {
      case_code: 'AIQ-SECOND', daily_slot: 2, daily_total: 0, review_status: 'AWAITING_HUMAN_REVIEW',
      mesh_format: 'stl', mesh_url: '/api/review-queue/AIQ-SECOND/mesh', triangle_count: 200,
    }
    vi.stubGlobal('fetch', vi.fn(() => jsonResponse({ cases: [completed, pending] })))
    render(<App/>)
    expect(await screen.findByTestId('review-workspace')).toHaveTextContent('AIQ-SECOND')
    expect(screen.getByTestId('mesh-viewer')).toHaveAttribute('data-source-url', pending.mesh_url)
  })
})
