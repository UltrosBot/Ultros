"""Simple Python command interpreter"""

__author__ = 'Gareth Coles'

from code import InteractiveInterpreter


class Interpreter(InteractiveInterpreter):
    """Simple Python command interpreter"""

    write_callable = None

    def set_output(self, func):
        """Set the output function"""

        self.write_callable = func

    def write(self, data):
        """Write output"""

        self.write_callable(data)
