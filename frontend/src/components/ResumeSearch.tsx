'use client';

import { useState, useEffect } from 'react';
import { Search, ChevronDown, ChevronUp, Bookmark, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

type SearchMode = 'story' | 'personality' | 'resume';
type SearchResult = {
  filename: string;
  score: number;
  story?: string;
  personality?: string;
  rawText?: string;
};

const Modal = ({ isOpen, onClose, candidate }: { 
  isOpen: boolean, 
  onClose: () => void, 
  candidate: SearchResult | null,
  darkMode: boolean 
}) => {
  if (!isOpen || !candidate) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg w-3/4 max-h-[90vh] overflow-y-auto p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold dark:text-white">{candidate.filename}</h2>
          <button onClick={onClose} className="p-2 dark:text-gray-300">
            <X className="w-6 h-6" />
          </button>
        </div>
        
        <div className="space-y-6">
          {candidate.rawText && (
            <div>
              <h3 className="font-semibold mb-2 dark:text-white">Resume + Story + Personality</h3>
              <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg whitespace-pre-wrap break-words overflow-x-auto">
                <ReactMarkdown className="prose dark:prose-invert max-w-none dark:text-white whitespace-pre-wrap break-words overflow-x-auto">{candidate.rawText}</ReactMarkdown>
              </div>
            </div>
          )}
          
          {candidate.personality && (
            <div>
              <h3 className="font-semibold mb-2 dark:text-white">Personality</h3>
              <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg whitespace-pre-wrap break-words">
                <ReactMarkdown className="prose dark:prose-invert max-w-none dark:text-white">{candidate.personality}</ReactMarkdown>
              </div>
            </div>
          )}
          
          {candidate.story && (
            <div>
              <h3 className="font-semibold mb-2 dark:text-white">Story</h3>
              <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg whitespace-pre-wrap break-words">
                <ReactMarkdown className="prose dark:prose-invert max-w-none dark:text-white">{candidate.story}</ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default function ResumeSearch({ darkMode }: { darkMode: boolean }) {
  const [mode, setMode] = useState<SearchMode>('story');
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedResults, setExpandedResults] = useState<Set<number>>(new Set());
  const [savedCandidates, setSavedCandidates] = useState<SearchResult[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<SearchResult | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    const searchResumes = async () => {
      setError(null);
      
      if (query.trim() === '') {
        setResults([]);
        return;
      }

      setLoading(true);
      
      try {
        const requestBody = {
          query: query.trim(),
          mode: mode
        };
        
        console.log('Making search request:', requestBody);
        
        const response = await fetch(`${import.meta.env.VITE_API_URL}/search`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          body: JSON.stringify(requestBody),
        });

        console.log('Response status:', response.status);
        const responseText = await response.text();
        console.log('Response text:', responseText);

        if (!response.ok) {
          throw new Error(`API Error: ${responseText}`);
        }

        const data = JSON.parse(responseText);
        setResults(data.results || []);
      } catch (error) {
        console.error('Search error:', error);
        setError(error instanceof Error ? error.message : 'An unknown error occurred');
        setResults([]);
      } finally {
        setLoading(false);
      }
    };

    const timeoutId = setTimeout(searchResumes, 300);
    return () => clearTimeout(timeoutId);
  }, [query, mode]);

  const toggleExpanded = (index: number) => {
    const newExpanded = new Set(expandedResults);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedResults(newExpanded);
  };

  const saveCandidate = (candidate: SearchResult) => {
    if (!savedCandidates.some(saved => saved.filename === candidate.filename)) {
      setSavedCandidates([...savedCandidates, candidate]);
    }
  };

  const removeCandidate = (filename: string) => {
    setSavedCandidates(savedCandidates.filter(candidate => candidate.filename !== filename));
  };

  const renderResultContent = (result: SearchResult, index: number) => {
    const isExpanded = expandedResults.has(index);
    let content;
    
    switch (mode) {
      case 'story':
        content = result.story;
        break;
      case 'personality':
        content = result.personality;
        break;
      case 'resume':
        content = result.rawText;
        break;
    }
    
    if (!content) return null;

    const truncatedContent = content.length > 400 && !isExpanded 
      ? `${content.slice(0, 400)}...` 
      : content;

    return (
      <>
        <div className="text-gray-600 dark:text-gray-300">
          <ReactMarkdown>{truncatedContent}</ReactMarkdown>
        </div>
        {content.length > 400 && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              toggleExpanded(index);
            }}
            className="mt-2 flex items-center text-blue-500 hover:text-blue-600 transition-colors"
          >
            {isExpanded ? (
              <>
                <ChevronUp className="w-4 h-4 mr-1" />
                Show Less
              </>
            ) : (
              <>
                <ChevronDown className="w-4 h-4 mr-1" />
                Show More
              </>
            )}
          </button>
        )}
      </>
    );
  };

  return (
    <div className="flex">
      <div className="flex-1 max-w-4xl p-4">
        <div className="mb-6">
          <div className="flex gap-4 mb-4">
            <button
              onClick={() => setMode('resume')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                mode === 'resume'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Resume + Story + Personality Mode
            </button>
            <button
              onClick={() => setMode('story')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                mode === 'story'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Story Mode
            </button>
            <button
              onClick={() => setMode('personality')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                mode === 'personality'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Personality Mode
            </button>
          </div>

          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={
                mode === 'story'
                  ? "Please ramble about your ideal candidate's experience..."
                  : mode === 'personality'
                  ? "Please ramble about your ideal candidate's personality..."
                  : "Search through everything - resumes, stories, and personality traits..."
              }
              className="w-full p-4 pr-12 rounded-lg border border-gray-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
            />
            <Search className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400" />
          </div>
        </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400">
          {error}
        </div>
      )}

        {loading ? (
          <div className="flex justify-center my-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
          </div>
        ) : (
          <div className="space-y-4">
            {results.map((result, index) => (
              <div
                key={index}
                className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold dark:text-white">{result.filename}</h3>
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      Score: {(result.score * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        setSelectedCandidate(result);
                        setIsModalOpen(true);
                      }}
                      className="px-3 py-1 text-sm bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 rounded hover:bg-blue-200 dark:hover:bg-blue-800"
                    >
                      View Details
                    </button>
                    <button
                      onClick={() => {
                        const isSaved = savedCandidates.some(saved => saved.filename === result.filename);
                        if (isSaved) {
                          removeCandidate(result.filename);
                        } else {
                          saveCandidate(result);
                        }
                      }}
                      className={`px-3 py-1 text-sm rounded ${
                        savedCandidates.some(saved => saved.filename === result.filename)
                          ? 'bg-green-500 dark:bg-green-600 text-white dark:text-white'
                          : 'bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-300'
                      } hover:opacity-80`}
                    >
                      <Bookmark className={`w-4 h-4 ${
                        savedCandidates.some(saved => saved.filename === result.filename)
                          ? 'fill-current'
                          : ''
                      }`} />
                    </button>
                  </div>
                </div>
                <div className="text-gray-600 dark:text-gray-300">
                  {renderResultContent(result, index)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {savedCandidates.length > 0 && (
        <div className="w-96 h-screen overflow-y-auto p-4 border-l border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
          <h2 className="text-xl font-bold mb-4 dark:text-white">Saved Candidates</h2>
          <div className="space-y-4">
            {savedCandidates.map((candidate, index) => (
              <div key={index} className="bg-white dark:bg-gray-700 p-4 rounded-lg shadow">
                <div className="flex justify-between items-start">
                  <h3 className="font-semibold mb-2 dark:text-white">{candidate.filename}</h3>
                  <button
                    onClick={() => removeCandidate(candidate.filename)}
                    className="text-green-500 dark:text-green-400 hover:text-green-600 dark:hover:text-green-300 transition-transform duration-200 hover:scale-110"
                  >
                    <Bookmark className="w-4 h-4 fill-current" />
                  </button>
                </div>
                <button
                  onClick={() => {
                    setSelectedCandidate(candidate);
                    setIsModalOpen(true);
                  }}
                  className="text-sm text-blue-500 dark:text-blue-400 hover:text-blue-600 dark:hover:text-blue-300"
                >
                  View Details
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <Modal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        candidate={selectedCandidate}
        darkMode={darkMode}
      />
    </div>
  );
}