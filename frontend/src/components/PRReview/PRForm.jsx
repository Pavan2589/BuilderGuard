import { useState } from 'react'
import { Loader2, Play, FlaskConical } from 'lucide-react'

const PR_URL_PATTERN = /^https:\/\/github\.com\/[^/]+\/[^/]+\/pull\/\d+\/?$/

export default function PRForm({ onSubmit, onLoadSample, loading }) {
  const [value, setValue] = useState('')
  const [touched, setTouched] = useState(false)

  const isValid = PR_URL_PATTERN.test(value.trim())
  const showError = touched && value.trim().length > 0 && !isValid

  function handleSubmit(e) {
    e.preventDefault()
    setTouched(true)
    if (!isValid) return
    onSubmit(value.trim())
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-xl border border-neutral-200 bg-white p-5 shadow-sm">
      <label htmlFor="pr-url" className="block text-sm font-medium text-neutral-700">
        GitHub pull request URL
      </label>
      <div className="mt-2 flex flex-col gap-3 sm:flex-row">
        <input
          id="pr-url"
          type="text"
          inputMode="url"
          placeholder="https://github.com/owner/repo/pull/123"
          value={value}
          disabled={loading}
          onChange={(e) => setValue(e.target.value)}
          onBlur={() => setTouched(true)}
          className={`flex-1 rounded-lg border px-3 py-2.5 text-sm text-neutral-900 placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-offset-0 disabled:bg-neutral-50 disabled:text-neutral-400 ${
            showError
              ? 'border-red-300 focus:ring-red-200'
              : 'border-neutral-300 focus:border-neutral-400 focus:ring-neutral-200'
          }`}
        />
        <button
          type="submit"
          disabled={loading || value.trim().length === 0}
          className="inline-flex flex-none items-center justify-center gap-2 rounded-lg bg-neutral-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-neutral-800 disabled:cursor-not-allowed disabled:bg-neutral-300"
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Reviewing...
            </>
          ) : (
            <>
              <Play className="h-4 w-4" />
              Start Review
            </>
          )}
        </button>
      </div>
      {showError && (
        <p className="mt-2 text-sm text-red-600">
          Enter a full pull request URL, e.g. https://github.com/owner/repo/pull/123
        </p>
      )}
      <div className="mt-3 flex items-center justify-between">
        <p className="text-xs text-neutral-400">
          BuilderGuard will fetch the PR, run its review tools, and report findings.
        </p>
        <button
          type="button"
          onClick={onLoadSample}
          disabled={loading}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-violet-600 hover:text-violet-700 disabled:text-neutral-300"
        >
          <FlaskConical className="h-3.5 w-3.5" />
          Load sample data
        </button>
      </div>
    </form>
  )
}
