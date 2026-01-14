"""
Solver dla trudniejszego przypadku Job Shop Scheduling.
15 jobów, 6 maszyn, dłuższe sekwencje operacji (4-6 kroków).
Zawiera pomiar czasu wykonania algorytmu.
"""

from ortools.sat.python import cp_model  # import solvera CP-SAT z OR-Tools
import time  # do pomiaru czasu wykonania algorytmu

# 1) Definiujesz zasoby (gniazda/maszyny)
machines = ["M1", "M2", "M3", "M4", "M5", "M6"]  # 6 maszyn w fabryce

# 2) Definiujesz joby: każdy job ma własny routing (kolejność maszyn)
#    Format: (machine_id, czas_trwania)
#    Każdy job to produkt przechodzący przez różne etapy obróbki
jobs = [
    # Job 0-4: Produkty typu A (routing przez M1 → M2 → M3 → M4 → M5)
    [(0, 3), (1, 2), (2, 4), (3, 2), (4, 3)],  # Job 0
    [(0, 2), (1, 3), (2, 2), (3, 4), (4, 2)],  # Job 1
    [(0, 4), (1, 2), (2, 3), (3, 2), (4, 4)],  # Job 2
    [(0, 3), (1, 4), (2, 2), (3, 3), (4, 2)],  # Job 3
    [(0, 2), (1, 2), (2, 5), (3, 2), (4, 3)],  # Job 4
    
    # Job 5-9: Produkty typu B (routing przez M2 → M4 → M6 → M1 → M3)
    [(1, 3), (3, 2), (5, 4), (0, 2), (2, 3)],  # Job 5
    [(1, 2), (3, 3), (5, 2), (0, 4), (2, 2)],  # Job 6
    [(1, 4), (3, 2), (5, 3), (0, 2), (2, 4)],  # Job 7
    [(1, 3), (3, 4), (5, 2), (0, 3), (2, 2)],  # Job 8
    [(1, 2), (3, 2), (5, 5), (0, 2), (2, 3)],  # Job 9
    
    # Job 10-14: Produkty typu C (różne routingi)
    [(2, 3), (4, 2), (5, 4), (1, 2), (3, 3), (0, 2)],  # Job 10: 6 operacji
    [(5, 2), (3, 3), (1, 2), (4, 4)],                   # Job 11: 4 operacje
    [(0, 4), (2, 2), (4, 3), (5, 2), (1, 4)],          # Job 12: 5 operacji
    [(3, 3), (1, 4), (5, 2), (2, 3), (0, 2)],          # Job 13: 5 operacji
    [(4, 2), (2, 2), (0, 5), (3, 2), (5, 3), (1, 2)],  # Job 14: 6 operacji
]

# === START POMIARU CZASU ===
start_time = time.perf_counter()  # precyzyjny timer do pomiaru wydajności

model = cp_model.CpModel()  # tworzysz model optymalizacyjny

# 3) Ustalasz horyzont czasu (górna granica, żeby solver miał zakres)
horizon = sum(d for job in jobs for _, d in job)  # suma czasów = bezpieczny max

# 4) Zmienne decyzyjne: start/koniec każdej operacji + IntervalVar do ograniczeń scheduling
starts, ends, intervals = {}, {}, {}  # słowniki na zmienne
by_machine = {m: [] for m in range(len(machines))}  # lista operacji przypiętych do maszyny

for j, job in enumerate(jobs):                # przechodzisz po jobach
    for o, (m, dur) in enumerate(job):        # przechodzisz po operacjach joba
        s = model.new_int_var(0, horizon, f"s{j}_{o}")          # start operacji (decyzja)
        e = model.new_int_var(0, horizon, f"e{j}_{o}")          # koniec operacji (decyzja)
        itv = model.new_interval_var(s, dur, e, f"itv{j}_{o}")  # przedział: start + dur = end

        starts[(j, o)], ends[(j, o)], intervals[(j, o)] = s, e, itv  # zapamiętaj zmienne
        by_machine[m].append(itv)  # ta operacja obciąża maszynę m

# 5) Ograniczenie technologiczne: routing w ramach joba (operacja o+1 po o)
for j, job in enumerate(jobs):
    for o in range(len(job) - 1):
        model.add(starts[(j, o + 1)] >= ends[(j, o)])  # kolejność kroków w produkcie

# 6) Ograniczenie zasobowe: maszyna robi tylko jedną operację naraz
for m, itvs in by_machine.items():
    model.add_no_overlap(itvs)  # zero nakładania na tej samej maszynie

# 7) KPI (Key Performance Indicator): minimalizuj makespan (czas zakończenia całości)
makespan = model.new_int_var(0, horizon, "makespan")  # zmienna "czas całego planu"
model.add_max_equality(makespan, [ends[(j, len(job)-1)] for j, job in enumerate(jobs)])  # max z końców jobów
model.minimize(makespan)  # minimalizacja makespan = typowy cel job shop

# 8) Rozwiązanie
solver = cp_model.CpSolver()
status = solver.solve(model)

# === KONIEC POMIARU CZASU ===
end_time = time.perf_counter()
elapsed_time = end_time - start_time

# Wyświetl statystyki rozwiązania
status_name = solver.status_name(status)
print(f"\n{'='*50}")
print(f"STATYSTYKI ROZWIĄZANIA (HARD CASE)")
print(f"{'='*50}")
print(f"Status: {status_name}")
print(f"Czas obliczeń: {elapsed_time:.4f} sekund")
print(f"Makespan (czas całkowity): {solver.value(makespan)} jednostek")
print(f"Liczba jobów: {len(jobs)}")
print(f"Liczba maszyn: {len(machines)}")
print(f"Liczba operacji: {sum(len(job) for job in jobs)}")
print(f"{'='*50}\n")

# 9) Wynik, który "karmi" biznes: finalna kolejność per maszyna (do Gantta/raportu)
schedule = {m: [] for m in range(len(machines))}  # tu zbierzesz: (start, end, job, op)

for j, job in enumerate(jobs):
    for o, (m, _) in enumerate(job):
        s = solver.value(starts[(j, o)])  # start policzony przez solver
        e = solver.value(ends[(j, o)])    # koniec policzony przez solver
        schedule[m].append((s, e, j, o))  # zapis do maszyny

for m in range(len(machines)):
    schedule[m].sort(key=lambda x: x[0])  # sort po starcie = kolejność na maszynie
    print(machines[m], schedule[m])       # to jest finalna sekwencja na tej maszynie

# 10) Wizualizacja wykresu Gantta
from visualization import plot_gantt
plot_gantt(schedule, machines, jobs, solver.value(makespan))
