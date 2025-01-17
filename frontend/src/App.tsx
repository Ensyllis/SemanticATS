'use client';

import ResumeSearch from './components/ResumeSearch'
import { useState, useEffect } from 'react'

function App() {
  const [darkMode, setDarkMode] = useState(false)

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <header className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto py-4 px-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Semantic ATS</h1>
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300"
          >
            {darkMode ? '🌞' : '🌙'}
          </button>
        </div>
      </header>
      <main className="max-w-7xl mx-auto py-6 px-4">
        <ResumeSearch darkMode={darkMode} />
      </main>
    </div>
  )
}

export default App