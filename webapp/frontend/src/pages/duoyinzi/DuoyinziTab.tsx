import { useQuery } from '@tanstack/react-query'
import { Search } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { request } from '../../api'
import { Badge, Button, Input, Spinner } from '../../components/ui'
import type { DuoyinziDetail, DuoyinziRow, PhrasePattern } from '../../types'
import { useDebouncedPagedSearch } from '../../useDebouncedPagedSearch'
import { useProject } from '../ProjectLayout'
import { SS_COLORS } from './colors'

export function DuoyinziTab() {
  const { projectId } = useProject()
  const { t } = useTranslation()
  const { query, setQuery, debounced, page, setPage } = useDebouncedPagedSearch()
  const [selected, setSelected] = useState<string | null>(null)

  const data = useQuery({
    queryKey: ['duoyinzi', projectId, debounced, page],
    queryFn: () =>
      request<{ total: number; items: DuoyinziRow[] }>(
        `/api/projects/${projectId}/duoyinzi?q=${encodeURIComponent(debounced)}&page=${page}&size=30`,
      ),
    placeholderData: (prev) => prev,
  })

  const totalPages = data.data ? Math.max(1, Math.ceil(data.data.total / 30)) : 1

  return (
    <div className="flex flex-1 overflow-hidden">
      <div className="flex-1 overflow-y-auto px-6 py-4">
      <div className="mb-4 flex items-center gap-3">
        <div className="relative max-w-xs flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-600" />
          <Input
            className="pl-9"
            placeholder={t('duoyinzi.list.searchPlaceholder')}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <span className="text-xs text-slate-500">
          {data.data
            ? t('duoyinzi.list.supportedCount', { count: data.data.total })
            : ''}
        </span>
        {data.isFetching && <Spinner />}
      </div>

      <div className="overflow-hidden rounded-xl border border-line">
        <table className="w-full text-sm">
          <thead className="bg-surface-raised text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">{t('duoyinzi.list.colChar')}</th>
              <th className="px-4 py-3">{t('duoyinzi.list.colReading')}</th>
              <th className="px-4 py-3">{t('duoyinzi.list.colPattern')}</th>
              <th className="px-4 py-3">{t('duoyinzi.list.colPhrases')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {data.data?.items.map((row) => (
              <tr
                key={row.char}
                onClick={() => setSelected(row.char)}
                className={`cursor-pointer align-top transition-colors ${
                  selected === row.char
                    ? 'bg-accent/10'
                    : 'hover:bg-surface-raised/50'
                }`}
              >
                <td className="px-4 py-3 text-2xl text-slate-100">{row.char}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1.5">
                    {row.readings.map((r, i) => (
                      <Badge key={r} tone={i === 0 ? 'success' : 'accent'}>
                        {r}
                      </Badge>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="space-y-1.5">
                    {row.pattern_one.map((p) => (
                      <div key={p.index} className="text-xs">
                        <span className="mr-2 font-medium text-accent-hover">{p.pinyin}</span>
                        <span className="text-slate-400">
                          {p.phrases.slice(0, 6).join('、')}
                          {p.phrases.length > 6 &&
                            t('duoyinzi.list.moreCount', {
                              count: p.phrases.length - 6,
                            })}
                        </span>
                      </div>
                    ))}
                    {row.pattern_one.length === 0 && (
                      <span className="text-xs text-slate-600">—</span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 text-xs text-slate-400">
                  {[...row.pattern_two_phrases, ...row.exceptional_phrases]
                    .slice(0, 5)
                    .join('、') || '—'}
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

      {selected && (
        <PatternGraphPanel
          projectId={projectId}
          char={selected}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  )
}

function PatternGraphPanel({
  projectId,
  char,
  onClose,
}: {
  projectId: string
  char: string
  onClose: () => void
}) {
  const { t } = useTranslation()
  const detail = useQuery({
    queryKey: ['duoyinzi-detail', projectId, char],
    queryFn: () =>
      request<DuoyinziDetail>(
        `/api/projects/${projectId}/duoyinzi/${encodeURIComponent(char)}`,
      ),
  })

  return (
    <aside className="w-[26rem] shrink-0 overflow-y-auto border-l border-line bg-surface-raised p-5">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-100">
          {t('duoyinzi.pattern.title')}
        </h3>
        <button onClick={onClose} className="text-slate-500 hover:text-slate-300">
          ✕
        </button>
      </div>

      {!detail.data ? (
        <div className="flex justify-center py-10">
          <Spinner />
        </div>
      ) : (
        <div className="space-y-6">
          <ReadingTree detail={detail.data} />

          {detail.data.pattern_two_detail.length > 0 && (
            <PhrasePatternList
              title={t('duoyinzi.pattern.patternTwo')}
              patterns={detail.data.pattern_two_detail}
              focusChar={char}
            />
          )}
          {detail.data.exceptional_detail.length > 0 && (
            <PhrasePatternList
              title={t('duoyinzi.pattern.exceptional')}
              patterns={detail.data.exceptional_detail}
              focusChar={char}
            />
          )}
        </div>
      )}
    </aside>
  )
}

/**
 * Tree: character -> readings -> trigger phrases.
 * Reading #1 is the default; others are applied by rclt context rules.
 */
function ReadingTree({ detail }: { detail: DuoyinziDetail }) {
  const { t } = useTranslation()
  const phrasesByPinyin = new Map(
    detail.pattern_one.map((p) => [p.pinyin, p] as const),
  )

  return (
    <div className="flex items-start gap-0">
      <div className="sticky top-0 flex h-16 w-16 shrink-0 items-center justify-center rounded-xl border-2 border-accent/50 bg-accent/10 text-4xl text-slate-100">
        {detail.char}
      </div>
      <div className="mt-8 w-5 shrink-0 border-t-2 border-line" />
      <div className="min-w-0 flex-1 border-l-2 border-line">
        {detail.readings.map((reading, index) => {
          const pattern = phrasesByPinyin.get(reading)
          const color = SS_COLORS[index % SS_COLORS.length]
          return (
            <div key={reading} className="relative pl-5 pb-4 last:pb-0">
              <span className="absolute left-0 top-4 w-4 border-t-2 border-line" />
              <div className="flex flex-wrap items-center gap-2 pt-1.5">
                <span
                  className={`rounded-full border px-2.5 py-0.5 text-sm font-medium ${color}`}
                >
                  {reading}
                </span>
                <span className="text-[10px] uppercase tracking-wide text-slate-600">
                  {index === 0
                    ? t('duoyinzi.tree.default')
                    : t('duoyinzi.tree.ssContext', { n: index + 1 })}
                </span>
                <span
                  className="rounded bg-surface px-1.5 py-0.5 font-mono text-[10px] text-slate-500"
                  title={t('duoyinzi.tree.forceIvsTitle', {
                    char: detail.char,
                    code: (0xe01e1 + index).toString(16).toUpperCase(),
                  })}
                >
                  IVS U+{(0xe01e1 + index).toString(16).toUpperCase()}
                </span>
              </div>
              {pattern && pattern.phrases.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {pattern.phrases.map((phrase) => (
                    <PhraseChip key={phrase} phrase={phrase} char={detail.char} color={color} />
                  ))}
                </div>
              )}
              {(!pattern || pattern.phrases.length === 0) && index > 0 && (
                <p className="mt-1 text-[11px] text-slate-600">
                  {t('duoyinzi.tree.noWordContext')}
                </p>
              )}
            </div>
          )
        })}
        <div className="relative pl-5 pt-1">
          <span className="absolute left-0 top-4 w-4 border-t-2 border-line" />
          <div className="flex items-center gap-2 pt-1.5">
            <span className="rounded-full border border-line px-2.5 py-0.5 text-sm text-slate-500">
              {t('duoyinzi.tree.noPinyin')}
            </span>
            <span className="text-[10px] uppercase tracking-wide text-slate-600">ss00</span>
            <span className="rounded bg-surface px-1.5 py-0.5 font-mono text-[10px] text-slate-500">
              IVS U+E01E0
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

/** One trigger phrase; ~ is the homograph position. */
function PhraseChip({
  phrase,
  char,
  color,
}: {
  phrase: string
  char: string
  color: string
}) {
  return (
    <span className="inline-flex overflow-hidden rounded-md border border-line text-sm">
      {[...phrase].map((c, i) =>
        c === '~' ? (
          <span key={i} className={`border-x px-1.5 py-0.5 font-medium ${color}`}>
            {char}
          </span>
        ) : (
          <span key={i} className="bg-surface px-1.5 py-0.5 text-slate-300">
            {c}
          </span>
        ),
      )}
    </span>
  )
}

/** Sequence diagrams for pattern-two / exceptional phrase rules. */
function PhrasePatternList({
  title,
  patterns,
  focusChar,
}: {
  title: string
  patterns: PhrasePattern[]
  focusChar: string
}) {
  const { t } = useTranslation()
  return (
    <div>
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
        {title}
      </h4>
      <div className="space-y-2">
        {patterns.map((pattern) => (
          <div
            key={pattern.phrase}
            className="rounded-lg border border-line bg-surface px-3 py-2"
          >
            <div className="flex flex-wrap items-center gap-1">
              {pattern.sequence.map((step, i) => (
                <span key={i} className="flex items-center gap-1">
                  {i > 0 && <span className="text-slate-700">→</span>}
                  <span
                    className={`rounded-md px-2 py-1 text-lg leading-none ${
                      step.lookup
                        ? 'bg-accent/15 text-accent-hover ring-1 ring-accent/40'
                        : step.char === focusChar
                          ? 'bg-surface-overlay text-slate-100'
                          : 'bg-surface-overlay text-slate-400'
                    }`}
                    title={step.lookup ?? undefined}
                  >
                    {step.char}
                  </span>
                </span>
              ))}
              <span className="ml-2 text-[10px] text-slate-600">
                {t('duoyinzi.pattern.frameHint')}
              </span>
            </div>
            {pattern.ignore && (
              <p className="mt-1.5 text-[11px] text-slate-500">
                {t('duoyinzi.pattern.ignoreContext')}
                <span className="text-slate-400">{pattern.ignore}</span>
                {t('duoyinzi.pattern.ignoreNote')}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
