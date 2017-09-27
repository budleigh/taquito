import threading
from selenium import webdriver


class FlowException(Exception):
    pass


def flow(route, ordinal, root_task=()):
    # root task may be another pair of [route, ordinal]
    # that signifies a point at which to branch into
    # a new route - this should only be used at the
    # first step of a new route
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
    root_url = ''

    def __init__(self):
        if not self.root_url:
            raise FlowException(
                'no root_url set on %s' % type(self).__name__
            )

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
                    route, fn, ord = (
                        package['route'],
                        package['fn'],
                        package['ordinal'],
                    )

                    if route not in routes:
                        routes[route] = FlowRoute(route)
                    routes[route].add_route_package(package)

        return routes

    def ensure_route_tree(self):
        """
        Ensures that route roots are properly applied across
        all routes (basically this builds our route tree, as
        the first pass building the routes may not have had
        all available connections built
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

    def generate_run_sequence(self):
        # this is the meat of the operation
        # generates a linear task sequence
        # based on routes, branches and route roots
        task_set = [
            [k, v] for (k, v) in sorted(self.routes.items(), reverse=True)
        ]
        return task_set

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
