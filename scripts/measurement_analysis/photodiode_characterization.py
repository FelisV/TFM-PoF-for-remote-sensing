import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

plt.close("all")

# laser optical power
laser_power = -3

# photodiode config
config = 3

measurements = {
    -3: "laser_minus_3dBm",
    0: "laser_0dBm",
    3: "laser_3dBm",
    6: "laser_6dBm",
}
measurement = measurements[laser_power]

csv_files = {
    1: "photodiode_characterization_1.csv",
    3: "photodiode_characterization_3_in_series.csv",
    4: "photodiode_characterization_4_in_series.csv",
}
csv_name = csv_files[config]

# repository root, scripts/measurement_analysis/
repo = Path(__file__).resolve().parents[2]
file = repo / "measurements" / "photodiode" / "results" / measurement / csv_name
print("Reading:", file)

with open(file, encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

start = 0
for n, line in enumerate(lines):
    if line.startswith("Time (s)"):
        start = n + 1
        break

data = np.loadtxt(lines[start:], delimiter=",", usecols=(0, 1, 2))
t = data[:, 0]
V = data[:, 1]
I = data[:, 2]

# end (OC)
end = 0
for n in range(1, len(I)):
    if I[n - 1] > 0 and I[n] <= 0 and V[n] > 0:
        end = n
        break

if end == 0:
    print("The current never reaches zero: the sweep did not reach Voc.")
    print("Increase the signal generator amplitude.")
    raise SystemExit     

# start: lowest voltage point before the end (where it starts rising),
# SC
ini = np.argmin(V[:end])
while V[ini] < 0:
    ini = ini + 1

t = t[ini:end]
V = V[ini:end]
I = I[ini:end]

t = (t - t[0]) * 1e6   # time in us, starting at 0
P = V * I

# MPP
k = np.argmax(P)
Vmp = V[k]
Imp = I[k]
Pmax = P[k]
tmp = t[k]

Isc = I[0]
Voc = V[-1]

print("Isc  =", round(Isc * 1e3, 4), "mA")
print("Voc  =", round(Voc, 4), "V")
print("Vmp  =", round(Vmp, 4), "V")
print("Imp  =", round(Imp * 1e3, 4), "mA")
print("Pmax =", round(Pmax * 1e6, 2), "uW")

# plot 1 - current and voltage over time
fig, ax1 = plt.subplots()
ax2 = ax1.twinx()
ax1.plot(t, I * 1e3, color="blue", label="Current")
ax2.plot(t, V, color="orange", label="Voltage")
ax1.axvline(tmp, color="gray", linestyle="--")
ax1.plot(tmp, Imp * 1e3, "ko")
ax2.plot(tmp, Vmp, "ko")
ax1.text(0.03, 0.75, f"MPP\nVmp = {Vmp:.4f} V\nImp = {Imp*1e3:.4f} mA",
         transform=ax1.transAxes, bbox=dict(facecolor="white"))
ax1.set_title("Current x Voltage")
ax1.set_xlabel("Time (µs)")
ax1.set_ylabel("Current (mA)", color="blue")
ax2.set_ylabel("Voltage (V)", color="orange")
ax1.set_ylim(0, Isc * 1e3 * 1.1)
ax2.set_ylim(0, Voc * 1.1)
ax1.set_xlim(0, t[-1])
ax1.grid()

# plot 2 - I-V curve
plt.figure()
plt.plot(V, I * 1e3, color="blue")
plt.plot(Vmp, Imp * 1e3, "ko")
plt.plot([Vmp, Vmp], [0, Imp * 1e3], "--", color="gray")
plt.plot([0, Vmp], [Imp * 1e3, Imp * 1e3], "--", color="gray")

plt.annotate(f"MPP\n{Vmp:.4f} V, {Imp*1e3:.4f} mA", (Vmp, Imp * 1e3),
             xytext=(-10, -35), textcoords="offset points", ha="right")
plt.annotate(f"Isc = {Isc*1e3:.4f} mA", (0, Isc * 1e3),
             xytext=(5, 5), textcoords="offset points")
plt.annotate(f"Voc = {Voc:.4f} V", (Voc, 0),
             xytext=(-12, 8), textcoords="offset points", ha="right",
             bbox=dict(facecolor="white", edgecolor="none"))

plt.title("I-V Curve")
plt.xlabel("Voltage (V)")
plt.ylabel("Current (mA)")
plt.xlim(0, Voc * 1.05)
plt.ylim(0, Isc * 1e3 * 1.1)
plt.grid()

# plot 3 - P-V curve
plt.figure()
plt.plot(V, P * 1e6, color="orange")
plt.plot(Vmp, Pmax * 1e6, "ko")
plt.plot([Vmp, Vmp], [0, Pmax * 1e6], "--", color="gray")
plt.annotate(f"Pmax = {Pmax*1e6:.2f} µW\n{Vmp:.4f} V", (Vmp, Pmax * 1e6),
             xytext=(-15, -30), textcoords="offset points", ha="right")
plt.title("P-V Curve")
plt.xlabel("Voltage (V)")
plt.ylabel("Power (µW)")
plt.xlim(0, Voc * 1.05)
plt.ylim(0, Pmax * 1e6 * 1.1)
plt.grid()

plt.show()
