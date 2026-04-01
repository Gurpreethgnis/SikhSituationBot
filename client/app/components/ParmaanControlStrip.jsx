'use client'

import React from 'react'
import { useTranslation } from '../contexts/TranslationContext.jsx'
import './ParmaanControlStrip.css'

const DISCOVERY_TYPES = [
  { id: 'similar', labelKey: 'parmaanDiscoverySimilar' },
  { id: 'topic', labelKey: 'parmaanDiscoveryTopic' },
  { id: 'dissimilar', labelKey: 'parmaanDiscoveryContrasts' },
]

const COMPOSER_ACTIONS = [
  { id: 'line', labelKey: 'parmaanSearchModeLine' },
  { id: 'theme', labelKey: 'parmaanSearchModeTheme' },
  { id: 'ask', labelKey: 'parmaanSearchModeAsk' },
]

/**
 * Single Parmaan footer toolbar: Line | Theme | Ask, discovery type, and shabad count.
 */
export default function ParmaanControlStrip({
  composerAction,
  onComposerActionChange,
  discoveryType,
  onDiscoveryTypeChange,
  shabadCount,
  onShabadCountChange,
  disabled,
}) {
  const { t } = useTranslation()

  return (
    <div className="parmaan-control-strip" role="toolbar" aria-label={t('parmaanControlStripLabel')}>
      <div
        className="parmaan-control-strip__group parmaan-control-strip__group--composer"
        role="tablist"
        aria-label={t('parmaanComposerModesLabel')}
      >
        {COMPOSER_ACTIONS.map(({ id, labelKey }) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={composerAction === id}
            className={`parmaan-control-strip__tab ${composerAction === id ? 'parmaan-control-strip__tab--active' : ''}`}
            onClick={() => onComposerActionChange(id)}
            disabled={disabled}
          >
            {t(labelKey)}
          </button>
        ))}
      </div>

      <span className="parmaan-control-strip__divider" aria-hidden="true" />

      <div
        className="parmaan-control-strip__group parmaan-control-strip__group--discovery"
        role="group"
        aria-label={t('parmaanDiscoveryGroupLabel')}
      >
        {DISCOVERY_TYPES.map(({ id, labelKey }) => (
          <button
            key={id}
            type="button"
            className={`parmaan-control-strip__pill ${discoveryType === id ? 'parmaan-control-strip__pill--active' : ''}`}
            onClick={() => onDiscoveryTypeChange(id)}
            disabled={disabled}
            aria-pressed={discoveryType === id}
          >
            {t(labelKey)}
          </button>
        ))}
      </div>

      <label className="parmaan-control-strip__count">
        <span className="parmaan-control-strip__count-label">{t('parmaanShabadCountLabel')}</span>
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
