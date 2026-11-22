import { Loader2, Play, MessageSquareText } from 'lucide-react'
import { formatCategory } from './CategorySelector'
import PayloadViewer from './PayloadViewer'
import VerdictBadge from './VerdictBadge'
import AssertionList from './AssertionList'
import ToolTimeline from '../common/ToolTimeline'
import ErrorBanner from '../common/ErrorBanner'
import SampleDataBadge from '../common/SampleDataBadge'

export default function AttackDetails({ test, runState, onRun }) {
  if (!test) {
    return (
      <div className="flex h-full items-center justify-center rounded-xl border border-dashed border-neutral-300 bg-white p-10 text-center">
        <p className="text-sm text-neutral-400">Select an attack test from the list to see details.</p>
      </div>
    )
  }

  const { status, result, error } = runState ?? { status: 'idle' }

  return (
    <div className="space-y-5">
      <div className="rounded-xl border border-neutral-200 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-neutral-400">
              {formatCategory(test.category)}
            </p>
            <h2 className="mt-1 text-lg font-semibold text-neutral-900">{test.name}</h2>
            <p className="mt-2 text-sm text-neutral-600">{test.description}</p>
          </div>
          <button
            onClick={() => onRun(test.id)}
            disabled={status === 'loading'}
            className="inline-flex flex-none items-center gap-2 rounded-lg bg-neutral-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-neutral-800 disabled:cursor-not-allowed disabled:bg-neutral-300"
          >
            {status === 'loading' ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Running...
              </>
            ) : (
              <>
                <Play className="h-4 w-4" />
                Run Test
              </>
            )}
          </button>
        </div>
        <p className="mt-3 text-xs font-mono text-neutral-400">{test.id}</p>
      </div>

      {status === 'loading' && (
        <div className="animate-pulse space-y-3">
          <div className="h-24 rounded-lg border border-neutral-200 bg-white" />
          <div className="h-24 rounded-lg border border-neutral-200 bg-white" />
        </div>
      )}

      {status === 'error' && <ErrorBanner title="Test run failed" message={error} onRetry={() => onRun(test.id)} />}

      {status === 'success' && result && (
        <>
          <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-neutral-200 bg-white p-5 shadow-sm">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-neutral-400">Verdict</p>
              <div className="mt-2">
                <VerdictBadge verdict={result.verdict} />
              </div>
            </div>
            {result._mock && <SampleDataBadge />}
          </div>

          <div className="rounded-lg border border-neutral-200 bg-white p-4">
            <h3 className="mb-2 text-sm font-semibold text-neutral-800">Explanation</h3>
            <p className="text-sm leading-relaxed text-neutral-600">{result.reason}</p>
          </div>

          <PayloadViewer payload={result.payload} />

          <div className="rounded-lg border border-neutral-200 bg-white p-4">
            <div className="mb-2 flex items-center gap-1.5 text-xs font-medium text-neutral-500">
              <MessageSquareText className="h-3.5 w-3.5" />
              Actual agent response
            </div>
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-neutral-800">
              {result.agent_response}
            </p>
          </div>

          <ToolTimeline toolCalls={result.tool_calls} title="Tool execution trace" />

          <div>
            <h3 className="mb-2 text-sm font-semibold text-neutral-800">Assertion results</h3>
            <AssertionList assertions={result.assertions} />
          </div>
        </>
      )}

      {status === 'idle' && (
        <div className="rounded-xl border border-dashed border-neutral-300 bg-white p-8 text-center">
          <p className="text-sm text-neutral-400">
            Run this test to see the attack payload, the agent&apos;s actual response, and the verdict.
          </p>
        </div>
      )}
    </div>
  )
}
