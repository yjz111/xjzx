def fun1(f):
    def fun():
        print('1')
        f()
    return fun
def fun2(f):
    def fun():
        print('2')
        f()
    return fun
@fun1
@fun2
def fun3():
    print('3')

if __name__ == '__main__':
    fun3()