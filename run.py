import os
from flows.welcome import WelcomeFlow


def build_flow_set():
    return [WelcomeFlow]


if __name__ == '__main__':
    print('launching taquito')
    flows = build_flow_set()

    for flow in build_flow_set():
        f = flow()
        flow_name = type(f).__name__
        print('\trunning %s' % flow_name)
        f.run_routes()
