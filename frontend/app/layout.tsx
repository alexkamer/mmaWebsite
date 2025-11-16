import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/providers/theme-provider";
import { QueryProvider } from "@/components/providers/query-provider";
import { Navigation } from "@/components/navigation";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: {
    default: "MMA Stats - Fighter Database, Rankings & Fight Analysis",
    template: "%s | MMA Stats",
  },
  description: "Comprehensive MMA fighter database with 36,000+ fighters, live UFC rankings, event schedules, fight history, and detailed statistics. Compare fighters, explore events, and track your favorite athletes.",
  keywords: ["MMA", "UFC", "fighters", "rankings", "fight stats", "mixed martial arts", "combat sports", "fight analysis", "tale of the tape"],
  authors: [{ name: "MMA Stats" }],
  creator: "MMA Stats",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "http://localhost:3000",
    title: "MMA Stats - Fighter Database, Rankings & Fight Analysis",
    description: "Comprehensive MMA fighter database with 36,000+ fighters, live UFC rankings, and detailed statistics.",
    siteName: "MMA Stats",
  },
  twitter: {
    card: "summary_large_image",
    title: "MMA Stats - Fighter Database, Rankings & Fight Analysis",
    description: "Comprehensive MMA fighter database with 36,000+ fighters, live UFC rankings, and detailed statistics.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <QueryProvider>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            <Navigation />
            <main className="container mx-auto px-4 py-8">
              {children}
            </main>
          </ThemeProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
