"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import Image from "next/image"
import { Calendar, MapPin, Globe, TrendingUp, Trophy, Scale } from "lucide-react"
import { espnAPI, type NextEventResponse, type NextEventFight } from "@/lib/api"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"

export default function NextEventPage() {
  const [eventData, setEventData] = useState<NextEventResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchNextEvent = async () => {
      try {
        const data = await espnAPI.getNextEvent()
        setEventData(data)
      } catch (err) {
        console.error("Error fetching next event:", err)
        setError("Failed to load upcoming event")
      } finally {
        setLoading(false)
      }
    }

    fetchNextEvent()
  }, [])

  // Calculate implied probability from American odds
  const calculateProbability = (odds: string | undefined): number => {
    if (!odds) return 50.0

    const oddsInt = parseInt(odds)
    if (isNaN(oddsInt)) return 50.0

    if (oddsInt < 0) {
      return ((-oddsInt / (-oddsInt + 100)) * 100)
    } else {
      return ((100 / (oddsInt + 100)) * 100)
    }
  }

  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    })
  }

  if (loading) {
    return (
      <div className="space-y-8">
        <Skeleton className="h-48 w-full rounded-xl bg-gray-800" />
        <Skeleton className="h-32 w-full rounded-xl bg-gray-800" />
        <Skeleton className="h-96 w-full rounded-xl bg-gray-800" />
      </div>
    )
  }

  if (error || !eventData) {
    return (
      <Card className="bg-gray-900 border-gray-800">
        <CardContent className="p-12 text-center">
          <Trophy className="w-12 h-12 mx-auto mb-4 text-gray-600" />
          <h3 className="text-lg font-semibold text-white mb-2">No Upcoming Event</h3>
          <p className="text-gray-400">{error || "Unable to load event data"}</p>
        </CardContent>
      </Card>
    )
  }

  const { event, fights } = eventData

  // Calculate betting insights
  const totalFights = fights.length
  const favoritesCount = fights.filter(f =>
    (f.fighter_1_odds && parseInt(f.fighter_1_odds) < 0) ||
    (f.fighter_2_odds && parseInt(f.fighter_2_odds) < 0)
  ).length

  const favoriteProbs = fights.flatMap(f => {
    const probs: number[] = []
    if (f.fighter_1_odds && parseInt(f.fighter_1_odds) < 0) {
      probs.push(calculateProbability(f.fighter_1_odds))
    }
    if (f.fighter_2_odds && parseInt(f.fighter_2_odds) < 0) {
      probs.push(calculateProbability(f.fighter_2_odds))
    }
    return probs
  })

  const avgFavoriteProb = favoriteProbs.length > 0
    ? (favoriteProbs.reduce((a, b) => a + b, 0) / favoriteProbs.length).toFixed(1)
    : "N/A"

  const mainEvent = fights[0]
  const otherFights = fights.slice(1)

  return (
    <div className="space-y-8 pb-8">
      {/* Event Header */}
      <div className="relative overflow-hidden rounded-2xl border border-gray-800 bg-gradient-to-br from-purple-900 via-indigo-900 to-purple-800 shadow-2xl">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>

        <div className="relative p-8">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-6">{event.event_name}</h1>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-white">
            <div className="flex items-center gap-3">
              <Calendar className="h-6 w-6" />
              <span className="text-lg font-semibold">{formatDate(event.date)}</span>
            </div>
            {event.venue_name && (
              <div className="flex items-center gap-3">
                <MapPin className="h-6 w-6" />
                <span className="text-lg">{event.venue_name}</span>
              </div>
            )}
            <div className="flex items-center gap-3">
              <Globe className="h-6 w-6" />
              <span className="text-lg">
                {event.city}
                {event.state && `, ${event.state}`}
                {event.country && `, ${event.country}`}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Betting Insights Summary */}
      <Card className="border-gray-800 bg-gradient-to-br from-blue-950 to-purple-950">
        <CardContent className="p-6">
          <div className="flex items-center justify-center gap-3 mb-6">
            <div className="rounded-full bg-gradient-to-r from-blue-500 to-purple-500 p-2">
              <TrendingUp className="h-5 w-5 text-white" />
            </div>
            <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Betting Insights
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="bg-gray-900 border-gray-800 text-center hover:border-purple-600 transition-all">
              <CardContent className="p-4">
                <div className="text-3xl font-bold text-purple-400">{totalFights}</div>
                <div className="text-sm text-gray-400 font-medium">Total Fights</div>
              </CardContent>
            </Card>

            <Card className="bg-gray-900 border-gray-800 text-center hover:border-blue-600 transition-all">
              <CardContent className="p-4">
                <div className="text-3xl font-bold text-blue-400">{favoritesCount}</div>
                <div className="text-sm text-gray-400 font-medium">Clear Favorites ⭐</div>
              </CardContent>
            </Card>

            <Card className="bg-gray-900 border-gray-800 text-center hover:border-green-600 transition-all">
              <CardContent className="p-4">
                <div className="text-3xl font-bold text-green-400">
                  {avgFavoriteProb !== "N/A" ? `${avgFavoriteProb}%` : "N/A"}
                </div>
                <div className="text-sm text-gray-400 font-medium">Avg Favorite Probability</div>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>

      {/* Main Event */}
      {mainEvent && (
        <div className="space-y-4">
          <div className="bg-gradient-to-r from-red-600 to-orange-600 text-white py-3 px-6 rounded-t-2xl">
            <h3 className="text-2xl font-bold text-center">🏆 MAIN EVENT 🏆</h3>
          </div>

          <Card className="border-4 border-red-600 bg-gradient-to-br from-gray-900 to-gray-800 shadow-2xl">
            <CardContent className="p-8">
              <div className="grid grid-cols-1 md:grid-cols-5 gap-6 items-center">
                {/* Fighter 1 */}
                <FighterCard
                  fighter={{
                    id: mainEvent.fighter_1_id,
                    name: mainEvent.fighter_1_name,
                    record: mainEvent.fighter_1_record,
                    image: mainEvent.fighter_1_image,
                    odds: mainEvent.fighter_1_odds
                  }}
                  probability={calculateProbability(mainEvent.fighter_1_odds)}
                  isMainEvent={true}
                />

                {/* VS Section */}
                <div className="flex flex-col items-center justify-center space-y-4">
                  <div className="w-20 h-20 bg-gradient-to-br from-red-500 to-orange-500 rounded-full flex items-center justify-center shadow-xl">
                    <span className="text-white text-2xl font-black">VS</span>
                  </div>
                  <Badge className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-4 py-2 text-sm font-bold">
                    {mainEvent.weight_class}
                  </Badge>
                  {mainEvent.rounds_format && (
                    <Badge variant="outline" className="border-gray-600 text-gray-300">
                      {mainEvent.rounds_format} Rounds
                    </Badge>
                  )}
                  <div className="flex gap-2 mt-4">
                    <Link
                      href={`/fighters/${mainEvent.fighter_1_id}`}
                      className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-all hover:scale-105 shadow-md"
                    >
                      View Fighters
                    </Link>
                    <Link
                      href={`/fighters/compare?fighter1=${mainEvent.fighter_1_id}&fighter2=${mainEvent.fighter_2_id}`}
                      className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-all hover:scale-105 shadow-md flex items-center gap-1"
                    >
                      <Scale className="h-4 w-4" />
                      Compare
                    </Link>
                  </div>
                </div>

                {/* Fighter 2 */}
                <FighterCard
                  fighter={{
                    id: mainEvent.fighter_2_id,
                    name: mainEvent.fighter_2_name,
                    record: mainEvent.fighter_2_record,
                    image: mainEvent.fighter_2_image,
                    odds: mainEvent.fighter_2_odds
                  }}
                  probability={calculateProbability(mainEvent.fighter_2_odds)}
                  isMainEvent={true}
                />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Other Fights */}
      {otherFights.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-2xl font-bold text-white">Fight Card</h3>
          <div className="space-y-4">
            {otherFights.map((fight, index) => (
              <Card key={fight.fight_id} className="bg-gray-900 border-gray-800 hover:border-purple-600 transition-all hover:shadow-lg">
                <CardContent className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-5 gap-6 items-center">
                    {/* Fighter 1 */}
                    <FighterCard
                      fighter={{
                        id: fight.fighter_1_id,
                        name: fight.fighter_1_name,
                        record: fight.fighter_1_record,
                        image: fight.fighter_1_image,
                        odds: fight.fighter_1_odds
                      }}
                      probability={calculateProbability(fight.fighter_1_odds)}
                      isMainEvent={false}
                    />

                    {/* VS Section */}
                    <div className="flex flex-col items-center justify-center space-y-3">
                      <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-indigo-500 rounded-full flex items-center justify-center shadow-lg">
                        <span className="text-white text-xl font-black">VS</span>
                      </div>
                      <Badge className="bg-gradient-to-r from-purple-400 to-pink-400 text-white text-xs font-bold">
                        {fight.weight_class}
                      </Badge>
                      <div className="flex gap-2">
                        <Link
                          href={`/fighters/compare?fighter1=${fight.fighter_1_id}&fighter2=${fight.fighter_2_id}`}
                          className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-medium rounded-lg transition-all hover:scale-105 shadow-md"
                        >
                          ⚖️
                        </Link>
                      </div>
                    </div>

                    {/* Fighter 2 */}
                    <FighterCard
                      fighter={{
                        id: fight.fighter_2_id,
                        name: fight.fighter_2_name,
                        record: fight.fighter_2_record,
                        image: fight.fighter_2_image,
                        odds: fight.fighter_2_odds
                      }}
                      probability={calculateProbability(fight.fighter_2_odds)}
                      isMainEvent={false}
                      rightAlign={true}
                    />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// Fighter Card Component
interface FighterCardProps {
  fighter: {
    id: string
    name: string
    record: string
    image?: string
    odds?: string
  }
  probability: number
  isMainEvent: boolean
  rightAlign?: boolean
}

function FighterCard({ fighter, probability, isMainEvent, rightAlign = false }: FighterCardProps) {
  const isFavorite = fighter.odds && parseInt(fighter.odds) < 0
  const imageSize = isMainEvent ? 128 : 80

  const content = (
    <>
      {fighter.image && !rightAlign && (
        <div
          className={`rounded-full overflow-hidden ${isMainEvent ? 'ring-4 ring-red-500' : 'ring-2 ring-purple-500'} shadow-xl flex-shrink-0`}
          style={{ width: imageSize, height: imageSize }}
        >
          <Image
            src={fighter.image}
            alt={fighter.name}
            width={imageSize}
            height={imageSize}
            className="object-cover"
          />
        </div>
      )}

      <div className={`flex-1 ${rightAlign ? 'text-right' : ''} space-y-2`}>
        <Link
          href={`/fighters/${fighter.id}`}
          className={`${isMainEvent ? 'text-2xl' : 'text-xl'} font-bold text-white hover:text-red-500 transition-colors block`}
        >
          {fighter.name}
        </Link>
        <p className={`${isMainEvent ? 'text-lg' : 'text-sm'} text-gray-400 font-semibold`}>
          {fighter.record}
        </p>

        {fighter.odds && (
          <>
            <Badge className={`${isFavorite ? 'bg-red-500' : 'bg-blue-500'} text-white font-bold ${isMainEvent ? 'text-lg px-4 py-2' : 'text-sm px-3 py-1'}`}>
              {isFavorite && '⭐ '}{fighter.odds}
            </Badge>

            <div className="space-y-1">
              <div className={`${isMainEvent ? 'text-sm' : 'text-xs'} font-bold text-gray-300`}>
                {probability.toFixed(1)}% Win Probability
              </div>
              <div className={`w-full bg-gray-700 rounded-full ${isMainEvent ? 'h-3' : 'h-2'} overflow-hidden`}>
                <div
                  className={`${isFavorite ? 'bg-gradient-to-r from-red-400 to-red-500' : 'bg-gradient-to-r from-blue-400 to-blue-500'} rounded-full transition-all duration-500`}
                  style={{ width: `${probability}%`, height: '100%' }}
                />
              </div>
            </div>
          </>
        )}
      </div>

      {fighter.image && rightAlign && (
        <div
          className={`rounded-full overflow-hidden ${isMainEvent ? 'ring-4 ring-red-500' : 'ring-2 ring-purple-500'} shadow-xl flex-shrink-0`}
          style={{ width: imageSize, height: imageSize }}
        >
          <Image
            src={fighter.image}
            alt={fighter.name}
            width={imageSize}
            height={imageSize}
            className="object-cover"
          />
        </div>
      )}
    </>
  )

  return (
    <div className={`md:col-span-2 flex items-center ${isMainEvent ? 'flex-col text-center' : rightAlign ? 'justify-end' : ''} ${isMainEvent ? 'space-y-3' : 'space-x-4'} ${rightAlign && !isMainEvent ? 'flex-row-reverse space-x-reverse' : ''}`}>
      {content}
    </div>
  )
}
