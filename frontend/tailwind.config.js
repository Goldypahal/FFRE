/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        "surface-bright": "#2f3a4c",
        "background": "#081425",
        "surface-dim": "#081425",
        "primary": "#bec6e0",
        "on-tertiary-container": "#728299",
        "on-secondary": "#4d2600",
        "surface-tint": "#bec6e0",
        "on-primary-container": "#798098",
        "on-secondary-container": "#432100",
        "error-container": "#93000a",
        "surface-container-low": "#111c2d",
        "tertiary-container": "#06182b",
        "on-primary-fixed-variant": "#3f465c",
        "on-error": "#690005",
        "secondary-container": "#d97707",
        "surface-container-high": "#1f2a3c",
        "on-surface": "#d8e3fb",
        "on-primary-fixed": "#131b2e",
        "inverse-on-surface": "#263143",
        "surface-variant": "#2a3548",
        "surface-container-highest": "#2a3548",
        "graph-edge": "#475569",
        "tertiary-fixed-dim": "#b7c8e1",
        "on-secondary-fixed": "#2f1500",
        "inverse-primary": "#565e74",
        "investigation-gold": "#FCD34D",
        "surface": "#081425",
        "risk-low": "#10B981",
        "graph-node-bg": "#334155",
        "inverse-surface": "#d8e3fb",
        "on-tertiary": "#213145",
        "tertiary": "#b7c8e1",
        "secondary": "#ffb77d",
        "tertiary-fixed": "#d3e4fe",
        "surface-container": "#152031",
        "secondary-fixed-dim": "#ffb77d",
        "outline-variant": "#45464d",
        "on-primary": "#283044",
        "on-tertiary-fixed": "#0b1c30",
        "secondary-fixed": "#ffdcc3",
        "on-secondary-fixed-variant": "#6e3900",
        "error": "#ffb4ab",
        "outline": "#909097",
        "on-error-container": "#ffdad6",
        "on-tertiary-fixed-variant": "#38485d",
        "primary-fixed": "#dae2fd",
        "on-background": "#d8e3fb",
        "primary-fixed-dim": "#bec6e0",
        "risk-medium": "#F59E0B",
        "on-surface-variant": "#c6c6cd",
        "risk-high": "#EF4444",
        "surface-container-lowest": "#040e1f",
        "primary-container": "#0f172a"
      },
      borderRadius: {
        "DEFAULT": "0.125rem",
        "lg": "0.25rem",
        "xl": "0.5rem",
        "full": "0.75rem"
      },
      spacing: {
        "stack-lg": "32px",
        "gutter": "24px",
        "stack-md": "16px",
        "container-max": "1440px",
        "unit": "4px",
        "stack-sm": "8px",
        "margin": "32px"
      },
      fontFamily: {
        "body-md": ["Inter"],
        "label-md": ["JetBrains Mono"],
        "label-sm": ["JetBrains Mono"],
        "body-sm": ["Inter"],
        "headline-md": ["Hanken Grotesk"],
        "headline-lg": ["Hanken Grotesk"],
        "display-lg": ["Hanken Grotesk"],
        "body-lg": ["Inter"]
      },
      fontSize: {
        "label-sm": ["12px", {lineHeight: "16px", fontWeight: "500"}],
        "headline-lg": ["32px", {lineHeight: "40px", fontWeight: "600"}],
        "label-md": ["14px", {lineHeight: "20px", letterSpacing: "0.02em", fontWeight: "500"}],
        "body-md": ["16px", {lineHeight: "24px", fontWeight: "400"}],
        "headline-md": ["24px", {lineHeight: "32px", fontWeight: "600"}],
        "body-sm": ["14px", {lineHeight: "20px", fontWeight: "400"}],
        "display-lg": ["48px", {lineHeight: "56px", letterSpacing: "-0.02em", fontWeight: "700"}],
        "headline-lg-mobile": ["28px", {lineHeight: "36px", fontWeight: "600"}],
        "body-lg": ["18px", {lineHeight: "28px", fontWeight: "400"}]
      }
    }
  },
  plugins: []
}