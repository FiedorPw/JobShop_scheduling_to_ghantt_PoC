from ortools.sat.python import cp_model  # import solvera CP-SAT z OR-Tools

# 1) Definiujesz zasoby (gniazda/maszyny)
machines = ["M1", "M2", "M3"]  # nazwy tylko do czytelnego wydruku

# 2) Definiujesz joby: każdy job ma własny routing (kolejność maszyn)
#    Format: (machine_id, czas_trwania)
jobs = [
    [(0, 3), (1, 2), (2, 2)],  # Job 0: M1 -> M2 -> M3
    [(1, 2), (2, 4)],          # Job 1: M2 -> M3
    [(0, 2), (2, 1), (1, 3)],  # Job 2: M1 -> M3 -> M2 (inna ścieżka)
]

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
        itv = model.new_interval_var(s, dur, e, f"itv{j}_{o}")  # przedział: start + dur = end  [oai_citation:2‡or-tools.github.io](https://or-tools.github.io/docs/python/classortools_1_1sat_1_1python_1_1cp__model_1_1IntervalVar.html?utm_source=chatgpt.com)

        starts[(j, o)], ends[(j, o)], intervals[(j, o)] = s, e, itv  # zapamiętaj zmienne
        by_machine[m].append(itv)  # ta operacja obciąża maszynę m

# 5) Ograniczenie technologiczne: routing w ramach joba (operacja o+1 po o)
for j, job in enumerate(jobs):
    for o in range(len(job) - 1):
        model.add(starts[(j, o + 1)] >= ends[(j, o)])  # kolejność kroków w produkcie

# 6) Ograniczenie zasobowe: maszyna robi tylko jedną operację naraz
for m, itvs in by_machine.items():
    model.add_no_overlap(itvs)  # zero nakładania na tej samej maszynie  [oai_citation:3‡Google for Developers](https://developers.google.com/optimization/scheduling/job_shop?utm_source=chatgpt.com)

# 7) KPI (Key Performance Indicator): minimalizuj makespan (czas zakończenia całości)
makespan = model.new_int_var(0, horizon, "makespan")  # zmienna “czas całego planu”
model.add_max_equality(makespan, [ends[(j, len(job)-1)] for j, job in enumerate(jobs)])  # max z końców jobów
model.minimize(makespan)  # minimalizacja makespan = typowy cel job shop  [oai_citation:4‡Google for Developers](https://developers.google.com/optimization/scheduling/job_shop?utm_source=chatgpt.com)

# 8) Rozwiązanie
solver = cp_model.CpSolver()
solver.solve(model)

# 9) Wynik, który "karmi" biznes: finalna kolejność per maszyna (do Gantta/raportu), który “karmi” biznes: finalna kolejność per maszyna (do Gantta/raportu)
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
