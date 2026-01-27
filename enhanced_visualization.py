mport numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from pyit2fls import Mamdani, min_t_norm, max_s_norm, IT2FS, tri_mf, ltri_mf, rtri_mf, crisp, IT2FS_plot
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import seaborn as sns

# Ustawienie stylu wykresów
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class FOPDTModel:
    def __init__(self, K=1.2, theta=240, tau=420, dt=60):
        self.K, self.theta, self.tau, self.dt = K, theta, tau, dt
        self.delay_steps = max(1, int(theta / dt))
        self.fuel_history = [100.0] * self.delay_steps
        self.T_crown = 1480.0

    def update(self, fuel_input):
        self.fuel_history.append(fuel_input)
        delayed_fuel = self.fuel_history.pop(0)
        T_target = 1480.0 + self.K * (delayed_fuel - 100.0)
        self.T_crown += (T_target - self.T_crown) / self.tau * self.dt
        return self.T_crown

class PIController:
    def __init__(self, tau, theta):
        self.Kp = 0.859 * (tau / theta)
        self.Ti = tau / 0.674
        self.integral = 0.0

    def compute(self, error, dt):
        self.integral += error * dt
        output = self.Kp * (error + self.integral / self.Ti)
        return np.clip(100.0 + output, 70, 130)

class SimpleFurnaceModel:
    def __init__(self, dt=60.0):
        self.T_bottom = 1230.0
        self.tau_bottom = 5400.0
        self.dt = dt
        self.crown_history = [1480.0] * int(1200 / dt)

    def update(self, T_crown_new):
        self.crown_history.append(T_crown_new)
        delayed_crown = self.crown_history.pop(0)
        T_target = delayed_crown - 200.0
        self.T_bottom += (T_target - self.T_bottom) / self.tau_bottom * self.dt + np.random.normal(0, 0.1)
        return self.T_bottom

def create_system_diagram():
    """Tworzy schemat blokowy systemu"""
    fig, ax = plt.subplots(1, 1, figsize=(14, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    # Regulator IT2
    it2_box = FancyBboxPatch((0.5, 5), 2, 1.5, boxstyle="round,pad=0.1", 
                             facecolor='lightblue', edgecolor='navy', linewidth=2)
    ax.add_patch(it2_box)
    ax.text(1.5, 5.75, 'Regulator IT2\n(Nadrzędny)', ha='center', va='center', 
            fontsize=11, fontweight='bold')
    
    # Regulator PI
    pi_box = FancyBboxPatch((4, 5), 2, 1.5, boxstyle="round,pad=0.1", 
                           facecolor='lightgreen', edgecolor='darkgreen', linewidth=2)
    ax.add_patch(pi_box)
    ax.text(5, 5.75, 'Regulator PI\n(Podrzędny)', ha='center', va='center', 
            fontsize=11, fontweight='bold')
    
    # Piec
    furnace_box = FancyBboxPatch((7.5, 4), 2, 2.5, boxstyle="round,pad=0.1", 
                                facecolor='lightcoral', edgecolor='darkred', linewidth=2)
    ax.add_patch(furnace_box)
    ax.text(8.5, 5.5, 'Piec\nFOPDT', ha='center', va='center', 
            fontsize=11, fontweight='bold')
    ax.text(8.5, 4.8, 'Sklepienie', ha='center', va='center', fontsize=9)
    ax.text(8.5, 4.3, 'Dno', ha='center', va='center', fontsize=9)
    
    # Sprzężenie zwrotne
    feedback_box = FancyBboxPatch((4, 1), 2, 1, boxstyle="round,pad=0.1", 
                                 facecolor='lightyellow', edgecolor='orange', linewidth=2)
    ax.add_patch(feedback_box)
    ax.text(5, 1.5, 'Pomiar i\nSprzężenie', ha='center', va='center', 
            fontsize=10, fontweight='bold')
    
    # Strzałki
    # IT2 -> PI
    ax.arrow(2.5, 5.75, 1.3, 0, head_width=0.15, head_length=0.1, fc='black', ec='black')
    ax.text(3.25, 5.95, 'ΔYsc', ha='center', fontsize=9)
    
    # PI -> Piec
    ax.arrow(6, 5.75, 1.3, 0, head_width=0.15, head_length=0.1, fc='black', ec='black')
    ax.text(6.65, 5.95, 'Fuel', ha='center', fontsize=9)
    
    # Piec -> Sprzężenie
    ax.arrow(8.5, 4, 0, -1.8, head_width=0.15, head_length=0.1, fc='black', ec='black')
    ax.text(8.8, 3.1, 'T_bottom', ha='center', fontsize=9, rotation=-90)
    
    # Sprzężenie -> IT2
    ax.arrow(4, 1.5, -2.5, 3, head_width=0.15, head_length=0.1, fc='black', ec='black')
    ax.text(2.75, 2.5, 'eb, deb', ha='center', fontsize=9, rotation=-35)
    
    # Setpoint
    ax.text(0.2, 5.75, 'T_sp\n1250°C', ha='center', va='center', 
            fontsize=9, bbox=dict(boxstyle="round,pad=0.3", facecolor='white', edgecolor='red'))
    ax.arrow(0.5, 5.75, 0.5, 0, head_width=0.1, head_length=0.05, fc='red', ec='red')
    
    plt.title('Schemat Blokowy Systemu Sterowania Kaskadowego', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('system_diagram.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_fuzzy_sets_visualization():
    """Tworzy wizualizację zbiorów rozmych"""
    universe = np.linspace(-1.0, 1.0, 100)
    
    def get_it2_sets(univ):
        s = {}
        s['NB'] = IT2FS(univ, rtri_mf, [-0.5, -1.0, 1.0], rtri_mf, [-0.7, -1.0, 1.0])
        s['NM'] = IT2FS(univ, tri_mf, [-1.0, -0.5, 0.0, 1.0], tri_mf, [-0.8, -0.5, -0.2, 1.0])
        s['ZO'] = IT2FS(univ, tri_mf, [-0.4, 0.0, 0.4, 1.0], tri_mf, [-0.2, 0.0, 0.2, 1.0])
        s['PM'] = IT2FS(univ, tri_mf, [0.0, 0.5, 1.0, 1.0], tri_mf, [0.2, 0.5, 0.8, 1.0])
        s['PB'] = IT2FS(univ, ltri_mf, [0.5, 1.0, 1.0], ltri_mf, [0.7, 1.0, 1.0])
        return s
    
    eb_sets = get_it2_sets(universe)
    
    plt.figure(figsize=(12, 6))
    IT2FS_plot(eb_sets['NB'], eb_sets['NM'], eb_sets['ZO'], eb_sets['PM'], eb_sets['PB'], 
               legends=["NB", "NM", "ZO", "PM", "PB"], title="Zbiory Rozmyte Typu II (IT2) - Błąd")
    plt.tight_layout()
    plt.savefig('fuzzy_sets.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_enhanced_simulation():
    """Uruchamia symulację z lepszymi wizualizacjami"""
    dt = 60.0
    steps = 400
    T_bottom_sp = 1250.0
    
    fopdt = FOPDTModel(dt=dt)
    pi = PIController(tau=420, theta=240)
    furnace = SimpleFurnaceModel(dt=dt)
    
    # Inicjalizacja regulatora IT2
    universe = np.linspace(-1.0, 1.0, 50)
    
    def get_it2_sets(univ):
        s = {}
        s['NB'] = IT2FS(univ, rtri_mf, [-0.5, -1.0, 1.0], rtri_mf, [-0.7, -1.0, 1.0])
        s['NM'] = IT2FS(univ, tri_mf, [-1.0, -0.5, 0.0, 1.0], tri_mf, [-0.8, -0.5, -0.2, 1.0])
        s['ZO'] = IT2FS(univ, tri_mf, [-0.4, 0.0, 0.4, 1.0], tri_mf, [-0.2, 0.0, 0.2, 1.0])
        s['PM'] = IT2FS(univ, tri_mf, [0.0, 0.5, 1.0, 1.0], tri_mf, [0.2, 0.5, 0.8, 1.0])
        s['PB'] = IT2FS(univ, ltri_mf, [0.5, 1.0, 1.0], ltri_mf, [0.7, 1.0, 1.0])
        return s
    
    eb_sets = get_it2_sets(universe)
    deb_sets = get_it2_sets(universe)
    ysc_sets = get_it2_sets(universe)
    ysc_sets['NS'] = IT2FS(universe, tri_mf, [-0.6, -0.2, 0.0, 1.0], tri_mf, [-0.4, -0.2, -0.1, 1.0])
    ysc_sets['PS'] = IT2FS(universe, tri_mf, [0.0, 0.2, 0.6, 1.0], tri_mf, [0.1, 0.2, 0.4, 1.0])
    
    it2_ctrl = Mamdani(min_t_norm, max_s_norm, method="Centroid", algorithm="KM")
    it2_ctrl.add_input_variable("eb")
    it2_ctrl.add_input_variable("deb")
    it2_ctrl.add_output_variable("out")
    
    # Dodanie reguł
    it2_ctrl.add_rule([("eb", eb_sets['NB']), ("deb", deb_sets['NB'])], [("out", ysc_sets['PB'])])
    it2_ctrl.add_rule([("eb", eb_sets['NM']), ("deb", deb_sets['NB'])], [("out", ysc_sets['PB'])])
    it2_ctrl.add_rule([("eb", eb_sets['ZO']), ("deb", deb_sets['NB'])], [("out", ysc_sets['PM'])])
    it2_ctrl.add_rule([("eb", eb_sets['PM']), ("deb", deb_sets['NB'])], [("out", ysc_sets['PM'])])
    it2_ctrl.add_rule([("eb", eb_sets['PB']), ("deb", deb_sets['NB'])], [("out", ysc_sets['PS'])])
    
    it2_ctrl.add_rule([("eb", eb_sets['NB']), ("deb", deb_sets['NM'])], [("out", ysc_sets['PB'])])
    it2_ctrl.add_rule([("eb", eb_sets['NM']), ("deb", deb_sets['NM'])], [("out", ysc_sets['PM'])])
    it2_ctrl.add_rule([("eb", eb_sets['ZO']), ("deb", deb_sets['NM'])], [("out", ysc_sets['PM'])])
    it2_ctrl.add_rule([("eb", eb_sets['PM']), ("deb", deb_sets['NM'])], [("out", ysc_sets['PS'])])
    it2_ctrl.add_rule([("eb", eb_sets['PB']), ("deb", deb_sets['NM'])], [("out", ysc_sets['PS'])])
    
    it2_ctrl.add_rule([("eb", eb_sets['NB']), ("deb", deb_sets['ZO'])], [("out", ysc_sets['PM'])])
    it2_ctrl.add_rule([("eb", eb_sets['NM']), ("deb", deb_sets['ZO'])], [("out", ysc_sets['ZO'])])
    it2_ctrl.add_rule([("eb", eb_sets['ZO']), ("deb", deb_sets['ZO'])], [("out", ysc_sets['ZO'])])
    it2_ctrl.add_rule([("eb", eb_sets['PM']), ("deb", deb_sets['ZO'])], [("out", ysc_sets['ZO'])])
    it2_ctrl.add_rule([("eb", eb_sets['PB']), ("deb", deb_sets['ZO'])], [("out", ysc_sets['NM'])])
    
    it2_ctrl.add_rule([("eb", eb_sets['NB']), ("deb", deb_sets['PM'])], [("out", ysc_sets['NS'])])
    it2_ctrl.add_rule([("eb", eb_sets['NM']), ("deb", deb_sets['PM'])], [("out", ysc_sets['NS'])])
    it2_ctrl.add_rule([("eb", eb_sets['ZO']), ("deb", deb_sets['PM'])], [("out", ysc_sets['NM'])])
    it2_ctrl.add_rule([("eb", eb_sets['PM']), ("deb", deb_sets['PM'])], [("out", ysc_sets['NM'])])
    it2_ctrl.add_rule([("eb", eb_sets['PB']), ("deb", deb_sets['PM'])], [("out", ysc_sets['NB'])])
    
    it2_ctrl.add_rule([("eb", eb_sets['NB']), ("deb", deb_sets['PB'])], [("out", ysc_sets['NS'])])
    it2_ctrl.add_rule([("eb", eb_sets['NM']), ("deb", deb_sets['PB'])], [("out", ysc_sets['NM'])])
    it2_ctrl.add_rule([("eb", eb_sets['ZO']), ("deb", deb_sets['PB'])], [("out", ysc_sets['NM'])])
    it2_ctrl.add_rule([("eb", eb_sets['PM']), ("deb", deb_sets['PB'])], [("out", ysc_sets['NB'])])
    it2_ctrl.add_rule([("eb", eb_sets['PB']), ("deb", deb_sets['PB'])], [("out", ysc_sets['NB'])])
    
    hist = {'yb':[], 'yc':[], 'yc_sp':[], 'fuel':[], 'err':[]}
    yc_sp = 1480.0
    yb_history = [1230.0] * 12
    
    print("Uruchamianie symulacji...")
    for s in range(steps):
        if s % 10 == 0:
            eb_val = (T_bottom_sp - furnace.T_bottom) / 40.0
            slope, *_ = stats.linregress(range(12), yb_history[-12:])
            deb_val = slope / 0.8
            eb_n, deb_n = np.clip(eb_val, -1, 1), np.clip(deb_val, -1, 1)
            _, tr = it2_ctrl.evaluate({"eb": eb_n, "deb": deb_n})
            yc_sp += crisp(tr["out"]) * 15.0
            yc_sp = np.clip(yc_sp, 1400, 1550)
        
        fuel = pi.compute(yc_sp - fopdt.T_crown, dt)
        t_crown = fopdt.update(fuel)
        t_bottom = furnace.update(t_crown)
        yb_history.append(t_bottom)
        
        hist['yb'].append(t_bottom); hist['yc'].append(t_crown)
        hist['yc_sp'].append(yc_sp); hist['fuel'].append(fuel)
        hist['err'].append(T_bottom_sp - t_bottom)
    
    # Tworzenie wykresów
    time = np.arange(steps) * dt / 60  # czas w minutach
    
    # Wykres 1: Temperatury
    fig, axes = plt.subplots(3, 1, figsize=(14, 12))
    
    axes[0].plot(time, hist['yb'], label='Temperatura dna', color='blue', linewidth=2)
    axes[0].axhline(T_bottom_sp, color='red', linestyle='--', linewidth=2, label='Wartość zadana (1250°C)')
    axes[0].fill_between(time, T_bottom_sp-5, T_bottom_sp+5, alpha=0.2, color='green', label='Strefa tolerancji ±5°C')
    axes[0].set_title('Temperatura Dna Pieca', fontweight='bold', fontsize=12)
    axes[0].set_ylabel('Temperatura [°C]')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(time, hist['yc'], label='Temperatura sklepienia', color='orange', linewidth=2)
    axes[1].plot(time, hist['yc_sp'], 'g--', label='Setpoint sklepienia (z Fuzzy)', linewidth=2)
    axes[1].set_title('Temperatura Sklepienia', fontweight='bold', fontsize=12)
    axes[1].set_ylabel('Temperatura [°C]')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    axes[2].plot(time, hist['fuel'], color='purple', linewidth=2, label='Strumień paliwa')
    axes[2].set_title('Zużycie Paliwa', fontweight='bold', fontsize=12)
    axes[2].set_xlabel('Czas [min]')
    axes[2].set_ylabel('Paliwo [j.u.]')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('simulation_results.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Wykres 2: Analiza błędu
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))
    
    ax1.plot(time, hist['err'], color='red', linewidth=1.5, label='Błąd regulacji')
    ax1.fill_between(time, -5, 5, alpha=0.3, color='green', label='Strefa tolerancji ±5°C')
    ax1.axhline(0, color='black', linestyle='--', alpha=0.5)
    ax1.set_title('Analiza Precyzji Regulacji', fontweight='bold', fontsize=12)
    ax1.set_ylabel('Błąd [°C]')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Statystyki błędu
    error_array = np.array(hist['err'])
    within_tolerance = np.sum(np.abs(error_array) <= 5)
    percentage = (within_tolerance / len(error_array)) * 100
    
    ax2.bar(['W tolerancji', 'Poza tolerancją'], 
            [within_tolerance, len(error_array) - within_tolerance],
            color=['green', 'red'], alpha=0.7)
    ax2.set_title(f'Statystyka Błędu: {percentage:.1f}% w strefie tolerancji', fontweight='bold', fontsize=12)
    ax2.set_ylabel('Liczba próbek')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('error_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return hist

def create_3d_surface():
    """Tworzy powierzchnię sterującą 3D"""
    universe = np.linspace(-1.0, 1.0, 50)
    
    def get_it2_sets(univ):
        s = {}
        s['NB'] = IT2FS(univ, rtri_mf, [-0.5, -1.0, 1.0], rtri_mf, [-0.7, -1.0, 1.0])
        s['NM'] = IT2FS(univ, tri_mf, [-1.0, -0.5, 0.0, 1.0], tri_mf, [-0.8, -0.5, -0.2, 1.0])
        s['ZO'] = IT2FS(univ, tri_mf, [-0.4, 0.0, 0.4, 1.0], tri_mf, [-0.2, 0.0, 0.2, 1.0])
        s['PM'] = IT2FS(univ, tri_mf, [0.0, 0.5, 1.0, 1.0], tri_mf, [0.2, 0.5, 0.8, 1.0])
        s['PB'] = IT2FS(univ, ltri_mf, [0.5, 1.0, 1.0], ltri_mf, [0.7, 1.0, 1.0])
        return s
    
    eb_sets = get_it2_sets(universe)
    deb_sets = get_it2_sets(universe)
    ysc_sets = get_it2_sets(universe)
    ysc_sets['NS'] = IT2FS(universe, tri_mf, [-0.6, -0.2, 0.0, 1.0], tri_mf, [-0.4, -0.2, -0.1, 1.0])
    ysc_sets['PS'] = IT2FS(universe, tri_mf, [0.0, 0.2, 0.6, 1.0], tri_mf, [0.1, 0.2, 0.4, 1.0])
    
    it2_ctrl = Mamdani(min_t_norm, max_s_norm, method="Centroid", algorithm="KM")
    it2_ctrl.add_input_variable("eb")
    it2_ctrl.add_input_variable("deb")
    it2_ctrl.add_output_variable("out")
    
    # Dodanie reguł (skrócona wersja)
    it2_ctrl.add_rule([("eb", eb_sets['NB']), ("deb", deb_sets['NB'])], [("out", ysc_sets['PB'])])
    it2_ctrl.add_rule([("eb", eb_sets['NM']), ("deb", deb_sets['NM'])], [("out", ysc_sets['PM'])])
    it2_ctrl.add_rule([("eb", eb_sets['ZO']), ("deb", deb_sets['ZO'])], [("out", ysc_sets['ZO'])])
    it2_ctrl.add_rule([("eb", eb_sets['PM']), ("deb", deb_sets['PM'])], [("out", ysc_sets['NM'])])
    it2_ctrl.add_rule([("eb", eb_sets['PB']), ("deb", deb_sets['PB'])], [("out", ysc_sets['NB'])])
    
    print("Generowanie powierzchni 3D...")
    x_r = np.linspace(-1, 1, 30)
    y_r = np.linspace(-1, 1, 30)
    X, Y = np.meshgrid(x_r, y_r)
    Z = np.zeros_like(X)
    
    for i in range(len(x_r)):
        for j in range(len(y_r)):
            _, tr_m = it2_ctrl.evaluate({"eb": X[i, j], "deb": Y[i, j]})
            Z[i, j] = crisp(tr_m["out"])
    
    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection='3d')
    surf = ax.plot_surface(X, Y, Z, cmap='viridis', edgecolor='none', alpha=0.9)
    
    ax.set_title('Powierzchnia Sterująca Regulatora IT2\n(Błąd vs Trend -> Korekta Setpointu)', 
                fontsize=14, fontweight='bold')
    ax.set_xlabel('Błąd (eb)', fontsize=11)
    ax.set_ylabel('Trend (deb)', fontsize=11)
    ax.set_zlabel('Korekta Ysc', fontsize=11)
    
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)
    plt.savefig('3d_surface.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """Główna funkcja generująca wszystkie wizualizacje"""
    print("Tworzenie dokumentacji wizualnej systemu sterowania rozmytego...")
    
    print("\n1. Tworzenie schematu blokowego systemu...")
    create_system_diagram()
    
    print("\n2. Tworzenie wizualizacji zbiorów rozmych...")
    create_fuzzy_sets_visualization()
    
    print("\n3. Uruchamianie symulacji z enhanced wizualizacjami...")
    hist = create_enhanced_simulation()
    
    print("\n4. Generowanie powierzchni sterującej 3D...")
    create_3d_surface()
    
    print("\n5. Obliczanie statystyk...")
    error_array = np.array(hist['err'])
    stats_summary = {
        'mean_error': np.mean(error_array),
        'std_error': np.std(error_array),
        'max_error': np.max(np.abs(error_array)),
        'within_tolerance': np.sum(np.abs(error_array) <= 5),
        'percentage_in_tolerance': (np.sum(np.abs(error_array) <= 5) / len(error_array)) * 100
    }
    
    print("\n=== STATYSTYKI SYMULACJI ===")
    print(f"Średni błąd: {stats_summary['mean_error']:.3f}°C")
    print(f"Odchylenie standardowe: {stats_summary['std_error']:.3f}°C")
    print(f"Maksymalny błąd: {stats_summary['max_error']:.3f}°C")
    print(f"Próbki w tolerancji: {stats_summary['within_tolerance']}/{len(error_array)}")
    print(f"Procent w tolerancji: {stats_summary['percentage_in_tolerance']:.1f}%")
    
    print("\nWizualizacje zostały zapisane jako pliki PNG:")
    print("- system_diagram.png")
    print("- fuzzy_sets.png") 
    print("- simulation_results.png")
    print("- error_analysis.png")
    print("- 3d_surface.png")

if __name__ == "__main__":
    main()
