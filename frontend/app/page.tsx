"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import Image from "next/image"
import { Flame } from "lucide-react"
import { FadeIn } from "@/components/animations/fade-in"
import { StaggerContainer, StaggerItem } from "@/components/animations/stagger-container"
import { eventsAPI, type RecentFinish } from "@/lib/api"

export default function HomePage() {
  const [finishes, setFinishes] = useState<RecentFinish[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchFinishes = async () => {
      try {
        const data = await eventsAPI.getRecentFinishes({ limit: 6 })
        setFinishes(data.finishes)
      } catch (error) {
        console.error("Error fetching recent finishes:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchFinishes()
  }, [])

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <FadeIn duration={0.6}>
        <section className="text-center space-y-4">
          <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
            MMA Fighter Database
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Comprehensive statistics, rankings, and fight analysis for MMA fighters worldwide
          </p>
        </section>
      </FadeIn>

      {/* Quick Links Grid */}
      <StaggerContainer className="grid gap-6 sm:grid-cols-2 lg:grid-cols-5" staggerDelay={0.1}>
        <StaggerItem>
          <Link
            href="/fighters"
            className="block group relative overflow-hidden rounded-lg border bg-card p-6 hover:shadow-lg transition-all"
          >
            <div className="space-y-2">
              <h3 className="text-2xl font-semibold">Fighters</h3>
              <p className="text-sm text-muted-foreground">
                Browse fighter profiles, stats, and fight history
              </p>
            </div>
            <div className="absolute bottom-0 right-0 h-24 w-24 -mr-8 -mb-8 opacity-10 group-hover:opacity-20 transition-opacity">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
              </svg>
            </div>
          </Link>
        </StaggerItem>

        <StaggerItem>
          <Link
            href="/events"
            className="block group relative overflow-hidden rounded-lg border bg-card p-6 hover:shadow-lg transition-all"
          >
            <div className="space-y-2">
              <h3 className="text-2xl font-semibold">Events</h3>
              <p className="text-sm text-muted-foreground">
                Upcoming and past fight cards with results
              </p>
            </div>
          </Link>
        </StaggerItem>

        <StaggerItem>
          <Link
            href="/rankings"
            className="block group relative overflow-hidden rounded-lg border bg-card p-6 hover:shadow-lg transition-all"
          >
            <div className="space-y-2">
              <h3 className="text-2xl font-semibold">Rankings</h3>
              <p className="text-sm text-muted-foreground">
                Current UFC rankings by division
              </p>
            </div>
          </Link>
        </StaggerItem>

        <StaggerItem>
          <Link
            href="/games"
            className="block group relative overflow-hidden rounded-lg border bg-card p-6 hover:shadow-lg transition-all"
          >
            <div className="space-y-2">
              <h3 className="text-2xl font-semibold">Games</h3>
              <p className="text-sm text-muted-foreground">
                Fighter Wordle, Tale of the Tape, and more
              </p>
            </div>
          </Link>
        </StaggerItem>

        <StaggerItem>
          <Link
            href="/tools"
            className="block group relative overflow-hidden rounded-lg border bg-card p-6 hover:shadow-lg transition-all"
          >
            <div className="space-y-2">
              <h3 className="text-2xl font-semibold">Tools</h3>
              <p className="text-sm text-muted-foreground">
                Analytics, betting systems, and advanced queries
              </p>
            </div>
          </Link>
        </StaggerItem>
      </StaggerContainer>

      {/* Recent Finishes Section */}
      <FadeIn delay={0.2} duration={0.6}>
        <section className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Flame className="h-6 w-6 text-orange-500" />
              <h2 className="text-2xl font-bold">Recent Finishes</h2>
            </div>
            <Link
              href="/events"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              View All Events →
            </Link>
          </div>

          {loading ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {[...Array(6)].map((_, i) => (
                <div
                  key={i}
                  className="h-40 animate-pulse rounded-lg border bg-muted"
                />
              ))}
            </div>
          ) : finishes.length > 0 ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {finishes.map((finish) => (
                <div
                  key={finish.fight_id}
                  className="group relative overflow-hidden rounded-lg border bg-card transition-all hover:shadow-lg"
                >
                  <div className="p-4 space-y-3">
                    {/* Finish Type Badge */}
                    <div className="flex items-center justify-between">
                      <span className="inline-flex items-center gap-1 rounded-full bg-orange-500/10 px-2.5 py-0.5 text-xs font-semibold text-orange-500">
                        {finish.finish_type}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        R{finish.round} {finish.time}
                      </span>
                    </div>

                    {/* Winner */}
                    <Link
                      href={`/fighters/${finish.winner_id}`}
                      className="block hover:underline"
                    >
                      <div className="flex items-center gap-3">
                        {finish.winner_image ? (
                          <div className="relative h-12 w-12 overflow-hidden rounded-full border-2 border-orange-500">
                            <Image
                              src={finish.winner_image}
                              alt={finish.winner_name}
                              fill
                              sizes="48px"
                              className="object-cover"
                            />
                          </div>
                        ) : (
                          <div className="flex h-12 w-12 items-center justify-center rounded-full border-2 border-orange-500 bg-muted text-sm font-bold">
                            {finish.winner_name.charAt(0)}
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <div className="font-semibold truncate">
                            {finish.winner_name}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            defeated {finish.fighter1_id === finish.winner_id ? finish.fighter2_name : finish.fighter1_name}
                          </div>
                        </div>
                      </div>
                    </Link>

                    {/* Event Info */}
                    <Link
                      href={`/events/${finish.event_id}`}
                      className="block text-xs text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {finish.event_name}
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-lg border bg-card p-12 text-center">
              <p className="text-muted-foreground">No recent finishes found</p>
            </div>
          )}
        </section>
      </FadeIn>

      {/* Stats Section */}
      <FadeIn delay={0.3} duration={0.6}>
        <section className="grid gap-6 sm:grid-cols-3">
          <div className="rounded-lg border bg-card p-6">
            <div className="text-3xl font-bold">36,000+</div>
            <div className="text-sm text-muted-foreground">Fighters</div>
          </div>
          <div className="rounded-lg border bg-card p-6">
            <div className="text-3xl font-bold">10,000+</div>
            <div className="text-sm text-muted-foreground">Events</div>
          </div>
          <div className="rounded-lg border bg-card p-6">
            <div className="text-3xl font-bold">Live</div>
            <div className="text-sm text-muted-foreground">UFC Rankings</div>
          </div>
        </section>
      </FadeIn>
    </div>
  )
}
