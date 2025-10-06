from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parents[1]

def plot_lci_scatter():
    p = BASE / "results" / "tables" / "lci_by_family.csv"
    if not p.exists():
        print("[WARN] lci_by_family.csv not found.")
        return
    df = pd.read_csv(p)
    for fam, df_f in df.groupby("family"):
        fig, ax = plt.subplots()
        ax.scatter(df_f["a"], df_f["LCI"])
        ax.set_title(f"LCI vs Accuracy — {fam}")
        ax.set_xlabel("Accuracy")
        ax.set_ylabel("LCI (USD per task-equivalent)")
        (BASE / "results" / "figures").mkdir(parents=True, exist_ok=True)
        fig.savefig(BASE / "results" / "figures" / f"lci_vs_accuracy_{fam}.pdf", bbox_inches="tight")
        plt.close(fig)

def main():
    plot_lci_scatter()
    print("[OK] Figures generated (if inputs existed).")

if __name__ == "__main__":
    main()
