"""How a clinical_compare plan entry's timing should be read and labelled.

Two schemas exist in the committed bundles and they do not mean the same thing:

  schema 1 (every bundle written before 2026-08-26) - `solve_time_s` bracketed the
      WHOLE of `solve_set`: DataExplorer, CT, Structures, ClinicalCriteria,
      InfluenceMatrix, `create_down_sample`, cvxpy problem construction, and only
      then MOSEK. The down-sampled variant was additionally charged for the
      down-sampling it exists to benefit from, which is why the down-sampled column
      often read SLOWER than full resolution (Lung_Patient_20: 923.7 s vs 28.2 s).
      That number is a pipeline time and must never be presented as a solve time.

  schema 2 - `solve_time_s` is the MOSEK solve alone; setup and total are recorded
      alongside it.

Rendering code asks this module for the label so a legacy bundle stays legible
instead of being silently relabelled into a claim it cannot support.
"""

TIMING_SCHEMA = 2

# (standalone, form that follows a prefix). Kept as pairs rather than lower-casing the
# first character, which turned "MOSEK" into "mOSEK".
_SOLVE_LABEL = ("MOSEK solve time", "MOSEK solve time")
_LEGACY_LABEL = ("Pipeline time (setup + solve)", "pipeline time (setup + solve)")


def timing_label(entry, prefix=""):
    """Label for `entry`'s `solve_time_s`, honest about which schema wrote it."""
    standalone, suffixed = _SOLVE_LABEL if is_true_solve_time(entry) else _LEGACY_LABEL
    return f"{prefix}{suffixed}" if prefix else standalone


def is_true_solve_time(entry):
    """True when `entry['solve_time_s']` times the solver and nothing else."""
    return entry.get("timing_schema", 1) >= 2


def solve_seconds(entry):
    """The seconds `solve_time_s` holds, whatever they turn out to measure."""
    return entry.get("solve_time_s")
