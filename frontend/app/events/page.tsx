"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Calendar, MapPin } from "lucide-react"
import { eventsAPI, type Event } from "@/lib/api"

export default function EventsPage() {
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [selectedYear, setSelectedYear] = useState<number | null>(null)
  const [availableYears, setAvailableYears] = useState<number[]>([])

  useEffect(() => {
    const fetchYears = async () => {
      try {
        const data = await eventsAPI.getYears()
        setAvailableYears(data.years)
      } catch (error) {
        console.error("Error fetching years:", error)
      }
    }
    fetchYears()
  }, [])

  useEffect(() => {
    const fetchEvents = async () => {
      setLoading(true)
      try {
        const data = await eventsAPI.list({
          year: selectedYear || undefined,
          limit: 100,
        })
        setEvents(data.events)
        setTotal(data.total)
      } catch (error) {
        console.error("Error fetching events:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchEvents()
  }, [selectedYear])

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="space-y-4">
        <h1 className="text-4xl font-bold">Events</h1>
        <p className="text-muted-foreground">
          Browse {total.toLocaleString()} MMA events
        </p>
      </div>

      {/* Year Filter */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setSelectedYear(null)}
          className={`rounded-lg border px-4 py-2 text-sm font-medium transition-colors ${
            selectedYear === null
              ? "bg-primary text-primary-foreground"
              : "bg-background hover:bg-muted"
          }`}
        >
          All Years
        </button>
        {availableYears.map((year) => (
          <button
            key={year}
            onClick={() => setSelectedYear(year)}
            className={`rounded-lg border px-4 py-2 text-sm font-medium transition-colors ${
              selectedYear === year
                ? "bg-primary text-primary-foreground"
                : "bg-background hover:bg-muted"
            }`}
          >
            {year}
          </button>
        ))}
      </div>

      {/* Loading State */}
      {loading ? (
        <div className="space-y-4">
          {[...Array(8)].map((_, i) => (
            <div
              key={i}
              className="h-24 animate-pulse rounded-lg border bg-muted"
            />
          ))}
        </div>
      ) : (
        <>
          {/* Events List */}
          {events.length > 0 ? (
            <div className="space-y-4">
              {events.map((event) => {
                const eventDate = event.date
                  ? new Date(event.date)
                  : null
                const isPast = eventDate ? eventDate < new Date() : false
                const isUpcoming = eventDate ? eventDate >= new Date() : false

                return (
                  <Link
                    key={event.id}
                    href={`/events/${event.id}`}
                    className="group block rounded-lg border bg-card p-6 transition-all hover:shadow-lg"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-3">
                          <h3 className="text-xl font-semibold group-hover:underline">
                            {event.name}
                          </h3>
                          {isUpcoming && (
                            <span className="rounded bg-green-900/30 px-2 py-1 text-xs font-semibold text-green-400">
                              UPCOMING
                            </span>
                          )}
                        </div>

                        <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                          {event.date && (
                            <div className="flex items-center gap-1">
                              <Calendar className="h-4 w-4" />
                              {eventDate?.toLocaleDateString("en-US", {
                                year: "numeric",
                                month: "long",
                                day: "numeric",
                              })}
                            </div>
                          )}
                          {event.location && (
                            <div className="flex items-center gap-1">
                              <MapPin className="h-4 w-4" />
                              {event.location}
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="text-right">
                        <span className="inline-block rounded border px-3 py-1 text-xs font-medium uppercase">
                          {event.promotion}
                        </span>
                      </div>
                    </div>
                  </Link>
                )
              })}
            </div>
          ) : (
            <div className="rounded-lg border bg-card p-12 text-center">
              <p className="text-muted-foreground">
                No events found for {selectedYear || "all years"}
              </p>
            </div>
          )}
        </>
      )}
    </div>
  )
}
