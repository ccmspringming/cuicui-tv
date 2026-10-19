import { NextResponse } from 'next/server';
import { fetchUpstream } from '@/lib/fetch-utils';
import { parseSubscriptionJson, parseSubscriptionPayload, describeParseStats } from '@/lib/tvbox-parser';
import { getEnvSubscriptions } from '@/lib/env-subscriptions';

export const runtime = 'nodejs';

/**
 * TEMPORARY diagnostic route — no auth, no parameters, no secrets.
 * Only answers: can this Worker fetch its own subscription URL, and does the
 * payload parse into sources? Delete after the investigation.
 */
export async function GET() {
  const subs = getEnvSubscriptions();
  const out: Record<string, unknown> = { envSubscriptions: subs };

  for (const sub of subs) {
    const entry: Record<string, unknown> = { url: sub.url };
    try {
      const res = await fetchUpstream(sub.url, { timeoutMs: 8000, headers: { Accept: 'application/json' } });
      entry.httpStatus = res.status;
      entry.ok = res.ok;
      const text = await res.text();
      entry.bytes = text.length;
      entry.head = text.slice(0, 120);
      try {
        const parsed = parseSubscriptionPayload(parseSubscriptionJson(text));
        entry.sources = parsed.sources.length;
        entry.liveSources = parsed.liveSources.length;
        entry.stats = describeParseStats(parsed.stats);
        entry.firstSource = parsed.sources[0] ?? null;
      } catch (e) {
        entry.parseError = e instanceof Error ? e.message : String(e);
      }
    } catch (e) {
      entry.fetchError = e instanceof Error ? `${e.name}: ${e.message}` : String(e);
    }
    out.result = entry;
  }
  return NextResponse.json(out);
}
