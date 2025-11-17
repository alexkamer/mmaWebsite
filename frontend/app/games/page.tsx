import Link from "next/link"
import { Gamepad2, Trophy, Zap } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function GamesPage() {
  const games = [
    {
      title: "Fighter Wordle",
      description: "Test your MMA knowledge! Guess the UFC fighter in 6 attempts with hints about their nationality, weight class, and age.",
      href: "/games/wordle",
      icon: Trophy,
      gradient: "from-purple-500 to-blue-500",
      features: [
        "Daily fighter challenges",
        "Color-coded hints",
        "Fighter photos",
        "6 attempts to guess"
      ]
    }
  ]

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950 border-b border-slate-800">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>

        <div className="relative container mx-auto px-4 py-16">
          <div className="max-w-4xl mx-auto text-center">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 bg-purple-600/10 border border-purple-600/20 text-purple-500 px-4 py-2 rounded-full text-sm font-semibold mb-4">
              <Gamepad2 className="w-4 h-4" />
              INTERACTIVE GAMES
            </div>

            {/* Title */}
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-4">
              MMA Games
            </h1>

            {/* Subtitle */}
            <p className="text-xl text-slate-400 mb-6">
              Test your MMA knowledge with fun, interactive games
            </p>
          </div>
        </div>
      </section>

      {/* Games Grid */}
      <section className="py-12 bg-slate-950">
        <div className="container mx-auto px-4">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 max-w-6xl mx-auto">
            {games.map((game) => {
              const Icon = game.icon
              return (
                <Link key={game.href} href={game.href} className="group">
                  <Card className="h-full bg-slate-900 border-slate-800 hover:border-purple-600 transition-all hover:shadow-lg hover:shadow-purple-600/10 overflow-hidden">
                    {/* Gradient Header */}
                    <div className={`h-2 bg-gradient-to-r ${game.gradient}`}></div>

                    <CardHeader>
                      <div className="flex items-center gap-3 mb-2">
                        <div className={`p-3 rounded-lg bg-gradient-to-r ${game.gradient} shadow-lg`}>
                          <Icon className="w-6 h-6 text-white" />
                        </div>
                        <CardTitle className="text-2xl text-white group-hover:text-purple-400 transition-colors">
                          {game.title}
                        </CardTitle>
                      </div>
                      <CardDescription className="text-slate-400 text-base">
                        {game.description}
                      </CardDescription>
                    </CardHeader>

                    <CardContent>
                      <div className="space-y-2">
                        <p className="text-sm font-semibold text-slate-300 mb-3">Features:</p>
                        <ul className="space-y-2">
                          {game.features.map((feature, index) => (
                            <li key={index} className="flex items-center gap-2 text-sm text-slate-400">
                              <Zap className="w-4 h-4 text-purple-500 flex-shrink-0" />
                              {feature}
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div className="mt-6 pt-4 border-t border-slate-800">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-purple-400 group-hover:text-purple-300 transition-colors">
                            Play Now →
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              )
            })}

            {/* Coming Soon Card */}
            <Card className="h-full bg-slate-900 border-slate-800 border-dashed opacity-60">
              <CardHeader>
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-3 rounded-lg bg-slate-800">
                    <Gamepad2 className="w-6 h-6 text-slate-600" />
                  </div>
                  <CardTitle className="text-2xl text-slate-500">
                    More Games
                  </CardTitle>
                </div>
                <CardDescription className="text-slate-600">
                  More exciting MMA games coming soon! Stay tuned for updates.
                </CardDescription>
              </CardHeader>

              <CardContent>
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-slate-600 mb-3">Coming Soon:</p>
                  <ul className="space-y-2">
                    <li className="flex items-center gap-2 text-sm text-slate-600">
                      <Zap className="w-4 h-4 text-slate-700 flex-shrink-0" />
                      Fight prediction challenges
                    </li>
                    <li className="flex items-center gap-2 text-sm text-slate-600">
                      <Zap className="w-4 h-4 text-slate-700 flex-shrink-0" />
                      Trivia quizzes
                    </li>
                    <li className="flex items-center gap-2 text-sm text-slate-600">
                      <Zap className="w-4 h-4 text-slate-700 flex-shrink-0" />
                      Fantasy matchups
                    </li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>
    </div>
  )
}
