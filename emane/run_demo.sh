#!/usr/bin/env bash
# Runs INSIDE the EMANE container (needs --privileged for network namespaces).
#
#   docker build -t tdma-emane emane/
#   docker run --rm -it --privileged -v "$PWD":/work tdma-emane bash emane/run_demo.sh
#
# What it does, step by step:
#   1. Make a schedule with Part 1 and convert it with the bridge.
#   2. Give every radio its own Linux network namespace (its own "computer").
#   3. Start one EMANE process per radio.
#   4. Tell EMANE who can hear whom (pathloss) and send it OUR TDMA schedule.
#   5. All radios ping all their neighbours AT THE SAME TIME, and we record loss.
#   6. Repeat with a naive distance-1 schedule. Hidden terminals should cause loss.
set -euo pipefail
cd /work
GEN=emane/generated
NODES=${NODES:-examples/grid_4x4.json}

start_network() {
  local n=$1
  ip link add br0 type bridge 2>/dev/null || true
  echo 0 > /sys/class/net/br0/bridge/multicast_snooping
  ip addr add 10.99.0.254/24 dev br0 2>/dev/null || true
  ip link set br0 up
  ip route add 224.0.0.0/4 dev br0 2>/dev/null || true
  for i in $(seq 1 "$n"); do
    ip netns add "n$i"
    ip link add "veth$i" type veth peer name backchan0 netns "n$i"
    ip link set "veth$i" master br0 up
    ip netns exec "n$i" ip addr add "10.99.0.$i/24" dev backchan0
    ip netns exec "n$i" ip link set backchan0 up
    ip netns exec "n$i" ip link set lo up
    ip netns exec "n$i" ip route add 224.0.0.0/4 dev backchan0
  done
}

start_emane() {
  local n=$1
  for i in $(seq 1 "$n"); do
    (cd $GEN && ip netns exec "n$i" emane "platform$i.xml" \
        -r -d -l 3 -f "/tmp/emane$i.log" --pidfile "/tmp/emane$i.pid")
  done
  sleep 3
}

stop_all() {
  local n=$1
  for i in $(seq 1 "$n"); do
    [ -f "/tmp/emane$i.pid" ] && kill "$(cat /tmp/emane$i.pid)" 2>/dev/null || true
    ip netns del "n$i" 2>/dev/null || true
  done
}

run_round() {   # $1 = label, rest = extra bridge flags
  local label=$1; shift
  python3 emane/bridge.py output/emane_input.json "$@"
  cp emane/config/*.xml $GEN/          # NEM, MAC and transport profiles next to the platform files
  local n; n=$(wc -l < $GEN/nodes.txt)
  start_network "$n"
  start_emane "$n"
  python3 emane/publish_pathloss.py $GEN/pathloss.json br0
  emaneevent-tdmaschedule -i br0 $GEN/schedule.xml
  sleep 2
  python3 emane/traffic_test.py output/emane_input.json "$label"
  for i in $(seq 1 "$n"); do                      # proof: per-slot TX/RX counters
    ip netns exec "n$i" emanesh localhost get table nems mac TxSlotStatusTable \
        > "output/emane_raw/${label}_tx_nem$i.txt" 2>&1 || true
    ip netns exec "n$i" emanesh localhost get table nems mac \
        > "output/emane_raw/${label}_drops_nem$i.txt" 2>&1 || true
    ip netns exec "n$i" emanesh localhost get table nems phy PathlossEventInfoTable ReceivePowerTable \
        >> "output/emane_raw/${label}_drops_nem$i.txt" 2>&1 || true
  done
  stop_all "$n"
}

mkdir -p output/emane_raw
python3 schedule.py --file "$NODES" --json-out output/emane_input.json > output/emane_part1.txt
run_round "optimized${SUFFIX:-}"
run_round "naive${SUFFIX:-}" --naive
echo "done: see output/emane_results_*.txt"
