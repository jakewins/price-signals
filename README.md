# Toy scenarios for controlling devices with price signals

This contains some toy code that explores simplified scenarios of residential devices following price signals and capacity limits.

## Running the scenarios

You need the `uv` python package manager installed. With that installed you should be able to run scenarios like this:

    uv run python -m <name-of-scenario>

For instance, to run the first scenario:

    uv run python -m scenario_01__two_ev_sessions_no_coordination

## Scenarios

### 01: Two EV sessions, no coordination

This scenario has two identical EV sessions start at hour 0 in the home.
Each EV is able to fully charge in one hour without tripping the main breaker - but if both EVSEs charge concurrently, the breaker throws.

The EVSEs get prices and capacity (breaker) limits from some assumed local source, perhaps the smart meter.
As it stands, this scenario fails, because the devices see the same prices and capacity limits, so each schedules identically.

If I understand the proposal from Bruce, this scenario would be solved in one of two ways:

- The EVSEs negotiate capacity, such that each device get allocated individual capacity OR;
- Some scheduler sees that is happening and changes the local prices to make the devices "move around" to fit

To read the scenario, it may help to start in the main() function towards the bottom of it.



