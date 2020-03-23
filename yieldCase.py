def case():
    print('--start--')

    m = yield 'start shutdown'

    print('--mid-- 获取外层传递到中断yield的值：' + m)

    k = yield "mid shutdown"

    print("--end-- 获取外层传递到中断yield的值：" + k)


def casetest():
    try:
        flag = case()
        k = flag.send(None)

        print("第一次中断返回结果：" + k)

        print("向中断yield中传递标识：" + "uzdz")
        v = flag.send('uzdz')

        print("第二次中断返回结果：" + v)

        print("向中断yield中传递标识：" + "dongzhen")
        flag.send('dongzhen')
    except StopIteration as ex:
        print("生成器无法找到下一个yield，抛出StopIteration异常！" + ex)

if __name__ == '__main__':
    casetest()

