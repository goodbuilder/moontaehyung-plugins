import json, sys
p = json.load(open(sys.argv[1]))["inputs"]
if min(p["capacitance"], p["duration"], *p["resistance"]) <= 0:
    sys.exit("nonpositive thermal parameters")
temperatures = []
for resistance in p["resistance"]:
    temperature = p["ambient"]
    dt = p["duration"] / 50000
    for _ in range(50000):
        temperature += dt * (p["power"] - (temperature-p["ambient"])/resistance) / p["capacitance"]
    temperatures.append(temperature)
print(json.dumps({"temperatures_C": temperatures}))
