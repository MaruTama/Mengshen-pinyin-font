import { useQuery } from '@tanstack/react-query'
import {
  ArrowLeft,
  BookOpenText,
  FileText,
  Grid3X3,
  Package,
  Pencil,
  ScrollText,
  SlidersHorizontal,
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { NavLink, Outlet, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api'
import { LanguageSwitcher } from '../components/LanguageSwitcher'
import { Spinner } from '../components/ui'
import type { Project } from '../types'

const STEPS = [
  { path: 'fonts', icon: FileText },
  { path: 'license', icon: ScrollText },
  { path: 'adjust', icon: SlidersHorizontal },
  { path: 'glyphs', icon: Grid3X3 },
  { path: 'readings', icon: Pencil },
  { path: 'duoyinzi', icon: BookOpenText },
  { path: 'build', icon: Package },
] as const

export function useProject(): { project: Project | undefined; projectId: string } {
  const { projectId = '' } = useParams()
  const { data: project } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => api.getProject(projectId),
    enabled: Boolean(projectId),
  })
  return { project, projectId }
}

export default function ProjectLayout() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { project, projectId } = useProject()

  if (!project) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Spinner />
      </div>
    )
  }

  return (
    <div className="flex h-screen">
      <aside className="flex w-56 shrink-0 flex-col border-r border-line bg-surface-raised">
        <button
          className="flex items-center gap-2 border-b border-line px-5 py-4 text-left text-sm text-slate-400 hover:text-slate-200"
          onClick={() => navigate('/')}
        >
          <ArrowLeft className="h-4 w-4" /> {t('nav.projectList')}
        </button>
        <div className="border-b border-line px-5 py-4">
          <p className="truncate font-semibold text-slate-100">{project.name}</p>
          <p className="mt-0.5 truncate text-xs text-slate-500">
            {project.base_font?.family_name ?? t('nav.unset')}
          </p>
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {STEPS.map(({ path, icon: Icon }) => (
            <NavLink
              key={path}
              to={`/projects/${projectId}/${path}`}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? 'bg-accent/15 font-medium text-accent-hover'
                    : 'text-slate-400 hover:bg-surface-overlay hover:text-slate-200'
                }`
              }
            >
              <Icon className="h-4 w-4" /> {t(`nav.steps.${path}`)}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-line px-5 py-3">
          <LanguageSwitcher />
        </div>
        <TaskIndicator project={project} />
      </aside>
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}

function TaskIndicator({ project }: { project: Project }) {
  const { t } = useTranslation()
  const running =
    project.tasks.prepare.status === 'running'
      ? t('nav.preparingTemplate')
      : project.tasks.build.status === 'running'
        ? t('nav.buildingFont')
        : null
  if (!running) return null
  return (
    <div className="flex items-center gap-2 border-t border-line px-5 py-3 text-xs text-accent-hover">
      <Spinner /> {running}
    </div>
  )
}
