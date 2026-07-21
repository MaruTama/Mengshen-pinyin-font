import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { DuoyinziTab } from './duoyinzi/DuoyinziTab'
import { GsubTab } from './duoyinzi/GsubTab'
import { IvsTab } from './duoyinzi/IvsTab'
import { VerifyTab } from './duoyinzi/VerifyTab'

export default function DuoyinziStep() {
  const { t } = useTranslation()
  const [tab, setTab] = useState<'duoyinzi' | 'gsub' | 'ivs' | 'verify'>('duoyinzi')

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b border-line px-6 py-3">
        {(['duoyinzi', 'gsub', 'ivs', 'verify'] as const).map((value) => (
          <button
            key={value}
            onClick={() => setTab(value)}
            className={`rounded-lg px-4 py-1.5 text-sm transition-colors ${
              tab === value
                ? 'bg-accent/15 font-medium text-accent-hover'
                : 'text-slate-400 hover:bg-surface-overlay'
            }`}
          >
            {t(`duoyinzi.tab.${value}`)}
          </button>
        ))}
      </div>
      {tab === 'duoyinzi' ? (
        <DuoyinziTab />
      ) : tab === 'gsub' ? (
        <GsubTab />
      ) : tab === 'ivs' ? (
        <IvsTab />
      ) : (
        <VerifyTab />
      )}
    </div>
  )
}
