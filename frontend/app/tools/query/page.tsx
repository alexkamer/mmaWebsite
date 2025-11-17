"use client"

import { useState, useEffect } from "react"
import { Search, Send, Loader2, HelpCircle, Sparkles, ChevronDown, ChevronUp } from "lucide-react"
import { queryAPI, type QueryResponse, type QueryExample } from "@/lib/api"
import Image from "next/image"

export default function MMAQueryPage() {
  const [question, setQuestion] = useState("")
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState<QueryResponse | null>(null)
  const [examples, setExamples] = useState<QueryExample[]>([])
  const [showExamples, setShowExamples] = useState(true)
  const [history, setHistory] = useState<QueryResponse[]>([])

  // Load examples on mount
  useEffect(() => {
    queryAPI.getExamples().then(data => {
      setExamples(data.examples)
    }).catch(err => {
      console.error("Error loading examples:", err)
    })

    // Load history from localStorage
    const saved = localStorage.getItem('query_history')
    if (saved) {
      try {
        setHistory(JSON.parse(saved))
      } catch (e) {
        console.error("Error loading history:", e)
      }
    }
  }, [])

  // Save history to localStorage
  useEffect(() => {
    if (history.length > 0) {
      localStorage.setItem('query_history', JSON.stringify(history.slice(0, 10))) // Keep last 10
    }
  }, [history])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim() || loading) return

    setLoading(true)
    setResponse(null)

    try {
      const result = await queryAPI.ask(question)
      setResponse(result)
      setHistory(prev => [result, ...prev])
      setShowExamples(false)
    } catch (err) {
      console.error("Error asking question:", err)
      setResponse({
        question,
        answer: "Sorry, I encountered an error processing your question. Please try again.",
        data: null,
        query_type: "error",
      })
    } finally {
      setLoading(false)
    }
  }

  const handleExampleClick = (exampleQuestion: string) => {
    setQuestion(exampleQuestion)
    setShowExamples(false)
  }

  const handleHistoryClick = (item: QueryResponse) => {
    setResponse(item)
    setQuestion(item.question)
    setShowExamples(false)
  }

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <Search className="h-10 w-10" />
          <h1 className="text-4xl font-bold">MMA Query</h1>
        </div>
        <p className="text-muted-foreground">
          Ask questions about MMA fighters, events, and statistics in natural language.
        </p>
      </div>

      {/* Search Form */}
      <form onSubmit={handleSubmit} className="relative">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a question... (e.g., What is Conor McGregor's record?)"
              disabled={loading}
              className="w-full rounded-lg border bg-background pl-10 pr-4 py-4 text-lg focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="rounded-lg bg-primary px-6 py-4 font-semibold text-primary-foreground transition-all hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </button>
        </div>
      </form>

      {/* Response */}
      {response && (
        <div className="rounded-lg border bg-card p-6 space-y-4">
          <div className="flex items-start gap-3">
            <div className="rounded-lg bg-primary/10 p-2">
              <Sparkles className="h-5 w-5 text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-muted-foreground mb-2">{response.question}</h3>
              <p className="text-lg">{response.answer}</p>
            </div>
          </div>

          {/* Fighter Data Display */}
          {response.data && response.query_type === "fighter_record" && response.data.fighter && (
            <div className="mt-4 flex items-center gap-4 rounded-lg border bg-muted/50 p-4">
              {response.data.fighter.headshot_url && (
                <div className="relative h-20 w-20 overflow-hidden rounded-full border-2 border-primary">
                  <Image
                    src={response.data.fighter.headshot_url}
                    alt={response.data.fighter.full_name}
                    fill
                    className="object-cover"
                  />
                </div>
              )}
              <div>
                <h4 className="text-xl font-bold">{response.data.fighter.full_name}</h4>
                {response.data.fighter.nickname && (
                  <p className="text-muted-foreground">"{response.data.fighter.nickname}"</p>
                )}
                <div className="mt-2 flex gap-4 text-sm">
                  <span className="font-semibold text-green-500">
                    {response.data.wins}W
                  </span>
                  <span className="font-semibold text-red-500">
                    {response.data.losses}L
                  </span>
                  {response.data.draws > 0 && (
                    <span className="font-semibold text-gray-500">
                      {response.data.draws}D
                    </span>
                  )}
                  {response.data.ko_wins > 0 && (
                    <span className="text-muted-foreground">
                      {response.data.ko_wins} KO/TKO
                    </span>
                  )}
                  {response.data.sub_wins > 0 && (
                    <span className="text-muted-foreground">
                      {response.data.sub_wins} SUB
                    </span>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Fighter Stats Display */}
          {response.data && response.query_type === "fighter_stats" && response.data.headshot_url && (
            <div className="mt-4 flex items-center gap-4 rounded-lg border bg-muted/50 p-4">
              <div className="relative h-20 w-20 overflow-hidden rounded-full border-2 border-primary">
                <Image
                  src={response.data.headshot_url}
                  alt={response.data.full_name}
                  fill
                  className="object-cover"
                />
              </div>
              <div>
                <h4 className="text-xl font-bold">{response.data.full_name}</h4>
                {response.data.nickname && (
                  <p className="text-muted-foreground text-sm">"{response.data.nickname}"</p>
                )}
              </div>
            </div>
          )}

          {/* Suggestions */}
          {response.suggestions && response.suggestions.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-semibold text-muted-foreground mb-2">Try asking:</h4>
              <div className="flex flex-wrap gap-2">
                {response.suggestions.map((suggestion, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleExampleClick(suggestion)}
                    className="rounded-full border bg-background px-3 py-1 text-sm transition-all hover:bg-muted"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Examples Section */}
      <div className="rounded-lg border bg-card">
        <button
          onClick={() => setShowExamples(!showExamples)}
          className="w-full flex items-center justify-between p-4 transition-all hover:bg-muted/50"
        >
          <div className="flex items-center gap-2">
            <HelpCircle className="h-5 w-5" />
            <h3 className="font-semibold">Example Questions</h3>
          </div>
          {showExamples ? (
            <ChevronUp className="h-5 w-5" />
          ) : (
            <ChevronDown className="h-5 w-5" />
          )}
        </button>

        {showExamples && (
          <div className="border-t p-4 space-y-6">
            {examples.map((example, idx) => (
              <div key={idx}>
                <h4 className="font-semibold mb-2">{example.category}</h4>
                <div className="flex flex-wrap gap-2">
                  {example.queries.map((query, qIdx) => (
                    <button
                      key={qIdx}
                      onClick={() => handleExampleClick(query)}
                      className="rounded-lg border bg-background px-3 py-2 text-sm transition-all hover:bg-muted hover:border-primary"
                    >
                      {query}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Query History */}
      {history.length > 0 && (
        <div className="rounded-lg border bg-card p-4">
          <h3 className="font-semibold mb-3">Recent Queries</h3>
          <div className="space-y-2">
            {history.slice(0, 5).map((item, idx) => (
              <button
                key={idx}
                onClick={() => handleHistoryClick(item)}
                className="w-full text-left rounded-lg border bg-background p-3 transition-all hover:bg-muted hover:border-primary"
              >
                <div className="flex items-center gap-2">
                  <Search className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                  <span className="text-sm truncate">{item.question}</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* How it Works */}
      <div className="rounded-lg border-l-4 border-blue-500 bg-blue-500/10 p-4">
        <h3 className="font-semibold mb-2">How it works</h3>
        <p className="text-sm text-muted-foreground">
          Ask questions in natural language and get instant answers from our MMA database.
          The system understands queries about fighter records, stats, upcoming events, rankings,
          and fight history. Try asking about your favorite fighters!
        </p>
      </div>
    </div>
  )
}
