set terminal pngcairo size 1200,700
set output "plots/rtt_smooth.png"
set title "Smoothed Average RTT (10s moving average)"
set xlabel "Time (s)"
set ylabel "RTT (ms)"
set key outside
set grid

plot \
 "dat/rtt_avg_smooth.dat" using 1:2 with lines title "Tahoe Flow1", \
 "dat/rtt_avg_smooth.dat" using 1:3 with lines title "Tahoe Flow2", \
 "dat/rtt_avg_smooth.dat" using 1:4 with lines title "Reno Flow1",  \
 "dat/rtt_avg_smooth.dat" using 1:5 with lines title "Reno Flow2",  \
 "dat/rtt_avg_smooth.dat" using 1:6 with lines title "Vegas Flow1", \
 "dat/rtt_avg_smooth.dat" using 1:7 with lines title "Vegas Flow2"
