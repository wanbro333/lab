export class ApiError extends Error {
  constructor(message, status, errors = {}) {
    super(message)
    this.status = status
    this.errors = errors
  }
}

export async function request(path, options = {}) {
  const method = options.method || 'GET'
  const headers = { ...options.headers }
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'
  if (!['GET', 'HEAD'].includes(method)) {
    const csrf = await request('/auth/csrf/')
    headers['X-CSRFToken'] = csrf.csrfToken
  }
  let response
  try {
    response = await fetch(`/api${path}`, {
      ...options,
      headers,
      credentials: 'same-origin',
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: options.signal || AbortSignal.timeout(10000),
    })
  } catch (error) {
    if (error.name === 'AbortError') throw error
    throw new ApiError('暂时连接不到服务，请确认服务已启动后重试。', 0)
  }
  const data = await response.json().catch(() => ({}))
  if (!response.ok)
    throw new ApiError(data.message || '请求未完成，请稍后重试。', response.status, data.errors)
  return data
}
