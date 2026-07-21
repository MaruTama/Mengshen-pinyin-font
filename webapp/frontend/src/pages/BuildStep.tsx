import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, CircleAlert, Download, FolderOpen, Hammer } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { api } from '../api'
import { Badge, Button, Card, Input, Progress, Spinner } from '../components/ui'
import type { TaskState } from '../types'
import { useProject } from './ProjectLayout'

export default function BuildStep() {
  const { project, projectId } = useProject()
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  const health = useQuery({ queryKey: ['health'], queryFn: api.health })

  const anyRunning =
    project?.tasks.prepare.status === 'running' ||
    project?.tasks.build.status === 'running'

  // Poll while a task is running
  useQuery({
    queryKey: ['project', projectId, 'poll'],
    queryFn: async () => {
      const fresh = await api.getProject(projectId)
      queryClient.setQueryData(['project', projectId], fresh)
      return fresh
    },
    refetchInterval: 1000,
    enabled: Boolean(anyRunning),
  })

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ['project', projectId] })

  const startPrepare = useMutation({
    mutationFn: () => api.startPrepare(projectId),
    onSuccess: invalidate,
  })
  const startBuild = useMutation({
    mutationFn: () => api.startBuild(projectId),
    onSuccess: invalidate,
  })
  const patchOutput = useMutation({
    mutationFn: (family_name: string) =>
      api.patchProject(projectId, {
        output: { ...project!.output, family_name },
      }),
    onSuccess: invalidate,
  })

  if (!project) return null

  const toolsOk = health.data ? health.data.missing_tools.length === 0 : true
  const licensesOk =
    project.license.base.acknowledged && project.license.pinyin.acknowledged
  const prepareDone = project.tasks.prepare.status === 'done'
  const buildDone = project.tasks.build.status === 'done'

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-8 py-8">
      <header>
        <h2 className="text-lg font-bold text-slate-100">{t('build.title')}</h2>
        <p className="mt-1 text-sm text-slate-500">{t('build.subtitle')}</p>
      </header>

      <Card title={t('build.checklist')}>
        <ul className="space-y-2">
          <CheckItem ok={toolsOk} label={t('build.check.tools')} />
          <CheckItem
            ok={Boolean(project.base_font && project.pinyin_font)}
            label={t('build.check.fonts')}
          />
          <CheckItem ok={licensesOk} label={t('build.check.licenses')} />
          <CheckItem ok={prepareDone} label={t('build.check.prepare')} />
        </ul>
      </Card>

      <Card title={t('build.output')}>
        <div className="flex items-center gap-3">
          <div className="flex-1">
            <label className="mb-1 block text-xs text-slate-500">
              {t('build.familyName')}
            </label>
            <Input
              defaultValue={project.output.family_name}
              onBlur={(e) => {
                if (e.target.value !== project.output.family_name) {
                  patchOutput.mutate(e.target.value)
                }
              }}
            />
          </div>
          <div className="w-28">
            <label className="mb-1 block text-xs text-slate-500">
              {t('build.version')}
            </label>
            <Input defaultValue={project.output.version} disabled />
          </div>
        </div>
        {project.base_font?.source.startsWith('builtin:') && (
          <p className="mt-2 text-xs text-slate-500">{t('build.presetNameNote')}</p>
        )}
      </Card>

      <TaskCard
        title={t('build.prepareTitle')}
        task={project.tasks.prepare}
        actionLabel={t('build.prepareAction')}
        onStart={() => startPrepare.mutate()}
        disabled={!licensesOk || !toolsOk || anyRunning}
      />
      <TaskCard
        title={t('build.buildTitle')}
        task={project.tasks.build}
        actionLabel={t('build.buildAction')}
        onStart={() => startBuild.mutate()}
        disabled={!prepareDone || !toolsOk || anyRunning}
        icon={<Hammer className="h-4 w-4" />}
      />

      {buildDone && (
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-slate-100">
                {t('build.builtFile', { name: project.output.family_name })}
              </p>
              <p className="text-xs text-slate-500">{t('build.buildDoneDownload')}</p>
            </div>
            <a href={`/api/projects/${projectId}/download`} download>
              <Button>
                <span className="flex items-center gap-2">
                  <Download className="h-4 w-4" /> {t('common.download')}
                </span>
              </Button>
            </a>
          </div>
        </Card>
      )}

      <StorageCard projectId={projectId} refreshKey={`${project.tasks.prepare.status}-${project.tasks.build.status}`} />
    </div>
  )
}

interface StorageEntry {
  name: string
  path: string
  size: number
}

const STORAGE_GROUPS = ['state', 'fonts', 'intermediate', 'output'] as const

function formatSize(bytes: number): string {
  if (bytes >= 1 << 30) return `${(bytes / (1 << 30)).toFixed(1)} GB`
  if (bytes >= 1 << 20) return `${(bytes / (1 << 20)).toFixed(1)} MB`
  if (bytes >= 1 << 10) return `${(bytes / (1 << 10)).toFixed(1)} KB`
  return `${bytes} B`
}

function StorageCard({ projectId, refreshKey }: { projectId: string; refreshKey: string }) {
  const { t } = useTranslation()
  const storage = useQuery({
    queryKey: ['storage', projectId, refreshKey],
    queryFn: async () => {
      const res = await fetch(`/api/projects/${projectId}/storage`)
      return res.json() as Promise<{ groups: Record<string, StorageEntry[]>; total: number }>
    },
  })

  if (!storage.data) return null

  return (
    <Card
      title={
        <span className="flex items-center gap-2">
          <FolderOpen className="h-4 w-4 text-slate-500" />
          {t('build.storage.title', { size: formatSize(storage.data.total) })}
        </span>
      }
    >
      <div className="space-y-4">
        {STORAGE_GROUPS.map((key) => {
          const rows = storage.data!.groups[key] ?? []
          if (rows.length === 0) return null
          return (
            <div key={key}>
              <p className="mb-1.5 text-xs font-medium text-slate-400">
                {t(`build.storage.group.${key}`)}
              </p>
              <ul className="space-y-1">
                {rows.map((row) => (
                  <li
                    key={row.path}
                    className="flex items-center justify-between rounded-md bg-surface px-3 py-1.5 text-xs"
                  >
                    <span className="truncate font-mono text-slate-400" title={row.path}>
                      {row.path}
                    </span>
                    <span className="ml-3 shrink-0 text-slate-500">
                      {formatSize(row.size)}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )
        })}
        <p className="text-xs text-slate-600">
          {t('build.storage.note', { id: projectId })}
        </p>
      </div>
    </Card>
  )
}

function CheckItem({ ok, label }: { ok: boolean; label: string }) {
  return (
    <li className="flex items-center gap-2 text-sm">
      {ok ? (
        <Check className="h-4 w-4 text-emerald-400" />
      ) : (
        <CircleAlert className="h-4 w-4 text-amber-400" />
      )}
      <span className={ok ? 'text-slate-300' : 'text-slate-500'}>{label}</span>
    </li>
  )
}

function TaskCard({
  title,
  task,
  actionLabel,
  onStart,
  disabled,
  icon,
}: {
  title: string
  task: TaskState
  actionLabel: string
  onStart: () => void
  disabled: boolean
  icon?: React.ReactNode
}) {
  const { t } = useTranslation()
  return (
    <Card
      title={title}
      actions={
        task.status === 'done' ? (
          <Badge tone="success">{t('build.status.done')}</Badge>
        ) : task.status === 'running' ? (
          <Badge tone="accent">{t('build.status.running', { stage: task.stage })}</Badge>
        ) : task.status === 'error' ? (
          <Badge tone="error">{t('build.status.error')}</Badge>
        ) : (
          <Badge>{t('build.status.idle')}</Badge>
        )
      }
    >
      {task.status === 'running' && (
        <div className="mb-3 flex items-center gap-3">
          <Spinner />
          <Progress value={task.progress} />
        </div>
      )}
      {task.status === 'error' && (
        <p className="mb-3 break-all rounded-lg bg-rose-500/10 px-3 py-2 text-xs text-rose-300">
          {task.error}
        </p>
      )}
      {task.status !== 'running' && (
        <Button variant={task.status === 'done' ? 'ghost' : 'primary'} disabled={disabled} onClick={onStart}>
          <span className="flex items-center gap-2">
            {icon}
            {task.status === 'done' ? t('build.status.rerun') : actionLabel}
          </span>
        </Button>
      )}
    </Card>
  )
}
