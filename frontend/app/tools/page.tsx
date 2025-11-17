import Link from "next/link"
import { TrendingUp, BarChart3, Zap, Wrench } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function ToolsPage() {
  const tools = [
    {
      title: "System Checker",
      description: "Comprehensive betting analytics dashboard with weight class performance, rounds analysis, and card-by-card results. Filter by league (UFC, PFL, Bellator) and year (2019-2025).",
      href: "/tools/system-checker",
      icon: TrendingUp,
      gradient: "from-blue-500 to-cyan-500",
      features: [
        "Betting system analytics",
        "Weight class performance",
        "Upset detection",
        "Card-by-card results"
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
            <div className="inline-flex items-center gap-2 bg-blue-600/10 border border-blue-600/20 text-blue-500 px-4 py-2 rounded-full text-sm font-semibold mb-4">
              <Wrench className="w-4 h-4" />
              ANALYTICS & TOOLS
            </div>

            {/* Title */}
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-4">
              MMA Analytics
            </h1>

            {/* Subtitle */}
            <p className="text-xl text-slate-400 mb-6">
              Advanced analytics and data tools for serious MMA fans
            </p>
          </div>
        </div>
      </section>

      {/* Tools Grid */}
      <section className="py-12 bg-slate-950">
        <div className="container mx-auto px-4">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 max-w-6xl mx-auto">
            {tools.map((tool) => {
              const Icon = tool.icon
              return (
                <Link key={tool.href} href={tool.href} className="group">
                  <Card className="h-full bg-slate-900 border-slate-800 hover:border-blue-600 transition-all hover:shadow-lg hover:shadow-blue-600/10 overflow-hidden">
                    {/* Gradient Header */}
                    <div className={`h-2 bg-gradient-to-r ${tool.gradient}`}></div>

                    <CardHeader>
                      <div className="flex items-center gap-3 mb-2">
                        <div className={`p-3 rounded-lg bg-gradient-to-r ${tool.gradient} shadow-lg`}>
                          <Icon className="w-6 h-6 text-white" />
                        </div>
                        <CardTitle className="text-2xl text-white group-hover:text-blue-400 transition-colors">
                          {tool.title}
                        </CardTitle>
                      </div>
                      <CardDescription className="text-slate-400 text-base">
                        {tool.description}
                      </CardDescription>
                    </CardHeader>

                    <CardContent>
                      <div className="space-y-2">
                        <p className="text-sm font-semibold text-slate-300 mb-3">Features:</p>
                        <ul className="space-y-2">
                          {tool.features.map((feature, index) => (
                            <li key={index} className="flex items-center gap-2 text-sm text-slate-400">
                              <Zap className="w-4 h-4 text-blue-500 flex-shrink-0" />
                              {feature}
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div className="mt-6 pt-4 border-t border-slate-800">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-blue-400 group-hover:text-blue-300 transition-colors">
                            Open Tool →
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
                    <BarChart3 className="w-6 h-6 text-slate-600" />
                  </div>
                  <CardTitle className="text-2xl text-slate-500">
                    More Tools
                  </CardTitle>
                </div>
                <CardDescription className="text-slate-600">
                  More analytics tools coming soon! Stay tuned for updates.
                </CardDescription>
              </CardHeader>

              <CardContent>
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-slate-600 mb-3">Coming Soon:</p>
                  <ul className="space-y-2">
                    <li className="flex items-center gap-2 text-sm text-slate-600">
                      <Zap className="w-4 h-4 text-slate-700 flex-shrink-0" />
                      Fighter performance trends
                    </li>
                    <li className="flex items-center gap-2 text-sm text-slate-600">
                      <Zap className="w-4 h-4 text-slate-700 flex-shrink-0" />
                      Advanced statistics
                    </li>
                    <li className="flex items-center gap-2 text-sm text-slate-600">
                      <Zap className="w-4 h-4 text-slate-700 flex-shrink-0" />
                      Historical data analysis
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
