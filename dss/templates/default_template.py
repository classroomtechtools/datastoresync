debug = False

class DefaultTemplate:

    def result_bool(self, result):
        return False

    def success(self, action, result):
        pass

    def fail(self, action, result):
        pass

    def __call__(self, action):
        debug and print(action.message)
        try:
            func_str = action.func_name   #action.message[:action.message.index('(')]
        except ValueError:
            print("WRONG FORMAT")
            return
        try:
            func = getattr(self, func_str)
        except AttributeError:
            debug and print('No attr {}: {}'.format(func_str, action.message))
            return
        return func(action)

