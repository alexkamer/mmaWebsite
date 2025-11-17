"use client"

import Link from "next/link"
import { TrendingUp, Search } from "lucide-react"

export default function ToolsPage() {
  const tools = [
    {
      title: "System Checker",
      description: "Betting analytics and system performance tracking",
      icon: TrendingUp,
      href: "/tools/system-checker",
      available: true,
    },
    {
      title: "MMA Query",
      description: "Ask questions about MMA data in natural language",
      icon: Search,
      href: "/tools/query",
      available: true,
    },
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="space-y-4">
        <h1 className="text-4xl font-bold">Analytics & Tools</h1>
        <p className="text-muted-foreground">
          Advanced analytics and data tools for serious MMA fans
        </p>
      </div>

      {/* Tools Grid */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {tools.map((tool) => {
          const Icon = tool.icon
          return (
            <Link
              key={tool.title}
              href={tool.available ? tool.href : "#"}
              className={`group relative overflow-hidden rounded-lg border bg-card p-6 transition-all ${
                tool.available
                  ? "hover:shadow-lg hover:border-primary"
                  : "opacity-50 cursor-not-allowed"
              }`}
              onClick={(e) => {
                if (!tool.available) e.preventDefault()
              }}
            >
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-primary/10 p-3">
                    <Icon className="h-6 w-6 text-primary" />
                  </div>
                  {!tool.available && (
                    <span className="rounded bg-yellow-900/30 px-2 py-1 text-xs font-semibold text-yellow-500">
                      COMING SOON
                    </span>
                  )}
                </div>

                <div>
                  <h3 className="text-xl font-semibold mb-2">{tool.title}</h3>
                  <p className="text-sm text-muted-foreground">
                    {tool.description}
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
