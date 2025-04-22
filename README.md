# Toy scenarios for controlling devices with price signals

This contains some toy code that explores simplified scenarios of residential devices following price signals and capacity limits.

## Running the scenarios

You need the `uv` python package manager installed. With that installed you should be able to run scenarios like this:

    uv run python -m <name-of-scenario>

For instance, to run the first scenario:

    uv run python -m scenario_01__two_ev_sessions_no_coordination

## Scenarios

To read the scenario, it may help to start in the main() function towards the bottom of it.

### 01: Two EV sessions, no coordination

This scenario has two identical EV sessions start at hour 0 in the home.
Each EV is able to fully charge in one hour without tripping the main breaker - but if both EVSEs charge concurrently, the breaker throws.

The EVSEs get prices and capacity (breaker) limits from some assumed local source, perhaps the smart meter.
As it stands, this scenario fails, because the devices see the same prices and capacity limits, so each schedules identically.

If I understand the proposal from Bruce, this scenario would be solved in one of three ways:

- A: The EVSEs request capacity, such that each device get allocated individual capacity OR;
- B: Scheduling is done in some central place (eg. a HEMS or similar system) and the scheduler models each device kind
- C: Scheduling is done in some central place but the scheduler is device kind agnostic, speaking only in prices and capacities 

If (B) is chosen, then the scheduler must *control* and *model* the EVSEs. 
In other words, the central scheduled needs to know things like state-of-charge, target state-of-charge, departure time.

If the scheduler must know the internals of the DER, then I would argue the price signal ought to terminate at the central scheduler.
The scheduler at this point needs a protocol to talk to the EVSE that communicates things like max current, departure times, states of charge and kWh's charged.
If a domain-specific protocol is needed already, it makes little sense - to me - to then turn around and use prices for control. 
The scheduler already talks to the DER in it's domain-specific language, and has calculated an energy schedule the DER should follow; it should just send that schedule.

The interesting question instead then becomes case (A) and (C) above - can a system be constructed that either removes central scheduling or makes it agnostic of device type?
And, if we can, are the capabilities of such a scheduling regime such that the home owner gets the same value out of their assets as they would in a centrally scheduled setup?

### 02: Same as 01, but with negotiated capacites

This scenario is not implemented yet.

This then becomes the first interesting scenario for me to understand. 
How would we extend scenario 01 to not surpass the main breaker, without introducing a central scheduler that knows the "innards" of the DERs it controls?

### Other scenarios / things I'd like to explore

- Two EVs, where the first arriving EV needs to "move" its schedule to make space for the second one
- Two EVs with happy schedules, and then a desire from an aggregator to move some kWhs of energy from H00 to, say, H02
- One EV and one PV system, with asymmetrical tariffs such that the EV curtailing causes net export at different prices than the EV charging costs