import { useCallback, useState } from 'react'
import { ShieldAlert } from 'lucide-react'
import PRForm from './PRForm'
import ReviewSummary from './ReviewSummary'
import FindingsList from './FindingsList'
import Limitations from './Limitations'
import ToolTimeline from '../common/ToolTimeline'
import ErrorBanner from '../common/ErrorBanner'
import { createReview, ApiError } from '../../api/client'
import { MOCK_REVIEW } from '../../data/mockData'

function ReviewSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-28 rounded-xl border border-neutral-200 bg-white p-5">
        <div className="h-3 w-32 rounded bg-neutral-200" />
        <div className="mt-4 h-3 w-full rounded bg-neutral-100" />
        <div className="mt-2 h-3 w-5/6 rounded bg-neutral-100" />
      </div>
      <div className="h-40 rounded-lg border border-neutral-200 bg-white p-4">
        <div className="h-3 w-24 rounded bg-neutral-200" />
        <div className="mt-4 h-3 w-full rounded bg-neutral-100" />
        <div className="mt-2 h-3 w-2/3 rounded bg-neutral-100" />
      </div>
    </div>
  )
}

export default function PRReviewTab() {
  const [prUrl, setPrUrl] = useState('')
  const [status, setStatus] = useState('idle') // idle | loading | success | error
  const [review, setReview] = useState(null)
  const [errorMessage, setErrorMessage] = useState('')

  const runReview = useCallback(async (url) => {
    setPrUrl(url)
    setStatus('loading')
    setErrorMessage('')
    try {
      const result = await createReview(url)
      setReview(result)
      if (result.status === 'failed') {
        setStatus('error')
        setErrorMessage(result.summary || 'The review agent could not complete this review.')
      } else {
        setStatus('success')
      }
    } catch (err) {
      setStatus('error')
      setErrorMessage(err instanceof ApiError ? err.message : 'Unexpected error while running the review.')
    }
  }, [])

  const loadSample = useCallback(() => {
    setPrUrl('https://github.com/owner/repo/pull/123')
    setReview(MOCK_REVIEW)
    setStatus('success')
    setErrorMessage('')
  }, [])

  const retry = useCallback(() => {
    if (prUrl) runReview(prUrl)
  }, [prUrl, runReview])

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PRForm onSubmit={runReview} onLoadSample={loadSample} loading={status === 'loading'} />

      {status === 'loading' && <ReviewSkeleton />}

      {status === 'error' && (
        <ErrorBanner
          title="Review failed"
          message={errorMessage}
          onRetry={prUrl ? retry : undefined}
        />
      )}

      {status === 'success' && review && (
        <>
          <ReviewSummary review={review} />

          <div>
            <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-neutral-500">
              <ShieldAlert className="h-4 w-4" />
              Findings
            </h2>
            <FindingsList findings={review.findings} />
          </div>

          <ToolTimeline toolCalls={review.tool_calls} title="Tool execution timeline" />

          <Limitations limitations={review.limitations} />
        </>
      )}

      {status === 'idle' && (
        <div className="rounded-xl border border-dashed border-neutral-300 bg-white p-10 text-center">
          <p className="text-sm text-neutral-400">
            Paste a GitHub pull request URL above and start a review, or load sample data to
            preview the layout.
          </p>
        </div>
      )}
    </div>
  )
}
