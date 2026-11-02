/**
 * Demo tools: storm replay, the resident phones, and the link between them. On only
 * when the build sets NEXT_PUBLIC_DEMO_MODE=true, so a real dispatcher never sees them.
 */
export const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === "true";
