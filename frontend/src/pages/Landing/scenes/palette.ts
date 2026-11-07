/** Colours the 3D scenes take from the landing page's own CSS tokens, so they follow light and dark. */
export interface Palette {
  bg: string;
  surface2: string;
  ink: string;
  inkOn: string;
  accent: string;
  bright: string;
  deep: string;
  ok: string;
  bad: string;
  gap: string;
}

const VARS: [keyof Palette, string, string][] = [
  ["bg", "--bg", "#ffffff"],
  ["surface2", "--surface-2", "#dbe6ff"],
  ["ink", "--ink", "#0a1b4d"],
  ["inkOn", "--accent-ink", "#ffffff"],
  ["accent", "--accent", "#1d4ed8"],
  ["bright", "--bright", "#2563eb"],
  ["deep", "--deep", "#0a1b4d"],
  ["ok", "--ok", "#1d4ed8"],
  ["bad", "--bad", "#b42318"],
  ["gap", "--gap", "#8a5a00"],
];

export function readPalette(el: Element): Palette {
  const cs = getComputedStyle(el);
  const out = {} as Palette;
  for (const [key, name, fallback] of VARS) out[key] = cs.getPropertyValue(name).trim() || fallback;
  return out;
}
