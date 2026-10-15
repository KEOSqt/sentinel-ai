import { NextResponse } from "next/server";

/**
 * Liveness probe for the dashboard container.
 *
 * Reports only that this app is serving. It deliberately does not fail when
 * the backend is down: that is a degraded state, not a dead frontend, and
 * failing here would make Docker restart a container that is working fine.
 */
export function GET() {
  return NextResponse.json({ status: "healthy" });
}