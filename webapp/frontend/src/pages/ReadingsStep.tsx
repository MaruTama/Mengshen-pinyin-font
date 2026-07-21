import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { GripVertical, Plus, RotateCcw, Trash2, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useSearchParams } from 'react-router-dom'
import { Badge, Button, Card, Input, Spinner } from '../components/ui'
import { ApiError, displayError } from '../i18n/apiError'
import type { PreviewResponse, ReadingOverride } from '../types'
import { useProject } from './ProjectLayout'

interface ReadingState {
  char: string
  readings: string[]
  override: ReadingOverride | null
}

async function fetchReading(projectId: string, char: string): Promise<ReadingState> {
  const res = await fetch(
    `/api/projects/${projectId}/readings/${encodeURIComponent(char)}`,
  )
  if (!res.ok) throw new ApiError((await res.json()).detail, res.statusText)
  return res.json()
}

export default function ReadingsStep() {
  const { project, projectId } = useProject()
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [params] = useSearchParams()
  const [char, setChar] = useState(params.get('char') ?? '')
  const [input, setInput] = useState(char)
  const [newReading, setNewReading] = useState('')
  const [error, setError] = useState<unknown>(null)

  const reading = useQuery({
    queryKey: ['reading', projectId, char],
    queryFn: () => fetchReading(projectId, char),
    enabled: char.length === 1,
  })

  const preview = useQuery({
    queryKey: ['reading-preview', projectId, char, reading.data?.readings],
    queryFn: async () => {
      const res = await fetch(`/api/projects/${projectId}/preview`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: char, canvas: null }),
      })
      return res.json() as Promise<PreviewResponse>
    },
    enabled: char.length === 1 && reading.isSuccess,
  })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['reading', projectId, char] })
    queryClient.invalidateQueries({ queryKey: ['project', projectId] })
  }

  // The list itself is the source of truth: any edit saves the full
  // ordered readings (first entry = default shown above the hanzi)
  const saveList = useMutation({
    mutationFn: async (pronunciations: string[]) => {
      const res = await fetch(
        `/api/projects/${projectId}/readings/${encodeURIComponent(char)}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mode: 'replace', pronunciations }),
        },
      )
      if (!res.ok) throw new ApiError((await res.json()).detail, res.statusText)
      return res.json()
    },
    onSuccess: () => {
      setError(null)
      setNewReading('')
      invalidate()
    },
    onError: (e) => setError(e),
  })

  const reset = useMutation({
    mutationFn: async () => {
      await fetch(`/api/projects/${projectId}/readings/${encodeURIComponent(char)}`, {
        method: 'DELETE',
      })
    },
    onSuccess: () => {
      setError(null)
      invalidate()
    },
  })

  useEffect(() => {
    const fromParam = params.get('char')
    if (fromParam) {
      setChar(fromParam)
      setInput(fromParam)
    }
  }, [params])

  if (!project) return null

  const overrides = Object.entries(project.glyph_overrides.readings)

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-8 py-8">
      <header>
        <h2 className="text-lg font-bold text-slate-100">{t('readings.title')}</h2>
        <p className="mt-1 text-sm text-slate-500">{t('readings.subtitle')}</p>
      </header>

      <Card title={t('readings.selectChar')}>
        <div className="flex gap-3">
          <Input
            className="max-w-[8rem] text-center text-2xl"
            value={input}
            maxLength={1}
            placeholder="中"
            onChange={(e) => setInput(e.target.value)}
          />
          <Button onClick={() => setChar(input)} disabled={input.length !== 1}>
            {t('readings.show')}
          </Button>
        </div>
      </Card>

      {char && reading.data && (
        <Card
          title={t('readings.readingOf', { char })}
          actions={
            reading.data.override ? (
              <Badge tone="accent">{t('readings.changed')}</Badge>
            ) : (
              <Badge>{t('readings.baseData')}</Badge>
            )
          }
        >
          <div className="flex gap-6">
            <div className="w-32 shrink-0">
              {preview.data?.items[0] ? (
                <div
                  className="text-slate-100"
                  dangerouslySetInnerHTML={{ __html: preview.data.items[0].svg }}
                />
              ) : (
                <div className="flex h-32 items-center justify-center">
                  <Spinner />
                </div>
              )}
            </div>

            <div className="flex-1 space-y-4">
              <ReadingList
                readings={reading.data.readings}
                onChange={(next) => saveList.mutate(next)}
                busy={saveList.isPending}
                t={t}
              />

              <div className="flex gap-2 border-t border-line pt-4">
                <Input
                  className="max-w-[10rem]"
                  placeholder="zhōng"
                  value={newReading}
                  onChange={(e) => setNewReading(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && newReading.trim()) {
                      saveList.mutate([...reading.data!.readings, newReading.trim()])
                    }
                  }}
                />
                <Button
                  disabled={!newReading.trim() || saveList.isPending}
                  onClick={() =>
                    saveList.mutate([...reading.data!.readings, newReading.trim()])
                  }
                >
                  <span className="flex items-center gap-1">
                    <Plus className="h-4 w-4" /> {t('common.add')}
                  </span>
                </Button>
                {reading.data.override && (
                  <Button variant="ghost" onClick={() => reset.mutate()}>
                    <span className="flex items-center gap-1">
                      <RotateCcw className="h-4 w-4" /> {t('readings.resetToBase')}
                    </span>
                  </Button>
                )}
              </div>
              {error != null && (
                <p className="text-sm text-rose-400">{displayError(error)}</p>
              )}
            </div>
          </div>
        </Card>
      )}

      {overrides.length > 0 && (
        <Card title={t('readings.changedChars', { count: overrides.length })}>
          <ul className="divide-y divide-line">
            {overrides.map(([overrideChar, override]) => (
              <li key={overrideChar} className="flex items-center gap-3 py-2">
                <button
                  className="text-xl text-slate-100 hover:text-accent-hover"
                  onClick={() => {
                    setChar(overrideChar)
                    setInput(overrideChar)
                  }}
                >
                  {overrideChar}
                </button>
                <span className="flex-1 text-sm text-slate-400">
                  {override.pronunciations.join(', ')}
                </span>
                <button
                  className="text-slate-600 hover:text-rose-400"
                  title={t('readings.discardTitle')}
                  onClick={async () => {
                    await fetch(
                      `/api/projects/${projectId}/readings/${encodeURIComponent(overrideChar)}`,
                      { method: 'DELETE' },
                    )
                    queryClient.invalidateQueries({ queryKey: ['project', projectId] })
                    queryClient.invalidateQueries({
                      queryKey: ['reading', projectId, overrideChar],
                    })
                  }}
                >
                  <X className="h-4 w-4" />
                </button>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  )
}

/** Ordered reading list with HTML5 drag & drop reordering and deletion. */
function ReadingList({
  readings,
  onChange,
  busy,
  t,
}: {
  readings: string[]
  onChange: (next: string[]) => void
  busy: boolean
  t: (key: string, opts?: Record<string, unknown>) => string
}) {
  const [dragIndex, setDragIndex] = useState<number | null>(null)
  const [overIndex, setOverIndex] = useState<number | null>(null)

  const drop = () => {
    if (dragIndex === null || overIndex === null || dragIndex === overIndex) {
      setDragIndex(null)
      setOverIndex(null)
      return
    }
    const next = [...readings]
    const [moved] = next.splice(dragIndex, 1)
    next.splice(overIndex, 0, moved)
    setDragIndex(null)
    setOverIndex(null)
    onChange(next)
  }

  if (readings.length === 0) {
    return <p className="text-sm text-slate-500">{t('readings.empty')}</p>
  }

  return (
    <ul className={`space-y-1.5 ${busy ? 'pointer-events-none opacity-60' : ''}`}>
      {readings.map((reading, index) => (
        <li
          key={`${reading}-${index}`}
          draggable
          onDragStart={() => setDragIndex(index)}
          onDragOver={(e) => {
            e.preventDefault()
            setOverIndex(index)
          }}
          onDrop={drop}
          onDragEnd={() => {
            setDragIndex(null)
            setOverIndex(null)
          }}
          className={`flex cursor-grab items-center gap-2 rounded-lg border px-3 py-2 transition-colors active:cursor-grabbing ${
            overIndex === index && dragIndex !== null && dragIndex !== index
              ? 'border-accent bg-accent/10'
              : 'border-line bg-surface'
          } ${dragIndex === index ? 'opacity-40' : ''}`}
        >
          <GripVertical className="h-4 w-4 shrink-0 text-slate-600" />
          <span className="flex-1 text-sm text-slate-200">{reading}</span>
          {index === 0 ? (
            <Badge tone="success">{t('readings.default')}</Badge>
          ) : (
            <Badge>ss0{index + 1}</Badge>
          )}
          <button
            className="text-slate-600 hover:text-rose-400 disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:text-slate-600"
            title={
              readings.length === 1
                ? t('readings.lastCannotDelete')
                : t('readings.deleteThis')
            }
            disabled={readings.length === 1}
            onClick={() => onChange(readings.filter((_, i) => i !== index))}
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </li>
      ))}
    </ul>
  )
}
