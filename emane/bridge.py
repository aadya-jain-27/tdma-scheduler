#!/usr/bin/env python3
"""Integration bridge: Part 1 schedule (JSON) -> files EMANE understands.

Input : the JSON written by  schedule.py --json-out schedule.json
Output (in emane/generated/):
  schedule.xml       EMANE TDMA schedule (sent with emaneevent-tdmaschedule)
  platformN.xml      one EMANE platform file per radio (NEM id N)
  pathloss.json      who can hear whom, same 500 m rule as Part 1
  nodes.txt          "nem_id node_name ip" lines for the run script

Mapping used everywhere:
  Node_01 -> NEM 1 -> radio IP 10.100.0.1, Node_02 -> NEM 2 -> 10.100.0.2, ...
  Our slot s        -> EMANE slot index s (1 ms each, slotduration=1000 us)
  Our frame length  -> EMANE "slots" per frame

Usage:
  python3 emane/bridge.py output/schedule.json
  python3 emane/bridge.py output/schedule.json --naive   # deliberately bad
"""

import argparse
import json
import math
import os
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))

SLOT_US = int(os.environ.get("SLOT_US", 1000))   # 1 ms slots, as the assignment asks
FREQUENCY = "2.4G"        # single shared channel
DATARATE = "10M"          # 10 Mbit/s x 1 ms = 1250 bytes per slot, fits a ping
IN_RANGE_DB = 90.0        # pathloss for radios within range: strong signal
OUT_OF_RANGE_DB = 200.0   # pathloss for radios out of range: never heard


def naive_one_hop_schedule(data):
    """A deliberately WRONG schedule for comparison: it only keeps direct
    neighbours apart (distance-1) and ignores hidden terminals. EMANE should
    show packet loss with this one and not with ours."""
    pos, rng = data["positions"], data["radio_range_m"]
    names = data["nodes"]
    slots = {}
    for a in names:
        taken = {slots[b] for b in slots if math.dist(pos[a], pos[b]) <= rng}
        s = 0
        while s in taken:
            s += 1
        slots[a] = s
    return slots


def schedule_xml(names, node_to_slot):
    frame = max(node_to_slot.values()) + 1
    root = ET.Element("emane-tdma-schedule")
    ET.SubElement(root, "structure", frames="1", slots=str(frame),
                  slotoverhead="0", slotduration=str(SLOT_US), bandwidth="1M")
    multiframe = ET.SubElement(root, "multiframe", frequency=FREQUENCY,
                               power="0", **{"class": "0"}, datarate=DATARATE)
    fr = ET.SubElement(multiframe, "frame", index="0")
    for s in range(frame):
        nems = [str(names.index(n) + 1) for n in names if node_to_slot[n] == s]
        # A slot listing several NEMs is spatial reuse: they all transmit at once.
        # Every NEM listens (rx) in every slot where it is not listed.
        ET.SubElement(fr, "slot", index=str(s), nodes=",".join(nems))
    ET.indent(root)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"


def platform_xml(nem_id):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE platform SYSTEM "file:///usr/share/emane/dtd/platform.dtd">
<platform>
  <param name="otamanagerchannelenable" value="on"/>
  <param name="otamanagerdevice" value="backchan0"/>
  <param name="otamanagergroup" value="224.1.2.8:45702"/>
  <param name="eventservicedevice" value="backchan0"/>
  <param name="eventservicegroup" value="224.1.2.8:45703"/>
  <param name="controlportendpoint" value="0.0.0.0:47000"/>
  <nem id="{nem_id}" definition="tdmanem.xml">
    <transport definition="transvirtual.xml">
      <param name="device" value="emane0"/>
      <param name="address" value="10.100.0.{nem_id}"/>
      <param name="mask" value="255.255.255.0"/>
    </transport>
  </nem>
</platform>
"""


def pathloss_table(data):
    pos, rng, names = data["positions"], data["radio_range_m"], data["nodes"]
    table = {}
    for i, a in enumerate(names, 1):
        table[i] = {j: (IN_RANGE_DB if math.dist(pos[a], pos[b]) <= rng else OUT_OF_RANGE_DB)
                    for j, b in enumerate(names, 1) if j != i}
    return table


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("schedule_json")
    p.add_argument("--out", default=os.path.join(HERE, "generated"))
    p.add_argument("--naive", action="store_true",
                   help="write the distance-1 only schedule instead (for comparison)")
    args = p.parse_args()

    with open(args.schedule_json) as f:
        data = json.load(f)
    if not data.get("verified"):
        raise SystemExit("refusing: Part 1 did not verify this schedule as conflict-free")

    names = data["nodes"]
    node_to_slot = naive_one_hop_schedule(data) if args.naive else data["node_to_slot"]
    os.makedirs(args.out, exist_ok=True)

    with open(os.path.join(args.out, "schedule.xml"), "w") as f:
        f.write(schedule_xml(names, node_to_slot))
    for nem_id in range(1, len(names) + 1):
        with open(os.path.join(args.out, f"platform{nem_id}.xml"), "w") as f:
            f.write(platform_xml(nem_id))
    with open(os.path.join(args.out, "pathloss.json"), "w") as f:
        json.dump(pathloss_table(data), f, indent=1)
    with open(os.path.join(args.out, "nodes.txt"), "w") as f:
        for nem_id, name in enumerate(names, 1):
            f.write(f"{nem_id} {name} 10.100.0.{nem_id} slot={node_to_slot[name]}\n")

    kind = "NAIVE distance-1" if args.naive else "optimized distance-2"
    frame = max(node_to_slot.values()) + 1
    print(f"wrote {kind} schedule: {len(names)} NEMs, {frame} slots x {SLOT_US} us "
          f"= {frame * SLOT_US / 1000:.0f} ms frame -> {args.out}")


if __name__ == "__main__":
    main()
