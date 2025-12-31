#!/usr/bin/env python3
import pandas as pd
import plotly.graph_objects as go
import os

FILES = [
    ("dat/throughput_avg.dat", "Throughput (Mbps)", "Average Throughput (2 flows × 3 TCP types)", "plots/throughput.html"),
    ("dat/rtt_avg.dat",        "RTT (ms)",          "Average RTT (2 flows × 3 TCP types)",        "plots/rtt.html"),
    ("dat/loss_avg.dat",       "Loss rate (%)",     "Average Packet Loss (2 flows × 3 TCP types)","plots/loss.html"),
]

COLS = ["t","Tahoe_f1","Tahoe_f2","Reno_f1","Reno_f2","Vegas_f1","Vegas_f2"]
LABELS = [
    ("Tahoe_f1","Tahoe Flow1"),
    ("Tahoe_f2","Tahoe Flow2"),
    ("Reno_f1","Reno Flow1"),
    ("Reno_f2","Reno Flow2"),
    ("Vegas_f1","Vegas Flow1"),
    ("Vegas_f2","Vegas Flow2"),
]

def make_plot(dat_path, y_label, title, out_html):
    df = pd.read_csv(dat_path, comment="#", sep=r"\s+", header=None)
    df.columns = COLS

    fig = go.Figure()
    for col, name in LABELS:
        fig.add_trace(go.Scatter(
            x=df["t"], y=df[col],
            mode="lines",
            name=name
        ))

    fig.update_layout(
        title=title,
        xaxis_title="Time (s)",
        yaxis_title=y_label,
        hovermode="x unified",
        legend_title="Click to hide/show<br>Double-click to isolate",
        template="plotly_white",
        width=1200,
        height=700
    )

    os.makedirs(os.path.dirname(out_html), exist_ok=True)
    fig.write_html(out_html, include_plotlyjs="cdn")
    print("Wrote:", out_html)

def main():
    for dat_path, y_label, title, out_html in FILES:
        make_plot(dat_path, y_label, title, out_html)

if __name__ == "__main__":
    main()
