# Optimal Fault Current Limiter Allocation via Multi-Objective Genetic Algorithm (NSGA-II)

Multi-objective optimization of Fault Current Limiter (FCL) placement in power systems using NSGA-II. Simultaneously minimizes three-phase short-circuit currents and installation costs across all buses.

> **BSc Thesis** — Electrical Engineering, State University of Santa Cruz (UESC), 2019

## Results

### Pareto Front
![Pareto front — crowding distance](img/pareto2.png)

*Trade-off between total fault current reduction (f₁) and FCL installation cost (f₂). Each point represents a non-dominated solution. Crowding distance preserves diversity along the frontier.*

### Test System
![IEEE 15-bus system](img/15bus.png)

*IEEE 15-bus test system with impedance and topology data.*

## How It Works

The power system is modeled through the bus impedance matrix (Z_bus), obtained by inverting the admittance matrix (Y_bus). Three-phase short-circuit analysis is performed for all buses, computing fault currents, bus voltages, and line currents.

![NSGA-II flowchart](img/fluxograma_nsgaii.png)

**NSGA-II configuration:**
- **Encoding:** Binary (12 bits per individual — 3 groups of 4 bits), each group representing a candidate FCL at a specific bus
- **Objectives:** f₁ = minimize total short-circuit current · f₂ = minimize total FCL cost
- **Selection:** Binary tournament based on dominance rank + crowding distance
- **Crossover:** Uniform crossover with random binary mask
- **Mutation:** Bit-flip on randomly selected individual
- **Diversity:** Crowding distance on the Pareto frontier

## Project Structure

```
├── nsgaii.py              # Main NSGA-II implementation
├── 15BusTestSystems.xlsx  # Power system data (lines, impedances, base values)
├── conexoes.xlsx          # Primary/backup relay pairs
├── requirements.txt       # Python dependencies
├── img/                   # Diagrams and results
└── README.md
```

## Stack

Python 3.x · NumPy · Pandas · Matplotlib

## Quick Start

```bash
pip install numpy pandas matplotlib pythonds
python nsgaii.py
```

**Outputs:**
- `saida.xlsx` — FCL impedances for each individual in the final population
- `final.xlsx` — Solutions filtered by problem constraints (f₁ > 30, 0 < f₂ < 80)
- Pareto front scatter plot (f₁ × f₂)

## Key References

- Deb, K. et al. (2002). *A Fast and Elitist Multiobjective Genetic Algorithm: NSGA-II.* IEEE Trans. Evolutionary Computation.
- Mahmoudian, A. et al. (2017). *Multi objective optimal allocation of fault current limiters in power systems.* Int. J. Electrical Power and Energy Systems.
- Elmitwally, A. et al. (2015). *Optimal allocation of fault current limiters for sustaining overcurrent relays coordination.* Alexandria Engineering Journal.

## License

MIT