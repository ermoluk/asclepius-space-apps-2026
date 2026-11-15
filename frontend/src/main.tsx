import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
// Self-hosted fonts (works offline in the cabin). Atkinson Hyperlegible is built for low vision:
// crews with SANS lose near acuity, so 0/O, 1/l/I and B/8 must never be confused.
import "@fontsource-variable/atkinson-hyperlegible-next";
import "@fontsource-variable/atkinson-hyperlegible-mono";
import App from "./App";
import "./styles.css";

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
