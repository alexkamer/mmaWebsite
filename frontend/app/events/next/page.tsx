"use client"

import { useState, useEffect } from "react"
import { Calendar, MapPin, Trophy, Users } from "lucide-react"
import { espnAPI, type NextEventResponse, type NextEventFight } from "@/lib/api"
import Image from "next/image"

export default function NextEventPage() {
  const [data, setData] = useState<NextEventResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      setError(null)
      try {
        const eventData = await espnAPI.getNextEvent()
        setData(eventData)
      } catch (err) {
        console.error("Error fetching next event:", err)
        setError("Failed to load event data. Please try again later.")
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="h-8 w-64 animate-pulse rounded bg-gray-700" />
        <div className="h-96 animate-pulse rounded-lg bg-gray-700" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6">
        <h3 className="mb-2 font-bold text-red-500">⚠️ Error</h3>
        <p className="text-muted-foreground">{error || "No event data available"}</p>
      </div>
    )
  }

  const { event, fights } = data

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="space-y-4">
        <h1 className="flex items-center gap-3 text-4xl font-bold">
          <Trophy className="h-10 w-10" />
          Next UFC Event
        </h1>
        <p className="text-muted-foreground">
          Live data from ESPN API - upcoming fights and odds
        </p>
      </div>

      {/* Event Card */}
      <div className="rounded-lg border bg-card p-6">
        <h2 className="mb-4 text-2xl font-bold">{event.event_name}</h2>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {/* Date */}
          <div className="flex items-center gap-3 rounded-lg bg-muted p-4">
            <Calendar className="h-5 w-5 text-primary" />
            <div>
              <div className="text-sm text-muted-foreground">Date</div>
              <div className="font-semibold">
                {new Date(event.date).toLocaleDateString("en-US", {
                  weekday: "long",
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </div>
            </div>
          </div>

          {/* Location */}
          {event.venue_name && (
            <div className="flex items-center gap-3 rounded-lg bg-muted p-4">
              <MapPin className="h-5 w-5 text-primary" />
              <div>
                <div className="text-sm text-muted-foreground">Location</div>
                <div className="font-semibold">{event.venue_name}</div>
                {(event.city || event.state) && (
                  <div className="text-sm text-muted-foreground">
                    {[event.city, event.state].filter(Boolean).join(", ")}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Total Fights */}
          <div className="flex items-center gap-3 rounded-lg bg-muted p-4">
            <Users className="h-5 w-5 text-primary" />
            <div>
              <div className="text-sm text-muted-foreground">Total Fights</div>
              <div className="text-2xl font-bold">{fights.length}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Fight Card */}
      <div className="space-y-4">
        <h2 className="text-2xl font-bold">Fight Card</h2>

        {fights.map((fight) => (
          <FightCard key={fight.fight_id} fight={fight} />
        ))}
      </div>

      {/* Disclaimer */}
      <div className="rounded-lg border-l-4 border-blue-500 bg-blue-500/10 p-4">
        <p className="text-sm text-muted-foreground">
          <strong>Note:</strong> Fight data and odds are provided by ESPN API and
          may be subject to change.
        </p>
      </div>
    </div>
  )
}

function FightCard({ fight }: { fight: NextEventFight }) {
  return (
    <div className="rounded-lg border bg-card p-6 transition-all hover:border-primary/50 hover:shadow-lg">
      {/* Weight Class & Round Info */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          {fight.weight_class && (
            <span className="rounded-full bg-primary/10 px-3 py-1 text-sm font-semibold">
              {fight.weight_class}
            </span>
          )}
          {fight.rounds_format && (
            <span className="rounded-full bg-muted px-3 py-1 text-sm">
              {fight.rounds_format} Rounds
            </span>
          )}
        </div>
        {fight.match_number && (
          <span className="text-sm text-muted-foreground">
            Fight #{fight.match_number}
          </span>
        )}
      </div>

      {/* Fighters */}
      <div className="grid gap-6 md:grid-cols-[1fr_auto_1fr]">
        {/* Fighter 1 */}
        <div className="flex flex-col items-center space-y-3">
          <div className="relative h-24 w-24 overflow-hidden rounded-full border-4 border-primary/20">
            {fight.fighter_1_image ? (
              <Image
                src={fight.fighter_1_image}
                alt={fight.fighter_1_name}
                fill
                className="object-cover"
              />
            ) : (
              <div className="flex h-full w-full items-center justify-center bg-muted">
                <Users className="h-12 w-12 text-muted-foreground" />
              </div>
            )}
          </div>

          <div className="text-center">
            <h3 className="text-xl font-bold">{fight.fighter_1_name}</h3>
            <p className="text-sm text-muted-foreground">{fight.fighter_1_record}</p>
          </div>

          {fight.fighter_1_odds && (
            <div
              className={`rounded-lg px-4 py-2 font-bold ${
                fight.fighter_1_odds.startsWith("-")
                  ? "bg-green-500/10 text-green-500"
                  : "bg-red-500/10 text-red-500"
              }`}
            >
              {fight.fighter_1_odds}
              {fight.fighter_1_odds.startsWith("-") && (
                <span className="ml-1 text-xs">(Favorite)</span>
              )}
            </div>
          )}
        </div>

        {/* VS Divider */}
        <div className="flex items-center justify-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 font-bold">
            VS
          </div>
        </div>

        {/* Fighter 2 */}
        <div className="flex flex-col items-center space-y-3">
          <div className="relative h-24 w-24 overflow-hidden rounded-full border-4 border-primary/20">
            {fight.fighter_2_image ? (
              <Image
                src={fight.fighter_2_image}
                alt={fight.fighter_2_name}
                fill
                className="object-cover"
              />
            ) : (
              <div className="flex h-full w-full items-center justify-center bg-muted">
                <Users className="h-12 w-12 text-muted-foreground" />
              </div>
            )}
          </div>

          <div className="text-center">
            <h3 className="text-xl font-bold">{fight.fighter_2_name}</h3>
            <p className="text-sm text-muted-foreground">{fight.fighter_2_record}</p>
          </div>

          {fight.fighter_2_odds && (
            <div
              className={`rounded-lg px-4 py-2 font-bold ${
                fight.fighter_2_odds.startsWith("-")
                  ? "bg-green-500/10 text-green-500"
                  : "bg-red-500/10 text-red-500"
              }`}
            >
              {fight.fighter_2_odds}
              {fight.fighter_2_odds.startsWith("-") && (
                <span className="ml-1 text-xs">(Favorite)</span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
