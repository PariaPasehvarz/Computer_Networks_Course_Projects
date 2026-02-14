set packetSize 1000

# Scenario selection
# 1 = TCP only
# 2 = TCP + UDP (no control)
# 3 = TCP + UDP (TCP-Friendly)

if {$argc > 0} {
    set scenario [lindex $argv 0]
} else {
    set scenario 1
}

# Simulator setup
set ns [new Simulator]

set tf [open out_$scenario.tr w]
$ns trace-all $tf

set nf [open out.nam w]
$ns namtrace-all $nf


# Create nodes
set n0 [$ns node]   ;# TCP sender
set n1 [$ns node]   ;# UDP sender
set r1 [$ns node]
set r2 [$ns node]
set n2 [$ns node]   ;# Receiver

# Links
$ns duplex-link $n0 $r1 10Mb 10ms DropTail
$ns duplex-link $n1 $r1 10Mb 10ms DropTail
$ns duplex-link $r1 $r2 1Mb 50ms DropTail   ;# Bottleneck
$ns duplex-link $r2 $n2 10Mb 10ms DropTail

$ns queue-limit $r1 $r2 20
set qmon [$ns monitor-queue $r1 $r2 ""]

# TCP flow
set tcp [new Agent/TCP]
$tcp set class_ 1
set sink [new Agent/TCPSink]

$ns attach-agent $n0 $tcp
$ns attach-agent $n2 $sink
$ns connect $tcp $sink

set ftp [new Application/FTP]
$ftp attach-agent $tcp

# UDP flow
if {$scenario != 1} {

    set udp [new Agent/UDP]
    set null [new Agent/Null]

    $ns attach-agent $n1 $udp
    $ns attach-agent $n2 $null
    $ns connect $udp $null

    set cbr [new Application/Traffic/CBR]
    $cbr attach-agent $udp
    $cbr set packetSize_ 1000
    $cbr set rate_ 1Mb
}

# TCP-Friendly Rate Control
set rate 1e6
set packetSize 1000
set last_loss 0

proc rate_control {} {
    global ns cbr packetSize rate last_loss

    set now [$ns now]

    if {$last_loss == 1} {
        set rate [expr $rate * 0.85]
        set last_loss 0
    } else {
        set rate [expr $rate * 1.01]
    }

    if {$rate < 0.2e6} { set rate 0.2e6 }
    if {$rate > 2e6}   { set rate 2e6 }

    set interval [expr ($packetSize * 8.0) / $rate]
    $cbr set interval_ $interval

    $ns at [expr $now + 0.1] "rate_control"
}

proc loss_event {} {
    global last_loss
    set last_loss 1
}

proc check_congestion {} {
    global ns qmon last_loss

    # current queue size
    set qsize [$qmon set pkts_]

    # if queue is near full → congestion
    if {$qsize >= 18} {
        set last_loss 1
    }

    $ns at [expr [$ns now] + 0.05] "check_congestion"
}

# Detect packet loss
proc detect_loss {} {
    global loss_detected
    set loss_detected 1
}

# Start traffic
$ns at 0.5 "$ftp start"

if {$scenario != 1} {
    $ns at 0.5 "$cbr start"
}

if {$scenario == 3} {
    $ns at 0.6 "rate_control"
    $ns at 0.6 "check_congestion"
}

# Stop simulation
$ns at 20.0 "finish"

proc finish {} {
    global ns tf nf
    $ns flush-trace
    close $tf
    close $nf
#    exec nam out.nam &
    exit 0
}

$ns run
close $tf