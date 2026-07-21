import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { request } from '../../api'
import { Badge, Button, Card, Input, Spinner } from '../../components/ui'
import { displayError } from '../../i18n/apiError'
import type { SimChar, VerifyReport } from '../../types'
import { useProject } from '../ProjectLayout'

const STATUS_TONE = {
  ok: 'success',
  fallback: 'warning',
  wrong: 'error',
} as const

const STATUS_TEXT = {
  ok: 'text-emerald-400',
  fallback: 'text-amber-400',
  wrong: 'text-rose-400',
} as const

export function VerifyTab() {
  const { projectId } = useProject()
  const { t } = useTranslation()
  const [text, setText] = useState('背着手')
  const [filter, setFilter] = useState<'all' | 'ok' | 'fallback' | 'wrong'>('wrong')

  const simulate = useMutation({
    mutationFn: (value: string) =>
      request<{ text: string; chars: SimChar[] }>(
        `/api/projects/${projectId}/gsub/simulate`,
        { method: 'POST', body: JSON.stringify({ text: value }) },
      ),
  })

  const verify = useMutation({
    mutationFn: () => request<VerifyReport>(`/api/projects/${projectId}/gsub/verify`),
  })

  const filtered =
    verify.data?.results.filter((r) => filter === 'all' || r.status === filter) ?? []
  const shown = filtered.slice(0, 300)

  return (
    <div className="flex-1 space-y-6 overflow-y-auto px-6 py-4">
      <Card title={t('duoyinzi.verify.simTitle')}>
        <p className="mb-3 text-xs leading-relaxed text-slate-600">
          {t('duoyinzi.verify.simNote')}
        </p>
        <div className="flex gap-2">
          <Input
            className="max-w-[14rem]"
            value={text}
            placeholder={t('duoyinzi.verify.simPlaceholder')}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && text.trim()) simulate.mutate(text.trim())
            }}
          />
          <Button
            disabled={!text.trim() || simulate.isPending}
            onClick={() => simulate.mutate(text.trim())}
          >
            {t('duoyinzi.verify.simRun')}
          </Button>
          {simulate.isPending && <Spinner />}
        </div>
        {simulate.isError && (
          <p className="mt-3 text-sm text-rose-400">{displayError(simulate.error)}</p>
        )}
        {simulate.data && (
          <div className="mt-4 flex flex-wrap gap-3">
            {simulate.data.chars.map((row, index) => {
              const substituted = row.applied.some((a) => a.to)
              const ignored = row.applied.some((a) => a.ignored)
              return (
                <div
                  key={`${row.char}-${index}`}
                  className={`min-w-[9rem] rounded-xl border p-3 ${
                    substituted
                      ? 'border-accent/50 bg-accent/5'
                      : ignored
                        ? 'border-rose-500/40 bg-rose-500/5'
                        : 'border-line bg-surface-raised'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-3xl text-slate-100">{row.char}</span>
                    {row.reading ? (
                      <Badge tone={substituted ? 'accent' : 'default'}>
                        {row.reading}
                      </Badge>
                    ) : (
                      <Badge>—</Badge>
                    )}
                  </div>
                  <div className="mt-2 space-y-0.5 text-[11px] text-slate-500">
                    {row.applied.length === 0 && <p>{t('duoyinzi.verify.noRule')}</p>}
                    {row.applied.map((a, applyIndex) => (
                      <p key={applyIndex} className="font-mono">
                        {a.ignored ? (
                          <span className="text-rose-400">
                            {a.lookup.replace('lookup_', '')} #{a.rule}:{' '}
                            {t('duoyinzi.verify.ignored')}
                          </span>
                        ) : (
                          <>
                            {a.lookup.replace('lookup_', '')} #{a.rule} →{' '}
                            {a.sub_lookup?.replace('lookup_', '')}
                          </>
                        )}
                      </p>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </Card>

      <Card title={t('duoyinzi.verify.batchTitle')}>
        <p className="mb-3 text-xs leading-relaxed text-slate-600">
          {t('duoyinzi.verify.batchNote')}
        </p>
        <div className="flex items-center gap-3">
          <Button disabled={verify.isPending} onClick={() => verify.mutate()}>
            {verify.isPending ? t('duoyinzi.verify.running') : t('duoyinzi.verify.run')}
          </Button>
          {verify.isPending && <Spinner />}
          {verify.data && (
            <div className="flex gap-1.5">
              <button onClick={() => setFilter('all')}>
                <Badge tone={filter === 'all' ? 'accent' : 'default'}>
                  {t('duoyinzi.verify.all', { count: verify.data.total })}
                </Badge>
              </button>
              {(['ok', 'fallback', 'wrong'] as const).map((status) => (
                <button key={status} onClick={() => setFilter(status)}>
                  <Badge
                    tone={filter === status ? STATUS_TONE[status] : 'default'}
                    title={t(`duoyinzi.verify.statusHint.${status}`)}
                  >
                    {t('duoyinzi.verify.filterLabel', {
                      label: t(`duoyinzi.verify.status.${status}`),
                      count: verify.data!.counts[status],
                    })}
                  </Badge>
                </button>
              ))}
            </div>
          )}
        </div>
        {verify.isError && (
          <p className="mt-3 text-sm text-rose-400">{displayError(verify.error)}</p>
        )}

        {verify.data && (
          <div className="mt-4 overflow-hidden rounded-xl border border-line">
            <table className="w-full text-sm">
              <thead className="bg-surface-raised text-left text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-2.5">{t('duoyinzi.verify.colPhrase')}</th>
                  <th className="px-4 py-2.5">{t('duoyinzi.verify.colSource')}</th>
                  <th className="px-4 py-2.5">{t('duoyinzi.verify.colDetail')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {shown.map((row) => (
                  <tr key={row.phrase} className="align-top">
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-2">
                        <Badge
                          tone={STATUS_TONE[row.status]}
                          title={t(`duoyinzi.verify.statusHint.${row.status}`)}
                        >
                          {t(`duoyinzi.verify.status.${row.status}`)}
                        </Badge>
                        <span className="text-lg text-slate-100">{row.phrase}</span>
                      </div>
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs text-slate-500">
                      {row.source}
                    </td>
                    <td className="px-4 py-2.5">
                      <div className="flex flex-wrap gap-2">
                        {row.chars.map((c, charIndex) => (
                          <span
                            key={charIndex}
                            className="rounded-md bg-surface px-2 py-1 text-xs"
                            title={t('duoyinzi.verify.expectedActual', {
                              expected: c.expected,
                              actual: c.actual ?? '—',
                            })}
                          >
                            <span className="mr-1 text-base text-slate-200">
                              {c.char}
                            </span>
                            {c.status === 'ok' ? (
                              <span className={STATUS_TEXT.ok}>{c.actual}</span>
                            ) : (
                              <span className={STATUS_TEXT[c.status]}>
                                {c.expected} → {c.actual ?? '—'}
                              </span>
                            )}
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filtered.length > shown.length && (
              <p className="border-t border-line px-4 py-2 text-xs text-slate-500">
                {t('duoyinzi.verify.truncated', {
                  shown: shown.length,
                  total: filtered.length,
                })}
              </p>
            )}
          </div>
        )}
      </Card>
    </div>
  )
}
