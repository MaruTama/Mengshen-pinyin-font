import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Languages, Plus, Trash2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { LanguageSwitcher } from '../components/LanguageSwitcher'
import { Badge, Button, Card, Spinner } from '../components/ui'

export default function Home() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  const projects = useQuery({ queryKey: ['projects'], queryFn: api.listProjects })
  const health = useQuery({ queryKey: ['health'], queryFn: api.health })

  const createMutation = useMutation({
    mutationFn: () => api.createProject(t('home.newProjectName')),
    onSuccess: (project) => navigate(`/projects/${project.id}/fonts`),
  })
  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteProject(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['projects'] }),
  })

  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <header className="mb-10 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent/20">
            <Languages className="h-5 w-5 text-accent-hover" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-100">{t('home.title')}</h1>
            <p className="text-sm text-slate-500">{t('home.subtitle')}</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <LanguageSwitcher />
          <Button onClick={() => createMutation.mutate()}>
            <span className="flex items-center gap-2">
              <Plus className="h-4 w-4" /> {t('home.newProject')}
            </span>
          </Button>
        </div>
      </header>

      {health.data && health.data.missing_tools.length > 0 && (
        <div className="mb-6 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-300">
          {t('home.missingTools', { tools: health.data.missing_tools.join(', ') })}
        </div>
      )}

      {projects.isLoading && (
        <div className="flex justify-center py-20">
          <Spinner />
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {projects.data?.map((project) => (
          <Card key={project.id} className="transition-colors hover:border-accent/50">
            <button
              className="w-full text-left"
              onClick={() => navigate(`/projects/${project.id}`)}
            >
              <div className="mb-2 flex items-center justify-between">
                <span className="font-semibold text-slate-100">{project.name}</span>
                <StepBadge project={project} />
              </div>
              <p className="text-xs text-slate-500">
                {project.base_font?.family_name ?? t('home.baseFontUnset')}
                {project.pinyin_font && ` + ${project.pinyin_font.family_name}`}
              </p>
              <p className="mt-1 text-xs text-slate-600">
                {t('home.updatedAt', {
                  date: new Date(project.updated_at).toLocaleString(),
                })}
              </p>
            </button>
            <div className="mt-3 flex justify-end border-t border-line pt-3">
              <Button
                variant="ghost"
                className="!px-2 !py-1"
                onClick={() => {
                  if (confirm(t('home.deleteConfirm', { name: project.name }))) {
                    deleteMutation.mutate(project.id)
                  }
                }}
              >
                <Trash2 className="h-4 w-4 text-slate-500" />
              </Button>
            </div>
          </Card>
        ))}
      </div>

      {projects.data?.length === 0 && (
        <div className="rounded-xl border border-dashed border-line py-20 text-center text-slate-500">
          {t('home.empty')}
        </div>
      )}
    </div>
  )
}

function StepBadge({ project }: { project: { tasks: { build: { status: string } }; step: string } }) {
  const { t } = useTranslation()
  if (project.tasks.build.status === 'done')
    return <Badge tone="success">{t('home.built')}</Badge>
  if (project.tasks.build.status === 'running')
    return <Badge tone="accent">{t('home.building')}</Badge>
  return <Badge>{t(`nav.steps.${project.step}`, project.step)}</Badge>
}
