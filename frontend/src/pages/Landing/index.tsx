import { useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties, FormEvent } from "react";
import { Link } from "react-router-dom";
import "@fontsource-variable/bricolage-grotesque/opsz.css";
import "@fontsource-variable/instrument-sans/wght.css";
import "./landing.css";
import { useFfl } from "./useFfl";
import { CONTACT_EMAIL, DEMO_ENDPOINT } from "./config";
import {
  CHAIN_STEPS,
  INITIAL_EVIDENCE,
  ORIGINAL_ENTRY,
  VERDICT_LABEL,
  evaluate,
  replayCheck,
} from "./verifier";
import type { Evidence, Verdict } from "./verifier";
import dfdContext from "../../assets/landing/dfd-context.png";
import dfdDetail from "../../assets/landing/dfd-detail.png";
import architecture from "../../assets/landing/architecture.png";
import pipeline from "../../assets/landing/pipeline.png";

const iv = (i: number): CSSProperties => ({ ["--i" as string]: i }) as CSSProperties;

/* ------------------------------------------------------------------ header */

function Header() {
  const [stuck, setStuck] = useState(false);
  useEffect(() => {
    const onScroll = () => setStuck(window.scrollY > 40);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  return (
    <header className={`top${stuck ? " stuck" : ""}`} id="topbar">
      <a className="mark" href="#top" aria-label="FFIRE, back to top">
        <svg viewBox="0 0 28 28" width="28" height="28" aria-hidden="true">
          <rect width="28" height="28" rx="8" fill="currentColor" />
          <path d="M8 20V8h11M8 14h8" stroke="var(--bg)" strokeWidth="3" fill="none" strokeLinecap="square" />
        </svg>
        <span>FFIRE</span>
      </a>
      <nav aria-label="Main">
        <a className="nl" href="#commands">Product</a>
        <a className="nl" href="#flow">How it works</a>
        <a className="nl" href="#replay">Replay</a>
        <a className="nl" href="#trust">Compliance</a>
        <a className="nl" href="#scope">FAQ</a>
        <Link className="signin" to="/auth">Sign in</Link>
        <a className="navbtn" href="#demo">Request a demo</a>
      </nav>
    </header>
  );
}

/* ---------------------------------------------------------------- verifier */

function Verifier() {
  const [ev, setEv] = useState<Evidence>(INITIAL_EVIDENCE);
  const result = useMemo(() => evaluate(ev), [ev]);
  const verdictOf = (id: string): Verdict => result.claims.find((c) => c.id === id)!.verdict;
  const set = (k: keyof Evidence) => (e: { target: { value: string } }) => setEv((p) => ({ ...p, [k]: e.target.value }));

  const [pulse, setPulse] = useState(false);
  const [live, setLive] = useState("");
  const sig = result.claims.map((c) => c.verdict).join("|");
  const first = useRef(true);
  useEffect(() => {
    if (first.current) {
      first.current = false;
      return;
    }
    setLive(`${result.counts.ok} of ${result.total} claims grounded. ${result.summary}.`);
    setPulse(true);
    const t = setTimeout(() => setPulse(false), 520);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sig]);

  const mark = (id: string, text: string) => (
    <mark data-claim={id} data-v={verdictOf(id)}>{text}</mark>
  );

  return (
    <>
      <div className="vf" data-ui id="vf">
        <div className="vf-head">
          <b>Evaluate a narrative</b>
          <span className="vf-ep">POST /api/v1/verifier/evaluate</span>
        </div>
        <p className="vf-n" id="vf-n">
          Transaction amount of {mark("amount", "9,500")} was transferred via {mark("channel", "WIRE")} by account{" "}
          {mark("account", "acc_corp_88")}. The account made {mark("velocity", "11 transfers")} in the previous 24
          hours. The beneficiary is {mark("beneficiary", "a shell company")}.
        </p>
        <div className="vf-ev">
          <p className="vf-lab">Evidence you can change</p>
          <div className="vf-fields">
            <div className="fld">
              <label htmlFor="ev-amount">Amount</label>
              <input id="ev-amount" type="number" inputMode="decimal" step="any" value={ev.amount} onChange={set("amount")} />
            </div>
            <div className="fld">
              <label htmlFor="ev-channel">Channel</label>
              <select id="ev-channel" value={ev.channel} onChange={set("channel")}>
                <option>WIRE</option>
                <option>ACH</option>
                <option>CASH</option>
                <option>CARD</option>
              </select>
            </div>
            <div className="fld">
              <label htmlFor="ev-account">Account</label>
              <input id="ev-account" type="text" value={ev.account} onChange={set("account")} autoComplete="off" spellCheck={false} />
            </div>
            <div className="fld">
              <label htmlFor="ev-velocity">Transfers, 24 h</label>
              <input id="ev-velocity" type="number" inputMode="numeric" step="1" min="0" value={ev.velocity} onChange={set("velocity")} />
            </div>
          </div>
        </div>
        <ul className="vf-rows" aria-label="Verdicts">
          {result.claims.map((c) => (
            <li className="row" key={c.id} data-claim={c.id} data-v={c.verdict}>
              <span className="c">{c.label}</span>
              <span className="e">
                {c.key ? (
                  <>
                    {c.key} <b>{c.shown}</b>
                  </>
                ) : (
                  "no matching evidence"
                )}
              </span>
              <span className="vt">{VERDICT_LABEL[c.verdict]}</span>
            </li>
          ))}
        </ul>
        <div className="vf-foot">
          <span>
            <b id="vf-score">{result.counts.ok} of {result.total}</b> claims grounded
          </span>
          <span className="vf-hash">
            sha256 <code id="vf-hash" title={result.digest}>{result.digest.slice(0, 10)}…{result.digest.slice(-6)}</code>
          </span>
        </div>
        <p className="sr" id="vf-live" aria-live="polite">{live}</p>
      </div>
      <div className={`seal${pulse ? " pulse" : ""}`} id="seal" data-v={result.overall} aria-hidden="true">
        <b id="seal-n">{result.counts.ok}/{result.total}</b>
        <span id="seal-s">{result.summary}</span>
      </div>
    </>
  );
}

/* ----------------------------------------------------------------- commands */

const COMMANDS = [
  { k: "E", n: "Evaluate a narrative", d: "Send any narrative with its evidence. Each claim gets a verdict and a grounding score." },
  { k: "S", n: "Start an investigation", d: "Plan the case, pull records in parallel and draft the narrative from what was found." },
  { k: "T", n: "Read the reasoning trace", d: "Open the full investigation with every step the engine took, tenant-scoped." },
  { k: "X", n: "Export a sealed bundle", d: "Package the case as a hash-chained replay bundle an examiner can check offline." },
  { k: "V", n: "Verify a bundle", d: "Recompute every hash in the chain and report the first entry that does not match." },
  { k: "H", n: "Apply a legal hold", d: "Stop deletion of a case while a regulatory inquiry or hold is active." },
  { k: "D", n: "Export a SAR dossier", d: "Prepare the audit dossier for human review. A person authorizes any filing." },
  { k: "L", n: "List the evidence vault", d: "Browse the stored evidence behind each case, with the digest of every item." },
];

function Commands() {
  const [q, setQ] = useState("");
  const [sel, setSel] = useState("E");
  const t = q.trim().toLowerCase();
  const visible = COMMANDS.filter((c) => !t || c.n.toLowerCase().includes(t) || c.d.toLowerCase().includes(t));
  const active = visible.some((c) => c.k === sel) ? sel : visible[0]?.k;

  const onKey = (e: React.KeyboardEvent) => {
    const i = visible.findIndex((c) => c.k === active);
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSel(visible[Math.min(visible.length - 1, i + 1)]?.k ?? sel);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSel(visible[Math.max(0, i - 1)]?.k ?? sel);
    } else if ((e.target as HTMLElement).tagName !== "INPUT" && e.key.length === 1) {
      const m = visible.find((c) => c.k === e.key.toUpperCase());
      if (m) setSel(m.k);
    }
  };

  return (
    <section className="cmds" id="commands">
      <div className="cmds-in">
        <div className="cmd-box" data-ui id="cmd" onKeyDown={onKey}>
          <label className="sr" htmlFor="cmd-q">Find a command</label>
          <input id="cmd-q" className="cmd-q rv" style={iv(0)} type="text" placeholder="Find a command" autoComplete="off" spellCheck={false} value={q} onChange={(e) => setQ(e.target.value)} />
          <ul className="cmd-list rv" style={iv(1)} id="cmd-list" role="listbox" aria-label="Commands">
            {visible.map((c) => (
              <li
                key={c.k}
                className={`cmd${c.k === active ? " on" : ""}`}
                role="option"
                aria-selected={c.k === active}
                data-k={c.k}
                onMouseEnter={() => setSel(c.k)}
                onClick={() => setSel(c.k)}
              >
                <div className="cmd-r">
                  <span className="cmd-n">{c.n}</span>
                  <kbd>{c.k}</kbd>
                </div>
                <p className="cmd-d">{c.d}</p>
              </li>
            ))}
          </ul>
          {visible.length === 0 && <p className="cmd-none">No command matches. Try &ldquo;export&rdquo; or &ldquo;verify&rdquo;.</p>}
        </div>
      </div>
    </section>
  );
}

/* --------------------------------------------------------------------- flow */

function Flow() {
  return (
    <section className="flow" id="flow">
      <h2 className="flow-h">How a case moves</h2>
      <div className="fields">
        <article className="fld-c f1 rv" style={iv(0)}>
          <div className="ticket" data-ui>
            <div className="tk-top"><b>Case FF-2041</b><span className="tk-st">Planned</span></div>
            <p className="tk-l">Customer</p><p className="tk-v">acc_corp_88</p>
            <p className="tk-l">Tasks</p>
            <ul className="tk-ul"><li>Customer</li><li>Transaction</li><li>Merchant</li><li>Device</li></ul>
          </div>
          <p className="fld-t">First it&rsquo;s planned.</p>
        </article>
        <article className="fld-c f2 rv" style={iv(1)}>
          <div className="ticket" data-ui>
            <div className="tk-top"><b>Case FF-2041</b><span className="tk-st">Retrieved</span></div>
            <p className="tk-l">Transfers</p>
            <ul className="tk-tab"><li><span>1 hour</span><b>2</b></li><li><span>24 hours</span><b>6</b></li><li><span>7 days</span><b>14</b></li></ul>
            <p className="tk-l">Records</p><p className="tk-v">4 sources loaded</p>
          </div>
          <p className="fld-t">Then the records load.</p>
        </article>
        <article className="fld-c f3 rv" style={iv(2)}>
          <div className="ticket" data-ui>
            <div className="tk-top"><b>Case FF-2041</b><span className="tk-st">Reasoned</span></div>
            <p className="tk-l">Rule engine</p><p className="tk-v">Amount sits just under 10,000</p>
            <p className="tk-l">Calibrated model</p><p className="tk-big">0.87 <small>risk score</small></p>
            <p className="tk-l">Case memory</p><p className="tk-v">4 similar cases</p>
          </div>
          <p className="fld-t">Then it reasons.</p>
        </article>
        <article className="fld-c f4 rv" style={iv(3)}>
          <div className="ticket" data-ui>
            <div className="tk-top"><b>Case FF-2041</b><span className="tk-st ok">Sealed</span></div>
            <ul className="tk-v3">
              <li data-v="ok"><i></i>3 verified</li>
              <li data-v="bad"><i></i>1 contradicted</li>
              <li data-v="gap"><i></i>1 ungrounded</li>
            </ul>
            <p className="tk-l">Digest</p><p className="tk-hash">sha256 0bd02f0476…21f030</p>
          </div>
          <p className="fld-t">Last, it&rsquo;s checked and sealed.</p>
        </article>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------- replay */

const REPLAY_EXAMPLES = [
  { v: ORIGINAL_ENTRY, b: "The original entry", s: "The seal matches again." },
  { v: "Wire of 9,400 from acc_corp_88", b: "Nudge the amount", s: "One hundred less. Watch every hash after it." },
  { v: "Cash deposit of 9,500 at branch 14", b: "Swap the channel", s: "A different kind of transaction altogether." },
];

function Replay() {
  const [text, setText] = useState(ORIGINAL_ENTRY);
  const r = useMemo(() => replayCheck(text), [text]);
  const intact = r.firstBroken < 0;
  return (
    <section className="type" id="replay">
      <h2 className="type-h">Change one entry in a sealed case.</h2>
      <div className="type-in" data-ui id="rp">
        <label className="sr" htmlFor="rp-in">Evidence entry</label>
        <input id="rp-in" className="rp-in" type="text" value={text} onChange={(e) => setText(e.target.value)} autoComplete="off" spellCheck={false} />
        <div className="rp-grid">
          <div className="rp-out rv" style={iv(0)}>
            <p className="rp-status" id="rp-status" data-v={intact ? "ok" : "bad"} aria-live="polite">
              {intact
                ? "Chain intact. Every hash matches the seal."
                : `Chain breaks at “${CHAIN_STEPS[r.firstBroken].toLowerCase()}”. Every hash after it stops matching.`}
            </p>
            <ol className="rp-chain" id="rp-chain">
              {CHAIN_STEPS.map((name, i) => (
                <li key={name} className={r.broken[i] ? "bad" : undefined}>
                  <span className="rp-n">{name}</span>
                  <code>{r.current[i].slice(0, 10)}…{r.current[i].slice(-4)}</code>
                </li>
              ))}
            </ol>
          </div>
          <div className="rp-side rv" style={iv(1)}>
            <p className="rp-ex-l">Or try</p>
            <div className="rp-ex">
              {REPLAY_EXAMPLES.map((x) => (
                <button type="button" key={x.b} onClick={() => setText(x.v)}>
                  <b>{x.b}</b>
                  <span>{x.s}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* -------------------------------------------------------------------- trust */

function CountUp({ to }: { to: number }) {
  const ref = useRef<HTMLElement>(null);
  const [n, setN] = useState(to);
  useEffect(() => {
    const el = ref.current;
    const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (!el || reduce || !("IntersectionObserver" in window)) return;
    setN(0);
    let raf = 0;
    const io = new IntersectionObserver(
      (es) => {
        if (!es[0].isIntersecting) return;
        io.disconnect();
        let t0: number | null = null;
        const step = (t: number) => {
          if (t0 === null) t0 = t;
          const k = Math.min(1, (t - t0) / 1100);
          setN(Math.round(to * (1 - Math.pow(1 - k, 3))));
          if (k < 1) raf = requestAnimationFrame(step);
        };
        raf = requestAnimationFrame(step);
      },
      { threshold: 0.4 },
    );
    io.observe(el);
    return () => {
      io.disconnect();
      cancelAnimationFrame(raf);
    };
  }, [to]);
  return <dt ref={ref}>{n}</dt>;
}

function Trust() {
  return (
    <section className="spec" id="trust">
      <h2 className="spec-h rv" style={iv(0)}>Built to be audited</h2>
      <div className="bento">
        <figure className="bt b-pipe rv" style={iv(0)}>
          <img src={pipeline} width={1316} height={1704} alt="Investigation pipeline from planner to report" loading="lazy" />
          <figcaption>The investigation pipeline, from planner to report.</figcaption>
        </figure>
        <div className="bt b-stats rv" style={iv(1)}>
          <dl>
            <div><CountUp to={5} /><dd>years of BSA retention, with legal hold</dd></div>
            <div><CountUp to={3} /><dd>verdicts on every claim</dd></div>
            <div><CountUp to={1} /><dd>hash chain per case, replayable offline</dd></div>
            <div><CountUp to={0} /><dd>filings made without a person&rsquo;s approval</dd></div>
          </dl>
        </div>
        <figure className="bt b-dfd rv" style={iv(2)}>
          <img src={dfdDetail} width={1310} height={765} alt="Data flow diagram with six processes and three data stores" loading="lazy" />
          <figcaption>How data moves through six processes and three stores.</figcaption>
        </figure>
        <figure className="bt b-arch rv" style={iv(3)}>
          <img src={architecture} width={1218} height={967} alt="Layered system architecture" loading="lazy" />
          <figcaption>The layered system architecture.</figcaption>
        </figure>
      </div>
    </section>
  );
}

/* ---------------------------------------------------------------------- faq */

const FAQ: { q: string; a: React.ReactNode }[] = [
  { q: "Why does a bank need an independent verifier?", a: "FFIRE is built on the position that banks must validate and reproduce automated conclusions themselves, under model risk guidance (SR 11-7, SR 26-2) and the EU AI Act. A vendor’s self-reported confidence score is not that validation." },
  { q: "Does it block payments?", a: "No. FFIRE is an advisory engine that works after the transaction. Real-time blocking inside a payment switch is out of scope." },
  { q: "Does it file reports with FinCEN?", a: "No. It prepares the SAR audit dossier for human review. A compliance officer has to authorize any electronic filing." },
  { q: "Whose narratives can it check?", a: "Any. The verifier takes a narrative and its evidence, whether the narrative came from Hawk, Oracle Investigation Hub, an in-house model or a custom agent." },
  { q: "Can a case be deleted?", a: "Not while a legal hold or regulatory inquiry is active. An approved deletion is a soft delete with an immutable tombstone in the audit log, and BSA retention runs five years." },
  { q: "How are model files trusted?", a: <>Serialized model artifacts are checked against the SHA-256 digests in <code>registry_manifest.json</code> before they are loaded.</> },
  { q: "Who can create an admin account?", a: <>Only someone holding the <code>ADMIN_INVITE_TOKEN</code>. Public registration is limited to viewer and investigator roles.</> },
  { q: "How do we get started?", a: "Request a demo. We walk through sample investigations with you, then set up FFIRE in your own environment. It ships with Docker Compose and Kubernetes manifests." },
  { q: "What does it run on?", a: "Python 3.11 to 3.13 with FastAPI and LangGraph, PostgreSQL 15, ChromaDB and Redis 7, and a React 19 and TypeScript frontend. Kubernetes manifests are included." },
];

function Faq() {
  return (
    <section className="faq" id="scope">
      <div className="faq-in">
        <h2 className="faq-h">Scope, plainly</h2>
        <div className="tiles">
          {FAQ.map((f, i) => (
            <details name="scope" className="tile rv" style={iv(i * 0.4)} key={f.q} open={i === 0}>
              <summary>
                {f.q}
                <span className="pm" aria-hidden="true"></span>
              </summary>
              <div className="ans"><p>{f.a}</p></div>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}

/* --------------------------------------------------------------- demo form */

function DemoForm() {
  const [note, setNote] = useState("We only use your details to reply to this request.");
  const [bad, setBad] = useState<Record<string, boolean>>({});
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const fd = new FormData(form);
    const data = {
      name: String(fd.get("name") ?? "").trim(),
      email: String(fd.get("email") ?? "").trim(),
      org: String(fd.get("org") ?? "").trim(),
      message: String(fd.get("message") ?? "").trim(),
    };
    const invalid = {
      name: !data.name,
      email: !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(data.email),
    };
    setBad(invalid);
    if (invalid.name || invalid.email) {
      setNote("Add your name and a work email so we can reply.");
      return;
    }
    const first = data.name.split(" ")[0];
    if (DEMO_ENDPOINT) {
      setBusy(true);
      setNote("Sending…");
      try {
        const res = await fetch(DEMO_ENDPOINT, {
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error("bad status");
        setNote(`Thank you, ${first}. We will reply to ${data.email}.`);
        form.reset();
      } catch {
        setNote("That did not send. Please try again, or write to us directly.");
      } finally {
        setBusy(false);
      }
    } else if (CONTACT_EMAIL) {
      const body = `Name: ${data.name}\nEmail: ${data.email}\nOrganisation: ${data.org}\n\n${data.message}`;
      window.location.href = `mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent("FFIRE demo request")}&body=${encodeURIComponent(body)}`;
      setNote(`Opening your email app. If nothing opens, write to ${CONTACT_EMAIL} directly.`);
    } else {
      setNote("Demo requests are not set up on this site yet. Ask the site owner to set VITE_DEMO_ENDPOINT or VITE_CONTACT_EMAIL.");
    }
  };

  const clear = (k: string) => () => setBad((b) => ({ ...b, [k]: false }));

  return (
    <form className="dlg rv" style={iv(1)} data-ui id="demo-form" noValidate aria-labelledby="dlg-t" onSubmit={onSubmit}>
      <p className="dlg-t" id="dlg-t">Request a demo</p>
      <div className="fl"><label htmlFor="d-name">Your name</label><input id="d-name" name="name" type="text" autoComplete="name" aria-invalid={bad.name ? "true" : "false"} onChange={clear("name")} /></div>
      <div className="fl"><label htmlFor="d-email">Work email</label><input id="d-email" name="email" type="email" autoComplete="email" aria-invalid={bad.email ? "true" : "false"} onChange={clear("email")} /></div>
      <div className="fl"><label htmlFor="d-org">Organisation</label><input id="d-org" name="org" type="text" autoComplete="organization" /></div>
      <div className="fl"><label htmlFor="d-msg">What would you like to check?</label><textarea id="d-msg" name="message" rows={3} placeholder="For example: SAR narratives written by our case tool" /></div>
      <button type="submit" className="dlg-b" disabled={busy}>Request a demo</button>
      <p className="dlg-n" id="demo-note" aria-live="polite">{note}</p>
    </form>
  );
}

/* ------------------------------------------------------------------- page */

export function Landing() {
  const ref = useFfl<HTMLDivElement>();
  return (
    <div className="ffl" ref={ref}>
      <a className="skip" href="#main">Skip to content</a>
      <Header />
      <main id="main">
        <section className="hero" id="top">
          <div className="hero-l">
            <div className="hero-copy">
              <h1 className="h1">
                <span className="ln"><span>Check every claim.</span></span>
                <span className="ln"><span>Replay every case.</span></span>
              </h1>
              <p className="hero-p">FFIRE checks every claim in an AI-written fraud investigation against the evidence, then seals the case so an examiner can replay it offline.</p>
              <div className="hero-cta">
                <a className="btn" href="#demo">Request a demo</a>
                <a className="btn-t" href="#vf">Try the verifier</a>
              </div>
            </div>
          </div>
          <div className="hero-r">
            <Verifier />
          </div>
        </section>

        <section className="intro">
          <div className="intro-in">
            <div className="intro-t">
              <h2 className="sr">Why a bank needs its own check</h2>
              <p className="lead rv" style={iv(0)}>A bank cannot take a vendor&rsquo;s word for its own score.</p>
              <p className="rv" style={iv(1)}>Fraud tools now write the investigation narrative themselves. Examiners still ask the bank to show that the narrative is true, and that the result can be reproduced.</p>
              <p className="rv" style={iv(2)}>FFIRE sits outside the tool that wrote the case. Every claim comes back <span className="vm ok">verified</span>, <span className="vm bad">contradicted</span> or <span className="vm gap">ungrounded</span>, and the whole case is sealed so it can be replayed offline.</p>
              <p className="rv" style={iv(3)}><a className="lnk" href="#flow">See how a case is checked</a></p>
            </div>
            <figure className="intro-f rv" style={iv(1)}>
              <img src={dfdContext} width={1218} height={707} alt="Context diagram: fraud analyst, core banking system, knowledge base and compliance around FFIRE" loading="lazy" />
              <figcaption>FFIRE sits between the analyst, the bank&rsquo;s systems and compliance.</figcaption>
            </figure>
          </div>
        </section>

        <Commands />
        <Flow />
        <Replay />
        <Trust />
        <Faq />

        <section className="cta" id="demo">
          <div className="cta-l rv" style={iv(0)}>
            <h2 className="cta-h"><span>See it on</span><span>your cases.</span></h2>
            <p className="cta-p">Tell us a little about your team. We reply with a walkthrough on sample investigations, so nothing real leaves your bank.</p>
          </div>
          <DemoForm />
        </section>
      </main>

      <footer className="foot">
        <div className="ft ft-s rv" style={iv(0)}><p>Every claim, checked. Every case, replayable.</p><small>&copy; 2026 FFIRE. All rights reserved.</small></div>
        <nav className="ft ft-n rv" style={iv(1)} aria-label="Footer">
          <a href="#commands">Product</a>
          <a href="#flow">How it works</a>
          <a href="#trust">Compliance</a>
          <a href="#scope">FAQ</a>
          <Link to="/auth">Sign in</Link>
        </nav>
        <div className="ft ft-v rv" style={iv(2)}><p>Advisory only</p><b>A person authorizes every filing.</b></div>
        {CONTACT_EMAIL ? (
          <a className="ft ft-e rv" style={iv(3)} href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>
        ) : (
          <a className="ft ft-e rv" style={iv(3)} href="#demo">Write to us</a>
        )}
        <div className="ft ft-w rv" style={iv(4)}>
          <svg viewBox="0 0 520 130" role="img" aria-label="FFIRE">
            <text x="260" y="112" textAnchor="middle" fill="currentColor" fontFamily="'Bricolage Grotesque Variable', 'Bricolage Grotesque', Arial, sans-serif" fontWeight="800" fontSize="150" letterSpacing="-6">FFIRE</text>
          </svg>
        </div>
        <a className="ft ft-a rv" style={iv(5)} href="#demo">
          <span>Request a demo</span>
          <svg viewBox="0 0 40 40" width="40" height="40" aria-hidden="true"><path d="M8 32L32 8M14 8h18v18" fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="square" /></svg>
        </a>
      </footer>
    </div>
  );
}

export default Landing;
