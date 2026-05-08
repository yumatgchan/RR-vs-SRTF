from tkinter import messagebox


def build_processes(num_entry, id_entries, arrival_entries, burst_entries):
    processes = []
    ids = set()

    try:
        n = int(num_entry.get())
    except ValueError:
        messagebox.showerror("Error", "Enter valid number of processes")
        return None

    try:
        for i in range(n):
            pid     = id_entries[i].get().strip()
            arrival = int(arrival_entries[i].get())
            burst   = int(burst_entries[i].get())

            if pid == "":
                messagebox.showerror("Error", "Process ID cannot be empty")
                return None

            if pid in ids:
                messagebox.showerror("Error", f"Duplicate ID: {pid}")
                return None
            ids.add(pid)

            if arrival < 0:
                messagebox.showerror("Error", f"Arrival time of {pid} cannot be negative")
                return None

            if burst <= 0:
                messagebox.showerror("Error", f"Burst time of {pid} must be a positive integer")
                return None

            processes.append({
                "id"        : pid,
                "arrival"   : arrival,
                "burst"     : burst,
                "remaining" : burst,
                "start"     : -1,
                "completion": 0,
            })

        return processes

    except ValueError:
        messagebox.showerror("Error", "Enter valid integers for arrival and burst times")
        return None


def validate_quantum(quantum_entry):
    """
    Returns the quantum value.
    If the user enters 0 or a negative number we silently treat it as 1
    so the scheduler never crashes.
    Returns None only if the field is non-numeric.
    """
    try:
        q = int(quantum_entry.get())
        if q <= 0:
            messagebox.showerror("Error", "Invalid Quantum: Time Quantum must be greater than 0")
            return None
        return q
    except ValueError:
        messagebox.showerror("Error", "Invalid Quantum: Time Quantum must be a valid integer")
        return None