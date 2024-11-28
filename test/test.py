import time


st = time.time()
time.sleep(0.5)
a = time.time()-st

st = time.time()
time.sleep(0.3)
a += time.time() - st
print(a)

st = time.time()
time.sleep(0.2)
a += time.time() - st
print(a)

st = time.time()
time.sleep(0.6)
a += time.time() - st
print(a)

st = time.time()
time.sleep(0.4)
a += time.time() - st
print(a)
