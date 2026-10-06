#!/usr/bin/env python3
"""Runs INSIDE the EMANE container. Tells every NEM who it can hear.

Reads generated/pathloss.json (made by bridge.py from the same 500 m rule
as Part 1) and publishes one EMANE Pathloss event per receiving NEM.
"""

import json
import sys

from emane.events import EventService, PathlossEvent

table = json.load(open(sys.argv[1]))
device = sys.argv[2] if len(sys.argv) > 2 else "br0"
service = EventService(("224.1.2.8", 45703, device))

for receiver, row in table.items():
    event = PathlossEvent()
    for sender, loss in row.items():
        event.append(int(sender), forward=loss, reverse=loss)
    service.publish(int(receiver), event)

print(f"published pathloss for {len(table)} NEMs on {device}")
