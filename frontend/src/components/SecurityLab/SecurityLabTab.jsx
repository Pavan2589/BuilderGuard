import { useCallback, useEffect, useMemo, useState } from 'react'
import { FlaskConical, ShieldAlert } from 'lucide-react'
import CategorySelector from './CategorySelector'
import AttackTestCard from './AttackTestCard'
import AttackDetails from './AttackDetails'
import ErrorBanner from '../common/ErrorBanner'
import SampleDataBadge from '../common/SampleDataBadge'
import { fetchSecurityTests, runSecurityTest, ApiError } from '../../api/client'
import { MOCK_SECURITY_TESTS, MOCK_SECURITY_RESULT } from '../../data/mockData'

export default function SecurityLabTab() {
  const [testsStatus, setTestsStatus] = useState('loading') // loading | success | error
  const [tests, setTests] = useState([])
  const [testsError, setTestsError] = useState('')
  const [usingSampleTests, setUsingSampleTests] = useState(false)

  const [selectedCategory, setSelectedCategory] = useState('all')
  const [selectedTestId, setSelectedTestId] = useState(null)
  const [runStates, setRunStates] = useState({}) // test_id -> { status, result, error }

  const loadTests = useCallback(async () => {
    setTestsStatus('loading')
    setTestsError('')
    setUsingSampleTests(false)
    try {
      const data = await fetchSecurityTests()
      setTests(data.tests ?? [])
      setTestsStatus('success')
    } catch (err) {
      setTestsStatus('error')
      setTestsError(err instanceof ApiError ? err.message : 'Unexpected error while loading tests.')
    }
  }, [])

  useEffect(() => {
    loadTests()
  }, [loadTests])

  const loadSampleTests = useCallback(() => {
    setTests(MOCK_SECURITY_TESTS)
    setUsingSampleTests(true)
    setTestsStatus('success')
    setTestsError('')
    setSelectedCategory('all')
    setSelectedTestId(null)
    setRunStates({})
  }, [])

  const categories = useMemo(
    () => [...new Set(tests.map((t) => t.category))].sort(),
    [tests]
  )

  const filteredTests = useMemo(
    () =>
      selectedCategory === 'all' ? tests : tests.filter((t) => t.category === selectedCategory),
    [tests, selectedCategory]
  )

  const selectedTest = useMemo(
    () => tests.find((t) => t.id === selectedTestId) ?? null,
    [tests, selectedTestId]
  )

  const handleRun = useCallback(
    async (testId) => {
      setRunStates((prev) => ({ ...prev, [testId]: { status: 'loading' } }))

      if (usingSampleTests) {
        await new Promise((resolve) => setTimeout(resolve, 600))
        setRunStates((prev) => ({
          ...prev,
          [testId]: { status: 'success', result: { ...MOCK_SECURITY_RESULT, test_id: testId } },
        }))
        return
      }

      try {
        const result = await runSecurityTest(testId)
        setRunStates((prev) => ({ ...prev, [testId]: { status: 'success', result } }))
      } catch (err) {
        setRunStates((prev) => ({
          ...prev,
          [testId]: {
            status: 'error',
            error: err instanceof ApiError ? err.message : 'Unexpected error while running the test.',
          },
        }))
      }
    },
    [usingSampleTests]
  )

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-neutral-500">
          <ShieldAlert className="h-4 w-4" />
          Attack categories
        </h2>
        <div className="flex items-center gap-2">
          {usingSampleTests && <SampleDataBadge />}
          <button
            onClick={loadSampleTests}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-violet-600 hover:text-violet-700"
          >
            <FlaskConical className="h-3.5 w-3.5" />
            Load sample data
          </button>
        </div>
      </div>

      {testsStatus === 'error' && (
        <ErrorBanner title="Could not load security tests" message={testsError} onRetry={loadTests} />
      )}

      {testsStatus === 'loading' && (
        <div className="grid animate-pulse gap-4 lg:grid-cols-[320px_1fr]">
          <div className="space-y-3">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-20 rounded-lg border border-neutral-200 bg-white" />
            ))}
          </div>
          <div className="h-64 rounded-xl border border-neutral-200 bg-white" />
        </div>
      )}

      {testsStatus === 'success' && (
        <>
          <div className="mb-4">
            <CategorySelector
              categories={categories}
              selected={selectedCategory}
              onSelect={setSelectedCategory}
            />
          </div>

          <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
            <div className="space-y-3">
              {filteredTests.length === 0 && (
                <p className="text-sm text-neutral-400">No tests in this category.</p>
              )}
              {filteredTests.map((test) => (
                <AttackTestCard
                  key={test.id}
                  test={test}
                  selected={test.id === selectedTestId}
                  lastVerdict={runStates[test.id]?.result?.verdict}
                  onSelect={setSelectedTestId}
                />
              ))}
            </div>

            <AttackDetails
              test={selectedTest}
              runState={runStates[selectedTestId]}
              onRun={handleRun}
            />
          </div>
        </>
      )}
    </div>
  )
}
