#!/usr/bin/env python3
import os
from collections import Counter

SIM_TIME = 1000
TCP_TYPES = ["Tahoe", "Reno", "Vegas"]
SEEDS = range(1, 11)

# Based on node creation order in phase2.tcl:
# n1=0, n2=1, rL=2, rR=3, n5=4, n6=5
DEST_NODE_BY_FID = {1: 4, 2: 5}

OUT_DIR = "out"
DAT_DIR = "dat"


def ensure_dirs():
    os.makedirs(DAT_DIR, exist_ok=True)


def read_time_value_file(path, sim_time=SIM_TIME):
    """
    Reads 'time value' lines into an array indexed by integer seconds.
    Assumes times are (now) exactly integers 1..SIM_TIME due to your fixed logger.
    """
    arr = [0.0] * (sim_time + 1)
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            sec = int(float(parts[0]))
            if 0 <= sec <= sim_time:
                arr[sec] = float(parts[1])
    return arr


def rtt_to_ms(rtt_arr):
    return rtt_arr  


def add_arrays(a, b):
    return [x + y for x, y in zip(a, b)]


def div_array(a, d):
    return [x / d for x in a]


def detect_payload_rule_from_trace(tr_path, sample_lines=200000):
    """
    Auto-detect header size and whether trace 'size' includes headers.
    We find:
      - header_size: mode of TCP sizes <= 80 (usually 40)
      - data_size_mode: mode of TCP sizes > header_size
    Then decide payload:
      - If data_size_mode - header_size is ~1000 (within [800,1200]),
        payload = size - header_size
      - Else payload = size (trace already looks like payload size)
    """
    small = Counter()
    large = Counter()

    with open(tr_path, "r") as f:
        for i, line in enumerate(f):
            if i >= sample_lines:
                break
            line = line.strip()
            if not line:
                continue
            p = line.split()
            if len(p) < 12:
                continue
            if p[4] != "tcp":
                continue
            try:
                size = int(float(p[5]))
            except Exception:
                continue

            if size <= 80:
                small[size] += 1
            else:
                large[size] += 1

    header_size = 40
    if small:
        header_size = small.most_common(1)[0][0]

    data_size_mode = None
    if large:
        data_size_mode = large.most_common(1)[0][0]

    # Decide rule
    if data_size_mode is not None and 800 <= (data_size_mode - header_size) <= 1200:
        def payload_bytes(size):
            return max(size - header_size, 0)
        rule_desc = f"payload=size-{header_size}"
    else:
        def payload_bytes(size):
            return max(size, 0) if size > header_size else 0
        rule_desc = "payload=size (acks ignored)"

    return payload_bytes, rule_desc, header_size, data_size_mode


def throughput_from_trace_payload_mbps(tr_path, dest_by_fid=DEST_NODE_BY_FID, sim_time=SIM_TIME):
    """
    Throughput per second per fid from trace:
      count bytes of TCP DATA packets received at final destination node
      (event 'r' where 'to' == destination node for that fid).
    """
    payload_bytes_fn, rule_desc, header_size, data_mode = detect_payload_rule_from_trace(tr_path)

    bytes_sec = {fid: [0] * (sim_time + 1) for fid in dest_by_fid.keys()}

    with open(tr_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            p = line.split()
            if len(p) < 12:
                continue

            ev = p[0]
            if ev != "r":
                continue

            # action time from to type size flags fid src dst seq pktid
            try:
                t = float(p[1])
                sec = int(t)
                to_node = int(p[3])
                ptype = p[4]
                size = int(float(p[5]))
                fid = int(p[7])
            except Exception:
                continue

            if ptype != "tcp":
                continue
            if sec < 0 or sec > sim_time:
                continue
            if fid not in dest_by_fid:
                continue
            if to_node != dest_by_fid[fid]:
                continue

            payload = payload_bytes_fn(size)
            if payload <= 0:
                continue

            bytes_sec[fid][sec] += payload

    mbps = {fid: [0.0] * (sim_time + 1) for fid in dest_by_fid.keys()}
    for fid in dest_by_fid.keys():
        for sec in range(0, sim_time + 1):
            mbps[fid][sec] = bytes_sec[fid][sec] * 8.0 / 1_000_000.0

    return mbps, (rule_desc, header_size, data_mode)


def parse_queue_trace_loss_percent(qtr_path, sim_time=SIM_TIME):
    """
    From q.tr (bottleneck queue trace):
      '+' = enqueue, 'd' = drop
    loss% per second per fid = 100 * drops / enqueues
    fid is field index 7 in your sample.
    """
    enq = {1: [0] * (sim_time + 1), 2: [0] * (sim_time + 1)}
    drp = {1: [0] * (sim_time + 1), 2: [0] * (sim_time + 1)}

    with open(qtr_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            p = line.split()
            if len(p) < 8:
                continue

            ev = p[0]
            try:
                t = float(p[1])
                sec = int(t)
                fid = int(p[7])
            except Exception:
                continue

            if sec < 0 or sec > sim_time:
                continue
            if fid not in (1, 2):
                continue

            if ev == "+":
                enq[fid][sec] += 1
            elif ev == "d":
                drp[fid][sec] += 1

    loss = {1: [0.0] * (sim_time + 1), 2: [0.0] * (sim_time + 1)}
    for fid in (1, 2):
        for sec in range(0, sim_time + 1):
            if enq[fid][sec] > 0:
                loss[fid][sec] = 100.0 * (drp[fid][sec] / enq[fid][sec])
            else:
                loss[fid][sec] = 0.0
    return loss


def write_dat(path, series, ylabel):
    """
    Column order:
      time  Tahoe_f1 Tahoe_f2 Reno_f1 Reno_f2 Vegas_f1 Vegas_f2
    """
    with open(path, "w") as f:
        f.write(f"# time  Tahoe_f1 Tahoe_f2 Reno_f1 Reno_f2 Vegas_f1 Vegas_f2   ({ylabel})\n")
        for sec in range(0, SIM_TIME + 1):
            row = [
                sec,
                series["Tahoe"][1][sec], series["Tahoe"][2][sec],
                series["Reno"][1][sec],  series["Reno"][2][sec],
                series["Vegas"][1][sec], series["Vegas"][2][sec],
            ]
            f.write("{:d} {:.6f} {:.6f} {:.6f} {:.6f} {:.6f} {:.6f}\n".format(*row))


def main():
    ensure_dirs()

    # Accumulators (sum over runs)
    sum_tp = {tcp: {1: [0.0]*(SIM_TIME+1), 2: [0.0]*(SIM_TIME+1)} for tcp in TCP_TYPES}
    sum_rtt = {tcp: {1: [0.0]*(SIM_TIME+1), 2: [0.0]*(SIM_TIME+1)} for tcp in TCP_TYPES}
    sum_loss = {tcp: {1: [0.0]*(SIM_TIME+1), 2: [0.0]*(SIM_TIME+1)} for tcp in TCP_TYPES}
    runs_found = {tcp: 0 for tcp in TCP_TYPES}

    # Optional: print the detected payload rule once per tcp (from seed 1 trace)
    printed_rule = set()

    for tcp in TCP_TYPES:
        for seed in SEEDS:
            prefix = os.path.join(OUT_DIR, f"{tcp}_{seed}")

            trfile = f"{prefix}.tr"
            rtt_f1 = f"{prefix}_rtt_f1.dat"
            rtt_f2 = f"{prefix}_rtt_f2.dat"
            qtr    = f"{prefix}_q.tr"

            for p in (trfile, rtt_f1, rtt_f2, qtr):
                if not os.path.exists(p):
                    raise FileNotFoundError(f"Missing file: {p}")

            # Throughput from trace
            tp, rule_info = throughput_from_trace_payload_mbps(trfile)
            if tcp not in printed_rule:
                rule_desc, header_size, data_mode = rule_info
                print(f"[{tcp}] throughput parsing rule: {rule_desc} (header={header_size}, data_mode={data_mode})")
                printed_rule.add(tcp)

            sum_tp[tcp][1] = add_arrays(sum_tp[tcp][1], tp[1])
            sum_tp[tcp][2] = add_arrays(sum_tp[tcp][2], tp[2])

            # RTT from logs
            r1 = rtt_to_ms(read_time_value_file(rtt_f1))
            r2 = rtt_to_ms(read_time_value_file(rtt_f2))
            sum_rtt[tcp][1] = add_arrays(sum_rtt[tcp][1], r1)
            sum_rtt[tcp][2] = add_arrays(sum_rtt[tcp][2], r2)

            # Loss from bottleneck queue trace
            loss = parse_queue_trace_loss_percent(qtr)
            sum_loss[tcp][1] = add_arrays(sum_loss[tcp][1], loss[1])
            sum_loss[tcp][2] = add_arrays(sum_loss[tcp][2], loss[2])

            runs_found[tcp] += 1

    # Average
    avg_tp   = {tcp: {fid: div_array(sum_tp[tcp][fid], runs_found[tcp])   for fid in (1,2)} for tcp in TCP_TYPES}
    avg_rtt  = {tcp: {fid: div_array(sum_rtt[tcp][fid], runs_found[tcp])  for fid in (1,2)} for tcp in TCP_TYPES}
    avg_loss = {tcp: {fid: div_array(sum_loss[tcp][fid], runs_found[tcp]) for fid in (1,2)} for tcp in TCP_TYPES}

    write_dat(os.path.join(DAT_DIR, "throughput_avg.dat"), avg_tp,   "Mbps (payload goodput at receiver)")
    write_dat(os.path.join(DAT_DIR, "rtt_avg.dat"),        avg_rtt,  "ms")
    write_dat(os.path.join(DAT_DIR, "loss_avg.dat"),       avg_loss, "loss% = drops/enqueues*100 at bottleneck")

    print("Wrote:")
    print("  dat/throughput_avg.dat")
    print("  dat/rtt_avg.dat")
    print("  dat/loss_avg.dat")


if __name__ == "__main__":
    main()
