import { useEffect, useRef, type ReactNode } from "react";
import type { Level } from "../types";
import { lvClass } from "../levels";

export function GlyphDefs() {
  return (
    <svg width="0" height="0" style={{ position: "absolute" }} aria-hidden="true" focusable="false">
      <defs>
        <symbol id="g-green" viewBox="0 0 20 20"><circle cx="10" cy="10" r="9" fill="currentColor" /><path d="M5.8 10.3l2.8 2.8 5.6-6" fill="none" stroke="var(--glyph-ink)" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round" /></symbol>
        <symbol id="g-yellow" viewBox="0 0 20 20"><path d="M10 .8 19.2 10 10 19.2.8 10Z" fill="currentColor" /><circle cx="10" cy="10" r="2.6" fill="var(--glyph-ink)" /></symbol>
        <symbol id="g-orange" viewBox="0 0 20 20"><path d="M10 1.6 19 17.9H1Z" fill="currentColor" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" /><path d="M10 7.4v4.8" stroke="var(--glyph-ink)" strokeWidth="2.3" strokeLinecap="round" /><circle cx="10" cy="15.1" r="1.3" fill="var(--glyph-ink)" /></symbol>
        <symbol id="g-red" viewBox="0 0 20 20"><path d="M6.4 1.3h7.2l5.1 5.1v7.2l-5.1 5.1H6.4l-5.1-5.1V6.4Z" fill="currentColor" /><path d="M10 5.6v8.8M5.6 10h8.8" stroke="var(--glyph-ink)" strokeWidth="2.5" strokeLinecap="round" /></symbol>
      </defs>
    </svg>
  );
}

export function Glyph({ level, className = "" }: { level: Level; className?: string }) {
  return (
    <svg className={`g ${lvClass(level)} ${className}`} viewBox="0 0 20 20" aria-hidden="true">
      <use href={`#g-${level.toLowerCase()}`} />
    </svg>
  );
}

export function NoData({ className = "" }: { className?: string }) {
  return (
    <svg className={`g ${className}`} viewBox="0 0 20 20" role="img" aria-label="Not assessed" style={{ color: "var(--na)" }}>
      <circle cx="10" cy="10" r="8" fill="none" stroke="currentColor" strokeWidth="1.8" strokeDasharray="3 2.5" />
      <path d="M6.5 10h7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export const Chevron = ({ className = "chev", dir = "down" }: { className?: string; dir?: "down" | "right" | "left" }) => (
  <svg className={className} viewBox="0 0 16 16" aria-hidden="true">
    <path d={dir === "down" ? "M3 6l5 5 5-5" : dir === "right" ? "M6 3l5 5-5 5" : "M10 3L5 8l5 5"} />
  </svg>
);

export function Modal({
  title, eyebrow, subtitle, onClose, children, footer, variant = "modal", level, wide = false, headIcon, actions, className = "",
}: {
  title: string; eyebrow?: string; subtitle?: ReactNode; onClose: () => void; children: ReactNode;
  footer?: ReactNode;
  /** "full": a full-screen window (passport, Health dynamics). */
  variant?: "modal" | "drawer" | "full"; level?: Level; wide?: boolean; headIcon?: ReactNode;
  /** Buttons shown in the header, before Close. */
  actions?: ReactNode; className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const closeRef = useRef(onClose);
  closeRef.current = onClose;
  useEffect(() => {
    const prev = document.activeElement as HTMLElement | null;
    document.documentElement.classList.add("lock");
    ref.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") { closeRef.current(); return; }
      if (e.key !== "Tab" || !ref.current) return;
      // Keep focus inside the dialog.
      const items = ref.current.querySelectorAll<HTMLElement>("button:not([disabled]), [href], input:not([disabled]), select, textarea, [tabindex]:not([tabindex='-1'])");
      if (!items.length) return;
      const first = items[0], last = items[items.length - 1];
      if (e.shiftKey && (document.activeElement === first || document.activeElement === ref.current)) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.documentElement.classList.remove("lock");
      document.removeEventListener("keydown", onKey);
      prev?.focus?.();
    };
  }, []);
  const drawer = variant === "drawer";
  return (
    <div className={`overlay ov-${variant}`} onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className={`dlg ${drawer ? "drawer" : variant === "full" ? "modal full" : "modal"} ${wide ? "wide" : ""} ${className}`} role="dialog" aria-modal="true" aria-label={title} tabIndex={-1} ref={ref}>
        <div className={drawer ? "dr-head" : "m-head"}>
          {headIcon ?? (level && <span className={`head-glyph bg-${level.toLowerCase()}`}><Glyph level={level} /></span>)}
          <div>
            {eyebrow && <p className="eyebrow">{eyebrow}</p>}
            <h2>{title}</h2>
            {subtitle && <p className="m-sub">{subtitle}</p>}
          </div>
          {actions && <div className="m-actions">{actions}</div>}
          <button className="icon-btn" type="button" onClick={onClose} aria-label="Close">
            <svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18" /></svg>
          </button>
        </div>
        <div className={drawer ? "dr-body" : "m-body"}>{children}</div>
        {footer && <div className="m-foot">{footer}</div>}
      </div>
    </div>
  );
}
