"use client"

import { useState, useEffect } from "react"
import { useSearchParams } from "next/navigation"
import Link from "next/link"
import Image from "next/image"
import { ArrowLeft, Trophy, TrendingUp, Users, Zap } from "lucide-react"
import { fightersAPI, type FighterComparison } from "@/lib/api"

export default function FighterComparePage() {
  const searchParams = useSearchParams()
  const fighter1Id = searchParams.get("fighter1")
  const fighter2Id = searchParams.get("fighter2")

  const [comparison, setComparison] = useState<FighterComparison | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (fighter1Id && fighter2Id) {
      fetchComparison()
    }
  }, [fighter1Id, fighter2Id])

  const fetchComparison = async () => {
    if (!fighter1Id || !fighter2Id) return

    setLoading(true)
    setError(null)

    try {
      const data = await fightersAPI.compare(parseInt(fighter1Id), parseInt(fighter2Id))
      setComparison(data)
    } catch (err) {
      setError("Failed to load fighter comparison")
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (!fighter1Id || !fighter2Id) {
    return (
      <div className="space-y-6">
        <Link href="/fighters" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" />
          Back to Fighters
        </Link>
        <div className="rounded-lg border bg-card p-12 text-center">
          <h2 className="text-2xl font-bold mb-4">Fighter Comparison</h2>
          <p className="text-muted-foreground mb-6">
            Select two fighters to compare their stats, records, and fighting styles
          </p>
          <Link
            href="/fighters"
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Browse Fighters
          </Link>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 animate-pulse rounded bg-muted" />
        <div className="grid gap-6 lg:grid-cols-2">
          {[1, 2].map((i) => (
            <div key={i} className="h-96 animate-pulse rounded-lg border bg-muted" />
          ))}
        </div>
      </div>
    )
  }

  if (error || !comparison) {
    return (
      <div className="space-y-6">
        <Link href="/fighters" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" />
          Back to Fighters
        </Link>
        <div className="rounded-lg border bg-card p-12 text-center">
          <p className="text-muted-foreground">{error || "Failed to load comparison"}</p>
        </div>
      </div>
    )
  }

  const { fighter1, fighter2 } = comparison

  const getAdvantage = (val1: number, val2: number, higherIsBetter = true) => {
    if (val1 === val2) return "equal"
    if (higherIsBetter) {
      return val1 > val2 ? "fighter1" : "fighter2"
    }
    return val1 < val2 ? "fighter1" : "fighter2"
  }

  const parseHeight = (height: string) => {
    const match = height.match(/(\d+)'\s*(\d+)"/)
    if (!match) return 0
    return parseInt(match[1]) * 12 + parseInt(match[2])
  }

  const parseWeight = (weight: string) => {
    const match = weight.match(/(\d+)/)
    return match ? parseInt(match[1]) : 0
  }

  const parseReach = (reach: string) => {
    return parseFloat(reach) || 0
  }

  const heightAdvantage = fighter1.height && fighter2.height
    ? getAdvantage(parseHeight(fighter1.height), parseHeight(fighter2.height))
    : "equal"

  const reachAdvantage = fighter1.reach && fighter2.reach
    ? getAdvantage(parseReach(fighter1.reach), parseReach(fighter2.reach))
    : "equal"

  const winPercentage1 = fighter1.record.wins / (fighter1.record.wins + fighter1.record.losses) * 100
  const winPercentage2 = fighter2.record.wins / (fighter2.record.wins + fighter2.record.losses) * 100

  const finishRate1 = (fighter1.record.ko_wins + fighter1.record.sub_wins) / fighter1.record.wins * 100
  const finishRate2 = (fighter2.record.ko_wins + fighter2.record.sub_wins) / fighter2.record.wins * 100

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Link href="/fighters" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" />
          Back to Fighters
        </Link>
        <h1 className="text-2xl font-bold">Fighter Comparison</h1>
        <div className="w-32" /> {/* Spacer */}
      </div>

      {/* Fighter Cards Header */}
      <div className="grid gap-6 lg:grid-cols-2">
        {[fighter1, fighter2].map((fighter, idx) => (
          <Link
            key={fighter.id}
            href={`/fighters/${fighter.id}`}
            className="group relative overflow-hidden rounded-lg border bg-card p-6 transition-all hover:shadow-lg"
          >
            <div className="flex items-start gap-4">
              {fighter.image_url ? (
                <div className="relative h-24 w-24 overflow-hidden rounded-full border-2 border-primary">
                  <Image
                    src={fighter.image_url}
                    alt={fighter.name}
                    fill
                    sizes="96px"
                    className="object-cover"
                  />
                </div>
              ) : (
                <div className="flex h-24 w-24 items-center justify-center rounded-full border-2 border-primary bg-muted text-2xl font-bold">
                  {fighter.name.charAt(0)}
                </div>
              )}
              <div className="flex-1 min-w-0">
                <h2 className="text-2xl font-bold truncate">{fighter.name}</h2>
                {fighter.nickname && (
                  <p className="text-sm text-muted-foreground">"{fighter.nickname}"</p>
                )}
                <div className="mt-2 flex items-center gap-4 text-sm">
                  <span className="font-semibold">{fighter.record.wins}-{fighter.record.losses}-{fighter.record.draws}</span>
                  <span className="text-muted-foreground">{fighter.weight_class}</span>
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Physical Stats Comparison */}
      <div className="rounded-lg border bg-card p-6">
        <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
          <Zap className="h-5 w-5 text-primary" />
          Physical Attributes
        </h3>
        <div className="space-y-4">
          {/* Height */}
          {fighter1.height && fighter2.height && (
            <div className="grid grid-cols-3 gap-4 items-center">
              <div className={`text-right ${heightAdvantage === "fighter1" ? "font-bold text-primary" : ""}`}>
                {fighter1.height}
              </div>
              <div className="text-center text-sm text-muted-foreground">Height</div>
              <div className={`text-left ${heightAdvantage === "fighter2" ? "font-bold text-primary" : ""}`}>
                {fighter2.height}
              </div>
            </div>
          )}

          {/* Weight */}
          {fighter1.weight && fighter2.weight && (
            <div className="grid grid-cols-3 gap-4 items-center">
              <div className="text-right">{fighter1.weight}</div>
              <div className="text-center text-sm text-muted-foreground">Weight</div>
              <div className="text-left">{fighter2.weight}</div>
            </div>
          )}

          {/* Reach */}
          {fighter1.reach && fighter2.reach && (
            <div className="grid grid-cols-3 gap-4 items-center">
              <div className={`text-right ${reachAdvantage === "fighter1" ? "font-bold text-primary" : ""}`}>
                {fighter1.reach}"
              </div>
              <div className="text-center text-sm text-muted-foreground">Reach</div>
              <div className={`text-left ${reachAdvantage === "fighter2" ? "font-bold text-primary" : ""}`}>
                {fighter2.reach}"
              </div>
            </div>
          )}

          {/* Age */}
          <div className="grid grid-cols-3 gap-4 items-center">
            <div className={`text-right ${fighter1.age < fighter2.age ? "font-bold text-primary" : ""}`}>
              {fighter1.age} years
            </div>
            <div className="text-center text-sm text-muted-foreground">Age</div>
            <div className={`text-left ${fighter2.age < fighter1.age ? "font-bold text-primary" : ""}`}>
              {fighter2.age} years
            </div>
          </div>

          {/* Stance */}
          <div className="grid grid-cols-3 gap-4 items-center">
            <div className="text-right">{fighter1.stance}</div>
            <div className="text-center text-sm text-muted-foreground">Stance</div>
            <div className="text-left">{fighter2.stance}</div>
          </div>
        </div>
      </div>

      {/* Record & Performance */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border bg-card p-6">
          <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
            <Trophy className="h-5 w-5 text-primary" />
            Fight Record
          </h3>
          <div className="space-y-6">
            {[fighter1, fighter2].map((fighter, idx) => (
              <div key={fighter.id}>
                <div className="text-sm text-muted-foreground mb-2">{fighter.name}</div>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm">Record</span>
                    <span className="font-semibold">{fighter.record.wins}-{fighter.record.losses}-{fighter.record.draws}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Win Rate</span>
                    <span className="font-semibold">{(idx === 0 ? winPercentage1 : winPercentage2).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">KO Wins</span>
                    <span>{fighter.record.ko_wins}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Submission Wins</span>
                    <span>{fighter.record.sub_wins}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Finish Rate</span>
                    <span className="font-semibold">{(idx === 0 ? finishRate1 : finishRate2).toFixed(1)}%</span>
                  </div>
                </div>
                {idx === 0 && <div className="my-4 border-t" />}
              </div>
            ))}
          </div>
        </div>

        {/* Recent Form */}
        <div className="rounded-lg border bg-card p-6">
          <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-primary" />
            Recent Form
          </h3>
          <div className="space-y-6">
            {[fighter1, fighter2].map((fighter, idx) => (
              <div key={fighter.id}>
                <div className="text-sm text-muted-foreground mb-2">{fighter.name}</div>
                <div className="space-y-2">
                  {fighter.recent_fights.slice(0, 5).map((fight) => (
                    <div key={fight.id} className="flex items-center justify-between text-sm">
                      <span className="truncate flex-1">{fight.opponent_name}</span>
                      <span className={`ml-2 font-semibold ${fight.result === 'win' ? 'text-green-500' : 'text-red-500'}`}>
                        {fight.result === 'win' ? 'W' : 'L'}
                      </span>
                      <span className="ml-2 text-muted-foreground text-xs">{fight.method}</span>
                    </div>
                  ))}
                </div>
                {idx === 0 && <div className="my-4 border-t" />}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Common Opponents (if available) */}
      {comparison.common_opponents && comparison.common_opponents.length > 0 && (
        <div className="rounded-lg border bg-card p-6">
          <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
            <Users className="h-5 w-5 text-primary" />
            Common Opponents
          </h3>
          <div className="space-y-3">
            {comparison.common_opponents.map((opponent: any) => (
              <div key={opponent.opponent_id} className="flex items-center justify-between">
                <span>{opponent.opponent_name}</span>
                <div className="flex gap-4 text-sm">
                  <span className={fighter1.name.includes(opponent.fighter1_result === 'win' ? '' : 'L') ? 'text-green-500' : 'text-red-500'}>
                    {fighter1.name}: {opponent.fighter1_result}
                  </span>
                  <span className={fighter2.name.includes(opponent.fighter2_result === 'win' ? '' : 'L') ? 'text-green-500' : 'text-red-500'}>
                    {fighter2.name}: {opponent.fighter2_result}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
