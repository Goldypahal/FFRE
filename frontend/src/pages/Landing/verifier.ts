import { sha256 } from "../../lib/sha256";

export type Verdict = "ok" | "bad" | "gap";

export interface Evidence {
  amount: string;
  channel: string;
  account: string;
  velocity: string;
}

export interface ClaimResult {
  id: "amount" | "channel" | "account" | "velocity" | "beneficiary";
  label: string;
  key: string | null;
  shown: string | null;
  verdict: Verdict;
}

export const INITIAL_EVIDENCE: Evidence = { amount: "9500", channel: "WIRE", account: "acc_corp_88", velocity: "6" };

export const VERDICT_LABEL: Record<Verdict, string> = { ok: "Verified", bad: "Contradicted", gap: "Ungrounded" };

const NARRATIVE =
  "Transaction amount of 9,500 was transferred via WIRE by account acc_corp_88. The account made 11 transfers in the previous 24 hours. The beneficiary is a shell company.";

const isBlankOrNaN = (v: string) => v.trim() === "" || Number.isNaN(Number(v));

export function evaluate(ev: Evidence) {
  const amount = ev.amount.trim();
  const account = ev.account.trim();
  const velocity = ev.velocity.trim();
  const claims: ClaimResult[] = [
    {
      id: "amount",
      label: "Amount is 9,500",
      key: "amount",
      shown: isBlankOrNaN(amount) ? "no value" : Number(amount).toLocaleString("en-US"),
      verdict: isBlankOrNaN(amount) ? "gap" : Number(amount) === 9500 ? "ok" : "bad",
    },
    {
      id: "channel",
      label: "Channel is WIRE",
      key: "channel",
      shown: ev.channel || "no value",
      verdict: ev.channel === "" ? "gap" : ev.channel === "WIRE" ? "ok" : "bad",
    },
    {
      id: "account",
      label: "Account is acc_corp_88",
      key: "account_id",
      shown: account || "no value",
      verdict: account === "" ? "gap" : account === "acc_corp_88" ? "ok" : "bad",
    },
    {
      id: "velocity",
      label: "11 transfers in 24 hours",
      key: "velocity_count_24h",
      shown: isBlankOrNaN(velocity) ? "no value" : String(Number(velocity)),
      verdict: isBlankOrNaN(velocity) ? "gap" : Number(velocity) === 11 ? "ok" : "bad",
    },
    { id: "beneficiary", label: "Beneficiary is a shell company", key: null, shown: null, verdict: "gap" },
  ];
  const counts = { ok: 0, bad: 0, gap: 0 };
  claims.forEach((c) => counts[c.verdict]++);
  const digest = sha256(
    JSON.stringify({
      narrative: NARRATIVE,
      evidence: { amount, channel: ev.channel, account_id: account, velocity_count_24h: velocity },
      verdicts: claims.map((c) => `${c.id}:${c.verdict}`),
    }),
  );
  const parts: string[] = [];
  if (counts.bad) parts.push(`${counts.bad} contradicted`);
  if (counts.gap) parts.push(`${counts.gap} ungrounded`);
  return {
    claims,
    counts,
    total: claims.length,
    digest,
    summary: parts.length ? parts.join(", ") : "All claims verified",
    overall: (counts.bad ? "bad" : counts.gap ? "gap" : "ok") as Verdict,
  };
}

export const ORIGINAL_ENTRY = "Wire of 9,500 from acc_corp_88";
export const CHAIN_STEPS = ["Case opened", "Evidence ingested", "Verdicts recorded", "Report sealed"];

/** Hash-chain a case: each entry's hash covers the previous hash and its own text. */
export function buildChain(evidenceText: string): string[] {
  const entries = [
    "Case FF-2041 opened",
    `Evidence ingested: ${evidenceText}`,
    "Verdicts: 3 verified, 1 contradicted, 1 ungrounded",
    "Report sealed",
  ];
  let h = "";
  return entries.map((t) => (h = sha256(`${h}|${t}`)));
}

const SEALED = buildChain(ORIGINAL_ENTRY);

/** Index of the first entry whose hash no longer matches the seal, or -1 when intact. */
export function replayCheck(evidenceText: string) {
  const current = buildChain(evidenceText);
  const broken = current.map((h, i) => h !== SEALED[i]);
  return { current, broken, firstBroken: broken.indexOf(true) };
}
