from data import load_train, load_test
import matplotlib.pyplot as plt


tr, te = load_train(path=r"D:\CMAPSSData"), load_test(path=r"D:\CMAPSSData")
print(tr.shape, tr["unit"].nunique(), "engines")   # expect 100 engines
print(te.shape)                                    # expect (100, ...)

e = tr[tr.unit == 1]
for s in ["s2", "s7", "s11", "s12"]:
    plt.plot(e["cycle"], e[s], label=s)
plt.legend(); plt.xlabel("cycle"); plt.show()