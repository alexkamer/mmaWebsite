"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Trophy, Shield, Search, Award, TrendingUp, Crown } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

// Types
interface RankedFighter {
  rank: number
  fighter_id: number | null
  fighter_name: string
  division: string
  is_champion: boolean
  is_interim: boolean
  headshot_url: string | null
  flag_url: string | null
  weight: number | null
  height: number | null
  reach: number | null
  stance: string | null
  fight_count: number
}

interface RankingsData {
  divisions: Record<string, RankedFighter[]>
  last_updated: string | null
}

// Division order matching the Flask template
const DIVISION_ORDER = [
  "Men's Pound-for-Pound",
  "Women's Pound-for-Pound",
  "Heavyweight",
  "Light Heavyweight",
  "Middleweight",
  "Welterweight",
  "Lightweight",
  "Featherweight",
  "Bantamweight",
  "Flyweight",
  "Women's Bantamweight",
  "Women's Flyweight",
  "Women's Strawweight",
]

// Component to render fighter card with enhanced styling
function FighterCard({ fighter, division }: { fighter: RankedFighter, division: string }) {
  return (
    <Link
      href={fighter.fighter_id ? `/fighters/${fighter.fighter_id}` : "#"}
      className={!fighter.fighter_id ? "pointer-events-none" : ""}
    >
      <div className="flex items-center gap-4 p-4 bg-slate-800 hover:bg-slate-750 rounded-lg transition-all group border border-slate-700 hover:border-red-600 hover:scale-[1.02] duration-300">
        {/* Rank Badge */}
        <div className="flex-shrink-0">
          <div className="w-14 h-14 bg-gradient-to-br from-slate-700 to-slate-900 group-hover:from-red-600 group-hover:to-red-700 text-white rounded-xl flex items-center justify-center font-black shadow-lg transition-all">
            <span className="text-lg">#{fighter.rank}</span>
          </div>
        </div>

        {/* Fighter Photo */}
        <div className="flex-shrink-0 hidden sm:block">
          {fighter.headshot_url ? (
            <img
              src={fighter.headshot_url}
              alt={fighter.fighter_name}
              className="w-16 h-16 rounded-xl object-cover border-2 border-slate-700 group-hover:border-red-500 shadow-lg transition-all"
            />
          ) : (
            <div className="w-16 h-16 rounded-xl bg-slate-700 flex items-center justify-center border-2 border-slate-600 shadow-lg">
              <span className="text-3xl">🥊</span>
            </div>
          )}
        </div>

        {/* Fighter Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            {fighter.flag_url && (
              <img
                src={fighter.flag_url}
                alt="Flag"
                className="w-5 h-4 rounded shadow-sm"
              />
            )}
            <h3 className="text-white font-bold group-hover:text-red-500 transition-colors truncate">
              {fighter.fighter_name}
            </h3>
          </div>

          {/* Stats */}
          {(fighter.height || fighter.reach || fighter.stance) && (
            <div className="flex items-center gap-3 text-xs text-slate-400 flex-wrap">
              {fighter.height && (
                <span>📏 {Math.round(fighter.height)}"</span>
              )}
              {fighter.reach && (
                <span>↔️ {fighter.reach.toFixed(1)}" reach</span>
              )}
              {fighter.stance && (
                <span>{fighter.stance}</span>
              )}
            </div>
          )}
        </div>
      </div>
    </Link>
  )
}

// Component to render champion spotlight
function ChampionSpotlight({ champion, division }: { champion: RankedFighter, division: string }) {
  return (
    <div className="mb-6 bg-gradient-to-br from-yellow-900/20 via-amber-900/20 to-orange-900/20 border-2 border-yellow-500/30 rounded-2xl p-6">
      <div className="flex flex-col md:flex-row items-center gap-6">
        {/* Champion Badge & Photo */}
        <div className="flex items-center gap-6">
          <div className="relative">
            <div className="w-20 h-20 bg-gradient-to-br from-yellow-400 via-yellow-500 to-yellow-600 rounded-2xl flex items-center justify-center shadow-2xl transform hover:rotate-6 transition-transform duration-300">
              <Crown className="w-12 h-12 text-white" />
            </div>
            <div className="absolute -top-2 -right-2 w-6 h-6 bg-yellow-400 rounded-full animate-pulse" />
          </div>

          {champion.headshot_url ? (
            <img
              src={champion.headshot_url}
              alt={champion.fighter_name}
              className="w-32 h-32 rounded-2xl object-cover border-4 border-yellow-500 shadow-2xl"
            />
          ) : (
            <div className="w-32 h-32 rounded-2xl bg-slate-800 flex items-center justify-center border-4 border-yellow-500 shadow-2xl">
              <span className="text-5xl">🥊</span>
            </div>
          )}
        </div>

        {/* Champion Info */}
        <div className="flex-1 text-center md:text-left">
          <div className="text-yellow-500 font-bold text-sm mb-2">REIGNING CHAMPION</div>
          <h3 className="text-3xl md:text-4xl font-black text-white mb-3">
            {champion.fighter_name}
          </h3>
          <div className="flex flex-wrap gap-2 justify-center md:justify-start mb-4">
            <Badge className="bg-yellow-500 text-black font-bold">
              👑 TITLE HOLDER
            </Badge>
            <Badge className="bg-red-600 text-white font-bold">
              {division}
            </Badge>
          </div>
          {champion.fighter_id && (
            <Link
              href={`/fighters/${champion.fighter_id}`}
              className="inline-flex items-center bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600 text-black px-6 py-3 rounded-xl font-black shadow-lg transition-all"
            >
              View Champion Profile →
            </Link>
          )}
        </div>
      </div>
    </div>
  )
}

export default function RankingsPage() {
  const [data, setData] = useState<RankingsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState("")

  useEffect(() => {
    const fetchRankings = async () => {
      try {
        const response = await fetch("http://localhost:8000/api/rankings/")
        const jsonData = await response.json()
        setData(jsonData)
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
      <div className="flex items-center justify-center min-h-screen bg-slate-950">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto mb-4"></div>
          <p className="text-slate-400">Loading Rankings...</p>
        </div>
      </div>
    )
  }

  // Filter fighters by search term
  const filterFighters = (fighters: RankedFighter[]) => {
    if (!searchTerm) return fighters
    return fighters.filter(f =>
      f.fighter_name.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }

  // Organize divisions in proper order
  const orderedDivisions = DIVISION_ORDER
    .filter(div => data?.divisions[div])
    .map(div => [div, data!.divisions[div]] as [string, RankedFighter[]])

  const mensDivisions = orderedDivisions.filter(
    ([div]) => !div.includes("Women's") && !div.includes("Pound-for-Pound")
  )

  const womensDivisions = orderedDivisions.filter(
    ([div]) => div.includes("Women's") && !div.includes("Pound-for-Pound")
  )

  const p4pDivisions = orderedDivisions.filter(
    ([div]) => div.includes("Pound-for-Pound")
  )

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950 border-b border-slate-800">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>

        <div className="relative container mx-auto px-4 py-16">
          <div className="max-w-4xl mx-auto text-center">
            {/* Live Badge */}
            <div className="inline-flex items-center gap-2 bg-red-600/10 border border-red-600/20 text-red-500 px-4 py-2 rounded-full text-sm font-semibold mb-4">
              <div className="w-2 h-2 bg-red-600 rounded-full animate-pulse"></div>
              🔥 LIVE RANKINGS • Updated from UFC.com
            </div>

            {/* Title */}
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-4">
              UFC <span className="text-red-500">RANKINGS</span>
            </h1>

            {/* Subtitle */}
            <p className="text-xl text-slate-400 mb-6">
              Official current champions and rankings across all divisions
            </p>

            {/* Last Updated */}
            {data?.last_updated && (
              <p className="text-sm text-slate-500">
                Last updated: {new Date(data.last_updated).toLocaleString()}
              </p>
            )}
          </div>
        </div>
      </section>

      {/* Search Section */}
      <section className="py-8 bg-slate-900 border-b border-slate-800">
        <div className="container mx-auto px-4">
          <div className="max-w-2xl mx-auto relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-slate-500 h-5 w-5" />
            <input
              type="text"
              placeholder="Search fighters by name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-12 pr-4 py-4 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-red-600 transition-colors"
            />
          </div>
        </div>
      </section>

      {/* Main Content */}
      <section className="py-12">
        <div className="container mx-auto px-4">
          <Tabs defaultValue="mens" className="w-full">
            <TabsList className="grid w-full max-w-md mx-auto grid-cols-3 bg-slate-900 border border-slate-800 mb-12">
              <TabsTrigger value="mens" className="data-[state=active]:bg-red-600 data-[state=active]:text-white">
                Men's
              </TabsTrigger>
              <TabsTrigger value="womens" className="data-[state=active]:bg-red-600 data-[state=active]:text-white">
                Women's
              </TabsTrigger>
              <TabsTrigger value="p4p" className="data-[state=active]:bg-red-600 data-[state=active]:text-white">
                P4P
              </TabsTrigger>
            </TabsList>

            {/* Men's Divisions */}
            <TabsContent value="mens">
              <div className="grid gap-8">
                {mensDivisions.map(([division, fighters]) => {
                  const champion = fighters.find(f => f.is_champion)
                  const rankedFighters = filterFighters(fighters).filter(f => !f.is_champion && !f.is_interim)

                  return (
                    <Card key={division} className="bg-slate-900 border-slate-800">
                      <CardContent className="p-6">
                        {/* Division Header */}
                        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-800">
                          <Trophy className="h-6 w-6 text-red-600" />
                          <h2 className="text-2xl font-bold text-white">{division}</h2>
                          {champion && (
                            <Badge className="ml-auto bg-yellow-500/20 text-yellow-500 border border-yellow-500/30">
                              Champion: {champion.fighter_name}
                            </Badge>
                          )}
                        </div>

                        {/* Champion Spotlight */}
                        {champion && <ChampionSpotlight champion={champion} division={division} />}

                        {/* Ranked Fighters Grid */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                          {rankedFighters.map((fighter) => (
                            <FighterCard key={`${division}-${fighter.rank}`} fighter={fighter} division={division} />
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )
                })}
              </div>
            </TabsContent>

            {/* Women's Divisions */}
            <TabsContent value="womens">
              <div className="grid gap-8">
                {womensDivisions.map(([division, fighters]) => {
                  const champion = fighters.find(f => f.is_champion)
                  const rankedFighters = filterFighters(fighters).filter(f => !f.is_champion && !f.is_interim)

                  return (
                    <Card key={division} className="bg-slate-900 border-slate-800">
                      <CardContent className="p-6">
                        {/* Division Header */}
                        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-800">
                          <Trophy className="h-6 w-6 text-red-600" />
                          <h2 className="text-2xl font-bold text-white">{division}</h2>
                          {champion && (
                            <Badge className="ml-auto bg-yellow-500/20 text-yellow-500 border border-yellow-500/30">
                              Champion: {champion.fighter_name}
                            </Badge>
                          )}
                        </div>

                        {/* Champion Spotlight */}
                        {champion && <ChampionSpotlight champion={champion} division={division} />}

                        {/* Ranked Fighters Grid */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                          {rankedFighters.map((fighter) => (
                            <FighterCard key={`${division}-${fighter.rank}`} fighter={fighter} division={division} />
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )
                })}
              </div>
            </TabsContent>

            {/* Pound-for-Pound */}
            <TabsContent value="p4p">
              <div className="grid md:grid-cols-2 gap-8">
                {p4pDivisions.map(([division, fighters]) => (
                  <Card key={division} className="bg-gradient-to-br from-purple-900/20 via-slate-900 to-blue-900/20 border-purple-800/30">
                    <CardContent className="p-6">
                      {/* Division Header */}
                      <div className="flex items-center gap-3 mb-6 pb-4 border-b border-purple-800/30">
                        <Award className="h-6 w-6 text-purple-400" />
                        <h2 className="text-2xl font-bold text-white">{division}</h2>
                      </div>

                      {/* Fighters List */}
                      <div className="space-y-3">
                        {filterFighters(fighters).slice(0, 15).map((fighter) => (
                          <Link
                            key={`${division}-${fighter.rank}`}
                            href={fighter.fighter_id ? `/fighters/${fighter.fighter_id}` : "#"}
                            className={!fighter.fighter_id ? "pointer-events-none" : ""}
                          >
                            <div className="flex items-center gap-4 p-4 bg-slate-800/50 hover:bg-slate-800 rounded-lg transition-all group border border-slate-700 hover:border-purple-500">
                              {/* Rank */}
                              <div className="flex-shrink-0 w-12 h-12 flex items-center justify-center">
                                <div className="text-2xl font-bold text-purple-400">
                                  {fighter.rank}
                                </div>
                              </div>

                              {/* Fighter Photo */}
                              {fighter.headshot_url && (
                                <img
                                  src={fighter.headshot_url}
                                  alt={fighter.fighter_name}
                                  className="w-12 h-12 rounded-lg object-cover border border-slate-700"
                                />
                              )}

                              {/* Fighter Info */}
                              <div className="flex-1 min-w-0">
                                <h3 className="text-white font-semibold group-hover:text-purple-400 transition-colors truncate flex items-center gap-2">
                                  {fighter.flag_url && (
                                    <img src={fighter.flag_url} alt="Flag" className="w-5 h-4 rounded shadow-sm" />
                                  )}
                                  {fighter.fighter_name}
                                </h3>
                              </div>

                              {/* Trend Icon */}
                              <TrendingUp className="h-4 w-4 text-slate-500 flex-shrink-0" />
                            </div>
                          </Link>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>
          </Tabs>

          {/* Footer */}
          <div className="text-center mt-12">
            <Card className="max-w-2xl mx-auto bg-slate-900/50 border-slate-800 p-6">
              <div className="flex items-center justify-center gap-3 mb-3">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
                <span className="text-white font-semibold">LIVE DATA</span>
              </div>
              <p className="text-slate-400">
                Rankings updated daily from <span className="font-bold text-red-500">UFC.com</span>
              </p>
            </Card>
          </div>
        </div>
      </section>
    </div>
  )
}
