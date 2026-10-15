import Link from "next/link";
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
      <body className="font-sans min-h-full flex flex-col bg-slate-950 text-slate-200">
        <nav className="border-b border-slate-800 bg-slate-900/60">
          <div className="mx-auto flex max-w-6xl items-center gap-6 px-4 py-3">
            <Link href="/" className="text-lg font-semibold tracking-tight text-white">
              Sentinel-AI
            </Link>
            <Link href="/" className="text-sm text-slate-400 hover:text-white">Overview</Link>
            <Link href="/assets" className="text-sm text-slate-400 hover:text-white">Assets</Link>
            <Link href="/findings" className="text-sm text-slate-400 hover:text-white">Findings</Link>
            <Link href="/scan" className="text-sm text-slate-400 hover:text-white">Scan</Link>
            <Link href="/reports" className="text-sm text-slate-400 hover:text-white">Reports</Link>
          </div>
        </nav>
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
