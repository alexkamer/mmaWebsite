"use client"

import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { Search, Clock, TrendingUp } from "lucide-react"
import { FighterAvatar } from "./fighter-avatar"
import { SearchSkeleton } from "./skeletons"
import { fightersAPI } from "@/lib/api"

interface Fighter {
  id: number
  name: string
  nickname?: string
  weight_class?: string
  image_url?: string
}

export function FighterSearch() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<Fighter[]>([])
  const [recentSearches, setRecentSearches] = useState<Fighter[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const router = useRouter()
  const searchRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Load recent searches from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("recentFighterSearches")
    if (saved) {
      try {
        setRecentSearches(JSON.parse(saved))
      } catch (e) {
        console.error("Failed to load recent searches:", e)
      }
    }
  }, [])

  // Search fighters with debounce
  useEffect(() => {
    if (!query.trim()) {
      setResults([])
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    const timer = setTimeout(async () => {
      try {
        const data = await fightersAPI.search(query, { limit: 8 })
        setResults(data.fighters || [])
      } catch (error) {
        console.error("Search error:", error)
        setResults([])
      } finally {
        setIsLoading(false)
      }
    }, 300)

    return () => clearTimeout(timer)
  }, [query])

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  // Save to recent searches
  const saveToRecent = (fighter: Fighter) => {
    const updated = [
      fighter,
      ...recentSearches.filter((f) => f.id !== fighter.id),
    ].slice(0, 5)
    setRecentSearches(updated)
    localStorage.setItem("recentFighterSearches", JSON.stringify(updated))
  }

  // Handle fighter selection
  const selectFighter = (fighter: Fighter) => {
    saveToRecent(fighter)
    router.push(`/fighters/${fighter.id}`)
    setQuery("")
    setIsOpen(false)
    setSelectedIndex(-1)
  }

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    const items = results.length > 0 ? results : recentSearches

    if (e.key === "ArrowDown") {
      e.preventDefault()
      setSelectedIndex((prev) => (prev < items.length - 1 ? prev + 1 : prev))
    } else if (e.key === "ArrowUp") {
      e.preventDefault()
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1))
    } else if (e.key === "Enter" && selectedIndex >= 0) {
      e.preventDefault()
      selectFighter(items[selectedIndex])
    } else if (e.key === "Escape") {
      setIsOpen(false)
      inputRef.current?.blur()
    }
  }

  const showRecent = isOpen && !query && recentSearches.length > 0
  const showResults = isOpen && query && (results.length > 0 || isLoading)

  return (
    <div ref={searchRef} className="relative w-full max-w-2xl">
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder="Search fighters..."
          className="w-full rounded-lg border bg-background pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>

      {/* Dropdown */}
      {(showRecent || showResults) && (
        <div className="absolute z-50 mt-2 w-full rounded-lg border bg-popover shadow-lg max-h-96 overflow-y-auto">
          {/* Recent Searches */}
          {showRecent && (
            <>
              <div className="flex items-center gap-2 px-3 py-2 text-xs font-semibold text-muted-foreground border-b">
                <Clock className="h-3 w-3" />
                Recent Searches
              </div>
              {recentSearches.map((fighter, index) => (
                <button
                  key={fighter.id}
                  onClick={() => selectFighter(fighter)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 hover:bg-accent transition-colors ${
                    index === selectedIndex ? "bg-accent" : ""
                  }`}
                >
                  <FighterAvatar
                    src={fighter.image_url}
                    alt={fighter.name}
                    size="sm"
                  />
                  <div className="flex-1 text-left">
                    <div className="text-sm font-medium">{fighter.name}</div>
                    {fighter.weight_class && (
                      <div className="text-xs text-muted-foreground">
                        {fighter.weight_class}
                      </div>
                    )}
                  </div>
                </button>
              ))}
            </>
          )}

          {/* Search Results */}
          {showResults && (
            <>
              {query && !isLoading && (
                <div className="flex items-center gap-2 px-3 py-2 text-xs font-semibold text-muted-foreground border-b">
                  <TrendingUp className="h-3 w-3" />
                  Search Results
                </div>
              )}

              {isLoading ? (
                <SearchSkeleton />
              ) : (
                results.map((fighter, index) => (
                  <button
                    key={fighter.id}
                    onClick={() => selectFighter(fighter)}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 hover:bg-accent transition-colors ${
                      index === selectedIndex ? "bg-accent" : ""
                    }`}
                  >
                    <FighterAvatar
                      src={fighter.image_url}
                      alt={fighter.name}
                      size="sm"
                    />
                    <div className="flex-1 text-left">
                      <div className="text-sm font-medium">
                        {fighter.name}
                        {fighter.nickname && (
                          <span className="text-muted-foreground ml-1">
                            "{fighter.nickname}"
                          </span>
                        )}
                      </div>
                      {fighter.weight_class && (
                        <div className="text-xs text-muted-foreground">
                          {fighter.weight_class}
                        </div>
                      )}
                    </div>
                  </button>
                ))
              )}

              {!isLoading && results.length === 0 && query && (
                <div className="px-3 py-8 text-center text-sm text-muted-foreground">
                  No fighters found for "{query}"
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
