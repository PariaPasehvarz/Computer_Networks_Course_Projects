set terminal pngcairo size 1200,700
set output "plots/rtt.png"
set title "Average RTT (2 flows × 3 TCP types)"
set xlabel "Time (s)"
set ylabel "RTT (ms)"
set key outside
set grid
plot \
 "dat/rtt_avg.dat" using 1:2 with lines title "Tahoe Flow1", \
 "dat/rtt_avg.dat" using 1:3 with lines title "Tahoe Flow2", \
 "dat/rtt_avg.dat" using 1:4 with lines title "Reno Flow1",  \
 "dat/rtt_avg.dat" using 1:5 with lines title "Reno Flow2",  \
 "dat/rtt_avg.dat" using 1:6 with lines title "Vegas Flow1", \
 "dat/rtt_avg.dat" using 1:7 with lines title "Vegas Flow2"
