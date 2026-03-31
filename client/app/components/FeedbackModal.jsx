'use client'

import React, { useCallback, useEffect, useId, useRef, useState } from 'react'
import './FeedbackModal.css'

const FEEDBACK_TYPES = [
  { value: 'bug', labelKey: 'feedbackTypeBug' },
  { value: 'improvement', labelKey: 'feedbackTypeImprovement' },
  { value: 'other', labelKey: 'feedbackTypeOther' },
]

export default function FeedbackModal({
  open,
  onClose,
  responseContent,
  chatId,
  token,
  baseUrl,
  t,
}) {
  const titleId = useId()
  const descId = useId()
  const fileInputRef = useRef(null)
  const [feedbackType, setFeedbackType] = useState('bug')
  const [description, setDescription] = useState('')
  const [screenshotDataUrl, setScreenshotDataUrl] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [issueUrl, setIssueUrl] = useState('')

  const reset = useCallback(() => {
    setFeedbackType('bug')
    setDescription('')
    setScreenshotDataUrl(null)
    setSubmitting(false)
    setError('')
    setIssueUrl('')
    if (fileInputRef.current) fileInputRef.current.value = ''
  }, [])

  useEffect(() => {
    if (!open) {
      reset()
      return
    }
    const onKey = (e) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onClose, reset])

  const handlePaste = useCallback(
    (e) => {
      if (!open) return
      const items = e.clipboardData?.items
      if (!items) return
      for (let i = 0; i < items.length; i += 1) {
        const item = items[i]
        if (item.type.startsWith('image/')) {
          e.preventDefault()
          const file = item.getAsFile()
          if (!file) continue
          if (file.size > 2 * 1024 * 1024) {
            setError(t('feedbackScreenshotTooLarge'))
            continue
          }
          const reader = new FileReader()
          reader.onload = () => {
            setScreenshotDataUrl(typeof reader.result === 'string' ? reader.result : null)
            setError('')
          }
          reader.readAsDataURL(file)
          break
        }
      }
    },
    [open, t],
  )

  useEffect(() => {
    if (!open) return
    window.addEventListener('paste', handlePaste)
    return () => window.removeEventListener('paste', handlePaste)
  }, [open, handlePaste])

  const onFileChange = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (!file.type.startsWith('image/')) {
      setError(t('feedbackScreenshotInvalid'))
      return
    }
    if (file.size > 2 * 1024 * 1024) {
      setError(t('feedbackScreenshotTooLarge'))
      return
    }
    const reader = new FileReader()
    reader.onload = () => {
      setScreenshotDataUrl(typeof reader.result === 'string' ? reader.result : null)
      setError('')
    }
    reader.readAsDataURL(file)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setIssueUrl('')
    if (!token) {
      setError(t('feedbackSignInRequired'))
      return
    }
    const desc = description.trim()
    if (!desc) {
      setError(t('feedbackDescriptionRequired'))
      return
    }
    setSubmitting(true)
    try {
      const res = await fetch(`${baseUrl}/api/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          type: feedbackType,
          description: desc,
          response_content: responseContent || '',
          screenshot_base64: screenshotDataUrl || undefined,
          chat_id: chatId ?? undefined,
        }),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        if (res.status === 429) {
          throw new Error(t('feedbackRateLimit'))
        }
        if (res.status === 401) {
          throw new Error(t('feedbackSignInRequired'))
        }
        throw new Error(data.error || t('feedbackError'))
      }
      if (data.issue_url) {
        setIssueUrl(data.issue_url)
      }
    } catch (err) {
      setError(err.message || t('feedbackError'))
    } finally {
      setSubmitting(false)
    }
  }

  if (!open) return null

  return (
    <div className="feedback-modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="feedback-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descId}
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => e.stopPropagation()}
      >
        <div className="feedback-modal__header">
          <h2 id={titleId} className="feedback-modal__title">
            {t('feedbackModalTitle')}
          </h2>
          <button type="button" className="feedback-modal__close" onClick={onClose} aria-label={t('feedbackClose')}>
            ×
          </button>
        </div>

        <p id={descId} className="feedback-modal__hint">
          {t('feedbackModalHint')}
        </p>

        {!token && !issueUrl ? (
          <p className="feedback-modal__signin-banner" role="status">
            {t('feedbackSignInRequired')}
          </p>
        ) : null}

        {issueUrl ? (
          <div className="feedback-modal__success">
            <p>{t('feedbackThanks')}</p>
            <a href={issueUrl} target="_blank" rel="noopener noreferrer" className="feedback-modal__issue-link">
              {t('feedbackViewIssue')}
            </a>
            <button type="button" className="feedback-modal__done" onClick={onClose}>
              {t('feedbackClose')}
            </button>
          </div>
        ) : (
          <form className="feedback-form" onSubmit={handleSubmit}>
            <fieldset className="feedback-form__types">
              <legend className="sr-only">{t('feedbackTypeLegend')}</legend>
              {FEEDBACK_TYPES.map(({ value, labelKey }) => (
                <label key={value} className="feedback-form__radio">
                  <input
                    type="radio"
                    name="feedbackType"
                    value={value}
                    checked={feedbackType === value}
                    onChange={() => setFeedbackType(value)}
                  />
                  <span>{t(labelKey)}</span>
                </label>
              ))}
            </fieldset>

            <label className="feedback-form__label" htmlFor="feedback-description">
              {t('feedbackDescription')}
            </label>
            <textarea
              id="feedback-description"
              className="feedback-form__textarea"
              rows={5}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={t('feedbackDescriptionPlaceholder')}
              maxLength={5000}
              required
            />

            <div className="feedback-form__screenshot">
              <span className="feedback-form__label">{t('feedbackScreenshotLabel')}</span>
              <p className="feedback-form__screenshot-hint">{t('feedbackScreenshotHint')}</p>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/gif,image/webp"
                onChange={onFileChange}
                className="feedback-form__file"
              />
              {screenshotDataUrl ? (
                <div className="feedback-form__preview-wrap">
              <img src={screenshotDataUrl} alt="" className="feedback-form__preview" />
                  <button
                    type="button"
                    className="feedback-form__remove-img"
                    onClick={() => {
                      setScreenshotDataUrl(null)
                      if (fileInputRef.current) fileInputRef.current.value = ''
                    }}
                  >
                    {t('feedbackRemoveScreenshot')}
                  </button>
                </div>
              ) : null}
            </div>

            {error ? (
              <div className="feedback-form__error" role="alert">
                {error}
              </div>
            ) : null}

            <div className="feedback-form__actions">
              <button type="button" className="feedback-form__cancel" onClick={onClose} disabled={submitting}>
                {t('feedbackCancel')}
              </button>
              <button type="submit" className="feedback-form__submit" disabled={submitting}>
                {submitting ? t('feedbackSubmitting') : t('feedbackSubmit')}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
