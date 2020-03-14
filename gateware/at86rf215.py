from nmigen import *
from nmigen.build import *
from nmigen_boards.ecp5_5g_evn import *


I_SYNC = 0b10
Q_SYNC = 0b01

class Blinky(Elaboratable):
    def elaborate(self, platform):
        m = Module()

        led   = platform.request("led", 0)
        led2  = platform.request("led", 1)
        sync_i = platform.request("sync_i", 0)
        sync_q = platform.request("sync_q", 0)
        rxd24 = platform.request("rxd24", 0)
        txclk = platform.request("txclk", 0)
        txd = platform.request("txd", 0)
        rxd24_delay = Signal()
        rxd24_data = Signal(2)
        txd_data = Signal(2)
        timer = Signal(20)

        m.submodules += [
            Instance("DELAYG",
                p_DEL_MODE="SCLK_CENTERED",
                i_A=rxd24,
                o_Z=rxd24_delay,
            ),
            Instance("IDDRX1F",
                i_D=rxd24_delay,
                i_SCLK=ClockSignal(),
                i_RST=Const(0),
                o_Q0=rxd24_data[1],
                o_Q1=rxd24_data[0],
            ),
            Instance("ODDRX1F",
                i_D0=txd_data[1],
                i_D1=txd_data[0],
                i_SCLK=ClockSignal(),
                i_RST=Const(0),
                o_Q=txd,
            ),
        ]

        m.d.comb += txclk.eq(ClockSignal())

        m.d.comb += led.o.eq(timer[-1])
        data_count = Signal(3)
        m.d.sync += [
            sync_i.eq(0),
            sync_q.eq(0),
            txd_data.eq(rxd24_data)
        ]
        with m.FSM() as fsm:
            with m.State("I_SYNC"):
                with m.If(rxd24_data == I_SYNC):
                    m.next = "I_DATA"
                    m.d.sync += [
                        data_count.eq(0),
                        sync_i.eq(1),
                    ]

            with m.State("I_DATA"):
                with m.If(data_count == 6):
                    m.next = "Q_SYNC"
                m.d.sync += data_count.eq(data_count + 1)

            with m.State("Q_SYNC"):
                with m.If(rxd24_data == Q_SYNC):
                    m.next = "Q_DATA"
                    m.d.sync += [
                        data_count.eq(0),
                        sync_q.eq(1),
                    ]
                with m.Else():
                    m.next = "I_SYNC"

            with m.State("Q_DATA"):
                with m.If(data_count == 6):
                    m.next = "I_SYNC"
                    m.d.sync += timer.eq(timer + 1)
                m.d.sync += data_count.eq(data_count + 1)

        return m


if __name__ == "__main__":
    platform = ECP55GEVNPlatform()
    platform.default_clk = "rxclk"
    resources = [
        Resource("rxclk", 0, DiffPairs("F2", "E2", dir="i"), Attrs(IO_TYPE="LVDS", DIFFRESISTOR="100", PULLMODE="UP")),
        Resource("txclk", 0, DiffPairs("G3", "F3", dir="o"), Attrs(IO_TYPE="LVDS")),
        Resource("rxd24", 0, DiffPairs("H5", "H3", dir="i"), Attrs(IO_TYPE="LVDS", DIFFRESISTOR="100")),
        Resource("txd",   0, DiffPairs("H4", "G5", dir="o"), Attrs(IO_TYPE="LVDS")),
        Resource("sync_i", 0, Pins("C2", dir="o"), Attrs(IO_TYPE="LVCMOS25")),
        Resource("sync_q", 0, Pins("B2", dir="o"), Attrs(IO_TYPE="LVCMOS25")),
    ]
    platform.add_resources(resources)
    platform.build(Blinky(), do_program=True)
