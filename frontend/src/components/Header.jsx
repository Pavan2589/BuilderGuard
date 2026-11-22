import { ShieldCheck, GitPullRequest, FlaskConical } from 'lucide-react'

const TABS = [
  { id: 'pr-review', label: 'PR Review', icon: GitPullRequest },
  { id: 'security-lab', label: 'Security Lab', icon: FlaskConical },
]

export default function Header({ activeTab, onChangeTab }) {
  return (
    <header className="border-b border-neutral-200 bg-white">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-6 w-6 text-neutral-900" />
          <span className="text-lg font-bold tracking-tight text-neutral-900">BuilderGuard</span>
        </div>

        <nav className="flex gap-1 rounded-lg bg-neutral-100 p-1">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => onChangeTab(id)}
              className={`inline-flex items-center gap-2 rounded-md px-3.5 py-2 text-sm font-medium transition ${
                activeTab === id
                  ? 'bg-white text-neutral-900 shadow-sm'
                  : 'text-neutral-500 hover:text-neutral-800'
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </nav>
      </div>
    </header>
  )
}
