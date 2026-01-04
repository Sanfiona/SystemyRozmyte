import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


# 1. DEFINICJA WEJSC I WYJSCIA 

error = ctrl.Antecedent(np.arange(-1000, 1001, 1), 'error')
delta_error = ctrl.Antecedent(np.arange(-100, 101, 1), 'delta_error')
power = ctrl.Consequent(np.arange(0, 101, 1), 'power')


# 2. UOGOLNIONE ZBIORY ROZMYTE 

def type2_trimf(x, a, b, c, delta):
    pts = sorted([
        a + np.random.uniform(-delta, delta),
        b + np.random.uniform(-delta, delta),
        c + np.random.uniform(-delta, delta)
    ])
    return fuzz.trimf(x, pts)

# Przeskalowane zbiory 
error['negative'] = type2_trimf(error.universe, -1000, -1000, 0, 20.0)
error['zero']     = type2_trimf(error.universe, -150, 0, 150, 10.0)
error['positive'] = type2_trimf(error.universe, 0, 1000, 1000, 20.0)

delta_error['negative'] = type2_trimf(delta_error.universe, -100, -100, 0, 5.0)
delta_error['zero']     = type2_trimf(delta_error.universe, -20, 0, 20, 2.0)
delta_error['positive'] = type2_trimf(delta_error.universe, 0, 100, 100, 5.0)

# Wyscia Sugeno 
power['low']    = fuzz.trimf(power.universe, [10, 10, 10])
power['medium'] = fuzz.trimf(power.universe, [50, 50, 50])
power['high']   = fuzz.trimf(power.universe, [100, 100, 100])

# 3. BAZA REGUL I SYMULATOR
rules = [
    ctrl.Rule(error['positive'] & delta_error['positive'], power['high']),
    ctrl.Rule(error['positive'] & delta_error['zero'],     power['high']),
    ctrl.Rule(error['positive'] & delta_error['negative'], power['medium']),
    ctrl.Rule(error['zero']     & delta_error['zero'],     power['medium']),
    ctrl.Rule(error['zero']     & delta_error['negative'], power['low']),
    ctrl.Rule(error['negative'],                           power['low'])
]

power_ctrl = ctrl.ControlSystem(rules)
power_sim = ctrl.ControlSystemSimulation(power_ctrl)

# 4. SYMULACJA REALISTYCZNEGO PIECA (T_set = 1350°C)
T = 25.0            # Temp. otoczenia (startowa)
T_set = 1350.0      # Realna temperatura wytopu szkla
alpha = 2.5         # Wyzsza moc grzania dla duzej skali
k = 0.005           # Mniejszy wspolczynnik strat (dobra izolacja pieca)
steps = 200

temps, powers = [], []
prev_err = T_set - T

for t in range(steps):
    err = T_set - T
    d_err = err - prev_err
    
    power_sim.input['error'] = err
    power_sim.input['delta_error'] = d_err
    
    try:
        power_sim.compute()
        P = power_sim.output['power']
    except:
        P = 15
    
    # T_next = T + grzanie - straty + zaklocenia przemyslowe
    noise = np.random.uniform(-2.0, 2.0)
    T_next = T + (alpha * P / 10) - (k * (T - 25)) + noise
    
    temps.append(T_next)
    powers.append(P)
    T, prev_err = T_next, err


# 5. WIZUALIZACJA

# Wykres 1: Dowod na Type-2 (Uchyb)
error.view()
plt.title('Uogólnione funkcje: Uchyb (Type-2)')

# Wykres 2: Dowod na Type-2 (Delta Error)
delta_error.view()
plt.title('Uogólnione funkcje: Delta Uchybu (Type-2)')

# Wykres 3: Dynamika procesu (Temperatura i Moc)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 9), sharex=True)
ax1.plot(temps, color='darkred', linewidth=2, label='Temperatura [°C]')
ax1.axhline(T_set, color='black', linestyle='--', label=f'Cel: {T_set}°C')
ax1.set_ylabel('Temp [°C]')
ax1.legend()
ax1.grid(True, alpha=0.3)

ax2.fill_between(range(steps), powers, color='orange', alpha=0.3)
ax2.plot(powers, color='darkorange', label='Moc [%]')
ax2.set_ylabel('Moc [%]')
ax2.set_xlabel('Kroki czasowe')
ax2.legend()
ax2.grid(True, alpha=0.3)

# Wykres 4: Powierzchnia sterujaca 3D
x_range = np.linspace(-1000, 1000, 20)
y_range = np.linspace(-100, 100, 20)
x_mesh, y_mesh = np.meshgrid(x_range, y_range)
z_mesh = np.zeros_like(x_mesh)
for i in range(20):
    for j in range(20):
        power_sim.input['error'] = x_mesh[i, j]
        power_sim.input['delta_error'] = y_mesh[i, j]
        power_sim.compute()
        z_mesh[i, j] = power_sim.output['power']

fig_3d = plt.figure(figsize=(10, 7))
ax_3d = fig_3d.add_subplot(111, projection='3d')
ax_3d.plot_surface(x_mesh, y_mesh, z_mesh, cmap='viridis')
ax_3d.set_title('Powierzchnia Sterująca 3D')
ax_3d.set_xlabel('Error')
ax_3d.set_ylabel('Delta Error')
ax_3d.set_zlabel('Moc [%]')

plt.show(block=True)