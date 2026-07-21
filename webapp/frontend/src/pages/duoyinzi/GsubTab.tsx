import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { request } from '../../api'
import { Button, Input, Spinner } from '../../components/ui'
import { displayError } from '../../i18n/apiError'
import type { GraphData, GraphRule, GsubOverview, GsubRules } from '../../types'
import { useDebouncedPagedSearch } from '../../useDebouncedPagedSearch'
import { useProject } from '../ProjectLayout'
import { SS_COLORS } from './colors'

export function GsubTab() {
  const { projectId } = useProject()
  const { t } = useTranslation()
  const [mode, setMode] = useState<'rules' | 'graph'>('rules')
  const [lookup, setLookup] = useState('lookup_rclt_0')
  const { query, setQuery, debounced, page, setPage } = useDebouncedPagedSearch()

  const overview = useQuery({
    queryKey: ['gsub', projectId],
    queryFn: () => request<GsubOverview>(`/api/projects/${projectId}/gsub`),
    retry: false,
  })

  const rules = useQuery({
    queryKey: ['gsub-rules', projectId, lookup, debounced, page],
    queryFn: () =>
      request<GsubRules>(
        `/api/projects/${projectId}/gsub/${lookup}?q=${encodeURIComponent(debounced)}&page=${page}&size=50`,
      ),
    enabled: overview.isSuccess,
    placeholderData: (prev) => prev,
  })

  if (overview.isError) {
    return (
      <div className="flex flex-1 items-center justify-center p-10 text-center">
        <div>
          <p className="text-slate-300">{displayError(overview.error)}</p>
          <p className="mt-2 text-sm text-slate-500">
            {t('duoyinzi.gsub.prepareRequired')}
          </p>
        </div>
      </div>
    )
  }
  if (!overview.data) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Spinner />
      </div>
    )
  }

  const rcltLookups = Object.entries(overview.data.lookups).filter(([name]) =>
    name.startsWith('lookup_rclt') || name.startsWith('lookup_aalt'),
  )
  const totalPages = rules.data ? Math.max(1, Math.ceil(rules.data.total / 50)) : 1

  const modeToggle = (
    <div className="flex gap-1 rounded-lg bg-surface p-0.5">
      {(['rules', 'graph'] as const).map((value) => (
        <button
          key={value}
          onClick={() => setMode(value)}
          className={`rounded-md px-3 py-1 text-xs transition-colors ${
            mode === value
              ? 'bg-accent/20 font-medium text-accent-hover'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          {t(`duoyinzi.gsub.mode.${value}`)}
        </button>
      ))}
    </div>
  )

  if (mode === 'graph') {
    return (
      <div className="flex flex-1 flex-col overflow-hidden">
        <div className="flex items-center gap-3 border-b border-line px-6 py-3">
          {modeToggle}
        </div>
        <GsubGraphView projectId={projectId} />
      </div>
    )
  }

  return (
    <div className="flex flex-1 overflow-hidden">
      <aside className="w-64 shrink-0 overflow-y-auto border-r border-line p-4">
        <div className="mb-4">{modeToggle}</div>
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
          {t('duoyinzi.gsub.featureLookup')}
        </h4>
        <div className="mb-4 space-y-1 text-xs text-slate-400">
          {Object.entries(overview.data.features).map(([feature, lookups]) => (
            <div key={feature} className="rounded-lg bg-surface-raised px-3 py-2">
              <span className="font-mono text-accent-hover">{feature}</span>
              <span className="ml-1 text-slate-600">
                {t('duoyinzi.gsub.lookupsCount', { count: lookups.length })}
              </span>
            </div>
          ))}
        </div>
        <div className="space-y-1">
          {rcltLookups.map(([name, meta]) => (
            <button
              key={name}
              onClick={() => {
                setLookup(name)
                setPage(1)
              }}
              className={`flex w-full items-center justify-between rounded-lg px-3 py-2 text-xs transition-colors ${
                lookup === name
                  ? 'bg-accent/15 text-accent-hover'
                  : 'text-slate-400 hover:bg-surface-overlay'
              }`}
            >
              <span className="font-mono">{name}</span>
              <span className="text-slate-600">{meta.rule_count}</span>
            </button>
          ))}
        </div>
        <p className="mt-4 text-[11px] leading-relaxed text-slate-600">
          {t('duoyinzi.gsub.legend')}
        </p>
      </aside>

      <div className="flex-1 overflow-y-auto p-4">
        <div className="mb-3 flex items-center gap-3">
          <Input
            className="max-w-xs"
            placeholder={t('duoyinzi.gsub.searchPlaceholder')}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <span className="text-xs text-slate-500">
            {rules.data &&
              t('duoyinzi.gsub.rulesCount', {
                count: rules.data.total,
                type: rules.data.type,
              })}
          </span>
          {rules.isFetching && <Spinner />}
        </div>

        <div className="space-y-2">
          {rules.data?.rules.map((rule, i) => (
            <RuleCard key={i} rule={rule} glyphChars={rules.data?.glyph_chars ?? {}} />
          ))}
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
    </div>
  )
}

function RuleCard({
  rule,
  glyphChars,
}: {
  rule: Record<string, unknown>
  glyphChars: Record<string, string>
}) {
  const match = (rule.match as string[][] | undefined) ?? []
  const apply = (rule.apply as { at: number; lookup: string }[] | undefined) ?? []

  const renderGroup = (group: string[], index: number) => {
    const applied = apply.some((a) => a.at === index)
    const label = group
      .slice(0, 3)
      .map((g) => glyphChars[g] ?? g)
      .join(' ')
    return (
      <span
        key={index}
        className={`rounded-md px-2 py-1 font-mono text-xs ${
          applied
            ? 'bg-accent/20 text-accent-hover ring-1 ring-accent/40'
            : 'bg-surface-overlay text-slate-300'
        }`}
        title={group.join(', ')}
      >
        {label}
        {group.length > 3 && <span className="text-slate-600"> +{group.length - 3}</span>}
      </span>
    )
  }

  if (match.length > 0) {
    return (
      <div className="flex flex-wrap items-center gap-1.5 rounded-lg border border-line bg-surface-raised px-3 py-2">
        {match.map(renderGroup)}
        {apply.length > 0 && (
          <span className="ml-2 text-xs text-slate-500">
            → {apply.map((a) => a.lookup).join(', ')}
          </span>
        )}
      </div>
    )
  }

  return (
    <pre className="overflow-x-auto rounded-lg border border-line bg-surface-raised px-3 py-2 text-xs text-slate-400">
      {JSON.stringify(rule, null, 1)}
    </pre>
  )
}

// SVG stroke colors matching SS_COLORS order (emerald/sky/amber/rose)
const EDGE_COLORS = ['#34d399', '#38bdf8', '#fbbf24', '#fb7185']
const IGNORE_COLOR = '#f43f5e'
const DEFAULT_COLOR = '#64748b'

const ROW_H = 52
const COL_CONTEXT_W = 280
const COL_LOOKUP_X = 340
const COL_LOOKUP_W = 170
const COL_OUTPUT_X = 570
const COL_OUTPUT_W = 170

function GsubGraphView({ projectId }: { projectId: string }) {
  const { t } = useTranslation()
  const [input, setInput] = useState('着')
  const [char, setChar] = useState('着')

  const graph = useQuery({
    queryKey: ['gsub-graph', projectId, char],
    queryFn: () =>
      request<GraphData>(
        `/api/projects/${projectId}/gsub/graph/${encodeURIComponent(char)}`,
      ),
    enabled: char.length === 1,
  })

  return (
    <div className="flex-1 overflow-auto px-6 py-4">
      <div className="mb-3 flex items-center gap-3">
        <Input
          className="max-w-[10rem] text-center text-lg"
          value={input}
          maxLength={1}
          placeholder={t('duoyinzi.graph.charPlaceholder')}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && input.length === 1) setChar(input)
          }}
        />
        <Button onClick={() => setChar(input)} disabled={input.length !== 1}>
          {t('duoyinzi.graph.show')}
        </Button>
        {graph.data && (
          <span className="text-xs text-slate-500">
            {t('duoyinzi.graph.rulesCount', { count: graph.data.rules.length })}
          </span>
        )}
        {graph.isFetching && <Spinner />}
      </div>

      <p className="mb-4 max-w-3xl text-xs leading-relaxed text-slate-600">
        {t('duoyinzi.graph.legend')}
      </p>

      {graph.data &&
        (graph.data.rules.length === 0 ? (
          <p className="text-sm text-slate-500">{t('duoyinzi.graph.noRules')}</p>
        ) : (
          <RuleGraph data={graph.data} />
        ))}
    </div>
  )
}

function RuleGraph({ data }: { data: GraphData }) {
  const { t } = useTranslation()
  const rules = data.rules

  // Middle column: unique sub-lookups (ignore rules get their own node)
  const lookupKeys: string[] = []
  for (const rule of rules) {
    const key = rule.ignore ? 'ignore' : (rule.sub_lookup ?? '—')
    if (!lookupKeys.includes(key)) lookupKeys.push(key)
  }
  // Right column: unique outputs (ignore -> keeps default)
  const outputKeys: string[] = []
  for (const rule of rules) {
    const key = rule.ignore ? '__default__' : (rule.output_reading ?? '?')
    if (!outputKeys.includes(key)) outputKeys.push(key)
  }

  const ruleY = (index: number) => index * ROW_H + ROW_H / 2
  const ruleKeyOf = (rule: GraphRule) => (rule.ignore ? 'ignore' : (rule.sub_lookup ?? '—'))
  const outputKeyOf = (rule: GraphRule) =>
    rule.ignore ? '__default__' : (rule.output_reading ?? '?')

  // Position middle/right nodes at the average of their sources, then
  // spread overlapping nodes apart
  const spread = (centers: number[]): number[] => {
    const order = centers
      .map((y, index) => ({ y, index }))
      .sort((a, b) => a.y - b.y)
    let previous = -Infinity
    const result = [...centers]
    for (const item of order) {
      const y = Math.max(item.y, previous + ROW_H * 0.85)
      result[item.index] = y
      previous = y
    }
    return result
  }

  const lookupY = spread(
    lookupKeys.map((key) => {
      const sources = rules
        .map((r, index) => ({ r, index }))
        .filter(({ r }) => ruleKeyOf(r) === key)
        .map(({ index }) => ruleY(index))
      return sources.reduce((a, b) => a + b, 0) / sources.length
    }),
  )
  const outputY = spread(
    outputKeys.map((key) => {
      const sources = rules
        .map((r, index) => ({ r, index }))
        .filter(({ r }) => outputKeyOf(r) === key)
        .map(({ index }) => ruleY(index))
      return sources.reduce((a, b) => a + b, 0) / sources.length
    }),
  )

  const colorOf = (rule: GraphRule): string => {
    if (rule.ignore) return IGNORE_COLOR
    if (rule.output_reading == null) return DEFAULT_COLOR
    const index = data.readings.indexOf(rule.output_reading)
    return index >= 0 ? EDGE_COLORS[index % EDGE_COLORS.length] : DEFAULT_COLOR
  }
  const chipColorOf = (readingIndex: number) =>
    SS_COLORS[readingIndex % SS_COLORS.length]

  const height = Math.max(
    rules.length * ROW_H,
    (lookupY[lookupY.length - 1] ?? 0) + ROW_H,
    (outputY[outputY.length - 1] ?? 0) + ROW_H,
  )
  const width = COL_OUTPUT_X + COL_OUTPUT_W

  return (
    <div className="relative" style={{ width, height }}>
      {/* edges */}
      <svg className="absolute inset-0" width={width} height={height}>
        {rules.map((rule, index) => {
          const y1 = ruleY(index)
          const y2 = lookupY[lookupKeys.indexOf(ruleKeyOf(rule))]
          const y3 = outputY[outputKeys.indexOf(outputKeyOf(rule))]
          const color = colorOf(rule)
          const dash = rule.ignore ? '5 4' : undefined
          return (
            <g key={`${rule.lookup}-${rule.rule}-${index}`} opacity={0.75}>
              <path
                d={`M ${COL_CONTEXT_W} ${y1} C ${COL_CONTEXT_W + 34} ${y1}, ${COL_LOOKUP_X - 34} ${y2}, ${COL_LOOKUP_X} ${y2}`}
                stroke={color}
                strokeWidth={1.5}
                strokeDasharray={dash}
                fill="none"
              />
              <path
                d={`M ${COL_LOOKUP_X + COL_LOOKUP_W} ${y2} C ${COL_LOOKUP_X + COL_LOOKUP_W + 34} ${y2}, ${COL_OUTPUT_X - 34} ${y3}, ${COL_OUTPUT_X} ${y3}`}
                stroke={color}
                strokeWidth={1.5}
                strokeDasharray={dash}
                fill="none"
              />
            </g>
          )
        })}
      </svg>

      {/* context nodes (one per rule) */}
      {rules.map((rule, index) => (
        <div
          key={`ctx-${index}`}
          className="absolute flex items-center gap-1"
          style={{ top: ruleY(index) - 16, left: 0, width: COL_CONTEXT_W, height: 32 }}
        >
          <span className="mr-1 font-mono text-[9px] text-slate-600">
            {rule.lookup.replace('lookup_', '')}
          </span>
          {rule.context.map((group, groupIndex) => (
            <span
              key={groupIndex}
              className={`rounded px-1.5 py-0.5 text-sm leading-none ${
                groupIndex === rule.target_at
                  ? rule.ignore
                    ? 'bg-rose-500/15 text-rose-300 ring-1 ring-rose-500/50'
                    : 'bg-accent/15 text-accent-hover ring-1 ring-accent/40'
                  : 'bg-surface-overlay text-slate-400'
              }`}
              title={group.join(' ')}
            >
              {group.length > 2 ? `${group.slice(0, 2).join('')}…` : group.join('')}
            </span>
          ))}
        </div>
      ))}

      {/* lookup nodes */}
      {lookupKeys.map((key, index) => (
        <div
          key={`lk-${key}`}
          className={`absolute flex items-center justify-center rounded-lg border px-2 font-mono text-[11px] ${
            key === 'ignore'
              ? 'border-rose-500/50 bg-rose-500/10 text-rose-300'
              : 'border-line bg-surface-raised text-slate-300'
          }`}
          style={{
            top: lookupY[index] - 15,
            left: COL_LOOKUP_X,
            width: COL_LOOKUP_W,
            height: 30,
          }}
        >
          {key === 'ignore' ? t('duoyinzi.graph.ignoreNode') : key}
        </div>
      ))}

      {/* output nodes */}
      {outputKeys.map((key, index) => {
        const readingIndex = key === '__default__' ? -1 : data.readings.indexOf(key)
        return (
          <div
            key={`out-${key}`}
            className={`absolute flex items-center justify-center rounded-full border px-2 text-sm ${
              key === '__default__'
                ? 'border-line bg-surface text-slate-500'
                : readingIndex >= 0
                  ? chipColorOf(readingIndex)
                  : 'border-line bg-surface text-slate-300'
            }`}
            style={{
              top: outputY[index] - 15,
              left: COL_OUTPUT_X,
              width: COL_OUTPUT_W,
              height: 30,
            }}
          >
            {key === '__default__' ? (
              <span className="text-xs">{t('duoyinzi.graph.defaultOutput')}</span>
            ) : (
              key
            )}
          </div>
        )
      })}
    </div>
  )
}
