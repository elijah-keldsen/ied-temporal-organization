#!/usr/bin/env python3
"""Validate scientific invariants, repository integrity, and deidentification."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/deidentified"
PUBLIC_ID = re.compile(r"^P\d{3}$")
PRIVATE_ID = re.compile(r"(?<![A-Za-z0-9])1[12]\d{7}(?!\d)")
TRANSIENT_PARTS = {".git", ".pytest_cache", ".venv", "__pycache__"}


def is_release_path(path: Path) -> bool:
    """Return whether a path belongs to the versioned public release."""
    relative = path.relative_to(ROOT)
    if any(part in TRANSIENT_PARTS for part in relative.parts):
        return False
    if relative.parts[:3] == ("supplement", "source", "build"):
        return False
    return path.suffix not in {".pyc", ".pyo"}


def release_files() -> list[Path]:
    return [path for path in ROOT.rglob("*") if path.is_file() and is_release_path(path)]


class Audit:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.passes = 0

    def check(self, condition: bool, message: str) -> None:
        if condition:
            self.passes += 1
        else:
            self.failures.append(message)

    def close(self) -> int:
        if self.failures:
            print(f"FAIL · {len(self.failures)} finding(s), {self.passes} checks passed")
            for failure in self.failures:
                print(f"  - {failure}")
            return 1
        print(f"PASS · {self.passes} scientific, structural, and privacy checks")
        return 0


def close(left: float, right: float, tolerance: float = 5e-8) -> bool:
    return bool(np.isclose(left, right, rtol=0, atol=tolerance))


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def extract_text(path: Path) -> str:
    suffixes = path.suffixes
    if path.suffix == ".gz":
        try:
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                return handle.read()
        except (OSError, UnicodeDecodeError):
            return ""
    if path.suffix == ".npz":
        pieces = []
        try:
            with np.load(path, allow_pickle=False) as archive:
                for key in archive.files:
                    pieces.append(key)
                    value = archive[key]
                    if value.dtype.kind in "US":
                        pieces.extend(value.astype(str).ravel().tolist())
        except Exception as exc:  # pragma: no cover - surfaced as audit text
            return f"NPZ_READ_ERROR {exc}"
        return "\n".join(pieces)
    if path.suffix == ".pdf" and shutil.which("pdftotext"):
        run = subprocess.run(
            ["pdftotext", str(path), "-"],
            check=False,
            capture_output=True,
            text=True,
        )
        return run.stdout
    if path.suffix == ".png":
        # PNG textual chunks are visible without OCR; publication pixels are audited
        # separately in the release procedure with tesseract when available.
        blob = path.read_bytes()
        return blob.decode("latin-1", errors="ignore")
    if path.suffix.lower() in {
        ".csv",
        ".json",
        ".md",
        ".py",
        ".tex",
        ".yml",
        ".yaml",
        ".txt",
        ".cff",
        ".toml",
        "",
    }:
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return ""
    return ""


def scientific_checks(audit: Audit) -> None:
    cohort = pd.read_csv(DATA / "cohort_features.csv")
    expected_cohort_columns = {
        "participant_id",
        "n_onset_events",
        "n_ied_positive_seconds",
        "fine_kernel_post_first_onset_hours",
        "ppglm_valid_eeg_hours",
        "ied_positive_seconds_per_valid_eeg_hour",
        "merged_onset_responses_per_hour",
    }
    legacy_cohort_columns = {
        "modeled_hours_after_first_onset",
        "modeled_onset_rate_per_hour",
        "mean_rate_per_h",
    }
    audit.check(
        expected_cohort_columns <= set(cohort.columns),
        "cohort_features is missing an explicitly defined response or exposure field",
    )
    audit.check(
        legacy_cohort_columns.isdisjoint(cohort.columns),
        "cohort_features contains an ambiguous legacy response or exposure field",
    )
    audit.check(len(cohort) == 114, "cohort_features must contain 114 participants")
    audit.check(
        cohort["participant_id"].nunique() == 114,
        "cohort participant IDs must be unique",
    )
    audit.check(
        cohort["participant_id"].map(lambda value: bool(PUBLIC_ID.fullmatch(value))).all(),
        "cohort IDs must use the P### namespace",
    )
    audit.check(
        int(cohort["n_ied_positive_seconds"].sum()) == 3_303_076,
        "IED-positive-second total must be 3,303,076",
    )
    audit.check(
        close(cohort["n_ied_positive_seconds"].median(), 4162.0),
        "median IED-positive-second count must be 4,162",
    )
    audit.check(
        int(cohort["n_onset_events"].sum()) == 1_094_298,
        "merged-onset total must be 1,094,298",
    )
    audit.check(
        close(cohort["n_onset_events"].median(), 3399.0),
        "median merged-onset count must be 3,399",
    )
    audit.check(
        close(cohort["split_half_residual_correlation"].median(), 0.9645380605886125),
        "median split-half residual correlation changed",
    )
    repeats = cohort["cross_admission_residual_correlation"].dropna()
    audit.check(len(repeats) == 39, "repeat-recording cohort must contain 39 participants")
    audit.check(
        close(repeats.median(), 0.9053368698744306),
        "median cross-admission residual correlation changed",
    )

    history = pd.read_csv(DATA / "history/history_curves.csv.gz")
    audit.check(history.shape[0] == 114 * 179, "history curve grid must be 114 × 179")
    audit.check(
        history.groupby("participant_id")["lag_s"].nunique().eq(179).all(),
        "every participant must have the complete 1–90 s history grid",
    )
    short_history = pd.read_csv(
        DATA / "history/manuscript_short_history_curves.csv.gz"
    )
    audit.check(
        short_history.shape[0] == 114 * 57,
        "manuscript short-history grid must be 114 × 57",
    )
    audit.check(
        short_history.groupby("participant_id")["lag_s"].nunique().eq(57).all(),
        "every participant must have the complete ratified 1–15 s history grid",
    )
    audit.check(
        ((history["full_multiplier"] >= history["lower_95"]) & (history["full_multiplier"] <= history["upper_95"])).all(),
        "history point estimates must lie inside their 95% intervals",
    )
    examples = json.loads((DATA / "history/figure3_examples.json").read_text())
    audit.check(
        all(
            "fine_kernel_post_first_onset_hours" in item
            and "merged_onset_responses_per_min" in item
            and "modeled_hours" not in item
            and "modeled_onset_rate_per_min" not in item
            for item in examples
        ),
        "Figure 3 example summaries contain an ambiguous response or exposure field",
    )
    repeat_curves = pd.read_csv(DATA / "history/repeat_recording_curves.csv.gz")
    audit.check(
        repeat_curves.shape[0] == 39 * 2 * 179,
        "repeat-recording curve grid must be 39 × 2 × 179",
    )
    audit.check(
        repeat_curves.groupby("participant_id")["recording"].nunique().eq(2).all(),
        "every repeat-recording participant must have anonymous recordings A and B",
    )

    detectability = pd.read_csv(DATA / "ppglm/bootstrap_detectability.csv")

    def detectable(prefix: str) -> pd.Series:
        return (detectability[f"{prefix}_lo95_B2000"] > 0) | (
            detectability[f"{prefix}_hi95_B2000"] < 0
        )

    history_detected = detectable("sa_H")
    vigilance_detected = detectable("sa_V")
    asm_detected = detectable("sa_A")
    classes = (
        int((vigilance_detected & asm_detected).sum()),
        int((vigilance_detected & ~asm_detected).sum()),
        int((~vigilance_detected & asm_detected).sum()),
        int((~vigilance_detected & ~asm_detected).sum()),
    )
    audit.check(int(history_detected.sum()) == 105, "history detectability count must be 105")
    audit.check(classes == (62, 39, 8, 5), "Vigilance/ASM detectability classes changed")
    dependency = pd.read_csv(DATA / "ppglm/dependency_coordinates.csv")
    detectable_asm = asm_detected.to_numpy()
    signs = dependency.loc[detectable_asm, "sa_A_ev"]
    audit.check(
        (int((signs > 0).sum()), int((signs < 0).sum())) == (35, 35),
        "detectable ASM coordinates must split 35 positive / 35 negative",
    )

    population = json.loads((DATA / "ppglm/population_inference.json").read_text())
    expected = {
        "sa_H": 0.9753851297853778,
        "sa_V": 0.1728015332563396,
        "sa_A": 0.059971740641911075,
        "un_H": 0.7665782071996314,
        "un_V": 0.05753573326012908,
        "un_A": -0.016420654547095393,
    }
    audit.check(
        all(close(population["pooled_fractions"][key]["point"], value) for key, value in expected.items()),
        "pooled standalone/unique fractions changed",
    )

    roc = pd.read_csv(DATA / "history/figure4_roc_curves.csv")
    auc = roc.groupby("comparison")["auc"].first().to_dict()
    audit.check(
        close(auc["same_recording_split_halves"], 0.8815741807554128),
        "Figure 4 leave-two-participants-out split-half ROC AUC changed",
    )
    audit.check(
        close(auc["same_participant_repeat_recording"], 0.7033461365445172),
        "cross-admission ROC AUC changed",
    )

    sleep = json.loads((DATA / "sleep_density_ae114.json").read_text())
    expected_sleep = {
        "n1": (112, 1.939977415290841),
        "n2": (114, 3.7966386535756276),
        "n3": (112, 3.6850164964261727),
        "rem": (84, 1.4974038396352465),
    }
    audit.check(
        all(
            sleep[stage]["n"] == number
            and close(sleep[stage]["geomean_ratio"], ratio)
            for stage, (number, ratio) in expected_sleep.items()
        ),
        "sleep-state sample sizes or geometric-mean ratios changed",
    )

    expected_penalties = {100, 1000, 10000}
    penalty_files = sorted((DATA / "ppglm").glob("cross_validated_models_lambda*.csv"))
    observed_penalties = set()
    for path in penalty_files:
        frame = pd.read_csv(path, usecols=["lam"])
        values = {int(value) for value in frame["lam"].unique()}
        suffix = int(path.stem.rsplit("lambda", 1)[1])
        audit.check(values == {suffix}, f"penalty value does not match {path.name}")
        observed_penalties.update(values)
    audit.check(
        observed_penalties == expected_penalties and len(penalty_files) == 3,
        "public cross-validation files must cover lambda 100, 1000, and 10000",
    )

    kernel_summary = pd.read_csv(
        ROOT / "supplement/source/tables/table_sa_kernel_feature_summary.csv",
        dtype=str,
        keep_default_na=False,
    )
    expected_kernel_summary = {
        "Modeled merged-onset responses": ("114", "3,399", "1,257–7,746", "504–103,544", "count"),
        "Modeled post-first-onset exposure": ("114", "80.6", "58.4–114.2", "16.4–302.3", "hours"),
        "Modeled onset-response rate (post-first-onset hours)": ("114", "45.1", "17.6–136.6", "4.2–406.5", "responses/hour"),
        "Apparent early boundary": ("114", "3.00", "3.00–3.25", "2.75–8.00", "seconds"),
        "Rebound peak lag": ("114", "5.00", "3.50–6.50", "3.50–12.00", "seconds"),
        "Rebound peak multiplier": ("114", "1.466", "1.370–1.606", "1.231–2.509", "rate multiplier"),
        "40–70 s mean multiplier": ("114", "1.733", "1.336–2.408", "0.920–27.017", "rate multiplier"),
        "Split-half residual correlation": ("114", "0.965", "0.915–0.987", "-0.144–1.000", "Pearson r"),
        "Cross-admission residual correlation": ("39", "0.905", "0.636–0.987", "-0.958–0.999", "Pearson r"),
    }
    observed_kernel_summary = {
        row["Characteristic"]: (
            row["n"],
            row["Median"],
            row["IQR"],
            row["Range"],
            row["Unit"],
        )
        for row in kernel_summary.to_dict(orient="records")
    }
    audit.check(
        observed_kernel_summary == expected_kernel_summary,
        "Supplementary Table S6 source values or response labels changed",
    )

    from reproduce_statistics import claims as paper_claims

    for claim in paper_claims():
        audit.check(
            claim.matches,
            f"paper/SI mismatch for {claim.statistic}: {claim.reproduced} != {claim.reported}",
        )


def structural_checks(audit: Audit, verify_manifest: bool = True) -> None:
    required = [
        ROOT / "README.md",
        ROOT / "DATA_DICTIONARY.md",
        ROOT / "PRIVACY.md",
        ROOT / "REPRODUCIBILITY.md",
        ROOT / "RESULTS_CHECKLIST.md",
        ROOT / "CITATION.cff",
        ROOT / "scripts/reproduce_statistics.py",
        DATA / "history/manuscript_short_history_curves.csv.gz",
        ROOT / "supplement/supplementary_appendix.pdf",
    ]
    required += sorted((ROOT / "figures/manuscript").glob("figure*.png"))
    audit.check(all(path.exists() for path in required), "one or more required release files are missing")
    audit.check(
        len(list((ROOT / "figures/manuscript").glob("figure*.png"))) == 6,
        "exactly six manuscript figures are required",
    )
    audit.check(
        not any(path.is_symlink() for path in ROOT.rglob("*") if is_release_path(path)),
        "release must not contain symbolic links",
    )
    audit.check(
        not any(path.stat().st_size > 50 * 1024 * 1024 for path in release_files()),
        "release contains a file larger than 50 MiB",
    )
    source_hashes = json.loads((ROOT / "provenance/source_artifact_hashes.json").read_text())
    audit.check(
        all(
            (ROOT / item["artifact"]).is_file()
            and hash_file(ROOT / item["artifact"]) == item["release_sha256"]
            for item in source_hashes
        ),
        "a frozen figure/supplement artifact differs from its recorded release hash",
    )
    for table in (ROOT / "supplement/source/tables").glob("table_sb*.csv"):
        content = table.read_text()
        audit.check(
            "Perturbation-stability" not in content
            and "rounded-hour denominator" not in content,
            f"stale response or reproducibility terminology remains in {table.name}",
        )
    aggregate_tables = "\n".join(
        path.read_text() for path in (ROOT / "supplement/source/tables").glob("*.csv")
    )
    audit.check(
        not re.search(r"\bGOV-\d+\b|overviewer", aggregate_tables, re.IGNORECASE),
        "internal governance markers remain in public supplement tables",
    )
    audit.check(
        not (ROOT / "supplement/source/tables/table_sd_pnas_display_map.csv").exists(),
        "internal supplement display-map table must not be published",
    )
    audit.check(
        not any((ROOT / "supplement/source/tables").glob("table_sc*.csv")),
        "unused n=113 PP-GLM component tables must not be published",
    )
    manifest_path = ROOT / "provenance/release_manifest.json"
    if verify_manifest and manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        recorded = {item["path"]: item for item in manifest.get("files", [])}
        current = {
            str(path.relative_to(ROOT)): path
            for path in release_files()
            if path != manifest_path
        }
        audit.check(
            set(recorded) == set(current),
            "release manifest file list does not match the public tree",
        )
        audit.check(
            set(recorded) == set(current)
            and all(
                recorded[name]["bytes"] == path.stat().st_size
                and recorded[name]["sha256"] == hash_file(path)
                for name, path in current.items()
            ),
            "release manifest hashes or byte counts do not match the public tree",
        )


def privacy_checks(audit: Audit, crosswalk: Path | None) -> None:
    known_ids: set[str] = set()
    if crosswalk:
        frame = pd.read_csv(crosswalk, dtype=str)
        audit.check("bdsp_pid" in frame, "private crosswalk lacks bdsp_pid column")
        known_ids = set(frame["bdsp_pid"].dropna())

    disallowed_columns = {
        "pid",
        "bdsp_pid",
        "mrn",
        "date_of_birth",
        "dob",
        "t_utc",
        "stay_id",
        "session_id",
        "site",
        "sex",
        "age",
    }
    for path in sorted(DATA.rglob("*.csv")) + sorted(DATA.rglob("*.csv.gz")):
        frame = pd.read_csv(path, nrows=2)
        overlap = disallowed_columns & {column.lower() for column in frame.columns}
        audit.check(not overlap, f"disallowed columns in {path.relative_to(ROOT)}: {sorted(overlap)}")

    patterns = {
        "private-shaped identifier": PRIVATE_ID,
        "absolute patient date": re.compile(r"\b20[0-2]\d-[01]\d-[0-3]\d\b"),
        "private filesystem path": re.compile(r"/(?:data/eli-work|home)/"),
        "cloud storage URI": re.compile("s3" + "://", re.IGNORECASE),
        "credential-like string": re.compile(
            r"AKIA[0-9A-Z]{16}|(?:access|refresh|client)[_-]?(?:token|secret)\s*[=:]",
            re.IGNORECASE,
        ),
    }
    for path in release_files():
        relative = path.relative_to(ROOT)
        audit.check(
            not PRIVATE_ID.search(str(relative)),
            f"private-shaped identifier in filename: {relative}",
        )
        text = extract_text(path)
        for label, pattern in patterns.items():
            match = pattern.search(text)
            audit.check(not match, f"{label} in {relative}: {match.group(0) if match else ''}")
        if known_ids:
            hit = next(
                (
                    private_id
                    for private_id in known_ids
                    if re.search(
                        rf"(?<![A-Za-z0-9]){re.escape(private_id)}(?!\d)", text
                    )
                ),
                None,
            )
            audit.check(hit is None, f"known private identifier in {relative}")

    # No individual-level demographic columns are released; demographic supplement
    # material is aggregate only. Published figure pixels are checked by OCR when the
    # executable is available.
    if shutil.which("tesseract"):
        for image in sorted((ROOT / "figures").rglob("*.png")) + sorted(
            (ROOT / "supplement/figures").glob("*.png")
        ):
            run = subprocess.run(
                ["tesseract", str(image), "stdout"],
                check=False,
                capture_output=True,
                text=True,
            )
            ocr = run.stdout
            audit.check(
                not PRIVATE_ID.search(ocr),
                f"private-shaped identifier visible in {image.relative_to(ROOT)}",
            )
            if known_ids:
                audit.check(
                    not any(private_id in ocr for private_id in known_ids),
                    f"known private identifier visible in {image.relative_to(ROOT)}",
                )


def write_manifest() -> None:
    destination = ROOT / "provenance/release_manifest.json"
    records = []
    for path in sorted(release_files()):
        if path == destination:
            continue
        records.append(
            {
                "path": str(path.relative_to(ROOT)),
                "bytes": path.stat().st_size,
                "sha256": hash_file(path),
            }
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({"files": records}, indent=2) + "\n")
    print(f"wrote {destination.relative_to(ROOT)} ({len(records)} files)")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--crosswalk",
        type=Path,
        help="optional private crosswalk for the stricter local release gate",
    )
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    audit = Audit()
    scientific_checks(audit)
    structural_checks(audit, verify_manifest=not args.write_manifest)
    privacy_checks(audit, args.crosswalk)
    result = audit.close()
    if result == 0 and args.write_manifest:
        write_manifest()
    return result


if __name__ == "__main__":
    raise SystemExit(main())
