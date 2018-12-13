L=[('b',2),('a',5),('c',3),('d',4)]
a = sorted(L, key=lambda x:x[1]) # 按第1列排序 # [('b', 2), ('c', 3), ('d', 4), ('a', 5)]
print(a)

L=[('b',2),('a',5),('c',3),('d',4)]
a = sorted(L, key=lambda x:x[0]) # 按第0列排序 # [('a', 5), ('b', 2), ('c', 3), ('d', 4)]
print(a)

