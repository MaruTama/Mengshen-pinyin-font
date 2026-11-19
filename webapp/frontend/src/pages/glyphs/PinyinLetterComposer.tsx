import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { RotateCcw, Save, Trash2, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../../api'
import { Badge, Button, SliderRow, Spinner, Switch } from '../../components/ui'
import { displayError } from '../../i18n/apiError'
import type { LetterRecipe, PinyinLetter } from '../../types'

const PREVIEW_DEBOUNCE_MS = 150

function fallbackRecipe(letter: string): LetterRecipe {
  return {
    base: letter.normalize('NFD').charAt(0),
    mark_source: '',
    mark_contours: null,
    dx: 0,
    dy: 0,
    scale: 1,
    flip_y: false,
  }
}

function initialRecipe(letter: PinyinLetter): LetterRecipe {
  return letter.recipe ?? letter.default_recipe ?? fallbackRecipe(letter.letter)
}

/** Placeholder cells for pinyin letters the selected pinyin font lacks. */
export function MissingLettersStrip({
  letters,
  selectedName,
  onSelect,
}: {
  letters: PinyinLetter[]
  selectedName: string | null
  onSelect: (letter: PinyinLetter) => void
}) {
  const { t } = useTranslation()
  const shown = letters.filter((l) => l.status !== 'font')
  if (shown.length === 0) return null
  return (
    <div className="mx-6 mt-4 rounded-lg border border-amber-500/30 bg-amber-500/5 px-4 py-3">
      <p className="text-sm font-medium text-amber-300">{t('letters.missingTitle')}</p>
      <p className="mt-0.5 text-xs text-slate-400">{t('letters.missingHint')}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {shown.map((letter) => (
          <button
            key={letter.name}
            onClick={() => onSelect(letter)}
            title={letter.stale ? t('letters.stale') : undefined}
            className={`flex h-16 w-16 flex-col items-center justify-center rounded-lg border text-2xl transition-colors ${
              selectedName === letter.name
                ? 'border-accent bg-accent/10 text-slate-100'
                : letter.status === 'custom'
                  ? 'border-emerald-500/50 text-slate-200 hover:border-emerald-400'
                  : 'border-dashed border-slate-500 text-slate-400 hover:border-slate-300'
            }`}
          >
            <span>{letter.letter}</span>
            <span className="text-[10px] text-slate-500">
              {letter.status === 'custom' ? t('letters.statusCustom') : t('letters.statusMissing')}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}

/** Compose a missing letter: base glyph + tone mark from an accented glyph. */
export function PinyinLetterComposer({
  projectId,
  letter,
  letters,
  onClose,
}: {
  projectId: string
  letter: PinyinLetter
  letters: PinyinLetter[]
  onClose: () => void
}) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [recipe, setRecipe] = useState<LetterRecipe>(() => initialRecipe(letter))
  const [debounced, setDebounced] = useState(recipe)
  const [contoursText, setContoursText] = useState(
    recipe.mark_contours ? recipe.mark_contours.join(', ') : '',
  )
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(recipe), PREVIEW_DEBOUNCE_MS)
    return () => clearTimeout(timer)
  }, [recipe])

  const update = (patch: Partial<LetterRecipe>) => {
    setSaved(false)
    setRecipe((current) => ({ ...current, ...patch }))
  }

  const preview = useQuery({
    queryKey: ['letter-preview', projectId, letter.name, debounced],
    queryFn: async ({ signal }) => ({
      recipe: debounced,
      data: await api.previewLetter(projectId, letter.name, debounced, signal),
    }),
    enabled: Boolean(debounced.base && debounced.mark_source),
    placeholderData: keepPreviousData,
    retry: false,
  })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['pinyin-letters', projectId] })
    queryClient.invalidateQueries({ queryKey: ['glyphs', projectId] })
    queryClient.invalidateQueries({ queryKey: ['project', projectId] })
  }

  const save = useMutation({
    mutationFn: () => api.saveLetter(projectId, letter.name, recipe),
    onSuccess: () => {
      setSaved(true)
      invalidate()
    },
  })

  const remove = useMutation({
    mutationFn: () => api.deleteLetter(projectId, letter.name),
    onSuccess: () => {
      invalidate()
      onClose()
    },
  })

  // Letters with a glyph can serve as base or mark source
  const candidates = letters.filter((l) => l.status !== 'missing' && l.name !== letter.name)

  const setContours = (text: string) => {
    setContoursText(text)
    const indices = text
      .split(/[\s,]+/)
      .filter(Boolean)
      .map(Number)
      .filter((n) => Number.isInteger(n) && n >= 0)
    update({ mark_contours: indices.length > 0 ? indices : null })
  }

  const resetToDefaults = () => {
    const defaults = letter.default_recipe ?? fallbackRecipe(letter.letter)
    setContoursText('')
    update({ ...defaults, mark_contours: null })
  }

  return (
    <aside className="w-96 shrink-0 overflow-y-auto border-l border-line bg-surface-raised p-5">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-100">
          {t('letters.composerTitle', { letter: letter.letter })}
        </h3>
        <button onClick={onClose} className="text-slate-500 hover:text-slate-300">
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="mb-3 flex flex-wrap gap-1.5">
        <Badge tone={letter.status === 'custom' ? 'success' : 'warning'}>
          {letter.status === 'custom' ? t('letters.statusCustom') : t('letters.statusMissing')}
        </Badge>
        <Badge>py_alphabet_{letter.name}</Badge>
        {letter.stale && <Badge tone="error">{t('letters.staleShort')}</Badge>}
      </div>

      <ComposerCanvas
        preview={preview.data}
        recipe={recipe}
        onDrag={(dx, dy) => update({ dx, dy })}
        loading={preview.isFetching}
      />
      <p className="mt-1 text-[11px] text-slate-500">{t('letters.dragHint')}</p>
      {preview.isError && (
        <p className="mt-2 text-sm text-rose-400">{displayError(preview.error)}</p>
      )}

      <div className="mt-4 space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <LetterSelect
            label={t('letters.base')}
            value={recipe.base}
            options={candidates}
            onChange={(base) => update({ base })}
          />
          <LetterSelect
            label={t('letters.markSource')}
            value={recipe.mark_source}
            options={candidates}
            onChange={(mark_source) => {
              setContoursText('')
              update({ mark_source, mark_contours: null })
            }}
          />
        </div>

        <SliderRow
          label={t('letters.dx')}
          value={recipe.dx}
          min={-500}
          max={500}
          onChange={(dx) => update({ dx })}
        />
        <SliderRow
          label={t('letters.dy')}
          value={recipe.dy}
          min={-500}
          max={500}
          onChange={(dy) => update({ dy })}
        />
        <SliderRow
          label={t('letters.scale')}
          value={recipe.scale}
          min={0.2}
          max={2}
          step={0.05}
          onChange={(scale) => update({ scale: scale > 0 ? scale : 0.05 })}
        />
        <Switch
          label={t('letters.flipY')}
          checked={recipe.flip_y}
          onChange={(flip_y) => update({ flip_y })}
        />

        <label className="block space-y-1 text-sm">
          <span className="text-slate-400">{t('letters.markContours')}</span>
          <input
            className="w-full rounded-md border border-line bg-surface px-2 py-1 font-mono text-xs text-slate-200 outline-none focus:border-accent"
            value={contoursText}
            placeholder={preview.data?.data.mark_contours.join(', ') ?? ''}
            onChange={(e) => setContours(e.target.value)}
          />
          <span className="block text-[11px] text-slate-500">
            {t('letters.markContoursHint', {
              count: preview.data?.data.source_contour_count ?? 0,
            })}
          </span>
        </label>
      </div>

      {save.isError && <p className="mt-3 text-sm text-rose-400">{displayError(save.error)}</p>}
      {remove.isError && (
        <p className="mt-3 text-sm text-rose-400">{displayError(remove.error)}</p>
      )}
      {saved && <p className="mt-3 text-sm text-emerald-400">{t('letters.saved')}</p>}

      <div className="mt-5 flex flex-wrap gap-2">
        <Button
          onClick={() => save.mutate()}
          disabled={save.isPending || preview.isError || !recipe.mark_source}
        >
          <span className="flex items-center gap-1.5">
            <Save className="h-4 w-4" /> {t('letters.save')}
          </span>
        </Button>
        <Button variant="ghost" onClick={resetToDefaults}>
          <span className="flex items-center gap-1.5">
            <RotateCcw className="h-4 w-4" /> {t('letters.reset')}
          </span>
        </Button>
        {(letter.status === 'custom' || letter.stale) && (
          <Button variant="danger" onClick={() => remove.mutate()} disabled={remove.isPending}>
            <span className="flex items-center gap-1.5">
              <Trash2 className="h-4 w-4" /> {t('letters.delete')}
            </span>
          </Button>
        )}
      </div>
    </aside>
  )
}

function LetterSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string
  value: string
  options: PinyinLetter[]
  onChange: (letter: string) => void
}) {
  const known = options.some((o) => o.letter === value)
  return (
    <label className="block space-y-1 text-sm">
      <span className="text-slate-400">{label}</span>
      <select
        className="w-full rounded-md border border-line bg-surface px-2 py-1.5 text-base text-slate-200 outline-none focus:border-accent"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {!known && <option value={value}>{value || '—'}</option>}
        {options.map((o) => (
          <option key={o.name} value={o.letter}>
            {o.letter}
            {o.status === 'custom' ? ' *' : ''}
          </option>
        ))}
      </select>
    </label>
  )
}

/**
 * Live outline preview. The mark is draggable: while a new preview is in
 * flight it is shifted by the not-yet-rendered part of the offset so the
 * drag feels immediate.
 */
function ComposerCanvas({
  preview,
  recipe,
  onDrag,
  loading,
}: {
  preview?: { recipe: LetterRecipe; data: Awaited<ReturnType<typeof api.previewLetter>> }
  recipe: LetterRecipe
  onDrag: (dx: number, dy: number) => void
  loading: boolean
}) {
  const svgRef = useRef<SVGSVGElement>(null)
  const drag = useRef<{ x: number; y: number; dx: number; dy: number } | null>(null)

  if (!preview) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-line bg-surface">
        {loading ? <Spinner /> : null}
      </div>
    )
  }

  const { data } = preview
  const margin = data.upem * 0.15
  const top = Math.max(data.ascent, data.upem) + margin
  const bottom = -data.descent - margin * 0.3
  const width = data.advance_width + margin * 2
  const height = top - bottom
  const pendingX = recipe.dx - preview.recipe.dx
  const pendingY = recipe.dy - preview.recipe.dy

  const unitsPerPixel = () => {
    const rect = svgRef.current?.getBoundingClientRect()
    return rect && rect.width > 0 ? width / rect.width : 1
  }

  return (
    <div className="relative rounded-xl border border-line bg-surface p-2">
      {loading && (
        <div className="absolute right-2 top-2">
          <Spinner />
        </div>
      )}
      <svg
        ref={svgRef}
        viewBox={`${-margin} 0 ${width} ${height}`}
        className="h-64 w-full touch-none select-none"
        onPointerMove={(e) => {
          if (!drag.current) return
          const scale = unitsPerPixel()
          onDrag(
            Math.round(drag.current.dx + (e.clientX - drag.current.x) * scale),
            // Screen Y grows downward, font Y upward
            Math.round(drag.current.dy - (e.clientY - drag.current.y) * scale),
          )
        }}
        onPointerUp={() => {
          drag.current = null
        }}
        onPointerLeave={() => {
          drag.current = null
        }}
      >
        <g transform={`translate(0 ${top}) scale(1 -1)`}>
          <line
            x1={-margin}
            x2={data.advance_width + margin}
            y1={0}
            y2={0}
            stroke="#475569"
            strokeWidth={data.upem / 300}
          />
          <rect
            x={0}
            y={-data.descent}
            width={data.advance_width}
            height={data.descent + Math.max(data.ascent, data.upem)}
            fill="none"
            stroke="#334155"
            strokeDasharray={`${data.upem / 60} ${data.upem / 60}`}
            strokeWidth={data.upem / 400}
          />
          <path d={data.base_path} fill="#cbd5e1" />
          <path
            d={data.mark_path}
            fill="#818cf8"
            transform={`translate(${pendingX} ${pendingY})`}
            className="cursor-move"
            onPointerDown={(e) => {
              e.currentTarget.ownerSVGElement?.setPointerCapture(e.pointerId)
              drag.current = { x: e.clientX, y: e.clientY, dx: recipe.dx, dy: recipe.dy }
            }}
          />
        </g>
      </svg>
    </div>
  )
}
