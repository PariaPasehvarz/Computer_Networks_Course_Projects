#!/usr/bin/env python3
import pandas as pd

IN_PATH  = "dat/throughput_avg.dat"
OUT_PATH = "dat/throughput_avg_smooth.dat"

WINDOW = 5  # seconds (moving average). Change to 10 if you want smoother.

def main():
    df = pd.read_csv(IN_PATH, comment="#", sep=r"\s+", header=None)
    df.columns = ["t","Tahoe_f1","Tahoe_f2","Reno_f1","Reno_f2","Vegas_f1","Vegas_f2"]

    # Moving average on the 6 value columns (keep t unchanged)
    value_cols = df.columns[1:]
    df_s = df.copy()
    df_s[value_cols] = df[value_cols].rolling(window=WINDOW, center=True, min_periods=1).mean()

    with open(OUT_PATH, "w") as f:
        f.write(f"# Smoothed throughput with {WINDOW}s moving average\n")
        f.write("# time  Tahoe_f1 Tahoe_f2 Reno_f1 Reno_f2 Vegas_f1 Vegas_f2   (Mbps)\n")
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
