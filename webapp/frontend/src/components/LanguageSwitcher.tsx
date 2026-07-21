import { Languages } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { LANGUAGES } from '../i18n'

export function LanguageSwitcher({ className = '' }: { className?: string }) {
  const { i18n, t } = useTranslation()
  const current = LANGUAGES.find((l) => i18n.language.startsWith(l.code)) ?? LANGUAGES[0]

  return (
    <label
      className={`flex items-center gap-1.5 text-xs text-slate-400 ${className}`}
      title={t('lang.label')}
    >
      <Languages className="h-4 w-4 text-slate-500" />
      <select
        value={current.code}
        onChange={(e) => i18n.changeLanguage(e.target.value)}
        className="cursor-pointer rounded-md border border-line bg-surface px-2 py-1 text-slate-300 outline-none focus:border-accent"
      >
        {LANGUAGES.map((lang) => (
          <option key={lang.code} value={lang.code}>
            {lang.label}
          </option>
        ))}
      </select>
    </label>
  )
}
