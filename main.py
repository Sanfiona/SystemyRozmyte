import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from pyit2fls import Mamdani, min_t_norm, max_s_norm, IT2FS, tri_mf, ltri_mf, rtri_mf, crisp, IT2FS_plot

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

def run_simulation():
    dt = 60.0
    steps = 400
    T_bottom_sp = 1250.0
    
    fopdt = FOPDTModel(dt=dt)
    pi = PIController(tau=420, theta=240)
    furnace = SimpleFurnaceModel(dt=dt)
    
    hist = {'yb':[], 'yc':[], 'yc_sp':[], 'fuel':[], 'err':[]}
    yc_sp = 1480.0
    yb_history = [1230.0] * 12

    print("Symulacja IT2 w toku...")
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

    # WYKRESY
    plt.figure(figsize=(12, 8))
    plt.subplot(211)
    plt.plot(hist['yb'], label='Temperatura dna (Bottom)', color='blue', lw=2)
    plt.axhline(T_bottom_sp, color='red', ls='--', label='Wartość zadana (1250°C)')
    plt.title("Symulacja Kaskadowa IT2 Fuzzy-PI - Temperatury", fontsize=14)
    plt.ylabel("Temp [°C]"); plt.legend(); plt.grid(True, alpha=0.3)

    plt.subplot(212)
    plt.plot(hist['yc'], label='Temperatura sklepienia (Crown)', color='orange')
    plt.plot(hist['yc_sp'], 'g--', label='Setpoint sklepienia (z Fuzzy Master)')
    plt.ylabel("Temp [°C]"); plt.xlabel("Czas [min]"); plt.legend(); plt.grid(True, alpha=0.3)
    plt.show()

    plt.figure(figsize=(12, 5))
    plt.plot(hist['err'], color='red', lw=1.5, label='Błąd regulacji dna')
    plt.fill_between(range(steps), -5, 5, color='green', alpha=0.2, label='Strefa tolerancji ±5°C')
    plt.axhline(0, color='black', ls='--', alpha=0.5)
    plt.title("Analiza precyzji: Błąd temperatury dna", fontsize=13)
    plt.xlabel("Czas [min]"); plt.ylabel("Błąd [°C]"); plt.legend(); plt.grid(True, alpha=0.2)
    plt.show()

    plt.figure(figsize=(12, 5))
    plt.plot(hist['fuel'], color='purple', label='Strumień paliwa')
    plt.title("Sygnał sterujący - zużycie paliwa", fontsize=13)
    plt.xlabel("Czas [min]"); plt.ylabel("Paliwo [j.u.]"); plt.legend(); plt.grid(True, alpha=0.2)
    plt.show()

    IT2FS_plot(eb_sets['NB'], eb_sets['NM'], eb_sets['ZO'], eb_sets['PM'], eb_sets['PB'], 
               legends=["NB", "NM", "ZO", "PM", "PB"], title="Zbiory IT2 (Błąd)")
    plt.show()

    # POWIERZCHNIA 3D
    print("Generowanie powierzchni 3D...")
    x_r = np.linspace(-1, 1, 15); y_r = np.linspace(-1, 1, 15)
    X, Y = np.meshgrid(x_r, y_r); Z = np.zeros_like(X)
    for i in range(len(x_r)):
        for j in range(len(y_r)):
            _, tr_m = it2_ctrl.evaluate({"eb": X[i, j], "deb": Y[i, j]})
            Z[i, j] = crisp(tr_m["out"])
    
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_surface(X, Y, Z, cmap='viridis', edgecolor='none')
    ax.set_title('Powierzchnia Sterująca IT2 (Błąd vs Trend)', fontsize=13)
    ax.set_xlabel('eb (Error)'); ax.set_ylabel('deb (Trend)'); ax.set_zlabel('Delta Ysc')
    plt.show()

if __name__ == "__main__":
    run_simulation()