from copy import deepcopy
from ..metrics.metrics import calculate_metrics
def round_robin(processes, quantum):
    processes = deepcopy(processes)
    processes = sorted(processes, key=lambda x: (x["arrival"], x["id"]))
    if quantum <= 0:
        quantum = 1
    time = 0
    queue= []
    gantt = []
    ready_queue_history = [] 
    n= len(processes)
    i= 0
    completed= 0

    while completed < n:
        while i < n and processes[i]["arrival"] <= time:
            queue.append(processes[i])
            i += 1
        if not queue:
            next_time = processes[i]["arrival"] if i < n else time + 1
            gantt.append(("IDLE", time, next_time))
            time = next_time
            continue
        ready_queue_history.append([p["id"] for p in queue])
        p = queue.pop(0)
        if p["start"] == -1:
            p["start"] = time

        exec_time = min(quantum, p["remaining"])
        gantt.append((p["id"], time, time + exec_time))
        time+= exec_time
        p["remaining"] -= exec_time
        while i < n and processes[i]["arrival"] <= time:
            queue.append(processes[i])
            i += 1

        if p["remaining"] > 0:
            queue.append(p)
        else:
            p["completion"] = time
            completed += 1

    metrics = calculate_metrics(processes)
    return gantt, ready_queue_history, metrics
