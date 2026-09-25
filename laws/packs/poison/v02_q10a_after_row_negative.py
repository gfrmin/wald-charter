# expect: KERNEL_ROW
# rule: V2.5
# QUESTIONS.md Q10a: the After-act's kernel is a table, and every row a table writes is a distribution (SURFACE v0 section 4).
world("monitor", closed=True)
horizon(1, source="elicited")
depth(1, source="elicited")
space({"rel": ["good", "poor"]})
globals(["rel"])
prior({"good": 1/2, "poor": 1/2}, source="elicited")
utility({"ship": {"good": 0, "poor": 0}}, source="elicited")
price({"audit": 0}, source="elicited")
after("audit", kernel=table({"ship": {"good": {"pass": -9/10, "fail": 1/10}, "poor": {"pass": 3/5, "fail": 2/5}}}, source="elicited"), reads=["rel"])
