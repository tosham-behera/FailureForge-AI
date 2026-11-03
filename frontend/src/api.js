// Vite can return an empty/non-JSON error when the backend is unavailable.
export async function requestJson(url, options) {
  let response
  try {
    response = await fetch(url, options)
  } catch {
    throw new Error('Cannot reach the API. Check that FastAPI is running on port 8000 and Vite on port 5173.')
  }
  const text = await response.text()
  const context = `API request failed (HTTP ${response.status}).`
  if (!text.trim()) {
    throw new Error(`${context} Empty response. Check that FastAPI is running on port 8000.`)
  }
  let data
  try {
    data = JSON.parse(text)
  } catch {
    throw new Error(`${context} Invalid JSON response. Check the backend and Vite proxy.`)
  }
  if (!response.ok) {
    const detail = typeof data?.detail === 'string' ? data.detail : 'Check your input and backend server.'
    throw new Error(`${context} ${detail}`)
  }
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    throw new Error('The API returned an invalid response object.')
  }
  return data
}
