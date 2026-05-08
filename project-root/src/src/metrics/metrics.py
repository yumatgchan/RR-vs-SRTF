def calculate_metrics(processes):
    metrics = {}
    n = len(processes)
    
    if n == 0:
        return {}
        
    total_wt = total_tat = total_rt = 0
    
    for p in processes:
        tat = p["completion"] - p["arrival"]
        wt  = tat - p["burst"]
        rt  = p["start"] - p["arrival"]
        
        metrics[p["id"]] = {
            "TAT": round(tat, 2),
            "WT" : round(wt,  2),
            "RT" : round(rt,  2),
        }
        
        total_wt  += wt
        total_tat += tat
        total_rt  += rt

    metrics["__avg__"] = {
        "TAT": round(total_tat / n, 2),
        "WT" : round(total_wt  / n, 2),
        "RT" : round(total_rt  / n, 2),
    }
    return metrics
