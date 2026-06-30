# Light Suppression Analysis Tools

Install dependencies:

```bash
pip install -r requirements.txt
```

Compare debug CSV files:

```bash
python compare_debug_csv.py --input spawn=../data/spawn_light_schedule_debug.csv --input nonspawn=../data/non_spawn_light_schedule_debug.csv --output ../output/debug
```



Compare batch CSV files:

```bash
python compare_batch_csv.py --input spawn=../data/spawn_light_schedule_debug_batches.csv --input nonspawn=../data/nonspawn_light_schedule_debug_batches.csv --output ../output/batch
```

Batch comparison outputs `top1Ratio` through `top5Ratio` as individual chunk ratios, and `top5SumRatio` as the cumulative ratio of the top 5 chunks.



Plot selected time series:

```bash
python plot_timeseries.py --input spawn=../data/spawn_light_schedule_debug.csv --input nonspawn=../data/non_spawn_light_schedule_debug.csv --columns avgRunUpdMs,nodes,blkDec,blkInc --rolling 30 --output ../output/core_timeseries.png
```




Render chunk frequency heatmap:

```bash
python plot_chunk_frequency.py --input ../data/spawn_light_schedule_debug_batches.csv --highlight=-2,-2:0,4 --annotate --output ../output/spawn_chunk_frequency.png
```


Render ticket plane:

```bash
python plot_ticket_plane.py --range=-12,-12:12,12 --start-ticket=0,0,START --highlight=-2,-2:0,4 --annotate --output ../output/spawn_ticket_plane.png
```

Render debug ticket plane:

```bash
python plot_ticket_plane.py --range=58,60:64,70 --ticket=62,64,11,DEBUG --highlight=60,62:62,68 --annotate --output ../output/debug_ticket_plane.png
```

Render portal and player tickets:

```bash
python plot_ticket_plane.py --range=49,53:73,77 --portal-ticket=61,65,PORTAL --player-ticket=61,65,10,PLAYER --highlight=60,62:62,68 --annotate --output ../output/portal_player_ticket_plane.png
```

`--ticket x,z,radius,label` is interpreted as a region ticket with center level `33 - radius`, then propagated outward until level 33. Use `--level-ticket x,z,level,label` for explicit center levels.

`--player-ticket x,z,viewDistance,label` draws the player loading ticket field. In 1.20.4, this is level 31 for all chunks within view distance, then it propagates outward to 32 and 33. The dashed boundary is the level 31 source field; the solid boundary is the propagated level 33 boundary. Use `--mode effective` for the minimum effective level field, `--mode separate` for one panel per ticket, or `--mode both` for both views.

By default, `*_light_schedule_debug.csv` tools filter inactive rows where the machine has not started producing light work. Use `--no-filter-active` to keep all rows.

Time series tools use `--x-axis recordMs` by default when available. Use `--x-axis normalized` to align files with different durations by recording progress from 0 to 1, `--x-axis sample` for raw row index, or `--x-axis tick` for the CSV tick column.
