from copy import deepcopy
from ..metrics.metrics import calculate_metrics


# ─── helpers ──────────────────────────────────────────────────────────────────

def compress_gantt(gantt):
    """Merge consecutive identical process segments."""
    if not gantt:
        return []
    compressed = [list(gantt[0])]
    for pid, start, end in gantt[1:]:
        if pid == compressed[-1][0] and start == compressed[-1][2]:
            compressed[-1][2] = end
        else:
            compressed.append([pid, start, end])
    return [tuple(x) for x in compressed]


# ─── scheduler ────────────────────────────────────────────────────────────────

def srtf(processes):
    processes = deepcopy(processes)

    time      = 0
    completed = 0
    n         = len(processes)
    gantt     = []

    while completed < n:

        ready = [p for p in processes
                 if p["arrival"] <= time and p["remaining"] > 0]

        if not ready:
            future = [p["arrival"] for p in processes
                      if p["remaining"] > 0 and p["arrival"] > time]
            if future:
                next_time = min(future)
                gantt.append(("IDLE", time, next_time))
                time = next_time
            else:
                time += 1
            continue

        # Pick process with shortest remaining time; break ties by arrival then id
        p = min(ready, key=lambda x: (x["remaining"], x["arrival"], x["id"]))

        if p["start"] == -1:
            p["start"] = time

        gantt.append((p["id"], time, time + 1))
        p["remaining"] -= 1
        time           += 1

        if p["remaining"] == 0:
            p["completion"] = time
            completed      += 1

    gantt   = compress_gantt(gantt)
    metrics = calculate_metrics(processes)
    return gantt, processes, metrics