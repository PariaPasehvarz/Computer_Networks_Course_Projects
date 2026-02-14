# Usage:
#   ns phase2.tcl <Tahoe|Reno|Vegas> <seed> <outPrefix>
# Example:
#   ns phase2.tcl Reno 3 out/Reno_3

if {$argc < 3} {
    puts "Usage: ns $argv0 <Tahoe|Reno|Vegas> <seed> <outPrefix>"
    exit 1
}

set tcpType   [lindex $argv 0]
set seed      [lindex $argv 1]
set outPrefix [lindex $argv 2]

# Random seed
ns-random $seed

set ns [new Simulator]

# --------- Outputs ----------
file mkdir [file dirname $outPrefix]

set tr [open "${outPrefix}.tr" w]
$ns trace-all $tr

# Queue trace on bottleneck (for per-flow drops)
set qtr [open "${outPrefix}_q.tr" w]

# RTT logs (per-flow, per-second)
set rtt1 [open "${outPrefix}_rtt_f1.dat" w]
set rtt2 [open "${outPrefix}_rtt_f2.dat" w]

# Receiver bytes logs (cumulative bytes; we convert to throughput later)
set b1 [open "${outPrefix}_bytes_f1.dat" w]
set b2 [open "${outPrefix}_bytes_f2.dat" w]

# --------- Global settings ----------
# Queue size = 10 packets (routers have DropTail queues)
Queue/DropTail set limit_ 10

# TCP payload size = 1000 bytes (project default)
Agent/TCP set packetSize_ 1000

# TTL = 64 (if your ns2 build errors on this line, comment it out and mention in report)
catch { Agent set ttl_ 64 }

# --------- Topology nodes ----------
# Create in this order so IDs are stable: 1,2,routerL,routerR,5,6
set n1 [$ns node]
set n2 [$ns node]
set rL [$ns node]
set rR [$ns node]
set n5 [$ns node]
set n6 [$ns node]

# --------- Links ----------
# As in the figure: 100Mb 5ms (top), 100Mb variable delay (bottom),
# bottleneck 100Kb 1ms, right side similarly. :contentReference[oaicite:3]{index=3}
$ns duplex-link $n1 $rL 100Mb 5ms DropTail
$ns duplex-link $n2 $rL 100Mb 5ms DropTail      ;# initial, will randomize
$ns duplex-link $rL $rR 100Kb 1ms DropTail
$ns duplex-link $rR $n5 100Mb 5ms DropTail
$ns duplex-link $rR $n6 100Mb 5ms DropTail      ;# initial, will randomize

# Trace the bottleneck queue (drops happen here because buffer is limited)
$ns trace-queue $rL $rR $qtr

# --------- Random variable delay (5..25ms) ----------
set rv [new RandomVariable/Uniform]
$rv set min_ 5
$rv set max_ 25

proc varyDelay {ns linkAB linkBA rv interval} {
    set d [$rv value]
    $linkAB set delay_ "${d}ms"
    $linkBA set delay_ "${d}ms"
    set t [expr [$ns now] + $interval]
    $ns at $t "varyDelay $ns $linkAB $linkBA $rv $interval"
}

# Make both directions variable for the two "variable delay" links
set l_n2_rL [$ns link $n2 $rL]
set l_rL_n2 [$ns link $rL $n2]
set l_rR_n6 [$ns link $rR $n6]
set l_n6_rR [$ns link $n6 $rR]

# Assumption: update delay every 0.5s (mention this in report as a chosen randomness granularity)
$ns at 0.0 "varyDelay $ns $l_n2_rL $l_rL_n2 $rv 0.5"
$ns at 0.0 "varyDelay $ns $l_rR_n6 $l_n6_rR $rv 0.5"

# --------- Choose TCP agent ----------
proc makeTcp {tcpType} {
    if {$tcpType == "Tahoe"} { return [new Agent/TCP] }
    if {$tcpType == "Reno"}  { return [new Agent/TCP/Reno] }
    if {$tcpType == "Vegas"} { return [new Agent/TCP/Vegas] }
    puts "Unknown TCP type: $tcpType"
    exit 1
}

# Flow 1: n1 -> n5
set tcp1 [makeTcp $tcpType]
$tcp1 set fid_ 1
set sink1 [new Agent/TCPSink]
$ns attach-agent $n1 $tcp1
$ns attach-agent $n5 $sink1
$ns connect $tcp1 $sink1

# Flow 2: n2 -> n6
set tcp2 [makeTcp $tcpType]
$tcp2 set fid_ 2
set sink2 [new Agent/TCPSink]
$ns attach-agent $n2 $tcp2
$ns attach-agent $n6 $sink2
$ns connect $tcp2 $sink2

# Always-on sending
set ftp1 [new Application/FTP]
$ftp1 attach-agent $tcp1
set ftp2 [new Application/FTP]
$ftp2 attach-agent $tcp2

# --------- Logging helpers ----------
proc logEverySec {ns sec tcp sink rttFile bytesFile} {
    set t $sec

    if {[catch {$tcp set srtt_} val] == 0} {
        puts $rttFile "$t $val"
    } else {
        puts $rttFile "$t 0"
    }

    puts $bytesFile "$t [$sink set bytes_]"

    set next [expr {$sec + 1}]
    if {$next <= 1000} {
        $ns at $next "logEverySec $ns $next $tcp $sink $rttFile $bytesFile"
    }
}

$ns at 1 "logEverySec $ns 1 $tcp1 $sink1 $rtt1 $b1"
$ns at 1 "logEverySec $ns 1 $tcp2 $sink2 $rtt2 $b2"


# --------- Run ----------
set SIM_TIME 1000.0
set END_TIME [expr {$SIM_TIME + 0.01}]

$ns at 0.1 "$ftp1 start"
$ns at 0.1 "$ftp2 start"

# stop apps at SIM_TIME
$ns at $SIM_TIME "$ftp1 stop"
$ns at $SIM_TIME "$ftp2 stop"

# finish slightly later than SIM_TIME
$ns at $END_TIME "finish"


proc finish {} {
    global ns tr qtr rtt1 rtt2 b1 b2
    $ns flush-trace
    close $tr
    close $qtr
    close $rtt1
    close $rtt2
    close $b1
    close $b2
    exit 0
}

$ns run
