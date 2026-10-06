EMANE results, 4x4 grid, 84 one-hop links, 50 pings per link

| Run | Schedule | Average loss | Links with 0% loss | Collision drops (SINR, bytes) | Timing drops (Slot Error + Long, bytes) |
|---|---|---|---|---|---|
| 1 ms slots | distance-2 (ours) | 9.9% | 37 / 84 | 0 | 166082 |
| 1 ms slots | one-hop (naive) | 63.8% | 0 / 84 | 1078 | 1053460 |
| 5 ms slots | distance-2 (ours) | 0.0% | 84 / 84 | 0 | 0 |
| 5 ms slots | one-hop (naive) | 61.4% | 0 / 84 | 20688 | 0 |
