export type Candidate = { id: string; score: number; collisionUm: number }
export type CandidateAssessment = {
  status: 'CANDIDATO' | 'AMBIGUO' | 'RECHAZO'
  confirmedId: null
  reason: string
}

export function assessCandidates(candidates: Candidate[]): CandidateAssessment {
  const ranked = [...candidates].sort((a, b) => b.score - a.score)
  const top = ranked[0]
  const second = ranked[1]
  if (!top || top.score < 0.75) {
    return { status: 'RECHAZO', confirmedId: null, reason: 'Evidencia geométrica insuficiente' }
  }
  if (second && (top.score - second.score < 0.03 || Math.min(top.collisionUm, second.collisionUm) <= 10)) {
    return { status: 'AMBIGUO', confirmedId: null, reason: 'Candidatos indistinguibles bajo el método' }
  }
  return { status: 'CANDIDATO', confirmedId: null, reason: 'Requiere CAD autorizado y confirmación humana' }
}

export function gate23Metrics() {
  return {
    total: 18,
    decided: 6,
    correctDecided: 5,
    accuracyDecided: 83.3,
    coverage: 33.3,
    ambiguous: 4,
    rejected: 8,
    confidentErrors: 1,
  }
}

export function isNovelHash(sourceSha256: string, reviewedHashes: string[]) {
  return !reviewedHashes.includes(sourceSha256)
}

type ReviewInput = {
  sourceSha256: string
  functionalClass: string
  verdict: string
  notes: string
}

type ReviewRecord = Record<string, unknown> & { reviewId: string }

export function recordReview(history: ReviewRecord[], input: ReviewInput, timestamp: string): ReviewRecord[] {
  if (!isNovelHash(input.sourceSha256, history.map(item => String(item.sourceSha256 ?? '')))) {
    throw new Error('NEVER_REPEAT_SOURCE_SHA256')
  }
  const suffix = input.sourceSha256.slice(0, 8).toUpperCase()
  const record: ReviewRecord = {
    reviewId: `HR-${suffix}-${timestamp.replaceAll(/[-:.TZ]/g, '').slice(0, 14)}`,
    timestamp,
    ...input,
    policy: 'NEVER_REPEAT_SOURCE_SHA256',
    evidenceLevel: 'HUMAN_LABEL',
    stableModelChanged: false,
  }
  return [...history, Object.freeze(record)]
}
