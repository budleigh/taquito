##TAQUITO
A basic selenium/python framework for running UI tests in an organized way.

    from flow import Flow, flow
    
    class WelcomeFlow(Flow):
        @flow('main', 1)
        def enter_zip_eggtest(self, driver):
            driver.get('www.google.com')
            assert('Google' in driver.page_data)
    
        @flow('main', 2)
        def continue_with_email_eggtest(self, driver):
            raise Exception('this will generate red text')
    
        @flow('social', 1, root_task=('main', 1))
        def continue_with_facebook_eggtest(self, driver):
            # this will generate a sequence of commands
            # from the task '1' of route 'main' - meaning
            # all tasks leading up to route 1 of main 
            # including 1 will execute in this route thread
            pass
