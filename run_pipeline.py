import subprocess
import sys

STEPS = [
    "src.collect_geography",
    "src.collect_bigquery",
    "src.collect_inpe_official",
    "src.collect_weather",
    "src.build_dataset",
    "src.eda",
    "src.model",
    "src.additional_analysis",
    "src.make_dashboard",
]

def main():
    for step in STEPS:
        print(f"\n{'=' * 70}\nExecutando {step}\n{'=' * 70}")
        subprocess.run([sys.executable, "-m", step], check=True)
    print("\nPipeline concluído.")

if __name__ == "__main__":
    main()
