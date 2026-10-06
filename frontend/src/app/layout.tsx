import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Sentinel-AI",
  description: "AI-powered cybersecurity analysis platform",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-slate-950 text-slate-200">
        <nav className="border-b border-slate-800 bg-slate-900/60">
          <div className="mx-auto flex max-w-6xl items-center gap-6 px-4 py-3">
            <a href="/" className="text-lg font-semibold tracking-tight text-white">
              Sentinel-AI
            </a>
            <a href="/" className="text-sm text-slate-400 hover:text-white">Overview</a>
            <a href="/assets" className="text-sm text-slate-400 hover:text-white">Assets</a>
            <a href="/findings" className="text-sm text-slate-400 hover:text-white">Findings</a>
            <a href="/scan" className="text-sm text-slate-400 hover:text-white">Scan</a>
            <a href="/reports" className="text-sm text-slate-400 hover:text-white">Reports</a>
          </div>
        </nav>
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
