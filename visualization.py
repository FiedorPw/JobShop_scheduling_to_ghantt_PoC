"""
Moduł wizualizacji wykresu Gantta dla harmonogramu produkcji.

Ten moduł zawiera funkcję do generowania czytelnego wykresu Gantta
na podstawie wyniku optymalizacji schedulingu jobów.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe


# === Konfiguracja kolorów dla każdego joba ===
# Używamy wyrazistej palety kolorów, by łatwo rozróżnić joby
JOB_COLORS = [
    "#4CAF50",  # Job 0 - zielony
    "#2196F3",  # Job 1 - niebieski  
    "#FF9800",  # Job 2 - pomarańczowy
    "#E91E63",  # Job 3 - różowy
    "#9C27B0",  # Job 4 - fioletowy
    "#00BCD4",  # Job 5 - cyjan
    "#795548",  # Job 6 - brązowy
    "#607D8B",  # Job 7 - szaro-niebieski
]


def plot_gantt(schedule: dict, machines: list, jobs: list, makespan: int) -> None:
    """
    Generuje wykres Gantta dla harmonogramu produkcji.
    
    Args:
        schedule: Słownik {machine_id: [(start, end, job_id, op_id), ...]}
                  zawierający harmonogram dla każdej maszyny.
        machines: Lista nazw maszyn, np. ["M1", "M2", "M3"].
        jobs: Lista jobów (potrzebna do ustalenia liczby jobów dla legendy).
        makespan: Całkowity czas wykonania (wynik optymalizacji).
    
    Returns:
        None - wyświetla wykres.
    """
    
    # === Tworzenie wykresu z lepszymi proporcjami ===
    fig, ax = plt.subplots(figsize=(12, 6))  # większy wykres = lepsza czytelność
    fig.patch.set_facecolor('#FAFAFA')  # jasnoszare tło figury
    ax.set_facecolor('#FFFFFF')  # białe tło wykresu

    # === Parametry wizualne pasków ===
    bar_height = 0.6  # wysokość paska (w jednostkach osi Y)

    # === Rysowanie pasków dla każdej maszyny ===
    for m, machine_name in enumerate(machines):
        y_pos = m  # pozycja Y = numer maszyny (prosta skala)
        
        for (s, e, j, o) in schedule[m]:
            duration = e - s
            color = JOB_COLORS[j % len(JOB_COLORS)]  # kolor zależny od joba
            
            # Rysuj prostokąt (pasek Gantta)
            ax.barh(
                y=y_pos,
                width=duration,
                left=s,
                height=bar_height,
                color=color,
                edgecolor='#333333',  # ciemna ramka
                linewidth=1.5,
                alpha=0.9,
            )
            
            # Etykieta na środku paska (biały tekst z cieniem dla czytelności)
            label = f"J{j}-Op{o}"
            ax.text(
                s + duration / 2,  # środek paska (oś X)
                y_pos,             # środek paska (oś Y)
                label,
                ha='center',       # wyśrodkowanie poziome
                va='center',       # wyśrodkowanie pionowe
                fontsize=10,
                fontweight='bold',
                color='white',
                # Dodaj cień dla lepszej czytelności na jasnych kolorach
                path_effects=[pe.withStroke(linewidth=2, foreground='#333333')]
            )

    # === Konfiguracja osi Y (maszyny) ===
    ax.set_yticks(range(len(machines)))
    ax.set_yticklabels(machines, fontsize=12, fontweight='bold')
    ax.set_ylim(-0.5, len(machines) - 0.5)

    # === Konfiguracja osi X (czas) ===
    ax.set_xlim(-0.5, makespan + 0.5)
    ax.set_xlabel("Czas [jednostki]", fontsize=12, fontweight='bold')

    # Siatka pionowa dla łatwiejszego odczytu czasu
    ax.xaxis.set_major_locator(plt.MultipleLocator(1))  # ticki co 1 jednostkę
    ax.grid(axis='x', linestyle='--', alpha=0.5, color='gray')

    # === Tytuł z informacją o wyniku ===
    ax.set_title(
        f"Wykres Gantta – Harmonogram produkcji\nMakespan (czas całkowity): {makespan} jednostek",
        fontsize=14,
        fontweight='bold',
        pad=15
    )

    # === Legenda z kolorami jobów ===
    legend_patches = [
        mpatches.Patch(color=JOB_COLORS[j % len(JOB_COLORS)], label=f"Job {j}", edgecolor='#333333', linewidth=1)
        for j in range(len(jobs))
    ]
    ax.legend(
        handles=legend_patches,
        loc='upper right',
        title='Joby',
        title_fontsize=11,
        fontsize=10,
        framealpha=0.95,
        edgecolor='#CCCCCC'
    )

    # === Finalne poprawki layoutu ===
    plt.tight_layout()
    plt.show()
