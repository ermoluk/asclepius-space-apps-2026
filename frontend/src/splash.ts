// Exit of the loading splash. Its markup, intro animation and failsafe live in index.html so they play
// before this bundle arrives; the app calls dismissSplash() once its first data is on screen.
// The exit is a plain fade: the whole splash dissolves and the console appears underneath.

/** The intro choreography in index.html ends by this point (ms after it started). */
const INTRO_MS = 3000;
const FADE_MS = 700;

/** One star of the splash sky: position in % of the sky box, size px, base opacity, twinkle delay/period s. */
export type SplashStar = { x: number; y: number; z: number; o: number; d: number; t: number; big: boolean };

declare global {
  interface Window {
    __splash?: { t0: number; skipped: boolean; stars?: SplashStar[] };
    __dismissSplash?: () => void;
  }
}

let started = false;

/** Ask the splash to leave: right away if the viewer skipped it, otherwise once the intro has played. Idempotent. */
export function dismissSplash(): void {
  if (started) return;
  const el = document.getElementById("splash");
  if (!el) { document.documentElement.classList.remove("splash-active"); return; }
  started = true;
  const st = window.__splash;
  const wait = !st || st.skipped ? 0 : Math.max(0, st.t0 + INTRO_MS - performance.now());
  let timer = 0;
  const go = () => { window.clearTimeout(timer); window.removeEventListener("splash:skip", go); leave(el); };
  timer = window.setTimeout(go, wait);
  window.addEventListener("splash:skip", go);
}
window.__dismissSplash = dismissSplash;

function leave(el: HTMLElement): void {
  el.classList.add("leaving");
  el.setAttribute("aria-hidden", "true");
  document.documentElement.classList.remove("splash-active");
  const remove = () => el.remove();
  const duration = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 200 : FADE_MS;
  el.animate([{ opacity: 1 }, { opacity: 0 }], { duration, easing: "ease-in-out", fill: "forwards" }).finished.then(remove, remove);
  // animations stall in a background tab; never leave the overlay behind
  window.setTimeout(remove, duration + 800);
}
