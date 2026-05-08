import tkinter as tk
from tkinter import messagebox
from copy import deepcopy
from ..scheduler.round_robin import round_robin
from ..scheduler.srtf import srtf
from ..util.validator import build_processes, validate_quantum
id_entries = []
arrival_entries = []
burst_entries = []
def create_inputs():
    global arrival_entries, burst_entries, id_entries
    for widget in inputs_frame.winfo_children():
        widget.destroy()

    arrival_entries = []
    burst_entries = []
    id_entries = []

    try:
        n = int(num_entry.get())
    except ValueError:
        messagebox.showerror("Error", "Enter valid number of processes")
        return

    for i in range(n):
        tk.Label(inputs_frame, text="ID").grid(row=i, column=0, padx=4)
        pid = tk.Entry(inputs_frame, width=8)
        pid.grid(row=i, column=1, padx=4)

        tk.Label(inputs_frame, text="Arrival").grid(row=i, column=2, padx=4)
        a = tk.Entry(inputs_frame, width=8)
        a.grid(row=i, column=3, padx=4)

        tk.Label(inputs_frame, text="Burst").grid(row=i, column=4, padx=4)
        b = tk.Entry(inputs_frame, width=8)
        b.grid(row=i, column=5, padx=4)

        id_entries.append(pid)
        arrival_entries.append(a)
        burst_entries.append(b)

def draw_gantt(canvas, gantt, y_offset=0, title=""):
    canvas.create_text(10, 10 + y_offset, text=title, anchor="w",
                       font=("Arial", 10, "bold"))
    if not gantt:
        return 0

    x     = 10
    scale = 60
    max_x = 0

    for p, start, end in gantt:
        fill = "#e0e0e0" if p == "IDLE" else "white"
        width = max(1, (end - start) * scale)

        canvas.create_rectangle(x, 28 + y_offset, x + width, 75 + y_offset,fill=fill, outline="black")
        canvas.create_text(x + width / 2, 51 + y_offset, text=p, font=("Arial", 9))
        canvas.create_text(x, 85 + y_offset, text=str(start), font=("Arial", 8))
        max_x = max(max_x, x + width)
        x+= width
    canvas.create_text(x, 85 + y_offset, text=str(gantt[-1][2]),
                       font=("Arial", 8))
    return max_x

def display_ready_queue(frame, ready_queue_history):
    for widget in frame.winfo_children():
        widget.destroy()

    tk.Label(frame, text="RR – Ready Queue",
             font=("Arial", 10, "bold"), relief="ridge",
             bg="#d0d0d0", pady=3
             ).grid(row=0, column=0, columnspan=2, sticky="ew")

    for col, h in enumerate(["Dispatch #", "Queue  (front -> back)"]):
        tk.Label(frame, text=h, font=("Arial", 9, "bold"),
                 relief="ridge", width=14 if col == 0 else 40,
                 bg="#ebebeb", pady=3
                 ).grid(row=1, column=col, sticky="nsew")

    for idx, snapshot in enumerate(ready_queue_history, start=1):
        queue_str = "  ->  ".join(snapshot) if snapshot else "(empty)"
        bg = "white" if idx % 2 == 0 else "#f7f7f7"
        tk.Label(frame, text=f"#{idx}", relief="ridge", width=14,
                 bg=bg, pady=2).grid(row=idx + 1, column=0, sticky="nsew")
        tk.Label(frame, text=queue_str, relief="ridge", width=40,
                 bg=bg, pady=2, anchor="w", padx=6
                 ).grid(row=idx + 1, column=1, sticky="nsew")

def display_comparison_table(frame, rr_metrics, srtf_metrics):
    for widget in frame.winfo_children():
        widget.destroy()

    tk.Label(frame, text="Comparison Table",
             font=("Arial", 10, "bold"), relief="ridge",
             bg="#d0d0d0", pady=3
             ).grid(row=0, column=0, columnspan=9, sticky="ew")

    headers = ["Process","RR - WT",  "RR - TAT",  "RR - RT",  "","SRTF - WT","SRTF - TAT","SRTF - RT"]

    for col, h in enumerate(headers):
        tk.Label(frame, text=h, font=("Arial", 9, "bold"),
                 relief="ridge", width=11,
                 bg="#ebebeb", pady=3
                 ).grid(row=1, column=col, sticky="nsew")

    all_ids = sorted(
        set(k for k in rr_metrics   if k != "__avg__") |
        set(k for k in srtf_metrics if k != "__avg__")
    )

    for row, pid in enumerate(all_ids, start=2):
        rr = rr_metrics.get(pid,   {})
        sm = srtf_metrics.get(pid, {})
        bg = "white" if row % 2 == 0 else "#f7f7f7"

        vals = [pid,
                rr.get("WT","-"), rr.get("TAT","-"), rr.get("RT","-"),
                "",
                sm.get("WT","-"), sm.get("TAT","-"), sm.get("RT","-")]

        for col, v in enumerate(vals):
            tk.Label(frame, text=v, relief="ridge", width=11,
                     bg=bg, pady=2).grid(row=row, column=col, sticky="nsew")

    avg_row  = len(all_ids) + 2
    rr_avg   = rr_metrics.get("__avg__",   {})
    srtf_avg = srtf_metrics.get("__avg__", {})

    avg_vals = ["Average",
                rr_avg.get("WT","-"),   rr_avg.get("TAT","-"),   rr_avg.get("RT","-"),
                "",
                srtf_avg.get("WT","-"), srtf_avg.get("TAT","-"), srtf_avg.get("RT","-")]

    for col, v in enumerate(avg_vals):
        tk.Label(frame, text=v, font=("Arial", 9, "bold"),
                 relief="ridge", width=11,
                 bg="#d0d0d0", pady=3
                 ).grid(row=avg_row, column=col, sticky="nsew")

def display_gantt_details(frame, rr_gantt, srtf_gantt):
    for widget in frame.winfo_children():
        widget.destroy()

    tk.Label(frame, text="Gantt Chart Details",
             font=("Arial", 10, "bold"), relief="ridge",
             bg="#d0d0d0", pady=3
             ).grid(row=0, column=0, columnspan=5, sticky="ew")

    for col, h in enumerate(["Algorithm","Process","Start","End","Duration"]):
        tk.Label(frame, text=h, font=("Arial", 9, "bold"),
                 relief="ridge", width=13,
                 bg="#ebebeb", pady=3
                 ).grid(row=1, column=col, sticky="nsew")

    row = 2
    for algo, gantt in [("Round Robin", rr_gantt), ("SRTF", srtf_gantt)]:
        first = True
        for pid, start, end in gantt:
            bg         = "white" if row % 2 == 0 else "#f7f7f7"
            algo_label = algo if first else ""
            first      = False
            for col, v in enumerate([algo_label, pid, start, end, end - start]):
                tk.Label(frame, text=v, relief="ridge", width=13,
                         bg=bg, pady=2).grid(row=row, column=col, sticky="nsew")
            row += 1

        for col in range(5):
            tk.Label(frame, text="", relief="flat", width=13,
                     bg="white").grid(row=row, column=col, sticky="nsew")
        row += 1
def display_best_algorithm(frame, rr_metrics, srtf_metrics):
    for widget in frame.winfo_children():
        widget.destroy()

    rr_avg   = rr_metrics.get("__avg__",   {})
    srtf_avg = srtf_metrics.get("__avg__", {})

    rr_wins = srtf_wins = 0
    for key in ("WT", "TAT", "RT"):
        try:
            rv = float(rr_avg.get(key, 0))
            sv = float(srtf_avg.get(key, 0))
            if rv < sv:
                rr_wins   += 1
            elif sv < rv:
                srtf_wins += 1
        except (TypeError, ValueError):
            pass

    if srtf_wins > rr_wins:
        best = "SRTF"
    elif rr_wins > srtf_wins:
        best = "Round Robin"
    else:
        best = "Tie (both equal)"

    tk.Label(frame,
             text=f"Best Algorithm:  {best}",
             font=("Arial", 11, "bold"),
             pady=6, padx=10,
             relief="ridge", bg="#d0d0d0"
             ).pack(fill="x")

scenarios = [
    {"name": "Scenario A",    "quantum": 3,
     "processes": [{"id":"P1","arrival":0,"burst":8},
                   {"id":"P2","arrival":1,"burst":4},
                   {"id":"P3","arrival":2,"burst":9},
                   {"id":"P4","arrival":3,"burst":5}]},
    {"name": "Scenario B(p1)","quantum": 2,
     "processes": [{"id":"P1","arrival":0,"burst":20},
                   {"id":"P2","arrival":0,"burst":3},
                   {"id":"P3","arrival":0,"burst":4}]},
    {"name": "Scenario B(p2)","quantum": 8,
     "processes": [{"id":"P1","arrival":0,"burst":20},
                   {"id":"P2","arrival":0,"burst":3},
                   {"id":"P3","arrival":0,"burst":4}]},
    {"name": "Scenario C",    "quantum": 3,
     "processes": [{"id":"P1","arrival":0,"burst":10},
                   {"id":"P2","arrival":1,"burst":1},
                   {"id":"P3","arrival":2,"burst":2},
                   {"id":"P4","arrival":3,"burst":1},
                   {"id":"P5","arrival":4,"burst":2}]},
    {"name": "Scenario D",    "quantum": 2,
     "processes": [{"id":"P1","arrival":0,"burst":20},
                   {"id":"P2","arrival":2,"burst":3},
                   {"id":"P3","arrival":4,"burst":3},
                   {"id":"P4","arrival":6,"burst":3}]},
    {"name": "Scenario E(p1)","quantum": 2,
     "processes": [{"id":"P1","arrival":0,"burst":5},
                   {"id":"P2","arrival":1,"burst":3}]},
    {"name": "Scenario E(p2)","quantum": 2,
     "processes": [{"id":"P1","arrival":-1,"burst":5},
                   {"id":"P2","arrival":1, "burst":3}]},
    {"name": "Scenario E(p3)","quantum": 2,
     "processes": [{"id":"P1","arrival":0,"burst":-3},
                   {"id":"P2","arrival":1,"burst":0}]},
    {"name": "Scenario E(p4)","quantum": 2,
     "processes": [{"id":"P1","arrival":0,"burst":5},
                   {"id":"P1","arrival":1,"burst":3}]},
    {"name": "Scenario E(p5)","quantum": 0,
     "processes": [{"id":"P1","arrival":0,"burst":5},
                   {"id":"P2","arrival":1,"burst":3}]},
]

def load_scenario(sc):
    global id_entries, arrival_entries, burst_entries
    for widget in inputs_frame.winfo_children():
        widget.destroy()
    id_entries = []; arrival_entries = []; burst_entries = []
    num_entry.delete(0, tk.END)
    num_entry.insert(0, len(sc["processes"]))
    quantum_entry.delete(0, tk.END)
    quantum_entry.insert(0, sc["quantum"])
    for i, p in enumerate(sc["processes"]):
        tk.Label(inputs_frame, text="ID").grid(row=i, column=0, padx=4)
        pid = tk.Entry(inputs_frame, width=8)
        pid.grid(row=i, column=1, padx=4)
        pid.insert(0, p["id"])

        tk.Label(inputs_frame, text="Arrival").grid(row=i, column=2, padx=4)
        a = tk.Entry(inputs_frame, width=8)
        a.grid(row=i, column=3, padx=4)
        a.insert(0, p["arrival"])

        tk.Label(inputs_frame, text="Burst").grid(row=i, column=4, padx=4)
        b = tk.Entry(inputs_frame, width=8)
        b.grid(row=i, column=5, padx=4)
        b.insert(0, p["burst"])

        id_entries.append(pid)
        arrival_entries.append(a)
        burst_entries.append(b)
    run()

def reset_all():
    global id_entries, arrival_entries, burst_entries

    for widget in inputs_frame.winfo_children():
        widget.destroy()

    id_entries = []; arrival_entries = []; burst_entries = []

    num_entry.delete(0, tk.END)
    quantum_entry.delete(0, tk.END)

    gantt_canvas.delete("all")
    gantt_canvas.configure(scrollregion=(0, 0, 0, 0))

    for f in (table_frame, gantt_detail_frame, ready_queue_frame, best_frame):
        for widget in f.winfo_children():
            widget.destroy()

def run():
    processes = build_processes(num_entry,id_entries, arrival_entries, burst_entries)
    if processes is None:
        return
    quantum = validate_quantum(quantum_entry)
    if quantum is None:
        return
    rr_p= deepcopy(processes)
    srtf_p = deepcopy(processes)
    rr_gantt,rr_queue_history, rr_metrics   = round_robin(rr_p,   quantum)
    srtf_gantt, _,srtf_metrics = srtf(srtf_p)
    gantt_canvas.delete("all")
    max_x1 = draw_gantt(gantt_canvas, rr_gantt,   0,   "Round Robin")
    max_x2 = draw_gantt(gantt_canvas, srtf_gantt, 130, "SRTF")
    total_width = max(max_x1, max_x2) + 40
    gantt_canvas.configure(scrollregion=(0, 0, total_width, 260))
    gantt_canvas.xview_moveto(0)

    display_comparison_table(table_frame, rr_metrics,srtf_metrics)
    display_gantt_details(gantt_detail_frame, rr_gantt, srtf_gantt)
    display_ready_queue(ready_queue_frame, rr_queue_history)
    display_best_algorithm(best_frame,rr_metrics,srtf_metrics)

root = tk.Tk()
root.title("CPU Scheduling - RR vs SRTF")
root.geometry("1050x900")
main_container = tk.Frame(root)
main_container.pack(fill="both", expand=True)
canvas_main    = tk.Canvas(main_container)
scrollbar_main = tk.Scrollbar(main_container, orient="vertical", command=canvas_main.yview)
scrollbar_main.pack(side="right", fill="y")
canvas_main.pack(side="left", fill="both", expand=True)
canvas_main.configure(yscrollcommand=scrollbar_main.set)

main_frame = tk.Frame(canvas_main)
canvas_main.create_window((0, 0), window=main_frame, anchor="nw")

def on_configure(event):
    canvas_main.configure(scrollregion=canvas_main.bbox("all"))

main_frame.bind("<Configure>", on_configure)
ctrl_top = tk.Frame(main_frame)
ctrl_top.pack(pady=6)
tk.Label(ctrl_top, text="Number of Processes").grid(row=0, column=0, padx=6)
num_entry = tk.Entry(ctrl_top, width=6)
num_entry.grid(row=0, column=1, padx=6)
tk.Label(ctrl_top, text="Time Quantum").grid(row=0, column=2, padx=6)
quantum_entry = tk.Entry(ctrl_top, width=6)
quantum_entry.grid(row=0, column=3, padx=6)
inputs_frame = tk.Frame(main_frame)
inputs_frame.pack(pady=6)
scenario_frame = tk.Frame(main_frame)
scenario_frame.pack(pady=4)

for sc in scenarios:
    tk.Button(scenario_frame, text=sc["name"],
              command=lambda s=sc: load_scenario(s),
              width=12).pack(side="left", padx=3)

control_frame = tk.Frame(main_frame)
control_frame.pack(pady=4)

tk.Button(control_frame, text="Create Inputs",command=create_inputs).pack(side="left", padx=5)
tk.Button(control_frame, text="Run",command=run).pack(side="left", padx=5)
tk.Button(control_frame, text="Reset", command=reset_all, bg="red", fg="white").pack(side="left", padx=5)
gantt_outer = tk.Frame(main_frame, bd=1, relief="sunken")
gantt_outer.pack(fill="x", padx=10, pady=5)
gantt_canvas = tk.Canvas(gantt_outer, bg="white", height=250)
scroll_x = tk.Scrollbar(gantt_outer, orient="horizontal",command=gantt_canvas.xview)
gantt_canvas.configure(xscrollcommand=scroll_x.set)
gantt_canvas.pack(fill="x", expand=True)
scroll_x.pack(fill="x")

table_frame = tk.Frame(main_frame)
table_frame.pack(pady=8, padx=10, anchor="w")

gantt_detail_frame = tk.Frame(main_frame)
gantt_detail_frame.pack(pady=8, padx=10, anchor="w")
ready_queue_frame = tk.Frame(main_frame)
ready_queue_frame.pack(pady=6, padx=10, anchor="w")
best_frame = tk.Frame(main_frame)
best_frame.pack(pady=8, padx=10, anchor="w", fill="x")
root.mainloop()
