import "./globals.css"
import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Forkfix — Parallel Reality Debugging (Nebius x NVIDIA)",
  description: "Fork 4 parallel repair realities from an immutable test checkpoint, find the smallest passing patch for pennies, and escalate with Tavily & Nemotron Ultra.",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="light">
      <body className="bg-obsidian-950 text-slate-800 min-h-screen antialiased selection:bg-cyber-emerald/30 selection:text-slate-900">
        {children}
      </body>
    </html>
  )
}
