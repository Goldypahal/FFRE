import { describe, expect, it } from "vitest";
import { sha256 } from "../../../lib/sha256";
import { INITIAL_EVIDENCE, ORIGINAL_ENTRY, evaluate, replayCheck } from "../verifier";

describe("sha256", () => {
  it("matches the known test vectors", () => {
    expect(sha256("")).toBe("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
    expect(sha256("abc")).toBe("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
  });
});

describe("evaluate", () => {
  it("starts with 3 verified, 1 contradicted, 1 ungrounded", () => {
    const r = evaluate(INITIAL_EVIDENCE);
    expect(r.counts).toEqual({ ok: 3, bad: 1, gap: 1 });
    expect(r.overall).toBe("bad");
  });

  it("flips the velocity claim when the evidence agrees", () => {
    const r = evaluate({ ...INITIAL_EVIDENCE, velocity: "11" });
    expect(r.claims.find((c) => c.id === "velocity")?.verdict).toBe("ok");
    expect(r.counts).toEqual({ ok: 4, bad: 0, gap: 1 });
  });

  it("marks a blank field ungrounded and a wrong one contradicted", () => {
    const r = evaluate({ ...INITIAL_EVIDENCE, amount: "", channel: "CASH" });
    expect(r.claims.find((c) => c.id === "amount")?.verdict).toBe("gap");
    expect(r.claims.find((c) => c.id === "channel")?.verdict).toBe("bad");
  });

  it("changes the digest when the evidence changes", () => {
    const a = evaluate(INITIAL_EVIDENCE).digest;
    const b = evaluate({ ...INITIAL_EVIDENCE, amount: "9400" }).digest;
    expect(a).toMatch(/^[0-9a-f]{64}$/);
    expect(a).not.toBe(b);
  });
});

describe("replayCheck", () => {
  it("is intact for the original entry", () => {
    expect(replayCheck(ORIGINAL_ENTRY).firstBroken).toBe(-1);
  });

  it("breaks at the evidence entry and every entry after it", () => {
    const r = replayCheck("Wire of 9,400 from acc_corp_88");
    expect(r.firstBroken).toBe(1);
    expect(r.broken).toEqual([false, true, true, true]);
  });
});
