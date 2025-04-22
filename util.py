from __future__ import annotations
import dataclasses
import typing as t
import datetime

Amps = t.NewType("Amps", float)
Volts = t.NewType("Volts", float)
KW = t.NewType("KW", float)
KWh = t.NewType("KWh", float)
EurPwrKWh = t.NewType("EurPwrKWh", float)

# To simplify we imagine the whole home is on a single-phase 240VAC circuit
VOLTAGE = Volts(240)
HOUR = datetime.timedelta(hours=1)


@dataclasses.dataclass(frozen=True)
class HourlyTimeseries[T]:
    """ Immutable hourly timeseries """

    @dataclasses.dataclass
    class Span[T]:
        start: datetime.datetime
        end: datetime.datetime
        value: T

    # To simplify the simulation we represent everything in discrete hourly steps; in practice
    # the timeline is continuous.
    start: datetime.datetime
    values: list[T]

    def __iter__(self) -> t.Iterator[Span[T]]:
        t = self.start
        for v in self.values:
            yield HourlyTimeseries.Span(t, t + HOUR, v)
            t += HOUR

    def at(self, search: datetime.datetime) -> T:
        t = self.start
        vs = iter(self.values)
        v = next(vs)
        while t > search:
            t += HOUR
            v = next(vs)
        return v

    def set(self, hour: datetime.datetime, v: T) -> HourlyTimeseries[T]:
        """ Return a new timeseries that is a copy of this one with the given hour replaced with v"""
        values = list(self.values)
        values[int((hour - self.start) / HOUR)] = v
        return HourlyTimeseries(self.start, values)
