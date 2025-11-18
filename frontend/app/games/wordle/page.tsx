"use client"

import { useState, useEffect, useRef } from "react"
import Link from "next/link"
import Image from "next/image"
import { ArrowLeft, Trophy, HelpCircle } from "lucide-react"
import { wordleAPI, fightersAPI, type WordleFighter, type WordleGuessResponse, type FighterBase } from "@/lib/api"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

export default function FighterWordlePage() {
  const [targetFighter, setTargetFighter] = useState<WordleFighter | null>(null)
  const [guesses, setGuesses] = useState<WordleGuessResponse[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [searchResults, setSearchResults] = useState<FighterBase[]>([])
  const [gameOver, setGameOver] = useState(false)
  const [won, setWon] = useState(false)
  const [loading, setLoading] = useState(true)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const searchTimeoutRef = useRef<NodeJS.Timeout>()
  const inputRef = useRef<HTMLInputElement>(null)

  const MAX_ATTEMPTS = 6

  useEffect(() => {
    initGame()
  }, [])

  const initGame = async () => {
    setLoading(true)
    try {
      const data = await wordleAPI.getDaily()
      // Don't set the target yet - it will be revealed when guessed or given up
      setGuesses([])
      setGameOver(false)
      setWon(false)
      setSearchQuery("")
      setSearchResults([])
    } catch (error) {
      console.error("Error initializing game:", error)
    } finally {
      setLoading(false)
    }
  }

  const searchFighters = async (query: string) => {
    if (!query || query.length < 2) {
      setSearchResults([])
      return
    }

    try {
      const data = await fightersAPI.search(query, { limit: 10 })
      setSearchResults(data.fighters)
      setShowSuggestions(true)
    } catch (error) {
      console.error("Error searching fighters:", error)
      setSearchResults([])
    }
  }

  const handleSearchInput = (value: string) => {
    setSearchQuery(value)

    // Clear previous timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }

    // Set new timeout to debounce search
    searchTimeoutRef.current = setTimeout(() => {
      searchFighters(value)
    }, 300)
  }

  const submitGuess = async (fighterId: number) => {
    if (gameOver) return

    try {
      const result = await wordleAPI.submitGuess(fighterId)
      setGuesses([...guesses, result])
      setSearchQuery("")
      setSearchResults([])
      setShowSuggestions(false)

      if (result.correct) {
        setWon(true)
        setGameOver(true)
        setTargetFighter(result.target || null)
      } else if (guesses.length + 1 >= MAX_ATTEMPTS) {
        setGameOver(true)
        // Reveal the answer
        const answer = await wordleAPI.reveal()
        setTargetFighter(answer)
      }

      // Focus input for next guess
      if (!result.correct && guesses.length + 1 < MAX_ATTEMPTS) {
        inputRef.current?.focus()
      }
    } catch (error) {
      console.error("Error submitting guess:", error)
    }
  }

  const handleSelectFighter = (fighter: FighterBase) => {
    setShowSuggestions(false)
    submitGuess(fighter.id)
  }

  const handleGiveUp = async () => {
    if (gameOver) return

    const answer = await wordleAPI.reveal()
    setTargetFighter(answer)
    setGameOver(true)
    setWon(false)
  }

  const getHintEmoji = (hint: string) => {
    return hint
  }

  const getHintBgClass = (hint: string) => {
    if (hint === "🟩") return "bg-green-100 text-green-800 border-green-300"
    if (hint === "🟨") return "bg-yellow-100 text-yellow-800 border-yellow-300"
    return "bg-gray-100 text-gray-600 border-gray-300"
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 animate-pulse rounded bg-muted" />
        <Card className="bg-card border-border">
          <CardContent className="p-6">
            <div className="h-96 animate-pulse rounded bg-muted" />
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Link href="/" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" />
          Back to Home
        </Link>
        <h1 className="text-3xl font-bold">Fighter Wordle</h1>
        <div className="w-24" /> {/* Spacer for centering */}
      </div>

      {/* Instructions */}
      <Card className="bg-gradient-to-br from-purple-50 to-blue-50 dark:from-purple-950 dark:to-blue-950 border-purple-200 dark:border-purple-800">
        <CardContent className="p-6">
          <div className="flex items-start gap-3">
            <HelpCircle className="h-5 w-5 text-purple-600 dark:text-purple-400 mt-0.5 flex-shrink-0" />
            <div className="space-y-2 text-sm">
              <h2 className="font-semibold text-purple-900 dark:text-purple-100">How to Play</h2>
              <ul className="list-disc list-inside space-y-1 text-purple-800 dark:text-purple-200">
                <li>Guess the UFC fighter in {MAX_ATTEMPTS} attempts</li>
                <li>After each guess, you'll get hints about the fighter</li>
                <li><span className="font-medium">🟩 Green:</span> Correct information</li>
                <li><span className="font-medium">🟨 Yellow:</span> Close but not exact</li>
                <li><span className="font-medium">⬜ Gray:</span> Incorrect information</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Game Board */}
      <Card className="bg-card border-border">
        <CardContent className="p-6 space-y-6">
          {/* Input */}
          {!gameOver && (
            <div className="relative">
              <div className="flex gap-4">
                <Input
                  ref={inputRef}
                  type="text"
                  value={searchQuery}
                  onChange={(e) => handleSearchInput(e.target.value)}
                  onFocus={() => searchQuery.length >= 2 && setShowSuggestions(true)}
                  placeholder="Enter fighter name..."
                  className="flex-1"
                  disabled={gameOver}
                />
                <Button onClick={handleGiveUp} variant="outline" className="whitespace-nowrap">
                  Give Up
                </Button>
              </div>

              {/* Autocomplete Suggestions */}
              {showSuggestions && searchResults.length > 0 && (
                <div className="absolute left-0 right-0 top-full mt-2 bg-background border border-border rounded-lg shadow-lg max-h-60 overflow-y-auto z-10">
                  {searchResults.map((fighter) => (
                    <button
                      key={fighter.id}
                      onClick={() => handleSelectFighter(fighter)}
                      className="w-full px-4 py-3 text-left hover:bg-muted transition-colors flex items-center gap-3 border-b border-border last:border-0"
                    >
                      {fighter.image_url && (
                        <Image
                          src={fighter.image_url}
                          alt={fighter.name}
                          width={32}
                          height={32}
                          className="rounded-full object-cover"
                        />
                      )}
                      <div>
                        <div className="font-medium">{fighter.name}</div>
                        {fighter.weight_class && (
                          <div className="text-xs text-muted-foreground">{fighter.weight_class}</div>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Guesses Table */}
          {guesses.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-muted">
                    <th className="border border-border p-3 text-left font-semibold">Fighter</th>
                    <th className="border border-border p-3 text-center font-semibold">Nationality</th>
                    <th className="border border-border p-3 text-center font-semibold">Weight Class</th>
                    <th className="border border-border p-3 text-center font-semibold">Age</th>
                  </tr>
                </thead>
                <tbody>
                  {guesses.map((guess, index) => (
                    <tr key={index} className="hover:bg-muted/50">
                      <td className="border border-border p-3">
                        <div className="flex items-center gap-3">
                          {guess.guess.image_url && (
                            <Image
                              src={guess.guess.image_url}
                              alt={guess.guess.name || "Fighter"}
                              width={48}
                              height={48}
                              className="rounded-full object-cover"
                            />
                          )}
                          <div className="font-medium">{guess.guess.name}</div>
                        </div>
                      </td>
                      <td className="border border-border p-3 text-center">
                        <div className={`inline-flex items-center justify-center px-3 py-1 rounded-full text-sm font-medium border ${getHintBgClass(guess.hints.nationality)}`}>
                          {getHintEmoji(guess.hints.nationality)} {guess.guess.nationality || "N/A"}
                        </div>
                      </td>
                      <td className="border border-border p-3 text-center">
                        <div className={`inline-flex items-center justify-center px-3 py-1 rounded-full text-sm font-medium border ${getHintBgClass(guess.hints.weight_class)}`}>
                          {getHintEmoji(guess.hints.weight_class)} {guess.guess.weight_class || "N/A"}
                        </div>
                      </td>
                      <td className="border border-border p-3 text-center">
                        <div className={`inline-flex items-center justify-center px-3 py-1 rounded-full text-sm font-medium border ${getHintBgClass(guess.hints.age)}`}>
                          {getHintEmoji(guess.hints.age)} {guess.guess.age || "N/A"}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Attempts Counter */}
          <div className="text-center text-sm text-muted-foreground">
            Attempts: {guesses.length} / {MAX_ATTEMPTS}
          </div>

          {/* Game Over Message */}
          {gameOver && (
            <div className={`p-6 rounded-lg border-2 text-center ${won ? "bg-green-50 dark:bg-green-950 border-green-500" : "bg-red-50 dark:bg-red-950 border-red-500"}`}>
              {won ? (
                <>
                  <Trophy className="h-12 w-12 mx-auto mb-4 text-green-600 dark:text-green-400" />
                  <h3 className="text-2xl font-bold text-green-900 dark:text-green-100 mb-2">
                    Congratulations!
                  </h3>
                  <p className="text-green-800 dark:text-green-200 mb-4">
                    You guessed <span className="font-bold">{targetFighter?.name}</span> correctly in {guesses.length} {guesses.length === 1 ? "attempt" : "attempts"}!
                  </p>
                </>
              ) : (
                <>
                  <div className="text-4xl mb-4">😔</div>
                  <h3 className="text-2xl font-bold text-red-900 dark:text-red-100 mb-2">
                    Game Over!
                  </h3>
                  <p className="text-red-800 dark:text-red-200 mb-4">
                    The fighter was <span className="font-bold">{targetFighter?.name}</span>
                  </p>
                  {targetFighter?.image_url && (
                    <Image
                      src={targetFighter.image_url}
                      alt={targetFighter.name || "Fighter"}
                      width={128}
                      height={128}
                      className="rounded-full mx-auto object-cover border-4 border-red-500"
                    />
                  )}
                </>
              )}
              <Button onClick={initGame} className="mt-6" size="lg">
                Play Again
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
