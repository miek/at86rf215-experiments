from nmigen import *
from nmigen_boards.ecp5_5g_evn import *


class Blinky(Elaboratable):
    def elaborate(self, platform):
        led   = platform.request("led", 0)
        timer = Signal(20)

        m = Module()
        m.d.sync += timer.eq(timer + 1)
        m.d.comb += led.o.eq(timer[-1])
        return m


if __name__ == "__main__":
    platform = ECP55GEVNPlatform()
    platform.build(Blinky(), do_program=True)
