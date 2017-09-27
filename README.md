##TAQUITO
A basic selenium/python framework for running UI tests in an organized way.

    from flow import Flow, flow
    
    class WelcomeFlow(Flow):
        root_url = 'http://www.goodeggs.dev:3000'
    
        @flow('main', 1)
        def enter_zip_eggtest(self, driver):
            pass
    
        @flow('main', 2)
        def continue_with_email_eggtest(self, driver):
            raise Exception('hello')
    
        @flow('social', 1, root_task=('main', 1))
        def continue_with_facebook_eggtest(self, driver):
            pass
