import type { Assessment, BiodoseModel, DatasetsSummary, DayRecord, ImportResult, KnowledgeCounts, Passport, PassportDoc, QuizAnswers, Scenario, ScenarioInfo } from "./types";

export class ApiError extends Error {
  status?: number;
  constructor(message: string, status?: number) { super(message); this.status = status; }
}

function describeDetail(detail: unknown): string {
  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        const loc = Array.isArray(d?.loc) ? d.loc.filter((p: unknown) => p !== "body").join(".") : "";
        return loc ? `${loc}: ${d?.msg ?? JSON.stringify(d)}` : String(d?.msg ?? JSON.stringify(d));
      })
      .join("; ");
  }
  return typeof detail === "string" ? detail : JSON.stringify(detail);
}

async function request<T>(url: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  let res: Response;
  try {
    res = await fetch(url, {
      method: body === undefined ? "GET" : "POST",
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    });
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") throw e;
    throw new ApiError("Cannot reach the assessment server. Is the backend running on port 8000?");
  }
  if (!res.ok) {
    let msg = `Server error ${res.status}`;
    try {
      const j = await res.json();
      if (j?.detail !== undefined) msg = `${res.status === 422 ? "Invalid data: " : ""}${describeDetail(j.detail)}`;
    } catch { /* keep default message */ }
    throw new ApiError(msg, res.status);
  }
  return res.json() as Promise<T>;
}

export const getScenarios = () => request<ScenarioInfo[]>("/api/scenarios");
export const getScenario = (id: string) => request<Scenario>(`/api/scenarios/${encodeURIComponent(id)}`);
export const getKnowledgeCounts = async () => (await request<{ counts: KnowledgeCounts }>("/api/knowledge")).counts;
/** The server assesses at most 60 days: send the latest 60 up to the selected day (enough for every rule). */
export const ASSESS_MAX_DAYS = 60;
export const assess = (passport: Passport, history: DayRecord[], signal?: AbortSignal) =>
  request<Assessment>("/api/assess", { passport, history: history.slice(-ASSESS_MAX_DAYS) }, signal);
export const derivePassport = (answers: QuizAnswers) => request<Passport>("/api/passport/derive", { answers });
/** Six-month passports do not change while the app runs: one request per crew id, retried after a failure. */
const passportCache = new Map<string, Promise<PassportDoc>>();
/** Six-month passports imported from a file ("My crew"): kept on the member in this browser, never on the server. */
const LOCAL = "local:";
const localDocs = new Map<string, PassportDoc>();
export const isLocalRef = (ref: string | null | undefined): ref is string => !!ref && ref.startsWith(LOCAL);
export const localRef = (id: string) => `${LOCAL}${id}@${Date.now().toString(36)}`;
export function setLocalPassport(ref: string, doc: PassportDoc | null): void {
  if (doc) localDocs.set(ref, doc); else localDocs.delete(ref);
}
export function getCrewPassport(id: string): Promise<PassportDoc> {
  if (isLocalRef(id)) {
    const doc = localDocs.get(id);
    return doc ? Promise.resolve(doc) : Promise.reject(new ApiError("The imported six-month data is not in this browser any more. Import the file again."));
  }
  let p = passportCache.get(id);
  if (!p) {
    p = request<PassportDoc>(`/api/crew/${encodeURIComponent(id)}/passport`);
    passportCache.set(id, p);
    p.catch(() => passportCache.delete(id));
  }
  return p;
}
export const parseImport = (body: { filename: string; content: string; launch_date?: string; name?: string }) =>
  request<ImportResult>("/api/import/parse", body);
export const getDatasets = () => request<DatasetsSummary>("/api/datasets");
export const getBiodosimetry = () => request<BiodoseModel>("/api/biodosimetry");
