# SURFACE v0.2 session 2, 2.2: a monitor, every component Global; one pass moves P(good) to 3/5.
# exercises: V2.1, V2.4
# A monitor: the only terminal pays 0; the After-act audits the instrument. rel persists.
world("monitor", closed=True)
horizon(1, source="elicited")
depth(1, source="elicited")
space({"rel": ["good", "poor"]})
globals(["rel"])
prior({"good": 1/2, "poor": 1/2}, source="elicited")
utility({"ship": {"good": 0, "poor": 0}}, source="elicited")
price({"audit": 0}, source="elicited")
after("audit", kernel=table({"ship": {"good": {"pass": 9/10, "fail": 1/10}, "poor": {"pass": 3/5, "fail": 2/5}}}, source="elicited"), reads=["rel"])
