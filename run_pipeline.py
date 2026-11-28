import subprocess
import sys

STEPS = [
    ("1/3 Engineering 8 domain features", [sys.executable, "ml_engine/src/feature_engineering.py"]),
    ("2/3 Running Isolation Forest anomaly model", [sys.executable, "ml_engine/src/anomaly_models.py"]),
    ("3/3 Aggregating Composite Risk Index (CRI)", [sys.executable, "ml_engine/src/cri_aggregator.py"]),
]


def main() -> None:
    for label, cmd in STEPS:
        print(f"\n=== {label} ===")
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            print(f"Failed at: {label}")
            sys.exit(result.returncode)
    print("\nAll E-NETRA ML & CRI pipeline steps completed cleanly.")


if __name__ == "__main__":
    main()