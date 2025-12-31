#!/usr/bin/env python3
import pandas as pd

IN_PATH  = "dat/loss_avg.dat"
OUT_PATH = "dat/loss_avg_smooth.dat"

WINDOW = 10  # seconds. (Try 5 if you want less smoothing.)

def main():
    df = pd.read_csv(IN_PATH, comment="#", sep=r"\s+", header=None)
    df.columns = ["t","Tahoe_f1","Tahoe_f2","Reno_f1","Reno_f2","Vegas_f1","Vegas_f2"]

    value_cols = df.columns[1:]
    df_s = df.copy()
    df_s[value_cols] = df[value_cols].rolling(window=WINDOW, center=True, min_periods=1).mean()

    with open(OUT_PATH, "w") as f:
        f.write(f"# Smoothed loss with {WINDOW}s moving average\n")
        f.write("# time  Tahoe_f1 Tahoe_f2 Reno_f1 Reno_f2 Vegas_f1 Vegas_f2   (loss%)\n")
        for _, row in df_s.iterrows():
            f.write("{:d} {:.6f} {:.6f} {:.6f} {:.6f} {:.6f} {:.6f}\n".format(
                int(row["t"]),
                row["Tahoe_f1"], row["Tahoe_f2"],
                row["Reno_f1"],  row["Reno_f2"],
                row["Vegas_f1"], row["Vegas_f2"],
            ))

    print("Wrote:", OUT_PATH)

if __name__ == "__main__":
    main()
