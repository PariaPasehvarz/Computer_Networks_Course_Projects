set terminal pngcairo size 1200,700
set output "plots/loss_smooth.png"
set title "Smoothed Packet Loss Rate at Bottleneck (10s moving average)"
set xlabel "Time (s)"
set ylabel "Loss rate (%)"
set key outside
set grid

# Optional: zoom to see differences better (comment out if you want full range)
# set yrange [0:5]

plot \
 "dat/loss_avg_smooth.dat" using 1:2 with lines title "Tahoe Flow1", \
 "dat/loss_avg_smooth.dat" using 1:3 with lines title "Tahoe Flow2", \
 "dat/loss_avg_smooth.dat" using 1:4 with lines title "Reno Flow1",  \
 "dat/loss_avg_smooth.dat" using 1:5 with lines title "Reno Flow2",  \
 "dat/loss_avg_smooth.dat" using 1:6 with lines title "Vegas Flow1", \
 "dat/loss_avg_smooth.dat" using 1:7 with lines title "Vegas Flow2"
