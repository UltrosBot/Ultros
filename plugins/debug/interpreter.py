__author__ = 'Gareth Coles'

from code import InteractiveInterpreter


class Interpreter(InteractiveInterpreter):

    write_callable = None

    def set_output(self, func):
        self.write_callable = func

    def write(self, data):
        self.write_callable(data)
