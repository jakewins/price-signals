from __future__ import annotations
import dataclasses
import datetime
from util import Amps, KWh, EurPwrKWh, VOLTAGE, HourlyTimeseries


# Key times in our simulation, a simpler time
H0000 = datetime.datetime.fromisoformat('2000-01-01T00:00:00Z')
H0100 = datetime.datetime.fromisoformat('2000-01-01T01:00:00Z')
H0200 = datetime.datetime.fromisoformat('2000-01-01T02:00:00Z')
H0300 = datetime.datetime.fromisoformat('2000-01-01T03:00:00Z')

class Events:
    # Things that can happen in this scenario

    @dataclasses.dataclass(frozen=True)
    class NewLocalPrices:
        """
        Some local system emitted calculated local price, like a HEMS communicating over
        OpenADR to local devices.
        """
        occurred_at: datetime.datetime
        prices: HourlyTimeseries[EurPwrKWh]

    @dataclasses.dataclass(frozen=True)
    class NewCapacityLimit:
        """
        Same as prices but communicating capacity limits for the local breaker
        """
        occurred_at: datetime.datetime
        import_limits: HourlyTimeseries[Amps]
        # omitting export for now b/c we don't have any export in this simulation

    @dataclasses.dataclass(frozen=True)
    class EVConnected:
        """
        An electric vehicle connected to some supply equipment
        """
        occurred_at: datetime.datetime

        evse_id: str
        # We imagine the EVSE finds out this information from the EV via
        # the newer charging protocols.
        # What's the state-of-charge?
        current_battery_level: KWh
        # What state-of-charge does the car want to reach?
        target_battery_level: KWh
        # When does it want the SoC?
        depart_at: datetime.datetime


    Any = NewLocalPrices | NewCapacityLimit | EVConnected

@dataclasses.dataclass
class EVSE:
    # Stateful model of an EVSE; this is highly simplified, for instance it only
    # schedules once when the EV plugs in

    device_id: str
    max_current: Amps

    # State this EVSE has built up - probably represented in a more organized way - from
    # things that have happened. Prices, capacity limits, connected EV parameters
    prices: HourlyTimeseries[EurPwrKWh] = HourlyTimeseries(H0000, [])
    import_limits: HourlyTimeseries[Amps] = HourlyTimeseries(H0000, [])

    # If there is an EV connected that needs charging, what is the planned schedule?
    current_schedule: HourlyTimeseries[Amps] = HourlyTimeseries(H0000, [])

    def step(self, event: Events.Any):
        """ Run one step of the simulation - some event occurred. """
        match event:
            case Events.NewLocalPrices(): self.prices = event.prices
            case Events.NewCapacityLimit(): self.import_limits = event.import_limits
            case Events.EVConnected():
                # An EV connected to us! Let's schedule it.

                # Hourly slots we *could* use, with the price and capacity limit of each
                options: list[tuple[datetime.datetime, EurPwrKWh, Amps]] = [
                    # Each option has a max current either limited by the EVSE, or by the main breaker; in practice
                    # there'd also be additional sources of limits, like the DSO emitting capacity limitations
                    (p_span.start, p_span.value, min(self.import_limits.at(p_span.start), self.max_current))
                    for p_span in self.prices
                    if p_span.start < event.depart_at
                ]
                # Schedule "into" cheapest options until we meet target; sort so we can "pop" the next cheapest option
                # off the end of the list
                options.sort(key=lambda o: o[1], reverse=True)

                remaining_kwh = event.target_battery_level - event.current_battery_level
                # Start with an empty schedule
                schedule = HourlyTimeseries(event.occurred_at, [Amps(0), Amps(0), Amps(0), Amps(0)])
                while remaining_kwh > 0:
                    option_ts, _, option_amps = options.pop()
                    remaining_kwh -= KWh(VOLTAGE * option_amps)
                    schedule = schedule.set(option_ts, option_amps)
                self.current_schedule = schedule


@dataclasses.dataclass
class World:
    """ Our overall simulated universe - in this case, just a home with EVSEs. """
    evses: list[EVSE]

    def step(self, event: Events.Any):
        """ Run one step of the simulation, processing some event that occurred. """
        match event:
            case Events.NewLocalPrices() | Events.NewCapacityLimit():
                # Fan-out to all evses
                for evse in self.evses:
                    evse.step(event)
            case Events.EVConnected(evse_id=evse_id):
                # This event is assumed to "arrive" in the communication path between
                # the EV and the EVSE, so only the relevant EVSE "sees" this
                evse = next(e for e in self.evses if e.device_id == evse_id)
                evse.step(event)


# This is our simulated scenario; we set up a world and play some events through it
def main():
    main_breaker = Amps(30)
    evse_roger = EVSE(device_id="roger", max_current=Amps(20))
    evse_danny = EVSE(device_id="danny", max_current=Amps(20))
    world = World(
        evses=[
            # Two EVSEs at the home, together capable of exceeding the panel max
            evse_roger,
            evse_danny,
        ]
    )

    # Assume something like the Smart Meter communicates the main breaker size via OpenADR
    world.step(Events.NewCapacityLimit(
        H0000,
        import_limits=HourlyTimeseries(H0000, [main_breaker, main_breaker, main_breaker, main_breaker])))

    # Assume something like the Smart Meter communicates local price via OpenADR or similar
    world.step(Events.NewLocalPrices(
        H0000,
        # Increasing prices - cheapest to charge H00, incrementing from there
        prices=HourlyTimeseries(H0000, [EurPwrKWh(1), EurPwrKWh(2), EurPwrKWh(3), EurPwrKWh(4)])))

    # Actual things happen! At H0000, a first EV connects
    world.step(Events.EVConnected(
        H0000,
        evse_id=evse_roger.device_id,
        current_battery_level=KWh(0),
        # We want the battery level to be at a level that's achievable if we get to
        # 100% subscribe the breaker for 1 hour
        target_battery_level=KWh(main_breaker * VOLTAGE / 1000.0),
        # Happy to charge in any of the three simulated hours, as long as we're full by H03
        depart_at=H0300,
    ))

    # At this point we expect the EVSE to have picked an optimal charging plan like this
    assert evse_roger.current_schedule == HourlyTimeseries(
        H0000,
        [
            # Should fully charge in the first, cheapest, hour
            Amps(20),
            # Then idle
            Amps(0),
            Amps(0),
            Amps(0),
        ]
    ), f"incorrect schedule: {evse_roger.current_schedule}"

    # So far so good.
    # Now the second EV shows up (again we set the timestamp to H0000, so in the simulation this all happens
    # at the same logical time, but the logical order of events is as outlined in this function)
    world.step(Events.EVConnected(
        H0000,
        evse_id=evse_danny.device_id,
        # Same SoC current->target reqs as the other one: Charge for 1hr at max amps to meet target
        current_battery_level=KWh(0),
        target_battery_level=KWh(main_breaker * VOLTAGE / 1000.0),
        # Same departure time as the other one: Eg. this EV is identical to the other one
        depart_at=H0300,
    ))

    # Now what needs to have happened is the two identical charging sessions are - via some mechanism - coordinated
    # so as to share the space provided by the main breaker.
    for t in [H0000, H0100, H0200, H0300]:
        total_amps = Amps(sum(evse.current_schedule.at(t) for evse in world.evses))
        assert total_amps <= main_breaker, f"schedules exceed main breaker at {t}, total amps drawn is {total_amps}"


if __name__ == "__main__":
    main()
