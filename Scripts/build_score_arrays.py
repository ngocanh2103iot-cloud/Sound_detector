import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path


def safe_name(value):
    name = re.sub(r"\W+", "_", value.strip().lower()).strip("_")
    if not name:
        name = "unknown"
    if name[0].isdigit():
        name = f"case_{name}"
    return name


def read_scores(logs_dir):
    scores_by_case = defaultdict(list)

    for csv_path in sorted(logs_dir.glob("*.csv")):
        with csv_path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                case_name = (row.get("case") or "").strip() or csv_path.stem
                score_text = (row.get("score") or "").strip()
                if not score_text:
                    continue

                scores_by_case[case_name].append(float(score_text))

    return dict(scores_by_case)


def write_python_arrays(scores_by_case, out_path):
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        f.write("# Auto-generated from logs/*.csv\n\n")

        variable_names = {}
        for case_name, scores in sorted(scores_by_case.items()):
            var_name = f"{safe_name(case_name)}_scores"
            variable_names[case_name] = var_name
            values = ", ".join(f"{score:.4f}" for score in scores)
            f.write(f"{var_name} = [{values}]\n\n")

        f.write("scores_by_case = {\n")
        for case_name, var_name in sorted(variable_names.items()):
            f.write(f"    {case_name!r}: {var_name},\n")
        f.write("}\n")


def print_summary(scores_by_case):
    for case_name, scores in sorted(scores_by_case.items()):
        if not scores:
            continue
        avg = sum(scores) / len(scores)
        print(
            f"{case_name}: count={len(scores)} "
            f"min={min(scores):.4f} mean={avg:.4f} max={max(scores):.4f}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Build Python score arrays from CSV logs."
    )
    parser.add_argument("--logs", type=Path, default=Path("logs"))
    parser.add_argument("--out", type=Path, default=Path("logs/score_arrays.py"))
    args = parser.parse_args()

    scores_by_case = read_scores(args.logs)
    if not scores_by_case:
        print(f"No score rows found in {args.logs}")
        return 1

    write_python_arrays(scores_by_case, args.out)
    print_summary(scores_by_case)
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
