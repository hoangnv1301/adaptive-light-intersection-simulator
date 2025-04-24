# Dual Mode Traffic Simulation

This simulation allows you to compare two traffic signal timing strategies side by side:
1. The adaptive timing system (left window) - Adjusts signal times based on traffic volume
2. The fixed timing system (right window) - Uses a fixed 30-second green time for all signals

## How to Run

Run the dual mode simulation with:

```
python dual_mode_simulation.py
```

This will open a side-by-side comparison with two traffic simulations running in parallel:
- Left side: Original adaptive traffic timing logic
- Right side: Fixed 30-second timing for each signal

## Features

- Both simulations run with identical vehicle generation patterns
- Accidents that occur in one simulation will also appear in the other
- Each simulation displays:
  - Signal states and timers
  - Number of vehicles that have crossed each intersection
  - Number of vehicles waiting at each lane
  - Time elapsed
  
## Purpose

This dual-mode simulation helps to visually compare the efficiency of adaptive vs. fixed-time traffic signal systems under identical conditions. The comparison can provide insights into:
- How adaptive timing responds to varying traffic patterns
- Where fixed timing may be sufficient vs. where adaptive timing offers clear benefits
- The impact of both systems during accident scenarios

## Implementation Details

The implementation doesn't affect the original simulation logic. It creates a separate copy of all necessary components for the fixed timing simulation while keeping the adaptive simulation intact. 