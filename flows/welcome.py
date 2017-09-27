from flows.flow import Flow, flow


class WelcomeFlow(Flow):
    root_url = 'http://www.goodeggs.dev:3000'

    @flow('main', 1)
    def enter_zip_eggtest(self, driver):
        pass

    @flow('main', 2)
    def continue_with_email_eggtest(self, driver):
        raise Exception('hello sir')

    @flow('social', 1, root_task=('main', 1))
    def continue_with_facebook(self, driver):
        pass
