"""Download raw sources into data/raw/<source>/ (git-ignored). Idempotent: existing files are kept."""
import json
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

from .common import RAW, SPACE_WEATHER

UA = {"User-Agent": "crew-health-console-data-pipeline/1.0"}

NHANES_BASE = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2011/DataFiles/"
# 2011-2012 ("_G") files used for passport exam donors and population norms.
NHANES_FILES = ["DEMO_G", "BMX_G", "BPX_G", "CBC_G", "BIOPRO_G", "GHB_G", "GLU_G", "TCHOL_G", "HDL_G", "VID_G",
                "DXX_G", "AUX_G", "MGX_G", "DPQ_G", "SLQ_G", "MCQ_G", "KIQ_U_G", "SMQ_G", "DIQ_G", "PAQ_G", "HSV_G"]

LIFESNAPS_URL = "https://zenodo.org/api/records/7229547/files/rais_anonymized.zip/content"

DONKI_URLS = ["https://api.nasa.gov/DONKI/SEP?startDate={s}&endDate={e}&api_key=DEMO_KEY",
              "https://ccmc.gsfc.nasa.gov/DONKI-API/get/SEP?startDate={s}&endDate={e}"]


def _download(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as f:
            shutil.copyfileobj(r, f)
        tmp.rename(dest)
        return True
    except Exception as e:  # network errors are reported, not fatal: transform steps skip missing sources
        print(f"  ! {url}: {e}")
        tmp.unlink(missing_ok=True)
        return False


def nhanes():
    out = RAW / "nhanes"
    ok = 0
    for name in NHANES_FILES:
        ok += _download(NHANES_BASE + f"{name}.xpt", out / f"{name}.xpt")
    print(f"nhanes: {ok}/{len(NHANES_FILES)} files in {out}")


def lifesnaps():
    out = RAW / "lifesnaps"
    z = out / "rais_anonymized.zip"
    if not _download(LIFESNAPS_URL, z):
        return
    csv_dir = out / "csv"
    if csv_dir.exists() and any(csv_dir.iterdir()):
        print(f"lifesnaps: CSVs already extracted in {csv_dir}")
        return
    csv_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(z) as zf:
        for info in zf.infolist():
            name = Path(info.filename).name
            # only plain CSV files, flattened, never paths from the archive (untrusted input)
            if info.is_dir() or not name.lower().endswith(".csv") or name.startswith("."):
                continue
            with zf.open(info) as src, open(csv_dir / name, "wb") as dst:
                shutil.copyfileobj(src, dst)
    print(f"lifesnaps: extracted {len(list(csv_dir.iterdir()))} CSV files to {csv_dir}")


def _donki_window(s: str, e: str):
    for tpl in DONKI_URLS:
        url = tpl.format(s=s, e=e)
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read()
            return url.split("?")[0], (json.loads(body) if body.strip() else [])
        except Exception as ex:
            print(f"  ! {url.split('?')[0]} {s}..{e}: {ex}")
    return None, None


def donki(start_year=2024, end_year=2025):
    """Snapshot of DONKI solar energetic particle events, committed so the demo works offline.

    The API rejects long ranges, so we ask month by month."""
    import calendar
    import time
    dest = SPACE_WEATHER / "donki_sep.json"
    if dest.exists():
        print(f"donki: snapshot exists ({dest})")
        return
    events, sources = [], []
    for y in range(start_year, end_year + 1):
        for m in range(1, 13):
            s = f"{y}-{m:02d}-01"
            e = f"{y}-{m:02d}-{calendar.monthrange(y, m)[1]:02d}"
            src, ev = _donki_window(s, e)
            if ev is None:
                print("donki: aborted (network or API change); no snapshot written")
                return
            if src not in sources:
                sources.append(src)
            events.extend(ev)
            time.sleep(1.5)  # DEMO_KEY rate limit
    SPACE_WEATHER.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps({"sources": sources, "startDate": f"{start_year}-01-01",
                                "endDate": f"{end_year}-12-31", "events": events}, indent=1), encoding="utf-8")
    print(f"donki: {len(events)} SEP events -> {dest}")


def run():
    nhanes()
    donki()
    lifesnaps()
    extra()


PHYSIONET = "https://physionet.org/files/"
EXTRA = {
    "mimic-ed": [(PHYSIONET + f"mimic-iv-ed-demo/2.2/ed/{n}.csv.gz", f"{n}.csv.gz")
                 for n in ("triage", "vitalsign", "edstays", "diagnosis")],
    "bigideas": [(PHYSIONET + f"big-ideas-glycemic-wearable/1.1.2/{i:03d}/Dexcom_{i:03d}.csv", f"Dexcom_{i:03d}.csv")
                 for i in range(1, 17)],
    "mmash": [(PHYSIONET + "mmash/1.0.0/MMASH.zip", "MMASH.zip")],
    "ptbxl": [(PHYSIONET + "ptb-xl/1.0.3/ptbxl_database.csv", "ptbxl_database.csv"),
              (PHYSIONET + "ptb-xl-plus/1.0.1/features/12sl_features.csv", "12sl_features.csv")],
    "noaa-sep": [("https://umbra.nascom.nasa.gov/SEP/", "sep_list.html")],
    "nhanes2003": [("https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2003/DataFiles/BAX_C.xpt", "BAX_C.xpt"),
                   ("https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2003/DataFiles/DEMO_C.xpt", "DEMO_C.xpt")],
    "osdr": [("https://osdr.nasa.gov/geode-py/ws/studies/OSD-572/download?source=datamanager"
              "&file=GLDS-564_GMetagenomics_Metaphlan-taxonomy_GLmetagenomics.tsv", "metaphlan_osd572.tsv")],
    "tilt": [("https://physionet.org/files/cerebral-vasoreg-diabetes/1.0.0/Data_Description/GE-71_Data_Summary_Table.csv",
              "GE-71_Data_Summary_Table.csv")],
    "osd410": [("https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GPL15207&targ=self&form=text&view=data",
                "GPL15207.txt")],
}


def extra():
    for group, items in EXTRA.items():
        ok = sum(_download(url, RAW / group / name) for url, name in items)
        print(f"{group}: {ok}/{len(items)} files")
