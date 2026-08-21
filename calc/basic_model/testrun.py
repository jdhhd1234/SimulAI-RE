from base_mode import TestBPTK
import matplotlib.pyplot as plt

model = TestBPTK()

print("time\tpopulation\tlabor\tproduction\tcapital")

#range에서 숫자 입력
for t in range(100):
    print(
        f"{t}\t"
        f"{model.evaluate_equation('population', t):.2f}\t"
        f"{model.evaluate_equation('labor', t):.2f}\t"
        f"{model.evaluate_equation('production', t):.2f}\t"
        f"{model.evaluate_equation('capital', t):.2f}"
    )