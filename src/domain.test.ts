import { describe, expect, it } from 'vitest'
import { assessCandidates, gate23Metrics, isNovelHash, recordReview } from './domain'

describe('assessCandidates', () => {
  it('abstains when the two best candidates collide geometrically', () => {
    const result = assessCandidates([
      { id: 'A', score: 0.94, collisionUm: 4 },
      { id: 'B', score: 0.93, collisionUm: 4 },
      { id: 'C', score: 0.72, collisionUm: 180 },
    ])
    expect(result.status).toBe('AMBIGUO')
    expect(result.confirmedId).toBeNull()
  })

  it('rejects weak evidence instead of forcing a label', () => {
    const result = assessCandidates([{ id: 'A', score: 0.58, collisionUm: 210 }])
    expect(result.status).toBe('RECHAZO')
    expect(result.confirmedId).toBeNull()
  })
})

describe('Gate 2.3 metrics', () => {
  it('reports decided accuracy separately from total coverage', () => {
    expect(gate23Metrics()).toEqual({
      total: 18,
      decided: 6,
      correctDecided: 5,
      accuracyDecided: 83.3,
      coverage: 33.3,
      ambiguous: 4,
      rejected: 8,
      confidentErrors: 1,
    })
  })
})

describe('append-only human review', () => {
  it('blocks a source SHA-256 that was already reviewed', () => {
    expect(isNovelHash('abc', ['abc'])).toBe(false)
    expect(isNovelHash('def', ['abc'])).toBe(true)
  })

  it('creates a new immutable record without mutating history', () => {
    const history = [{ reviewId: 'old' }]
    const next = recordReview(history, {
      sourceSha256: 'new-sha',
      functionalClass: 'implantologia_scanbody',
      verdict: 'correcta',
      notes: 'Scanbody presente',
    }, '2026-08-18T10:00:00.000Z')
    expect(history).toEqual([{ reviewId: 'old' }])
    expect(next).toHaveLength(2)
    expect(next[1]).toMatchObject({ sourceSha256: 'new-sha', policy: 'NEVER_REPEAT_SOURCE_SHA256' })
  })
})
