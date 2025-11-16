"use client"

import { useState, useEffect } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { ArrowLeft, Calendar, MapPin, Trophy } from "lucide-react"
import { eventsAPI, type EventDetail } from "@/lib/api"

export default function EventDetailPage() {
  const params = useParams()
  const eventId = parseInt(params.id as string)

  const [event, setEvent] = useState<EventDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchEvent = async () => {
      setLoading(true)
      try {
        const data = await eventsAPI.get(eventId)
        setEvent(data)
      } catch (error) {
        console.error("Error fetching event:", error)
      } finally {
        setLoading(false)
      }
    }

    if (eventId) {
      fetchEvent()
    }
  }, [eventId])

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="h-8 w-48 animate-pulse rounded bg-gray-700" />
        <div className="h-32 animate-pulse rounded-lg bg-gray-700" />
        <div className="h-96 animate-pulse rounded-lg bg-gray-700" />
      </div>
    )
  }

  if (!event) {
    return (
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold mb-4">Event not found</h1>
        <Link href="/events" className="text-blue-500 hover:underline">
          Back to events
        </Link>
      </div>
    )
  }

  const eventDate = event.date ? new Date(event.date) : null

  return (
    <div className="space-y-8">
      {/* Back Button */}
      <Link
        href="/events"
        className="inline-flex items-center gap-2 text-sm hover:underline"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to events
      </Link>

      {/* Event Header */}
      <div className="rounded-lg border bg-card p-8">
        <div className="space-y-4">
          <h1 className="text-4xl font-bold">{event.name}</h1>

          <div className="flex flex-wrap gap-4 text-muted-foreground">
            {eventDate && (
              <div className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                {eventDate.toLocaleDateString("en-US", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </div>
            )}
            {event.location && (
              <div className="flex items-center gap-2">
                <MapPin className="h-5 w-5" />
                {event.location}
              </div>
            )}
            {event.venue && (
              <div className="flex items-center gap-2">
                <Trophy className="h-5 w-5" />
                {event.venue}
              </div>
            )}
          </div>

          {event.promotion && (
            <div className="inline-block rounded border px-3 py-1 text-sm font-medium uppercase">
              {event.promotion}
            </div>
          )}
        </div>
      </div>

      {/* Fight Card */}
      <div className="space-y-4">
        <h2 className="text-2xl font-bold">Fight Card</h2>

        {event.fights && event.fights.length > 0 ? (
          <div className="space-y-4">
            {event.fights.map((fight, idx) => (
              <div
                key={fight.id}
                className="rounded-lg border bg-card p-6 transition-all hover:shadow-lg"
              >
                <div className="flex items-center justify-between gap-4">
                  {/* Fighter 1 */}
                  <Link
                    href={`/fighters/${fight.fighter1_id}`}
                    className="flex flex-1 items-center gap-4 hover:underline"
                  >
                    {fight.fighter1_image ? (
                      <img
                        src={fight.fighter1_image}
                        alt={fight.fighter1_name}
                        className="h-16 w-16 rounded-full object-cover"
                      />
                    ) : (
                      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gray-800 text-2xl font-bold">
                        {fight.fighter1_name.charAt(0)}
                      </div>
                    )}
                    <div className="flex-1">
                      <div className="font-semibold text-lg">
                        {fight.fighter1_name}
                      </div>
                      {fight.winner === "fighter1" && (
                        <span className="text-sm text-green-400">Winner</span>
                      )}
                    </div>
                  </Link>

                  {/* VS and Result */}
                  <div className="flex flex-col items-center gap-2 px-4">
                    <div className="text-2xl font-bold text-muted-foreground">
                      VS
                    </div>
                    {fight.method && (
                      <div className="text-center">
                        <div className="text-sm font-medium">{fight.method}</div>
                        {fight.round && fight.time && (
                          <div className="text-xs text-muted-foreground">
                            R{fight.round} {fight.time}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Fighter 2 */}
                  <Link
                    href={`/fighters/${fight.fighter2_id}`}
                    className="flex flex-1 flex-row-reverse items-center gap-4 hover:underline"
                  >
                    {fight.fighter2_image ? (
                      <img
                        src={fight.fighter2_image}
                        alt={fight.fighter2_name}
                        className="h-16 w-16 rounded-full object-cover"
                      />
                    ) : (
                      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gray-800 text-2xl font-bold">
                        {fight.fighter2_name.charAt(0)}
                      </div>
                    )}
                    <div className="flex-1 text-right">
                      <div className="font-semibold text-lg">
                        {fight.fighter2_name}
                      </div>
                      {fight.winner === "fighter2" && (
                        <span className="text-sm text-green-400">Winner</span>
                      )}
                    </div>
                  </Link>
                </div>

                {/* Weight Class */}
                {fight.weight_class && (
                  <div className="mt-4 text-center text-sm text-muted-foreground">
                    {fight.weight_class}
                    {fight.is_title_fight && " • Title Fight"}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-lg border bg-card p-8 text-center text-muted-foreground">
            No fights scheduled for this event yet
          </div>
        )}
      </div>
    </div>
  )
}
