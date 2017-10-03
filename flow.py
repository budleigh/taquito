import threading
from selenium import webdriver


class FlowException(Exception):
    pass


def flow(route, ordinal, root_task=()):
    """
    Decorator enabling the configuration of flow routes.
    A 'flowroute' is a path through a particular 'flow'.
    For example, a path through the 'welcome flow' might
    include the routes 'email signin' and 'social signin'.

    Use:
        flag a test function in a flow class with this
        decorator, signifying route (string) name,
        ordinal (where in the route sequence it should
        be), and optionally a root_task.

    Root_task:
        root_task is used on PRIMARY ORDINAL route tasks
        only - it establishes a 'branching' route that
        depends on some (or all) of another route's final
        state. Use this to capture general first-steps in
        a flow, like signing in.
    :param route:
    :param ordinal:
    :param root_task:
    :return:
    """
    def inner(fn):
        package = {
            'route': route,
            'ordinal': ordinal,
            'fn': fn,
        }
        if root_task:
            if ordinal != 1:
                raise FlowException(
                    'cannot root on a non-1 flow task'
                )
            package['root'] = root_task
        return package
    return inner


class FlowRoute(object):
    """
    A potentially branching route through a flow.
    For example:
        The 'welcome' flow might have the routes
        'email signin' and 'social signin'.

    The internals of this shouldn't be of any interest
    to clients of the framework.
    """
    def __init__(self, name, root_ordinal=None, root_route=None):
        self.name = name
        self.sequence = []
        self.root_route = None
        self.root_ordinal = None

    def add_route_package(self, package):
        self._insert_package_sorted(package)

    def _insert_package_sorted(self, package):
        inserted = False
        for x in range(len(self.sequence)):
            seq_package = self.sequence[x]
            if seq_package['ordinal'] > package['ordinal']:
                self.sequence.insert(x, package)
                inserted = True
        if not inserted:
            self.sequence.append(package)

    def build_sequence(self, to_index=0):
        my_sequence = [
            package['fn'] for package in self.sequence
        ]
        if to_index:
            my_sequence = my_sequence[:to_index]

        if self.root_route:
            root_sequence = self.root_route.build_sequence(
                to_index=self.root_ordinal
            )
            return root_sequence + my_sequence
        else:
            return my_sequence

    def __getitem__(self, index):
        if type(index) != int:
            raise TypeError('indexed without a number')

        # since ordinals are 1-indexed
        return self.sequence[index - 1]


class Flow(object):
    """
    A flow defines an overarching user experience on
    a website. For example, a flow might be the
    'welcome flow', or a users experience on the welcome
    landing pages. There may be a number of branching
    routes through that flow - for instance, social
    signin vs. email signin in the welcome flow.

    Use:
        Subclass Flow to create a new flow. Define step
        functions in your flow that are the discreet
        events of that user experience. See the @flow
        decorator for more insight into how to annotate
        these task functions.

        Make sure to put _eggtest somewhere in your task
        functions. The class itself is parsed and processed
        to get ready for running.
    """
    def __init__(self):
        self.routes = self.build_routes()
        self.ensure_route_tree()
        self.passed_tests = set()
        self.failed_tests = set()
        self.seen_tests = set()

    def build_routes(self):
        routes = {}
        for member in dir(self):
            if '_eggtest' in member:
                package = getattr(self, member)
                if self.validate_package(package):
                    route = package['route']
                    if route not in routes:
                        routes[route] = FlowRoute(route)
                    routes[route].add_route_package(package)

        return routes

    def ensure_route_tree(self):
        """
        Ensures that route roots are properly applied across
        all routes (basically this builds our route tree, as
        the first pass building the routes may not have had
        all available connections built.
        :return:
        """
        for _, route in self.routes.items():
            root_details = route.sequence[0].get('root', None)
            if root_details:
                route_name, ordinal = root_details
                if route_name not in self.routes:
                    raise FlowException('no route named %s found to branch off' % route_name)

                route.root_route = self.routes[route_name]
                route.root_ordinal = ordinal

    def validate_package(self, package):
        if type(package) != dict:
            return False
        for key in ['fn', 'ordinal', 'route']:
            if key not in package:
                return False
        return True

    def launch_and_join_workers(self):
        workers = []
        workers_done = set()

        for _, route in self.routes.items():
            worker = RouteWorker(self, route)
            workers.append(worker)
            worker.start()

        while True:
            for worker in workers:
                if worker.done:
                    workers_done.add(worker)
            if len(workers_done) == len(workers):
                break

    def run_routes(self):
        self.launch_and_join_workers()


class RouteWorker(threading.Thread):
    """
    Basic paralellization of flow routes. Since
    dependencies are baked in to each individual
    route worker, we can do this safely as each
    has its own browser state.

    NOTE: this seems to not actually work right now.
    """
    def __init__(self, flow, route):
        threading.Thread.__init__(self)
        self.flow = flow
        self.route = route
        self.driver = webdriver.Chrome()
        self.done = False

    def run(self):
        sequence = self.route.build_sequence()

        for task in sequence:
            try:
                task(self.flow, self.driver)
                if task not in self.flow.seen_tests:
                    self.flow.seen_tests.add(task)
                    print('\t\t\033[92m %s passed' % task)
                self.flow.passed_tests.add(task)

            except BaseException as e:
                if task not in self.flow.seen_tests:
                    self.flow.seen_tests.add(task)
                    print(
                        '\t\t\033[91m %s failed: %s' %
                        (task, e)
                    )
                self.flow.failed_tests.add(task)
                break

        self.driver.close()
        self.done = True
