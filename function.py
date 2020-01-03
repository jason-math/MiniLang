from value_types import *
from symbol_table import *
from context import *


class Function(Value):
    def __init__(self, name, body, arg_names):
        super().__init__()
        self.name = name or '<NULL>'
        self.body = body
        self.arg_names = arg_names

    def execute(self, args):
        response = RTResult()
        interpreter = Interpreter()
        new_context = Context(self.name, self.context, self.pos_start)
        new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)
        if len(args) > len(self.arg_names):
            return response.failure(RTError(self.pos_start,
                                            self.pos_end,
                                            f"{len(args) - len(self.arg_names)} too many args "
                                            f"passed into '{self.name}'", self.context))
        if len(args) < len(self.arg_names):
            return response.failure(RTError(self.pos_start,
                                            self.pos_end,
                                            f"{len(self.arg_names) - len(args)} too few args "
                                            f"passed into '{self.name}'", self.context))
        for i in range(len(args)):
            arg_name = self.arg_names[i]
            arg_val = args[i]
            arg_val.set_context(new_context)
            new_context.symbol_table.set(arg_name, arg_val)

        val = response.register(interpreter.visit(self.body, new_context))
        if response.error:
            return response
        return response.success(val)

    def copy(self):
        copy = Function(self.name, self.body, self.arg_names)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self):
        return f"<function {self.name}>"
