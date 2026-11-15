import { useMemo, type CSSProperties } from "react";
import type { SplashStar } from "../splash";

/** Random sky in the same style as the splash (used when the page opened without it, e.g. ?nosplash). */
function makeStars(n: number): SplashStar[] {
  return Array.from({ length: n }, () => {
    const big = Math.random() < 0.1;
    return {
      x: Math.random() * 100, y: Math.random() * 100,
      z: big ? 2 + Math.random() * 1.2 : 0.8 + Math.random() * 1.1,
      o: 0.35 + Math.random() * 0.6, d: Math.random() * 0.9, t: 1.6 + Math.random() * 2.4, big,
    };
  });
}

/**
 * Dark-theme sky behind the console. It reuses the splash's stars at the same positions, so when the
 * splash dissolves the stars stay where they were. Fixed, behind all content, decorative only;
 * dimmer than on the splash so dots never compete with figures.
 */
export function Starfield() {
  const stars = useMemo(() => window.__splash?.stars ?? makeStars(140), []);
  return (
    <div className="starfield" aria-hidden="true">
      <div className="starfield-sky">
        {stars.map((s, i) => (
          <i key={i} className={s.big ? "big" : undefined}
            style={{ left: `${s.x}%`, top: `${s.y}%`, "--z": `${s.z}px`, "--o": s.o, "--t": `${s.t}s`, "--d": `${-s.d - s.t}s` } as CSSProperties} />
        ))}
      </div>
    </div>
  );
}
