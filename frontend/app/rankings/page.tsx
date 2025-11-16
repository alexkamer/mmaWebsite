"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Trophy, Crown, Scale, Check } from "lucide-react"
import { rankingsAPI, type RankingEntry } from "@/lib/api"

export default function RankingsPage() {
  const router = useRouter()
  const [divisions, setDivisions] = useState<Record<string, RankingEntry[]>>({})
  const [loading, setLoading] = useState(true)
  const [compareMode, setCompareMode] = useState(false)
  const [selectedFighters, setSelectedFighters] = useState<number[]>([])

  useEffect(() => {
    const fetchRankings = async () => {
      setLoading(true)
      try {
        const data = await rankingsAPI.getAll()
        setDivisions(data.divisions)
      } catch (error) {
        console.error("Error fetching rankings:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchRankings()
  }, [])

  const toggleFighterSelection = (fighterId: number) => {
    setSelectedFighters(prev => {
      if (prev.includes(fighterId)) {
        return prev.filter(id => id !== fighterId)
      }
      if (prev.length < 2) {
        return [...prev, fighterId]
      }
      return prev
    })
  }

  const handleCompare = () => {
    if (selectedFighters.length === 2) {
      router.push(`/fighters/compare?fighter1=${selectedFighters[0]}&fighter2=${selectedFighters[1]}`)
    }
  }

  const handleCancelCompare = () => {
    setCompareMode(false)
    setSelectedFighters([])
  }

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="h-8 w-48 animate-pulse rounded bg-gray-700" />
        <div className="h-96 animate-pulse rounded-lg bg-gray-700" />
      </div>
    )
  }

  const divisionOrder = [
    "Heavyweight",
    "Light Heavyweight",
    "Middleweight",
    "Welterweight",
    "Lightweight",
    "Featherweight",
    "Bantamweight",
    "Flyweight",
    "Women's Featherweight",
    "Women's Bantamweight",
    "Women's Flyweight",
    "Women's Strawweight",
    "Pound-for-Pound",
  ]

  const sortedDivisions = divisionOrder.filter((div) => divisions[div])

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold">UFC Rankings</h1>
          <p className="text-muted-foreground">
            Official UFC rankings across all divisions
          </p>
        </div>

        {!compareMode ? (
          <button
            onClick={() => setCompareMode(true)}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
          >
            <Scale className="h-4 w-4" />
            Compare Fighters
          </button>
        ) : (
          <div className="flex items-center gap-2">
            <div className="text-sm text-muted-foreground">
              {selectedFighters.length}/2 selected
            </div>
            <button
              onClick={handleCompare}
              disabled={selectedFighters.length !== 2}
              className="inline-flex items-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Scale className="h-4 w-4" />
              Compare
            </button>
            <button
              onClick={handleCancelCompare}
              className="rounded-lg border bg-background px-4 py-2 text-sm font-medium hover:bg-muted transition-colors"
            >
              Cancel
            </button>
          </div>
        )}
      </div>

      {/* Rankings by Division */}
      <div className="space-y-8">
        {sortedDivisions.map((divisionName) => {
          const rankings = divisions[divisionName]
          if (!rankings || rankings.length === 0) return null

          const champion = rankings.find((r) => r.is_champion)
          const rankedFighters = rankings.filter((r) => !r.is_champion)

          return (
            <div key={divisionName} className="space-y-4">
              <h2 className="text-2xl font-bold flex items-center gap-2">
                <Trophy className="h-6 w-6" />
                {divisionName}
              </h2>

              <div className="rounded-lg border bg-card">
                {/* Champion */}
                {champion && champion.fighter_id && (
                  <>
                    {compareMode ? (
                      <button
                        onClick={() => toggleFighterSelection(champion.fighter_id!)}
                        disabled={!selectedFighters.includes(champion.fighter_id!) && selectedFighters.length >= 2}
                        className={`w-full border-b bg-gradient-to-r from-yellow-900/30 to-transparent p-4 text-left transition-all ${
                          selectedFighters.includes(champion.fighter_id!) ? 'ring-2 ring-blue-500' : ''
                        } ${!selectedFighters.includes(champion.fighter_id!) && selectedFighters.length >= 2 ? 'opacity-50 cursor-not-allowed' : 'hover:bg-yellow-900/10'}`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <Crown className="h-6 w-6 text-yellow-500" />
                            <div>
                              <div className="text-xs font-semibold uppercase text-yellow-500">
                                {champion.is_interim ? "Interim Champion" : "Champion"}
                              </div>
                              <div className="text-lg font-bold">
                                {champion.fighter_name}
                              </div>
                            </div>
                          </div>
                          {selectedFighters.includes(champion.fighter_id!) && (
                            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-600 text-white">
                              <Check className="h-4 w-4" />
                            </div>
                          )}
                        </div>
                      </button>
                    ) : (
                      <div className="border-b bg-gradient-to-r from-yellow-900/30 to-transparent p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <Crown className="h-6 w-6 text-yellow-500" />
                            <div>
                              <div className="text-xs font-semibold uppercase text-yellow-500">
                                {champion.is_interim ? "Interim Champion" : "Champion"}
                              </div>
                              <Link
                                href={`/fighters/${champion.fighter_id}`}
                                className="text-lg font-bold hover:underline"
                              >
                                {champion.fighter_name}
                              </Link>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </>
                )}
                {champion && !champion.fighter_id && (
                  <div className="border-b bg-gradient-to-r from-yellow-900/30 to-transparent p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Crown className="h-6 w-6 text-yellow-500" />
                        <div>
                          <div className="text-xs font-semibold uppercase text-yellow-500">
                            {champion.is_interim ? "Interim Champion" : "Champion"}
                          </div>
                          <div className="text-lg font-bold">
                            {champion.fighter_name}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Ranked Fighters */}
                <div className="divide-y">
                  {rankedFighters.map((fighter) => {
                    const isSelected = fighter.fighter_id && selectedFighters.includes(fighter.fighter_id)
                    const isSelectable = compareMode && fighter.fighter_id && (isSelected || selectedFighters.length < 2)

                    if (compareMode && fighter.fighter_id) {
                      return (
                        <button
                          key={`${divisionName}-${fighter.rank}`}
                          onClick={() => toggleFighterSelection(fighter.fighter_id!)}
                          disabled={!isSelectable}
                          className={`flex w-full items-center gap-4 p-4 text-left transition-all ${
                            isSelected ? 'bg-blue-50 dark:bg-blue-950 ring-2 ring-blue-500' : 'hover:bg-muted/50'
                          } ${!isSelectable ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-muted font-bold">
                            {fighter.rank}
                          </div>
                          <div className="flex-1 font-semibold">
                            {fighter.fighter_name}
                          </div>
                          {isSelected && (
                            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-600 text-white">
                              <Check className="h-4 w-4" />
                            </div>
                          )}
                        </button>
                      )
                    }

                    return (
                      <div
                        key={`${divisionName}-${fighter.rank}`}
                        className="flex items-center gap-4 p-4 hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-muted font-bold">
                          {fighter.rank}
                        </div>
                        <div className="flex-1">
                          {fighter.fighter_id ? (
                            <Link
                              href={`/fighters/${fighter.fighter_id}`}
                              className="font-semibold hover:underline"
                            >
                              {fighter.fighter_name}
                            </Link>
                          ) : (
                            <div className="font-semibold">
                              {fighter.fighter_name}
                            </div>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
