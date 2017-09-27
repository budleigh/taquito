import os
from flows.welcome import WelcomeFlow


def build_flow_set():
    return [WelcomeFlow]


if __name__ == '__main__':
    print('launching dat taquito flow')
    print('The sauce is the boss\n')
    flows = build_flow_set()

    for flow in build_flow_set():
        f = flow()
        flow_name = type(f).__name__
        try:
            print('\trunning %s' % flow_name)
            f.run_tasks()
        except BaseException as e:
            print('error: %s, aborting %s' % (e, flow_name))
            f.driver.close()
