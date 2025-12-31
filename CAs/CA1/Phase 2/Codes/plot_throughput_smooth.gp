set terminal pngcairo size 1200,700
set output "plots/throughput_smooth.png"
set title "Smoothed Average Throughput (5s moving average)"
set xlabel "Time (s)"
set ylabel "Throughput (Mbps)"
set key outside
set grid

plot \
 "dat/throughput_avg_smooth.dat" using 1:2 with lines title "Tahoe Flow1", \
 "dat/throughput_avg_smooth.dat" using 1:3 with lines title "Tahoe Flow2", \
 "dat/throughput_avg_smooth.dat" using 1:4 with lines title "Reno Flow1",  \
 "dat/throughput_avg_smooth.dat" using 1:5 with lines title "Reno Flow2",  \
 "dat/throughput_avg_smooth.dat" using 1:6 with lines title "Vegas Flow1", \
 "dat/throughput_avg_smooth.dat" using 1:7 with lines title "Vegas Flow2"
