import { useEffect, useState } from "react";
import { getCrewPassport } from "./api";
import type { PassportDoc } from "./types";

/** Six-month passports for the given crew ids (null ids are skipped). Requests are shared through the api cache. */
export function usePassportDocs(refs: (string | null | undefined)[]): Record<string, PassportDoc> {
  const [docs, setDocs] = useState<Record<string, PassportDoc>>({});
  const key = [...new Set(refs.filter((r): r is string => !!r))].sort().join("\n");
  useEffect(() => {
    let live = true;
    for (const id of key.split("\n").filter(Boolean)) {
      getCrewPassport(id)
        .then((d) => { if (live) setDocs((p) => (p[id] ? p : { ...p, [id]: d })); })
        .catch(() => undefined);
    }
    return () => { live = false; };
  }, [key]);
  return docs;
}
