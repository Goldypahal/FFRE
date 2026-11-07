import { lazy, Suspense, useEffect, useRef, useState } from "react";
import type { CSSProperties } from "react";
import { readPalette } from "./palette";
import type { Palette } from "./palette";

/** three.js and react-three-fiber load only when a stage first nears the viewport. */
const Scenes = lazy(() => import("./Scenes"));

export type SceneKind = "orbit" | "case" | "pipeline" | "chain" | "field";

function hasWebGL(): boolean {
  try {
    if (typeof window === "undefined" || typeof window.WebGLRenderingContext === "undefined") return false;
    const c = document.createElement("canvas");
    return !!(c.getContext("webgl2") || c.getContext("webgl"));
  } catch {
    return false;
  }
}

interface StageProps {
  kind: SceneKind;
  className?: string;
  height?: number | string;
  /** Chain scene: which entries no longer match the seal. */
  broken?: boolean[];
}

/**
 * A decorative 3D scene. It renders nothing without WebGL, draws one still frame under
 * reduced motion, and only animates while it is on screen.
 */
export function Stage({ kind, className = "", height, broken }: StageProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [ok] = useState(hasWebGL);
  const [mounted, setMounted] = useState(false);
  const [visible, setVisible] = useState(false);
  const [palette, setPalette] = useState<Palette | null>(null);
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el || !ok) return;
    const root = el.closest(".ffl") ?? el;
    const refresh = () => setPalette(readPalette(root));
    refresh();
    const mq = window.matchMedia?.("(prefers-color-scheme: dark)");
    mq?.addEventListener?.("change", refresh);
    const rm = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    const setRm = () => setReduced(!!rm?.matches);
    setRm();
    rm?.addEventListener?.("change", setRm);

    let io: IntersectionObserver | undefined;
    if ("IntersectionObserver" in window) {
      io = new IntersectionObserver(
        (entries) => {
          for (const e of entries) {
            setVisible(e.isIntersecting);
            if (e.isIntersecting) setMounted(true);
          }
        },
        { rootMargin: "240px 0px 240px 0px" },
      );
      io.observe(el);
    } else {
      setVisible(true);
      setMounted(true);
    }
    return () => {
      io?.disconnect();
      mq?.removeEventListener?.("change", refresh);
      rm?.removeEventListener?.("change", setRm);
    };
  }, [ok]);

  const style: CSSProperties | undefined = height === undefined ? undefined : { height };
  if (!ok) return null;
  return (
    <div ref={ref} className={`s3 s3-${kind} ${className}`.trim()} style={style} aria-hidden="true" data-scene={kind}>
      {mounted && palette ? (
        <Suspense fallback={null}>
          <Scenes kind={kind} palette={palette} active={visible} reduced={reduced} broken={broken} />
        </Suspense>
      ) : null}
    </div>
  );
}
