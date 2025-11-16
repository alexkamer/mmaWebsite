"use client"

import Link from "next/link"
import { Gamepad2, Swords, Trophy, TrendingUp, Search } from "lucide-react"

export default function GamesPage() {
  const games = [
    {
      title: "System Checker",
      description: "Betting analytics and system performance tracking",
      icon: TrendingUp,
      href: "/games/system-checker",
      available: true,
    },
    {
      title: "Fighter Wordle",
      description: "Guess the UFC fighter with hints",
      icon: Gamepad2,
      href: "/games/fighter-wordle",
      available: true,
    },
    {
      title: "Tale of the Tape",
      description: "Compare two fighters side-by-side",
      icon: Swords,
      href: "/games/tale-of-tape",
      available: true,
    },
    {
      title: "Next Event",
      description: "View upcoming UFC events with ESPN data",
      icon: Trophy,
      href: "/games/next-event",
      available: true,
    },
    {
      title: "MMA Query",
      description: "Ask questions about MMA data in natural language",
      icon: Search,
      href: "/games/mma-query",
      available: true,
    },
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="space-y-4">
        <h1 className="text-4xl font-bold">Games & Tools</h1>
        <p className="text-muted-foreground">
          Interactive tools and games for MMA fans
        </p>
      </div>

      {/* Games Grid */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {games.map((game) => {
          const Icon = game.icon
          return (
            <Link
              key={game.title}
              href={game.available ? game.href : "#"}
              className={`group relative overflow-hidden rounded-lg border bg-card p-6 transition-all ${
                game.available
                  ? "hover:shadow-lg hover:border-primary"
                  : "opacity-50 cursor-not-allowed"
              }`}
              onClick={(e) => {
                if (!game.available) e.preventDefault()
              }}
            >
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-primary/10 p-3">
                    <Icon className="h-6 w-6 text-primary" />
                  </div>
                  {!game.available && (
                    <span className="rounded bg-yellow-900/30 px-2 py-1 text-xs font-semibold text-yellow-500">
                      COMING SOON
                    </span>
                  )}
                </div>

                <div>
                  <h3 className="text-xl font-semibold mb-2">{game.title}</h3>
                  <p className="text-sm text-muted-foreground">
                    {game.description}
                  </p>
                </div>
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
