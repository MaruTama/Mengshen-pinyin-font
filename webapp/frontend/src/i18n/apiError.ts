import i18n from './index'

type StructuredDetail = {
  code?: string
  message?: string
  params?: Record<string, unknown>
}
type Detail = string | StructuredDetail | undefined

// Translate an API error `detail` into a localized message. The backend
// sends { code, message, params } for known errors; we map the code to an
// errors.* key and fall back to the English message, then to statusText.
export function apiErrorMessage(detail: Detail, statusText = ''): string {
  if (detail && typeof detail === 'object' && detail.code) {
    const params: Record<string, unknown> = { ...detail.params }
    // The `role` param is itself a translatable token (base/pinyin)
    if (typeof params.role === 'string') {
      params.role = i18n.t(`errors.role.${params.role}`, params.role)
    }
    return i18n.t(`errors.${detail.code}`, {
      ...params,
      defaultValue: detail.message ?? '',
    })
  }
  if (typeof detail === 'string') return detail
  return statusText || i18n.t('errors.unknown')
}

// An Error whose message is re-translatable: `.message` is a snapshot at
// throw time (for console/log use), but `.detail`/`.statusText` let
// displayError() re-run the translation later — necessary because thrown
// errors end up frozen in React Query error state or component state, and
// a plain string wouldn't follow a later language switch.
export class ApiError extends Error {
  detail: Detail
  statusText: string

  constructor(detail: Detail, statusText = '') {
    super(apiErrorMessage(detail, statusText))
    this.name = 'ApiError'
    this.detail = detail
    this.statusText = statusText
  }
}

// Render-time error message: re-translates ApiError from its raw detail
// so displayed errors follow language switches, unlike `error.message`.
export function displayError(error: unknown): string {
  if (error instanceof ApiError) return apiErrorMessage(error.detail, error.statusText)
  if (error instanceof Error) return error.message
  return String(error)
}
