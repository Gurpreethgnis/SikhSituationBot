'use client'

import React from 'react'
import { useTranslation } from '../contexts/TranslationContext.jsx'
import './ParmaanDiscoveryBar.css'

const TYPES = [
  { id: 'similar', labelKey: 'parmaanDiscoverySimilar' },
  { id: 'topic', labelKey: 'parmaanDiscoveryTopic' },
  { id: 'dissimilar', labelKey: 'parmaanDiscoveryContrasts' },
]

/**
 * Shown when chat is in Parmaan Search mode: discovery type + optional shabad count (1–15).
 */
export default function ParmaanDiscoveryBar({
  discoveryType,
  onDiscoveryTypeChange,
  shabadCount,
  onShabadCountChange,
  disabled,
}) {
  const { t } = useTranslation()

  return (
    <div className="parmaan-discovery-bar" role="group" aria-label={t('parmaanDiscoveryGroupLabel')}>
      <div className="parmaan-discovery-bar__types">
        {TYPES.map(({ id, labelKey }) => (
          <button
            key={id}
            type="button"
            className={`parmaan-discovery-bar__pill ${discoveryType === id ? 'parmaan-discovery-bar__pill--active' : ''}`}
            onClick={() => onDiscoveryTypeChange(id)}
            disabled={disabled}
            aria-pressed={discoveryType === id}
          >
            {t(labelKey)}
          </button>
        ))}
      </div>
      <label className="parmaan-discovery-bar__count">
        <span className="parmaan-discovery-bar__count-label">{t('parmaanShabadCountLabel')}</span>
        <select
          value={shabadCount}
          onChange={(e) => onShabadCountChange(Number(e.target.value))}
          disabled={disabled}
          aria-label={t('parmaanShabadCountLabel')}
        >
          {Array.from({ length: 15 }, (_, i) => i + 1).map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </select>
      </label>
    </div>
  )
}
