import { AlertTriangle } from 'lucide-react'

export default function ErrorBanner({ title = 'Something went wrong', message, onRetry }) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-4">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 h-5 w-5 flex-none text-red-600" />
        <div className="flex-1">
          <p className="text-sm font-semibold text-red-800">{title}</p>
          {message && <p className="mt-1 text-sm text-red-700">{message}</p>}
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="flex-none rounded-md border border-red-300 bg-white px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50"
          >
            Try again
          </button>
        )}
      </div>
    </div>
  )
}
