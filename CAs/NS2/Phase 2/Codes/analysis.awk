BEGIN {
    tcp_bytes = 0
    udp_bytes = 0
    simtime = 20
}

{
    event = $1
    pkt_type = $5
    size = $6

    if (event == "r" && pkt_type == "tcp") {
        tcp_bytes += size
    }

    if (event == "r" && pkt_type == "cbr") {
        udp_bytes += size
    }
}

END {
    tcp_tp = (tcp_bytes * 8) / (simtime * 1000000)
    udp_tp = (udp_bytes * 8) / (simtime * 1000000)

    print "TCP Throughput (Mbps):", tcp_tp
    print "UDP Throughput (Mbps):", udp_tp

    if ((tcp_tp^2 + udp_tp^2) > 0) {
        fairness = (tcp_tp + udp_tp)^2 / (2 * (tcp_tp^2 + udp_tp^2))
        print "Jain Fairness Index:", fairness
    } else {
        print "Jain Fairness Index: undefined (no traffic)"
    }
}
