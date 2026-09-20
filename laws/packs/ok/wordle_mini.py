# Wordle on three words. Feedback is a host instrument: a pure function of the state, so its rows sum to 1 by construction.
world("wordle mini", closed=True)
clock(horizon=3, depth=3, source="data")
space(answer=["cat", "cot", "dog"])
prior({"cat": 1/3, "cot": 1/3, "dog": 1/3}, source="data")
utility({"give up": {"cat": -10, "cot": -10, "dog": -10}},
        ending={"cat": {"ggg": {"cat": 0, "cot": 0, "dog": 0}},
                "cot": {"ggg": {"cat": 0, "cot": 0, "dog": 0}},
                "dog": {"ggg": {"cat": 0, "cot": 0, "dog": 0}}}, source="data")
price({"cat": 1, "cot": 1, "dog": 1}, source="data")
act("cat", once=True, kernel=host("fb_cat"))
act("cot", once=True, kernel=host("fb_cot"))
act("dog", once=True, kernel=host("fb_dog"))
