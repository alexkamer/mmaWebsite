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
      <div className="space-y-6">
        <h2 className="text-2xl font-bold">Fight Card</h2>

        {event.fights && event.fights.length > 0 ? (
          <div className="space-y-6">
            {/* Group fights by card segment */}
            {(() => {
              const mainEvent = event.fights.filter(f => f.match_number === Math.max(...event.fights.map(ff => ff.match_number || 0)))
              const mainCard = event.fights.filter(f =>
                f.card_segment?.toLowerCase().includes('main') &&
                f.match_number !== Math.max(...event.fights.map(ff => ff.match_number || 0))
              )
              const prelims = event.fights.filter(f =>
                f.card_segment?.toLowerCase().includes('prelim') &&
                !f.card_segment?.toLowerCase().includes('early')
              )
              const earlyPrelims = event.fights.filter(f =>
                f.card_segment?.toLowerCase().includes('early')
              )

              const sections = [
                { title: "Main Event", fights: mainEvent, highlight: true },
                { title: "Main Card", fights: mainCard, highlight: false },
                { title: "Prelims", fights: prelims, highlight: false },
                { title: "Early Prelims", fights: earlyPrelims, highlight: false },
              ].filter(section => section.fights.length > 0)

              return sections.map((section, sectionIdx) => (
                <div key={sectionIdx} className="space-y-4">
                  <h3 className={`text-xl font-bold ${section.highlight ? 'text-yellow-400' : ''}`}>
                    {section.title}
                  </h3>

                  {section.fights.map((fight) => (
                    <div
                      key={fight.id}
                      className={`rounded-lg border bg-card p-4 md:p-6 transition-all hover:shadow-lg ${
                        fight.is_title_fight ? 'border-yellow-500/50' : ''
                      }`}
                    >
                      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                        {/* Fighter 1 */}
                        <Link
                          href={`/fighters/${fight.fighter1_id}`}
                          className="flex flex-1 items-center gap-3 md:gap-4 hover:underline"
                        >
                          {fight.fighter1_image ? (
                            <img
                              src={fight.fighter1_image}
                              alt={fight.fighter1_name}
                              className="h-12 w-12 md:h-16 md:w-16 rounded-full object-cover flex-shrink-0"
                            />
                          ) : (
                            <div className="flex h-12 w-12 md:h-16 md:w-16 items-center justify-center rounded-full bg-gray-800 text-xl md:text-2xl font-bold flex-shrink-0">
                              {fight.fighter1_name.charAt(0)}
                            </div>
                          )}
                          <div className="flex-1 min-w-0">
                            <div className="font-semibold text-base md:text-lg truncate">
                              {fight.fighter1_name}
                            </div>
                            <div className="flex flex-wrap items-center gap-2 text-xs md:text-sm text-muted-foreground">
                              {fight.fighter1_record && (
                                <span className="font-mono">{fight.fighter1_record}</span>
                              )}
                              {fight.fighter1_odds && (
                                <span className={`font-mono ${
                                  fight.fighter1_odds.startsWith('-') ? 'text-blue-400' : 'text-orange-400'
                                }`}>
                                  {fight.fighter1_odds}
                                </span>
                              )}
                            </div>
                            {fight.winner === "fighter1" && (
                              <span className="text-xs md:text-sm text-green-400 font-semibold">Winner</span>
                            )}
                          </div>
                        </Link>

                        {/* VS and Result */}
                        <div className="flex flex-col items-center gap-2 px-2 md:px-4 self-center">
                          <div className="text-xl md:text-2xl font-bold text-muted-foreground">
                            VS
                          </div>
                          {fight.method && (
                            <div className="text-center">
                              <div className="text-xs md:text-sm font-medium">{fight.method}</div>
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
                          className="flex flex-1 flex-row-reverse items-center gap-3 md:gap-4 hover:underline"
                        >
                          {fight.fighter2_image ? (
                            <img
                              src={fight.fighter2_image}
                              alt={fight.fighter2_name}
                              className="h-12 w-12 md:h-16 md:w-16 rounded-full object-cover flex-shrink-0"
                            />
                          ) : (
                            <div className="flex h-12 w-12 md:h-16 md:w-16 items-center justify-center rounded-full bg-gray-800 text-xl md:text-2xl font-bold flex-shrink-0">
                              {fight.fighter2_name.charAt(0)}
                            </div>
                          )}
                          <div className="flex-1 text-right min-w-0">
                            <div className="font-semibold text-base md:text-lg truncate">
                              {fight.fighter2_name}
                            </div>
                            <div className="flex flex-wrap items-center justify-end gap-2 text-xs md:text-sm text-muted-foreground">
                              {fight.fighter2_odds && (
                                <span className={`font-mono ${
                                  fight.fighter2_odds.startsWith('-') ? 'text-blue-400' : 'text-orange-400'
                                }`}>
                                  {fight.fighter2_odds}
                                </span>
                              )}
                              {fight.fighter2_record && (
                                <span className="font-mono">{fight.fighter2_record}</span>
                              )}
                            </div>
                            {fight.winner === "fighter2" && (
                              <span className="text-xs md:text-sm text-green-400 font-semibold">Winner</span>
                            )}
                          </div>
                        </Link>
                      </div>

                      {/* Weight Class */}
                      {fight.weight_class && (
                        <div className="mt-3 md:mt-4 text-center text-xs md:text-sm text-muted-foreground">
                          {fight.weight_class}
                          {fight.is_title_fight && " • ⭐ Title Fight"}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ))
            })()}
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
