"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Trophy, Crown } from "lucide-react"
import { rankingsAPI, type RankingEntry } from "@/lib/api"

export default function RankingsPage() {
  const [divisions, setDivisions] = useState<Record<string, RankingEntry[]>>({})
  const [loading, setLoading] = useState(true)

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
      <div className="space-y-4">
        <h1 className="text-4xl font-bold">UFC Rankings</h1>
        <p className="text-muted-foreground">
          Official UFC rankings across all divisions
        </p>
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
                {champion && (
                  <div className="border-b bg-gradient-to-r from-yellow-900/30 to-transparent p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Crown className="h-6 w-6 text-yellow-500" />
                        <div>
                          <div className="text-xs font-semibold uppercase text-yellow-500">
                            {champion.is_interim ? "Interim Champion" : "Champion"}
                          </div>
                          {champion.fighter_id ? (
                            <Link
                              href={`/fighters/${champion.fighter_id}`}
                              className="text-lg font-bold hover:underline"
                            >
                              {champion.fighter_name}
                            </Link>
                          ) : (
                            <div className="text-lg font-bold">
                              {champion.fighter_name}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Ranked Fighters */}
                <div className="divide-y">
                  {rankedFighters.map((fighter) => (
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
                  ))}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
