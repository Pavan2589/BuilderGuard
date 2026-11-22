import { useState } from 'react'
import Header from './components/Header.jsx'
import PRReviewTab from './components/PRReview/PRReviewTab.jsx'
import SecurityLabTab from './components/SecurityLab/SecurityLabTab.jsx'

export default function App() {
  const [activeTab, setActiveTab] = useState('pr-review')

  return (
    <div className="min-h-screen bg-neutral-50">
      <Header activeTab={activeTab} onChangeTab={setActiveTab} />
      <main className="px-4 py-8">
        {activeTab === 'pr-review' ? <PRReviewTab /> : <SecurityLabTab />}
      </main>
    </div>
  )
}
