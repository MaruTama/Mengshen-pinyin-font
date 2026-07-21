import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { X } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { Button, Card, Input, SliderRow, Switch } from '../components/ui'
import type { Canvas, OutlineGlyph, PreviewResponse } from '../types'
import { useProject } from './ProjectLayout'

export default function AdjustStep() {
  const { project, projectId } = useProject()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  const [canvas, setCanvas] = useState<Canvas | null>(null)
  const [text, setText] = useState('你好中国装')
  const [preview, setPreview] = useState<PreviewResponse | null>(null)
  const [selectedChar, setSelectedChar] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const previewTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  const saveTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  // Seed local state once the project loads
  useEffect(() => {
    if (project && !canvas) setCanvas(structuredClone(project.canvas))
  }, [project, canvas])

  const patchCanvas = useMutation({
    mutationFn: (next: Canvas) => api.patchProject(projectId, { canvas: next }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ['project', projectId] }),
  })

  const runPreview = useCallback(
    (nextCanvas: Canvas, nextText: string) => {
      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller
      api
        .preview(projectId, nextText, nextCanvas, controller.signal)
        .then(setPreview)
        .catch((e) => {
          if ((e as Error).name !== 'AbortError') console.error(e)
        })
    },
    [projectId],
  )

  // Initial preview
  useEffect(() => {
    if (canvas) runPreview(canvas, text)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canvas === null])

  const update = (mutate: (draft: Canvas) => void) => {
    if (!canvas) return
    const next = structuredClone(canvas)
    mutate(next)
    setCanvas(next)

    clearTimeout(previewTimer.current)
    previewTimer.current = setTimeout(() => runPreview(next, text), 150)

    clearTimeout(saveTimer.current)
    saveTimer.current = setTimeout(() => patchCanvas.mutate(next), 500)
  }

  if (!project || !canvas) return null

  return (
    <div className="flex h-full">
      <div className="w-80 shrink-0 space-y-5 overflow-y-auto border-r border-line p-6">
        <h2 className="text-lg font-bold text-slate-100">{t('adjust.title')}</h2>

        <Card title={t('adjust.canvas')}>
          <div className="space-y-4">
            <SliderRow
              label={t('adjust.width')}
              value={canvas.pinyin.width}
              min={200}
              max={1200}
              onChange={(v) => update((d) => (d.pinyin.width = v))}
            />
            <SliderRow
              label={t('adjust.height')}
              value={canvas.pinyin.height}
              min={100}
              max={600}
              step={0.1}
              onChange={(v) => update((d) => (d.pinyin.height = v))}
            />
            <SliderRow
              label={t('adjust.baseLine')}
              value={canvas.pinyin.base_line}
              min={600}
              max={1200}
              onChange={(v) => update((d) => (d.pinyin.base_line = v))}
            />
            <SliderRow
              label={t('adjust.tracking')}
              value={canvas.pinyin.tracking}
              min={0}
              max={120}
              step={0.1}
              onChange={(v) => update((d) => (d.pinyin.tracking = v))}
            />
          </div>
        </Card>

        <Card title={t('adjust.avoidOverlap')}>
          <div className="space-y-4">
            <Switch
              label={t('adjust.avoidOverlapMode')}
              checked={canvas.is_avoid_overlapping_mode}
              onChange={(v) => update((d) => (d.is_avoid_overlapping_mode = v))}
            />
            <SliderRow
              label={t('adjust.xReduction')}
              value={canvas.x_scale_reduction_for_avoid_overlapping}
              min={0}
              max={0.3}
              step={0.01}
              onChange={(v) =>
                update((d) => (d.x_scale_reduction_for_avoid_overlapping = v))
              }
            />
            <p className="text-xs leading-relaxed text-slate-500">
              {t('adjust.avoidNote')}
            </p>
          </div>
        </Card>

        <div className="flex justify-end">
          <Button onClick={() => navigate(`/projects/${projectId}/glyphs`)}>
            {t('adjust.next')}
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="mb-4 flex items-center gap-3">
          <Input
            value={text}
            onChange={(e) => {
              setText(e.target.value)
              clearTimeout(previewTimer.current)
              previewTimer.current = setTimeout(
                () => runPreview(canvas, e.target.value),
                300,
              )
            }}
            placeholder={t('adjust.previewPlaceholder')}
            className="max-w-sm"
          />
          <span className="text-xs text-slate-500">{t('adjust.liveHint')}</span>
        </div>

        {preview && preview.warnings.length > 0 && (
          <div className="mb-4 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-2 text-xs text-amber-300">
            {preview.warnings.map((w, i) => (
              <p key={i}>{w}</p>
            ))}
          </div>
        )}

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {preview?.items.map((item, i) => (
            <button
              key={`${item.char}-${i}`}
              type="button"
              onClick={() => setSelectedChar(item.char)}
              className="rounded-xl border border-line bg-surface-raised p-4 text-left transition hover:border-accent-hover/60 hover:bg-surface"
            >
              <div
                className="mx-auto w-full max-w-[160px] text-slate-100"
                dangerouslySetInnerHTML={{ __html: item.svg }}
              />
              <p className="mt-2 text-center text-xs text-slate-500">
                {item.char} <span className="text-accent-hover">{item.pinyin}</span>
              </p>
            </button>
          ))}
        </div>
      </div>

      {selectedChar && (
        <GlyphOutlineDetailPanel
          projectId={projectId}
          canvas={canvas}
          char={selectedChar}
          onClose={() => setSelectedChar(null)}
        />
      )}
    </div>
  )
}

function GlyphOutlineDetailPanel({
  projectId,
  canvas,
  char,
  onClose,
}: {
  projectId: string
  canvas: Canvas
  char: string
  onClose: () => void
}) {
  const { t } = useTranslation()
  const detail = useQuery({
    queryKey: ['previewDetail', projectId, char, canvas],
    queryFn: () => api.previewDetail(projectId, char, canvas),
  })

  return (
    <aside className="w-[26rem] shrink-0 overflow-y-auto border-l border-line bg-surface-raised p-5">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-100">
          {t('adjust.detail.title')} <span className="text-accent-hover">{char}</span>
        </h3>
        <button onClick={onClose} className="text-slate-500 hover:text-slate-300">
          <X className="h-4 w-4" />
        </button>
      </div>

      {detail.isLoading && <p className="text-xs text-slate-500">{t('adjust.detail.loading')}</p>}
      {detail.isError && (
        <p className="text-xs text-red-400">{t('adjust.detail.error')}</p>
      )}

      {detail.data && (
        <>
          <div className="mb-4 rounded-xl border border-line bg-surface p-3">
            <GlyphOutlineCanvas data={detail.data} />
          </div>

          <dl className="space-y-2 text-xs">
            <DetailRow label={t('adjust.detail.pinyin')} value={detail.data.pinyin || '—'} />
            <DetailRow label={t('adjust.detail.upem')} value={String(detail.data.upem)} mono />
            <DetailRow
              label={t('adjust.detail.hanziAdvance')}
              value={detail.data.hanzi_width.toFixed(1)}
              mono
            />
            <DetailRow label={t('adjust.detail.baseLine')} value={detail.data.base_line.toFixed(1)} mono />
            <DetailRow
              label={t('adjust.detail.pinyinBox')}
              value={`${detail.data.pinyin_width.toFixed(1)} × ${detail.data.pinyin_height.toFixed(1)}`}
              mono
            />
            <DetailRow label={t('adjust.detail.tracking')} value={detail.data.tracking.toFixed(1)} mono />
            <DetailRow label={t('adjust.detail.descent')} value={detail.data.descent.toFixed(1)} mono />
          </dl>

          {detail.data.pinyin_glyphs.length > 0 && (
            <div className="mt-4">
              <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">
                {t('adjust.detail.glyphs')}
              </p>
              <div className="space-y-1.5">
                {detail.data.pinyin_glyphs.map((g, i) => (
                  <div
                    key={`${g.glyph}-${i}`}
                    className="flex items-center gap-2 rounded-md bg-surface px-2 py-1.5 text-xs"
                  >
                    <span className="text-slate-300">{g.label}</span>
                    <span className="ml-auto font-mono text-slate-500">{g.glyph}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <p className="mt-4 text-xs leading-relaxed text-slate-500">{t('adjust.detail.legend')}</p>
        </>
      )}
    </aside>
  )
}

function GlyphOutlineCanvas({
  data,
}: {
  data: {
    hanzi: OutlineGlyph
    pinyin_glyphs: OutlineGlyph[]
    upem: number
    hanzi_width: number
    total_height: number
    descent: number
  }
}) {
  const { t } = useTranslation()
  const {
    hanzi,
    pinyin_glyphs: pinyinGlyphs,
    upem,
    hanzi_width: hanziWidth,
    total_height: totalHeight,
    descent,
  } = data

  // Pinyin letters can extend past the hanzi's own [0, hanziWidth] span
  // (e.g. a 5-6 letter word like "zhuāng"), so fit the horizontal bounds
  // to whatever actually renders instead of clipping to hanziWidth.
  const pinyinMinX = pinyinGlyphs.length
    ? Math.min(...pinyinGlyphs.map((g) => g.x))
    : 0
  const pinyinMaxX = pinyinGlyphs.length
    ? Math.max(...pinyinGlyphs.map((g) => g.x + g.advance_width * g.a))
    : hanziWidth
  const contentMinX = Math.min(0, pinyinMinX)
  const contentMaxX = Math.max(hanziWidth, pinyinMaxX)
  const contentWidth = contentMaxX - contentMinX

  const marginX = Math.max(contentWidth * 0.08, 40)
  const labelBand = upem * 0.12
  const marginTop = labelBand
  const marginBottom = descent + labelBand * 2.4
  const viewW = contentWidth + marginX * 2
  const viewH = totalHeight + marginTop + marginBottom
  // Font coords are Y-up; flip to SVG Y-down, keeping top/bottom margins for name labels.
  // X needs no shift here: the viewBox's own min-x (contentMinX - marginX)
  // already places the margin, since path/matrix x values are in the same
  // absolute coordinate space as the viewBox. Adding a translate here too
  // double-counted marginX and pushed everything right.
  const originY = totalHeight + marginTop

  const gridLine = (y: number) => (
    <line
      x1={contentMinX - marginX}
      x2={contentMaxX + marginX}
      y1={y}
      y2={y}
      stroke="#475569"
      strokeWidth={1}
      vectorEffect="non-scaling-stroke"
    />
  )

  const nameLabel = (x: number, y: number, text: string) => (
    <g transform={`translate(${x} ${y}) scale(1 -1)`}>
      <text fontSize={upem * 0.05} fill="#94a3b8" textAnchor="middle">
        {text}
      </text>
    </g>
  )

  // Left-anchored label sitting just above a horizontal guide line, so the
  // grid stays identifiable (baseline, UPM, etc.) without a separate legend.
  const lineLabel = (y: number, text: string) => (
    <g transform={`translate(${contentMinX - marginX + upem * 0.015} ${y + upem * 0.012}) scale(1 -1)`}>
      <text fontSize={upem * 0.04} fill="#64748b" textAnchor="start">
        {text}
      </text>
    </g>
  )

  // Label for a vertical sidebearing line, tucked in the bottom margin so it
  // never collides with the centered hanzi-glyph-name label above it.
  const vLineLabel = (x: number, text: string, anchor: 'start' | 'end') => (
    <g transform={`translate(${x} ${-descent - labelBand * 1.3}) scale(1 -1)`}>
      <text
        fontSize={upem * 0.04}
        fill="#64748b"
        textAnchor={anchor}
        dx={anchor === 'start' ? upem * 0.015 : -upem * 0.015}
      >
        {text}
      </text>
    </g>
  )

  return (
    <div className="overflow-hidden rounded-lg border border-line bg-surface">
      <div className="flex items-center justify-end border-b border-line px-3 py-1 font-mono text-[0.65rem] text-slate-500">
        {upem}
      </div>
      <svg
        viewBox={`${contentMinX - marginX} ${-marginTop} ${viewW} ${viewH}`}
        className="w-full text-slate-100"
      >
        <g transform={`translate(0 ${originY}) scale(1 -1)`}>
          {/* ruled grid: UPM/em-box top, baseline, descender floor */}
          {gridLine(upem)}
          {gridLine(0)}
          {gridLine(-descent)}
          {lineLabel(upem, t('adjust.detail.lineUpm'))}
          {lineLabel(0, t('adjust.detail.lineBaseline'))}
          {lineLabel(-descent, t('adjust.detail.lineDescent'))}
          <line
            x1={0}
            x2={0}
            y1={-descent}
            y2={totalHeight}
            stroke="#475569"
            strokeWidth={1}
            vectorEffect="non-scaling-stroke"
          />
          <line
            x1={hanziWidth}
            x2={hanziWidth}
            y1={-descent}
            y2={totalHeight}
            stroke="#475569"
            strokeWidth={1}
            vectorEffect="non-scaling-stroke"
          />
          {vLineLabel(0, t('adjust.detail.lineLeftBearing'), 'start')}
          {vLineLabel(hanziWidth, t('adjust.detail.lineRightBearing'), 'end')}

          <path
            d={hanzi.path}
            fill="none"
            stroke="currentColor"
            strokeWidth={upem * 0.006}
          />
          {/* Pinyin can legitimately dip below the upm line (avoid-overlap
              tone marks), so the hanzi name label goes in the empty
              bottom margin instead of risking an overlap up top. */}
          {nameLabel(hanziWidth / 2, -descent - labelBand * 0.2, hanzi.glyph)}

          {pinyinGlyphs.map((g, i) => (
            <g key={`${g.glyph}-${i}`}>
              <path
                d={g.path}
                fill="none"
                stroke="currentColor"
                strokeWidth={upem * 0.006}
                transform={`matrix(${g.a} 0 0 ${g.d} ${g.x} ${g.y})`}
              />
              {nameLabel(
                g.x + (g.advance_width * g.a) / 2,
                totalHeight + labelBand * 0.35,
                g.glyph,
              )}
            </g>
          ))}
        </g>
      </svg>
    </div>
  )
}

function DetailRow({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <dt className="text-slate-500">{label}</dt>
      <dd className={mono ? 'font-mono text-slate-200' : 'text-slate-200'}>{value}</dd>
    </div>
  )
}
