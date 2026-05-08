from copy import deepcopy
from ..metrics.metrics import calculate_metrics


def round_robin(processes, quantum):
    processes = deepcopy(processes)
    processes = sorted(processes, key=lambda x: (x["arrival"], x["id"]))

    # Guard: quantum must be >= 1
    if quantum <= 0:
        quantum = 1

    time               = 0
    queue              = []          # ready queue  (list of process dicts)
    gantt              = []
    ready_queue_history = []         # snapshot of queue IDs before each dispatch
    n                  = len(processes)
    i                  = 0
    completed          = 0

    while completed < n:

        # Enqueue all processes that have arrived by 'time'
        while i < n and processes[i]["arrival"] <= time:
            queue.append(processes[i])
            i += 1

        if not queue:
            # CPU is idle — jump to the next arrival
            next_time = processes[i]["arrival"] if i < n else time + 1
            gantt.append(("IDLE", time, next_time))
            time = next_time
            continue

        # ── snapshot the ready queue BEFORE dispatching ──────────────────────
        ready_queue_history.append([p["id"] for p in queue])

        p = queue.pop(0)

        if p["start"] == -1:
            p["start"] = time

        exec_time = min(quantum, p["remaining"])
        gantt.append((p["id"], time, time + exec_time))

        time           += exec_time
        p["remaining"] -= exec_time

        # Enqueue processes that arrived during this slice
        while i < n and processes[i]["arrival"] <= time:
            queue.append(processes[i])
            i += 1

        if p["remaining"] > 0:
            queue.append(p)          # re-queue unfinished process
        else:
            p["completion"] = time
            completed += 1

    metrics = calculate_metrics(processes)
    return gantt, ready_queue_history, metrics