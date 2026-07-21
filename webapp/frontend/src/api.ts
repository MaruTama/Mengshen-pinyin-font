import { ApiError } from './i18n/apiError'
import type {
  Canvas,
  GlyphDetail,
  GlyphPage,
  PreviewDetail,
  PreviewResponse,
  Project,
  TaskState,
} from './types'

export async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    let detail: unknown
    try {
      detail = (await res.json()).detail
    } catch {
      /* not json */
    }
    throw new ApiError(detail as never, res.statusText)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const api = {
  health: () => request<{ status: string; missing_tools: string[] }>('/api/health'),
  builtinFonts: () => request<{ fonts: Record<string, BuiltinFont> }>('/api/builtin-fonts'),

  listProjects: () => request<Project[]>('/api/projects'),
  createProject: (name: string) =>
    request<Project>('/api/projects', { method: 'POST', body: JSON.stringify({ name }) }),
  getProject: (id: string) => request<Project>(`/api/projects/${id}`),
  patchProject: (id: string, patch: Partial<{ name: string; step: string; canvas: Canvas; output: Project['output'] }>) =>
    request<Project>(`/api/projects/${id}`, { method: 'PATCH', body: JSON.stringify(patch) }),
  deleteProject: (id: string) =>
    request<void>(`/api/projects/${id}`, { method: 'DELETE' }),

  selectBuiltin: (id: string, role: 'base' | 'pinyin', style: string) =>
    request<Project>(`/api/projects/${id}/fonts/${role}/builtin`, {
      method: 'PUT',
      body: JSON.stringify({ style }),
    }),
  uploadFont: async (id: string, role: 'base' | 'pinyin', file: File) => {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`/api/projects/${id}/fonts/${role}`, {
      method: 'POST',
      body: form,
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new ApiError(body.detail, res.statusText)
    }
    return res.json() as Promise<Project>
  },
  acknowledgeLicense: (id: string, role: 'base' | 'pinyin', acknowledged: boolean) =>
    request<Project>(`/api/projects/${id}/license/acknowledge`, {
      method: 'POST',
      body: JSON.stringify({ role, acknowledged }),
    }),

  preview: (id: string, text: string, canvas: Canvas | null, signal?: AbortSignal) =>
    request<PreviewResponse>(`/api/projects/${id}/preview`, {
      method: 'POST',
      body: JSON.stringify({ text, canvas }),
      signal,
    }),
  previewDetail: (id: string, char: string, canvas: Canvas | null, signal?: AbortSignal) =>
    request<PreviewDetail>(`/api/projects/${id}/preview/detail`, {
      method: 'POST',
      body: JSON.stringify({ char, canvas }),
      signal,
    }),

  listGlyphs: (id: string, params: { q?: string; category?: string; page?: number; size?: number }) => {
    const search = new URLSearchParams()
    if (params.q) search.set('q', params.q)
    if (params.category) search.set('category', params.category)
    search.set('page', String(params.page ?? 1))
    search.set('size', String(params.size ?? 200))
    return request<GlyphPage>(`/api/projects/${id}/glyphs?${search}`)
  },
  glyphDetail: (id: string, name: string) =>
    request<GlyphDetail>(`/api/projects/${id}/glyphs/${encodeURIComponent(name)}`),

  startPrepare: (id: string) =>
    request<TaskState>(`/api/projects/${id}/prepare`, { method: 'POST' }),
  startBuild: (id: string) =>
    request<TaskState>(`/api/projects/${id}/build`, { method: 'POST' }),
  taskState: (id: string, kind: 'prepare' | 'build') =>
    request<TaskState>(`/api/projects/${id}/tasks/${kind}`),
}

export interface BuiltinFont {
  style: string
  label: string
  base_path: string
  pinyin_path: string
  base_family: string | null
  pinyin_family: string | null
  base_name_renderable: boolean
  pinyin_name_renderable: boolean
  default_canvas: Canvas
}
