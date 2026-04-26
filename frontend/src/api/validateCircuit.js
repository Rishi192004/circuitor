/**
 * POST the already-translated backend Circuit JSON to the FastAPI endpoint.
 * Returns the raw PipelineResult object on success.
 * Throws a descriptive Error on network or server failure.
 */
export async function validateCircuit(backendPayload) {
  const response = await fetch('/api/run_pipeline', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(backendPayload),
  })

  if (!response.ok) {
    let detail = `HTTP ${response.status}`
    try {
      const err = await response.json()
      detail = err.detail ?? detail
    } catch { /* ignore parse error */ }
    throw new Error(detail)
  }

  return response.json()
}
