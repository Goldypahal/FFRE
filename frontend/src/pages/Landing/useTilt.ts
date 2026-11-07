import { useEffect } from "react";
import type { RefObject } from "react";

/** Pointer tilt for `[data-tilt]` cards. Fine pointers only, and off under reduced motion. */
export function useTilt(root: RefObject<HTMLElement | null>) {
  useEffect(() => {
    const el = root.current;
    if (!el || !window.matchMedia) return;
    if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const move = (e: PointerEvent) => {
      const t = (e.target as Element | null)?.closest?.<HTMLElement>("[data-tilt]");
      if (!t) return;
      const r = t.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width - 0.5;
      const y = (e.clientY - r.top) / r.height - 0.5;
      t.style.setProperty("--ry", `${(x * 9).toFixed(2)}deg`);
      t.style.setProperty("--rx", `${(-y * 9).toFixed(2)}deg`);
    };
    const leave = (e: PointerEvent) => {
      const t = (e.target as Element | null)?.closest?.<HTMLElement>("[data-tilt]");
      if (!t) return;
      t.style.removeProperty("--ry");
      t.style.removeProperty("--rx");
    };
    el.addEventListener("pointermove", move);
    el.addEventListener("pointerout", leave);
    return () => {
      el.removeEventListener("pointermove", move);
      el.removeEventListener("pointerout", leave);
    };
  }, [root]);
}
