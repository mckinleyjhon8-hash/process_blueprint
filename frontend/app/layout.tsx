import type { Metadata } from "next";
import { Figtree, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/shell/Sidebar";
import { Topbar } from "@/components/shell/Topbar";
import { CommandPalette } from "@/components/shell/CommandPalette";

// Figtree: the friendly geometric sans of the Monday-class light system.
const jakarta = Figtree({
  variable: "--font-jakarta",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

const jet = JetBrains_Mono({
  variable: "--font-jet",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Process Blueprint — Consulting Intelligence",
  description: "Evidence-based process analysis for SME consulting engagements.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${jakarta.variable} ${jet.variable} h-full antialiased`}>
      <body className="h-full">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[70] focus:rounded-lg focus:bg-primary-strong focus:px-3 focus:py-2 focus:text-xs focus:font-semibold focus:text-white"
        >
          Skip to content
        </a>
        <div className="flex h-screen">
          <Sidebar />
          <div className="flex min-w-0 flex-1 flex-col">
            <Topbar />
            <main id="main" className="min-h-0 flex-1 overflow-y-auto">
              {children}
            </main>
          </div>
        </div>
        <CommandPalette />
      </body>
    </html>
  );
}
