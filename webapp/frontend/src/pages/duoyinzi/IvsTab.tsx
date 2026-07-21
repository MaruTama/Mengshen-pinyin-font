import { useQuery } from '@tanstack/react-query'
import { Search } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { request } from '../../api'
import { Badge, Button, Input, Spinner } from '../../components/ui'
import type { IvsRow } from '../../types'
import { useDebouncedPagedSearch } from '../../useDebouncedPagedSearch'
import { useProject } from '../ProjectLayout'

export function IvsTab() {
  const { projectId } = useProject()
  const { t } = useTranslation()
  const { query, setQuery, debounced, page, setPage } = useDebouncedPagedSearch()
  const [homographsOnly, setHomographsOnly] = useState(true)

  const data = useQuery({
    queryKey: ['ivs', projectId, debounced, homographsOnly, page],
    queryFn: () =>
      request<{ total: number; items: IvsRow[] }>(
        `/api/projects/${projectId}/ivs?q=${encodeURIComponent(debounced)}&homographs_only=${homographsOnly}&page=${page}&size=30`,
      ),
    placeholderData: (prev) => prev,
  })

  const totalPages = data.data ? Math.max(1, Math.ceil(data.data.total / 30)) : 1

  return (
    <div className="flex-1 overflow-y-auto px-6 py-4">
      <div className="mb-4 flex items-center gap-4">
        <div className="relative max-w-xs flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-600" />
          <Input
            className="pl-9"
            placeholder={t('duoyinzi.ivs.searchPlaceholder')}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-400">
          <input
            type="checkbox"
            className="h-4 w-4 accent-indigo-500"
            checked={homographsOnly}
            onChange={(e) => {
              setHomographsOnly(e.target.checked)
              setPage(1)
            }}
          />
          {t('duoyinzi.ivs.homographsOnly')}
        </label>
        <span className="ml-auto text-xs text-slate-500">
          {data.data &&
            t('duoyinzi.ivs.assignedCount', {
              count: data.data.total.toLocaleString(),
            })}
        </span>
        {data.isFetching && <Spinner />}
      </div>

      <p className="mb-3 text-xs leading-relaxed text-slate-600">
        {t('duoyinzi.ivs.note')}
      </p>

      <div className="overflow-hidden rounded-xl border border-line">
        <table className="w-full text-sm">
          <thead className="bg-surface-raised text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">{t('duoyinzi.ivs.colChar')}</th>
              <th className="px-4 py-3">{t('duoyinzi.ivs.colGlyph')}</th>
              <th className="px-4 py-3">{t('duoyinzi.ivs.colSequence')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {data.data?.items.map((row) => (
              <tr key={row.char} className="align-top hover:bg-surface-raised/50">
                <td className="px-4 py-3 text-2xl text-slate-100">{row.char}</td>
                <td className="px-4 py-3 font-mono text-xs text-slate-500">
                  {row.glyph}
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1.5">
                    {row.sequences.map((seq) => (
                      <span
                        key={seq.selector}
                        className="inline-flex items-center gap-1.5 rounded-md border border-line bg-surface px-2 py-1 text-xs"
                        title={seq.description}
                      >
                        <span className="font-mono text-slate-400">
                          {row.char}
                          <span className="text-accent-hover">+{seq.selector}</span>
                        </span>
                        <span className="text-slate-700">→</span>
                        {seq.reading ? (
                          <Badge tone="success">{seq.reading}</Badge>
                        ) : (
                          <Badge>{t('duoyinzi.noPinyin')}</Badge>
                        )}
                      </span>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="mt-4 flex items-center justify-center gap-4 text-sm">
          <Button variant="ghost" disabled={page <= 1} onClick={() => setPage(page - 1)}>
            {t('common.prev')}
          </Button>
          <span className="text-slate-500">
            {page} / {totalPages}
          </span>
          <Button
            variant="ghost"
            disabled={page >= totalPages}
            onClick={() => setPage(page + 1)}
          >
            {t('common.next')}
          </Button>
        </div>
      )}
    </div>
  )
}
