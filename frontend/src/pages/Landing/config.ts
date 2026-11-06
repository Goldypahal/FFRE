/** Deployment settings. Set these in a .env file (see .env.example). */
export const CONTACT_EMAIL: string = (import.meta.env.VITE_CONTACT_EMAIL as string | undefined) ?? "";
export const DEMO_ENDPOINT: string = (import.meta.env.VITE_DEMO_ENDPOINT as string | undefined) ?? "";
