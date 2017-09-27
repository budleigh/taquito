from selenium import webdriver


class Status(object):
    NOT_RUN = 1
    RUN_WIN = 2
    RUN_FAI = 3


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
    return inner


class FlowRoute(object):

    def __init__(self, name, root=()):
        self.name = name
        self.sequence = []
        self.root = root
        self.status = Status.NOT_RUN

    def add_route_package(self, package):
        pass


class Flow(object):
    root_url = ''

    def __init__(self):
        if not self.root_url:
            raise FlowException(
                'no root_url set on %s' % type(self).__name__
            )

        self.routes = self.load_routes()
        self.ensure_route_tree()
        self.driver = webdriver.Chrome()

    def load_routes(self):
        routes = {}
        for member in dir(self):
            if '_eggtest' in member:
                package = self.retrieve_package(member)
                route, fn, ord = (
                    package['route'],
                    package['fn'],
                    package['ord'],
                )


        return routes

    def ensure_route_tree(self):
        """
        Ensures that route roots are properly applied across
        all routes
        :return:
        """
        pass

    def retrieve_package(self, member):
        """
        Retrieve and validate an _eggtest member.
        :param member:
        :return:
        """
        package = getattr(self, member)
        if type(package) != dict:
            raise FlowException(
                'member %s is not annotated' %
                member
            )
        if ['fn', 'route', 'ordinal'] not in package:
            raise FlowException(
                'invalid flow package: %s' %
                package
            )

    def generate_run_sequence(self):
        # this is the meat of the operation
        # generates a linear task sequence
        # based on routes, branches and route roots
        task_set = [
            [k, v] for (k, v) in sorted(self.routes.items(), reverse=True)
        ]
        return task_set

    def run_tasks(self):
        sequence = self.generate_run_sequence()

        for task in sequence:
            try:
                task[1](self, self.driver)
                print(
                    '\t\t\033[92m %s passed' %
                    task[1].__name__
                )
            except BaseException as e:
                print(
                    '\t\t\033[91m failed task %s: %s' %
                    (task[1].__name__, e)
                )

        self.driver.close()
