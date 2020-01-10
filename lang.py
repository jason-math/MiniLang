from context import *
from symbol_table import *
import string
from error_handling import *
from node_types import *
import os
import math

# Constants
DIGITS = '0123456789'
LETTERS = string.ascii_letters
LETTERS_DIGITS = LETTERS + DIGITS

# Token Types
TT_INT = 'INT'
TT_FLOAT = 'FLOAT'
TT_STRING = 'STRING'
TT_IDENTIFIER = 'IDENTIFIER'
TT_KEYWORD = 'KEYWORD'
TT_EQ = 'EQ'

TT_ADD = 'ADD'
TT_SUB = 'SUB'
TT_MUL = 'MUL'
TT_DIV = 'DIV'
TT_MOD = 'MOD'
TT_LPAR = 'LPAR'
TT_RPAR = 'RPAR'
TT_POW = 'POW'

TT_EEQ = 'EEQ'
TT_NEQ = 'NEQ'
TT_LT = 'LT'
TT_GT = 'GT'
TT_LTE = 'LTE'
TT_GTE = 'GTE'

TT_COMMA = 'COMMA'
TT_ARROW = 'ARROW'
TT_LBRAK = 'LBRAK'
TT_RBRAK = 'RBRAK'
TT_EOL = 'EOL'

TT_EOF = 'EOF'

KEYWORDS = [
    'VAR',
    'AND',
    'OR',
    'NOT',
    'IF',
    'THEN',
    'END',
    'ELIF',
    'ELSE',
    'FOR',
    'TO',
    'STEP',
    'WHILE',
    'FUN',
    'RETURN',
    'CONTINUE',
    'BREAK'
]


# Position Class
class Position:
    def __init__(self, index, ln, col, file_name, file_txt):
        self.index = index
        self.ln = ln
        self.col = col
        self.file_name = file_name
        self.file_txt = file_txt

    def advance(self, curr_char=None):
        self.index += 1
        self.col += 1

        if curr_char == '\n':
            self.ln += 1
            self.col = 0

        return self

    def copy(self):
        return Position(self.index, self.ln, self.col, self.file_name, self.file_txt)


# Token Class
class Token:
    def __init__(self, type_, val=None, pos_start=None, pos_end=None):
        self.type = type_
        self.val = val

        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance()
        if pos_end:
            self.pos_end = pos_end

    def matches(self, type_, val):
        return self.type == type_ and self.val == val

    # String representation
    def __repr__(self):
        if self.val:
            return f'{self.type}:{self.val}'
        else:
            return f'{self.type}'


class Lexer:
    def __init__(self, file_name, text):
        self.file_name = file_name
        self.text = text
        self.pos = Position(-1, 0, -1, file_name, text)
        self.curr_char = None
        self.advance()

    def advance(self):
        self.pos.advance(self.curr_char)
        self.curr_char = self.text[self.pos.index] if self.pos.index < len(self.text) else None

    def make_tokens(self):
        tokens = []
        while self.curr_char is not None:
            if self.curr_char in ' \t':
                self.advance()
            elif self.curr_char in ';\n':
                tokens.append(Token(TT_EOL, pos_start=self.pos))
                self.advance()
            elif self.curr_char == '#':
                self.skip_comment()
            elif self.curr_char in DIGITS:
                tokens.append(self.make_num())
            elif self.curr_char in LETTERS:
                tokens.append(self.make_identifier())
            elif self.curr_char == '"':
                tokens.append(self.make_string())
            elif self.curr_char == '+':
                tokens.append(Token(TT_ADD, pos_start=self.pos))
                self.advance()
            elif self.curr_char == '-':
                tokens.append(self.make_sub_or_arrow())
            elif self.curr_char == '*':
                tokens.append(Token(TT_MUL, pos_start=self.pos))
                self.advance()
            elif self.curr_char == '/':
                tokens.append(Token(TT_DIV, pos_start=self.pos))
                self.advance()
            elif self.curr_char == '%':
                tokens.append(Token(TT_MOD, pos_start=self.pos))
                self.advance()
            elif self.curr_char == '^':
                tokens.append(Token(TT_POW, pos_start=self.pos))
                self.advance()
            elif self.curr_char == '(':
                tokens.append(Token(TT_LPAR, pos_start=self.pos))
                self.advance()
            elif self.curr_char == ')':
                tokens.append(Token(TT_RPAR, pos_start=self.pos))
                self.advance()
            elif self.curr_char == '[':
                tokens.append(Token(TT_LBRAK, pos_start=self.pos))
                self.advance()
            elif self.curr_char == ']':
                tokens.append(Token(TT_RBRAK, pos_start=self.pos))
                self.advance()
            elif self.curr_char == ',':
                tokens.append(Token(TT_COMMA, pos_start=self.pos))
                self.advance()
            elif self.curr_char == '!':
                token, error = self.make_not_equals()
                if error:
                    return [], error
                tokens.append(token)
            elif self.curr_char == '=':
                tokens.append(self.make_equals())
            elif self.curr_char == '<':
                tokens.append(self.make_less_than())
            elif self.curr_char == '>':
                tokens.append(self.make_greater_than())
            else:
                pos_start = self.pos.copy()
                char = self.curr_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, "'" + char + "'")
        tokens.append(Token(TT_EOF, pos_start=self.pos))
        return tokens, None

    def make_num(self):
        num_str = ''
        dot_count = 0
        pos_start = self.pos.copy()

        while self.curr_char is not None and self.curr_char in DIGITS + '.':
            if self.curr_char == '.':
                if dot_count == 1:
                    break
                dot_count += 1
                num_str += '.'
            else:
                num_str += self.curr_char
            self.advance()

        if dot_count == 0:
            return Token(TT_INT, int(num_str), pos_start, self.pos)
        else:
            return Token(TT_FLOAT, float(num_str), pos_start, self.pos)

    def make_string(self):
        str_builder = ''
        pos_start = self.pos.copy()
        esc_char = False
        self.advance()
        esc_char_list = {
            'n': '\n',
            't': '\t',
        }

        while self.curr_char is not None and (self.curr_char != '"' or esc_char):
            if esc_char:
                str_builder += esc_char_list.get(self.curr_char, self.curr_char)
                esc_char = False
            else:
                if self.curr_char == '\\':
                    esc_char = True
                else:
                    str_builder += self.curr_char
            self.advance()
        self.advance()
        return Token(TT_STRING, str_builder, pos_start, self.pos)

    def make_identifier(self):
        id_str = ''
        pos_start = self.pos.copy()

        while self.curr_char is not None and self.curr_char in LETTERS_DIGITS + '_':
            id_str += self.curr_char
            self.advance()

        token_type = TT_KEYWORD if id_str in KEYWORDS else TT_IDENTIFIER
        return Token(token_type, id_str, pos_start, self.pos)

    def make_sub_or_arrow(self):
        token_type = TT_SUB
        pos_start = self.pos.copy()
        self.advance()
        if self.curr_char == '>':
            self.advance()
            token_type = TT_ARROW
        return Token(token_type, pos_start=pos_start, pos_end=self.pos)

    def make_not_equals(self):
        pos_start = self.pos.copy()
        self.advance()
        if self.curr_char == '=':
            self.advance()
            return Token(TT_NEQ, pos_start=pos_start, pos_end=self.pos), None

        self.advance()
        return None, ExpectedCharError(pos_start, self.pos, "'=' (after '!')")

    def make_equals(self):
        token_type = TT_EQ
        pos_start = self.pos.copy()
        self.advance()

        if self.curr_char == '=':
            self.advance()
            token_type = TT_EEQ

        return Token(token_type, pos_start=pos_start, pos_end=self.pos)

    def make_less_than(self):
        token_type = TT_LT
        pos_start = self.pos.copy()
        self.advance()

        if self.curr_char == '=':
            self.advance()
            token_type = TT_LTE

        return Token(token_type, pos_start=pos_start, pos_end=self.pos)

    def make_greater_than(self):
        token_type = TT_GT
        pos_start = self.pos.copy()
        self.advance()

        if self.curr_char == '=':
            self.advance()
            token_type = TT_GTE

        return Token(token_type, pos_start=pos_start, pos_end=self.pos)

    def skip_comment(self):
        self.advance()
        while self.curr_char != '\n':
            self.advance()
        self.advance()


class Value:
    def __init__(self):
        self.set_pos()
        self.set_context()
        self.pos_start = None
        self.pos_end = None
        self.context = None

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def add_to(self, other):
        return None, self.illegal_operation(other)

    def sub_by(self, other):
        return None, self.illegal_operation(other)

    def mul_by(self, other):
        return None, self.illegal_operation(other)

    def div_by(self, other):
        return None, self.illegal_operation(other)

    def pow_by(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_eeq(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_neq(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_lt(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_gt(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_lte(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_gte(self, other):
        return None, self.illegal_operation(other)

    def and_with(self, other):
        return None, self.illegal_operation(other)

    def or_with(self, other):
        return None, self.illegal_operation(other)

    def not_of(self):
        return None, self.illegal_operation()

    def execute(self, args):
        return RTResult().failure(self.illegal_operation())

    def copy(self):
        raise Exception('No copy method defined')

    def is_true(self):
        return False

    def illegal_operation(self, other=None):
        if not other:
            other = self
        return RTError(
            self.pos_start, other.pos_end,
            'Illegal operation',
            self.context
        )


class Number(Value):
    def __init__(self, val):
        super().__init__()
        self.val = val

    def add_to(self, other):
        if isinstance(other, Number):
            return Number(self.val + other.val).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def sub_by(self, other):
        if isinstance(other, Number):
            return Number(self.val - other.val).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def mul_by(self, other):
        if isinstance(other, Number):
            return Number(self.val * other.val).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def div_by(self, other):
        if isinstance(other, Number):
            if other.val == 0:
                return None, RTError(other.pos_start, other.pos_end,
                                     'Division by Zero', self.context)
            return Number(self.val / other.val).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def mod_by(self, other):
        if isinstance(other, Number):
            if other.val == 0:
                return None, RTError(other.pos_start, other.pos_end,
                                     'Division by Zero', self.context)
            return Number(self.val % other.val).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def pow_by(self, other):
        if isinstance(other, Number):
            return Number(self.val ** other.val).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def get_comparison_eeq(self, other):
        if isinstance(other, Number):
            return Number(int(self.val == other.val)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def get_comparison_neq(self, other):
        if isinstance(other, Number):
            return Number(int(self.val != other.val)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def get_comparison_lt(self, other):
        if isinstance(other, Number):
            return Number(int(self.val < other.val)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def get_comparison_gt(self, other):
        if isinstance(other, Number):
            return Number(int(self.val > other.val)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def get_comparison_lte(self, other):
        if isinstance(other, Number):
            return Number(int(self.val <= other.val)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def get_comparison_gte(self, other):
        if isinstance(other, Number):
            return Number(int(self.val >= other.val)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def and_with(self, other):
        if isinstance(other, Number):
            return Number(int(self.val and other.val)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def or_with(self, other):
        if isinstance(other, Number):
            return Number(int(self.val or other.val)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)

    def not_of(self):
        return Number(1 if self.val == 0 else 0).set_context(self.context), None

    def is_true(self):
        return self.val != 0

    def copy(self):
        copy = Number(self.val)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __repr__(self):
        return str(self.val)


Number.null = Number(0)
Number.false = Number(0)
Number.true = Number(1)
Number.math_PI = Number(math.pi)


class String(Value):
    def __init__(self, val):
        super().__init__()
        self.val = val

    def add_to(self, other):
        if isinstance(other, String):
            return String(self.val + other.val).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def mul_by(self, other):
        if isinstance(other, Number):
            return String(self.val * other.val).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def is_true(self):
        return len(self.val) > 0

    def copy(self):
        copy = String(self.val)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __str__(self):
        return self.val

    def __repr__(self):
        return f'"{self.val}"'


class List(Value):
    def __init__(self, elements):
        super().__init__()
        self.elements = elements

    def add_to(self, other):
        new_list = self.copy()
        new_list.elements.append(other)
        return new_list, None

    def sub_by(self, other):
        if isinstance(other, Number):
            new_list = self.copy()
            try:
                new_list.elements.pop(other.val)
                return new_list, None
            except RuntimeError:
                return None, RTError(other.pos_start, other.pos_end,
                                     'IndexOutOfBoundsException', self.context)
        else:
            return None, Value.illegal_operation(self, other)

    def mul_by(self, other):
        if isinstance(other, List):
            new_list = self.copy()
            new_list.elements.extend(other.elements)
            return new_list, None
        else:
            return None, Value.illegal_operation(self, other)

    def div_by(self, other):
        if isinstance(other, Number):
            try:
                return self.elements[other.val], None
            except RuntimeError:
                return None, RTError(other.pos_start, other.pos_end,
                                     'IndexOutOfBoundsException', self.context)
        else:
            return None, Value.illegal_operation(self, other)

    def copy(self):
        copy = List(self.elements)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __str__(self):
        return ", ".join([str(x) for x in self.elements])

    def __repr__(self):
        return f'[{", ".join([str(x) for x in self.elements])}]'


class BaseFunction(Value):
    def __init__(self, name):
        super().__init__()
        self.name = name or '<NULL>'

    def make_new_context(self):
        new_context = Context(self.name, self.context, self.pos_start)
        new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)
        return new_context

    def check_args(self, arg_names, args):
        response = RTResult()
        if len(args) > len(arg_names):
            return response.failure(RTError(self.pos_start,
                                            self.pos_end,
                                            f"{len(args) - len(arg_names)} too many args "
                                            f"passed into '{self.name}'", self.context))
        if len(args) < len(arg_names):
            return response.failure(RTError(self.pos_start,
                                            self.pos_end,
                                            f"{len(arg_names) - len(args)} too few args "
                                            f"passed into '{self.name}'", self.context))
        return response.success(None)

    # noinspection PyMethodMayBeStatic
    def populate_args(self, arg_names, args, context):
        for i in range(len(args)):
            arg_name = arg_names[i]
            arg_val = args[i]
            arg_val.set_context(context)
            context.symbol_table.set(arg_name, arg_val)

    def check_and_populate_args(self, arg_names, args, context):
        response = RTResult()
        response.register(self.check_args(arg_names, args))
        if response.should_ret():
            return response
        self.populate_args(arg_names, args, context)
        return response.success(None)


class Function(BaseFunction):
    def __init__(self, name, body, arg_names, auto_ret):
        super().__init__(name)
        self.body = body
        self.arg_names = arg_names
        self.auto_ret = auto_ret

    def execute(self, args):
        response = RTResult()
        interpreter = Interpreter()
        context = self.make_new_context()
        response.register(self.check_and_populate_args(self.arg_names, args, context))
        if response.should_ret():
            return response
        val = response.register(interpreter.visit(self.body, context))
        if response.should_ret() and response.fun_ret_val is None:
            return response
        ret_val = (val if self.auto_ret else None) or response.fun_ret_val or Number.null
        return response.success(ret_val)

    def copy(self):
        copy = Function(self.name, self.body, self.arg_names, self.auto_ret)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self):
        return f"<function {self.name}>"


class BuiltInFunction(BaseFunction):
    def __init__(self, name):
        super().__init__(name)

    def execute(self, args):
        response = RTResult()
        context = self.make_new_context()
        method_name = f'execute_{self.name}'
        method = getattr(self, method_name, self.no_visit_method)
        response.register(self.check_and_populate_args(method.arg_names, args, context))
        if response.should_ret():
            return response
        return_value = response.register(method(context))
        if response.should_ret():
            return response
        return response.success(return_value)

    def no_visit_method(self, node, context):
        raise Exception(f'No execute_{self.name} method defined')

    def copy(self):
        copy = BuiltInFunction(self.name)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self):
        return f'<built-in function {self.name}>'

    def execute_print(self, context):
        print(str(context.symbol_table.get('value')))
        return RTResult().success(Number.null)
    execute_print.arg_names = ['value']

    def execute_print_ret(self, context):
        return RTResult().success(String(str(context.symbol_table.get('value'))))
    execute_print_ret.arg_names = ['value']

    def execute_input(self):
        text = input()
        return RTResult().success(String(text))
    execute_input.arg_names = []

    def execute_input_int(self):
        while True:
            text = input()
            try:
                num = int(text)
                break
            except ValueError:
                print(f"'{text}' must be an integer.")
        return RTResult().success(Number(num))
    execute_input_int.arg_names = []

    def execute_clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        return RTResult().success(Number.null)
    execute_clear.arg_names = []

    def execute_is_num(self, context):
        is_num = isinstance(context.symbol_table.get("value"), Number)
        return RTResult().success(Number.true if is_num else Number.false)
    execute_is_num.arg_names = ['value']

    def execute_is_str(self, context):
        is_str = isinstance(context.symbol_table.get("value"), String)
        return RTResult().success(Number.true if is_str else Number.false)
    execute_is_str.arg_names = ['value']

    def execute_is_list(self, context):
        is_list = isinstance(context.symbol_table.get("value"), List)
        return RTResult().success(Number.true if is_list else Number.false)
    execute_is_list.arg_names = ['value']

    def execute_is_fun(self, context):
        is_fun = isinstance(context.symbol_table.get("value"), Function)
        return RTResult().success(Number.true if is_fun else Number.false)
    execute_is_fun.arg_names = ['value']

    def execute_append(self, context):
        list_ = context.symbol_table.get("list")
        value = context.symbol_table.get("value")
        if not isinstance(list_, List):
            return RTResult().failure(RTError(self.pos_start,
                                              self.pos_end,
                                              "First argument must be type 'List'",
                                              context))
        list_.elements.append(value)
        return RTResult().success(Number.null)
    execute_append.arg_names = ['list', 'value']

    def execute_pop(self, context):
        list_ = context.symbol_table.get("list")
        index = context.symbol_table.get("index")
        if not isinstance(list_, List):
            return RTResult().failure(RTError(self.pos_start,
                                              self.pos_end,
                                              "First argument must be list",
                                              context))
        if not isinstance(index, Number):
            return RTResult().failure(RTError(self.pos_start,
                                              self.pos_end,
                                              "Second argument must be number",
                                              context))
        try:
            element = list_.elements.pop(index.val)
        except RuntimeError:
            return RTResult().failure(RTError(self.pos_start,
                                              self.pos_end,
                                              'IndexOutOfBoundsException',
                                              context))
        return RTResult().success(element)
    execute_pop.arg_names = ["list", "index"]

    def execute_extend(self, context):
        list_a = context.symbol_table.get("list_a")
        list_b = context.symbol_table.get("list_b")

        if not isinstance(list_a, List):
            return RTResult().failure(RTError(self.pos_start,
                                              self.pos_end,
                                              "First argument must be type 'List'",
                                              context))

        if not isinstance(list_b, List):
            return RTResult().failure(RTError(self.pos_start,
                                              self.pos_end,
                                              "Second argument must be type 'List'",
                                              context))
        list_a.elements.extend(list_b.elements)
        return RTResult().success(Number.null)
    execute_extend.arg_names = ["listA", "listB"]

    def execute_len(self, context):
        list_ = context.symbol_table.get("list")
        if not isinstance(list_, List):
            return RTResult().failure(RTError(self.pos_start,
                                              self.pos_end,
                                              "Argument must be type 'List'",
                                              context))
        return RTResult().success(Number(len(list_.elements)))
    execute_len.arg_names = ["list"]

    def execute_run(self, context):
        file_name = context.symbol_table.get("file_name")
        if not isinstance(file_name, String):
            return RTResult().failure(RTError(self.pos_start,
                                              self.pos_end,
                                              "Argument must be type 'String'",
                                              context))
        file_name = file_name.val
        try:
            with open(file_name, 'r') as f:
                script = f.read()
        except RuntimeError as e:
            return RTResult().failure(RTError(self.pos_start,
                                              self.pos_end,
                                              f"Failed to load script \"{file_name}\"\n" + str(e),
                                              context))
        _, error = run(file_name, script)
        if error:
            return RTResult().failure(RTError(self.pos_start,
                                              self.pos_end,
                                              f"Failed to finish executing script \"{file_name}\"\n" +
                                              error.to_string(),
                                              context))
        return RTResult().success(Number.null)
    execute_run.arg_names = ["file_name"]


BuiltInFunction.print = BuiltInFunction("print")
BuiltInFunction.print_ret = BuiltInFunction("print_ret")
BuiltInFunction.input = BuiltInFunction("input")
BuiltInFunction.input_int = BuiltInFunction("input_int")
BuiltInFunction.clear = BuiltInFunction("clear")
BuiltInFunction.is_num = BuiltInFunction("is_num")
BuiltInFunction.is_str = BuiltInFunction("is_str")
BuiltInFunction.is_list = BuiltInFunction("is_list")
BuiltInFunction.is_fun = BuiltInFunction("is_fun")
BuiltInFunction.append = BuiltInFunction("append")
BuiltInFunction.pop = BuiltInFunction("pop")
BuiltInFunction.extend = BuiltInFunction("extend")
BuiltInFunction.len = BuiltInFunction("len")
BuiltInFunction.run = BuiltInFunction("run")


class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None
        self.advance_count = 0
        self.last_advance_count = 0
        self.to_reverse_count = 0

    def register(self, response):
        self.last_advance_count = response.advance_count
        self.advance_count += response.advance_count
        if response.error:
            self.error = response.error
        return response.node

    def register_advancement(self):
        self.advance_count += 1
        self.last_advance_count = 1

    def try_register(self, response):
        if response.error:
            self.to_reverse_count = response.advance_count
            return None
        return self.register(response)

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        if not self.error or self.last_advance_count == 0:
            self.error = error
        return self


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.token_index = -1
        if 0 <= self.token_index < len(self.tokens):
            self.curr_token = self.tokens[self.token_index]
        self.advance()

    def advance(self):
        self.token_index += 1
        self.update_curr_token()
        return self.curr_token

    def reverse(self, count=1):
        self.token_index -= count
        self.update_curr_token()
        return self.curr_token

    def update_curr_token(self):
        if 0 <= self.token_index < len(self.tokens):
            self.curr_token = self.tokens[self.token_index]

    def parse(self):
        response = self.statements()
        if not response.error and self.curr_token.type != TT_EOF:
            return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                       self.curr_token.pos_end,
                                                       "Expected '+', '-', '*', '/', '%', '^', '==', '!=', "
                                                       "'<', '>', '<=', '>=', '(', '[', 'IF', 'FOR',"
                                                       "'While', 'AND', or 'OR'"))
        return response

    def statements(self):
        response = ParseResult()
        statements = []
        pos_start = self.curr_token.pos_start.copy()
        while self.curr_token.type == TT_EOL:
            response.register_advancement()
            self.advance()
        statement = response.register(self.statement())
        if response.error:
            return response
        statements.append(statement)
        more_statements = True
        while True:
            eol_count = 0
            while self.curr_token.type == TT_EOL:
                response.register_advancement()
                self.advance()
                eol_count += 1
            if eol_count == 0:
                more_statements = False
            if not more_statements:
                break
            statement = response.try_register(self.statement())
            if not statement:
                self.reverse(response.to_reverse_count)
                more_statements = False
                continue
            statements.append(statement)
        return response.success(ListNode(statements,
                                         pos_start,
                                         self.curr_token.pos_end.copy()))

    def statement(self):
        response = ParseResult()
        pos_start = self.curr_token.pos_start.copy()
        if self.curr_token.matches(TT_KEYWORD, 'RETURN'):
            response.register_advancement()
            self.advance()
            expression = response.try_register(self.expr())
            if not expression:
                self.reverse(response.to_reverse_count)
            return response.success(ReturnNode(expression, pos_start, self.curr_token.pos_start.copy()))
        if self.curr_token.matches(TT_KEYWORD, 'CONTINUE'):
            response.register_advancement()
            self.advance()
            return response.success(ContinueNode(pos_start, self.curr_token.pos_start.copy()))
        if self.curr_token.matches(TT_KEYWORD, 'BREAK'):
            response.register_advancement()
            self.advance()
            return response.success(BreakNode(pos_start, self.curr_token.pos_start.copy()))
        expression = response.register(self.expr())
        if response.error:
            return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                       self.curr_token.pos_end,
                                                       "Expected 'RETURN', 'CONTINUE', 'BREAK', 'VAR', "
                                                       "'IF', 'FOR', 'WHILE', 'FUN', "
                                                       "int, float, identifier, '+', '-', '[' or '('"))
        return response.success(expression)

    def list_expr(self):
        response = ParseResult()
        elements = []
        pos_start = self.curr_token.pos_start.copy()
        if self.curr_token.type != TT_LBRAK:
            return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                       self.curr_token.pos_end,
                                                       f"Expected '['"))
        response.register_advancement()
        self.advance()
        if self.curr_token.type == TT_RBRAK:
            response.register_advancement()
            self.advance()
        else:
            elements.append((response.register(self.expr())))
            if response.error:
                return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                           self.curr_token.pos_end,
                                                           "Expected ']', '[', 'VAR', 'If', 'FOR', 'WHILE', 'FUN', "
                                                           "int, float, identifier, '+', '-' or '('"))
            while self.curr_token.type == TT_COMMA:
                response.register_advancement()
                self.advance()
                elements.append(response.register(self.expr()))
                if response.error:
                    return response
            if self.curr_token.type != TT_RBRAK:
                return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                           self.curr_token.pos_end,
                                                           f"Expected ',' or ']'"))
            response.register_advancement()
            self.advance()
        return response.success(ListNode(elements, pos_start, self.curr_token.pos_end.copy()))

    def if_expr(self):
        response = ParseResult()
        all_cases = response.register(self.if_expr_cases('IF'))
        if response.error:
            return response
        cases, else_case = all_cases
        return response.success(IfNode(cases, else_case))

    def elif_expr(self):
        return self.if_expr_cases('ELIF')

    def else_expr(self):
        response = ParseResult()
        else_case = None

        if self.curr_token.matches(TT_KEYWORD, 'ELSE'):
            response.register_advancement()
            self.advance()
            if self.curr_token.type == TT_EOL:
                response.register_advancement()
                self.advance()
                statements = response.register(self.statements())
                if response.error:
                    return response
                else_case = (statements, True)
                if self.curr_token.matches(TT_KEYWORD, 'END'):
                    response.register_advancement()
                    self.advance()
                else:
                    return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                               self.curr_token.pos_end,
                                                               "Expected 'END'"))
            else:
                expr = response.register(self.statement())
                if response.error:
                    return response
                else_case = (expr, False)
        return response.success(else_case)

    def if_elif_and_else(self):
        response = ParseResult()
        cases, else_case = [], None

        if self.curr_token.matches(TT_KEYWORD, 'ELIF'):
            all_cases = response.register(self.elif_expr())
            if response.error:
                return response
            cases, else_case = all_cases
        else:
            else_case = response.register(self.else_expr())
            if response.error:
                return response
        return response.success((cases, else_case))

    def if_expr_cases(self, case_keyword):
        response = ParseResult()
        cases = []
        else_case = None
        if not self.curr_token.matches(TT_KEYWORD, case_keyword):
            return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                       self.curr_token.pos_end,
                                                       f"Expected '{case_keyword}'"))
        response.register_advancement()
        self.advance()
        condition = response.register(self.expr())
        if response.error:
            return response
        if not self.curr_token.matches(TT_KEYWORD, 'THEN'):
            return response.failure(InvalidSyntaxError(
                self.curr_token.pos_start, self.curr_token.pos_end,
                f"Expected 'THEN'"
            ))
        response.register_advancement()
        self.advance()

        if self.curr_token.type == TT_EOL:
            response.register_advancement()
            self.advance()
            statements = response.register(self.statements())
            if response.error:
                return response
            cases.append((condition, statements, True))
            if self.curr_token.matches(TT_KEYWORD, 'END'):
                response.register_advancement()
                self.advance()
            else:
                all_cases = response.register(self.if_elif_and_else())
                if response.error:
                    return response
                new_cases, else_case = all_cases
                cases.extend(new_cases)
        else:
            expression = response.register(self.statement())
            if response.error:
                return response
            cases.append((condition, expression, False))

            all_cases = response.register(self.if_elif_and_else())
            if response.error:
                return response
            new_cases, else_case = all_cases
            cases.extend(new_cases)
        return response.success((cases, else_case))

    def for_expr(self):
        response = ParseResult()
        if not self.curr_token.matches(TT_KEYWORD, 'FOR'):
            return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                       self.curr_token.pos_end,
                                                       f"Expected 'FOR'"))
        response.register_advancement()
        self.advance()
        if self.curr_token.type != TT_IDENTIFIER:
            return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                       self.curr_token.pos_end,
                                                       f"Expected identifier"))
        var = self.curr_token
        response.register_advancement()
        self.advance()
        if self.curr_token.type != TT_EQ:
            return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                       self.curr_token.pos_end,
                                                       f"Expected '='"))
        response.register_advancement()
        self.advance()
        start = response.register(self.expr())
        if response.error:
            return response
        if not self.curr_token.matches(TT_KEYWORD, 'TO'):
            return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                       self.curr_token.pos_end,
                                                       f"Expected 'TO'"))
        response.register_advancement()
        self.advance()
        end = response.register(self.expr())
        if response.error:
            return response
        if self.curr_token.matches(TT_KEYWORD, 'STEP'):
            response.register_advancement()
            self.advance()
            step = response.register(self.expr())
            if response.error:
                return response
        else:
            step = None
        if not self.curr_token.matches(TT_KEYWORD, 'THEN'):
            return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                       self.curr_token.pos_end,
                                                       f"Expected 'THEN'"))
        response.register_advancement()
        self.advance()
        if self.curr_token.type == TT_EOL:
            response.register_advancement()
            self.advance()
            body = response.register(self.statements())
            if response.error:
                return response
            if not self.curr_token.matches(TT_KEYWORD, 'END'):
                return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                           self.curr_token.pos_end,
                                                           f"Expected 'END'"))
            response.register_advancement()
            self.advance()
            return response.success(ForNode(var, start, end, step, body, True))
        body = response.register(self.statement())
        if response.error:
            return response
        return response.success(ForNode(var, start, end, step, body, False))

    def while_expr(self):
        response = ParseResult()
        if not self.curr_token.matches(TT_KEYWORD, 'WHILE'):
            return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                       self.curr_token.pos_end,
                                                       f"Expected 'WHILE'"))
        response.register_advancement()
        self.advance()
        condition = response.register(self.expr())
        if response.error:
            return response
        if not self.curr_token.matches(TT_KEYWORD, 'THEN'):
            return response.failure(InvalidSyntaxError(
                self.curr_token.pos_start, self.curr_token.pos_end,
                f"Expected 'THEN'"
            ))
        response.register_advancement()
        self.advance()
        if self.curr_token.type == TT_EOL:
            response.register_advancement()
            self.advance()
            body = response.register(self.statements())
            if response.error:
                return response
            if not self.curr_token.matches(TT_KEYWORD, 'END'):
                return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                           self.curr_token.pos_end,
                                                           f"Expected 'END'"))

            response.register_advancement()
            self.advance()
            return response.success(WhileNode(condition, body, True))
        body = response.register(self.statement())
        if response.error:
            return response
        return response.success(WhileNode(condition, body, False))

    def call(self):
        response = ParseResult()
        atom = response.register(self.atom())
        if response.error:
            return response
        if self.curr_token.type == TT_LPAR:
            response.register_advancement()
            self.advance()
            args = []
            if self.curr_token.type == TT_RPAR:
                response.register_advancement()
                self.advance()
            else:
                args.append((response.register(self.expr())))
                if response.error:
                    return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                               self.curr_token.pos_end,
                                                               "Expected ')', '[', 'VAR', 'If', 'FOR', 'WHILE', 'FUN', "
                                                               "int, float, identifier, '+', '-' or '('"))
                while self.curr_token.type == TT_COMMA:
                    response.register_advancement()
                    self.advance()
                    args.append(response.register(self.expr()))
                    if response.error:
                        return response
                if self.curr_token.type != TT_RPAR:
                    return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                               self.curr_token.pos_end,
                                                               f"Expected ',' or ')'"))
                response.register_advancement()
                self.advance()
            return response.success(CallNode(atom, args))
        return response.success(atom)

    def atom(self):
        response = ParseResult()
        token = self.curr_token
        if token.type in (TT_INT, TT_FLOAT):
            response.register_advancement()
            self.advance()
            return response.success(NumberNode(token))
        elif token.type == TT_STRING:
            response.register_advancement()
            self.advance()
            return response.success(StringNode(token))
        elif token.type == TT_IDENTIFIER:
            response.register_advancement()
            self.advance()
            return response.success(VarAccessNode(token))
        elif token.type == TT_LPAR:
            response.register_advancement()
            self.advance()
            expression = response.register(self.expr())
            if response.error:
                return response
            if self.curr_token.type == TT_RPAR:
                response.register_advancement()
                self.advance()
                return response.success(expression)
            else:
                return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                           self.curr_token.pos_end,
                                                           "Expected ')'"))
        elif self.curr_token.type == TT_LBRAK:
            list_expr = response.register(self.list_expr())
            if response.error:
                return response
            return response.success(list_expr)
        elif token.matches(TT_KEYWORD, 'IF'):
            if_expr = response.register(self.if_expr())
            if response.error:
                return response
            return response.success(if_expr)
        elif token.matches(TT_KEYWORD, 'FOR'):
            for_expr = response.register(self.for_expr())
            if response.error:
                return response
            return response.success(for_expr)
        elif token.matches(TT_KEYWORD, 'WHILE'):
            while_expr = response.register(self.while_expr())
            if response.error:
                return response
            return response.success(while_expr)
        elif token.matches(TT_KEYWORD, 'FUN'):
            while_expr = response.register(self.func_def())
            if response.error:
                return response
            return response.success(while_expr)
        return response.failure(InvalidSyntaxError(token.pos_start,
                                                   token.pos_end,
                                                   "Expected 'IF', 'FOR', 'WHILE', 'FUN', "
                                                   "int, float, identifier, '+', '-' or '('"))

    def power(self):
        return self.bin_op(self.call, (TT_POW,), self.factor)

    def factor(self):
        response = ParseResult()
        token = self.curr_token
        if token.type in (TT_ADD, TT_SUB):
            response.register_advancement()
            self.advance()
            factor = response.register(self.factor())
            if response.error:
                return response
            return response.success(UnaryOpNode(token, factor))

        return self.power()

    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV, TT_MOD))

    def arith_expr(self):
        return self.bin_op(self.term, (TT_ADD, TT_SUB))

    def comp_expr(self):
        response = ParseResult()
        if self.curr_token.matches(TT_KEYWORD, 'NOT'):
            op_token = self.curr_token
            response.register_advancement()
            self.advance()

            node = response.register(self.comp_expr())
            if response.error:
                return response
            return response.success(UnaryOpNode(op_token, node))
        node = response.register(self.bin_op(self.arith_expr,
                                             (TT_EEQ, TT_NEQ, TT_LT, TT_GT, TT_LTE, TT_GTE)))
        if response.error:
            return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                       self.curr_token.pos_end,
                                                       "Expected int, float, identifier, '+', '-', '(' or 'NOT'"))
        return response.success(node)

    def expr(self):
        response = ParseResult()
        if self.curr_token.matches(TT_KEYWORD, 'VAR'):
            response.register_advancement()
            self.advance()
            if self.curr_token.type != TT_IDENTIFIER:
                return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                           self.curr_token.pos_end,
                                                           "Expected identifier"))
            var_name = self.curr_token
            response.register_advancement()
            self.advance()
            if self.curr_token.type != TT_EQ:
                return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                           self.curr_token.pos_end,
                                                           "Expected'='"))
            response.register_advancement()
            self.advance()
            expression = response.register(self.expr())
            if response.error:
                return response
            return response.success(VarAssignNode(var_name, expression))
        node = response.register(self.bin_op(self.comp_expr, ((TT_KEYWORD, "AND"), (TT_KEYWORD, "OR"))))
        if response.error:
            return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                       self.curr_token.pos_end,
                                                       "Expected 'VAR', 'IF', 'FOR', 'WHILE', 'FUN', "
                                                       "int, float, identifier, '+', '-', '[' or '('"))
        return response.success(node)

    def func_def(self):
        response = ParseResult()
        if not self.curr_token.matches(TT_KEYWORD, 'FUN'):
            return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                       self.curr_token.pos_end,
                                                       f"Expected 'FUN"))
        response.register_advancement()
        self.advance()
        if self.curr_token.type == TT_IDENTIFIER:
            var = self.curr_token
            response.register_advancement()
            self.advance()
            if self.curr_token.type != TT_LPAR:
                return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                           self.curr_token.pos_end,
                                                           f"Expected '('"))
        else:
            var = None
            if self.curr_token.type != TT_LPAR:
                return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                           self.curr_token.pos_end,
                                                           f"Expected identifier or '('"))
        response.register_advancement()
        self.advance()
        args = []
        if self.curr_token.type == TT_IDENTIFIER:
            args.append(self.curr_token)
            response.register_advancement()
            self.advance()
            while self.curr_token.type == TT_COMMA:
                response.register_advancement()
                self.advance()
                if self.curr_token.type != TT_IDENTIFIER:
                    return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                               self.curr_token.pos_end,
                                                               f"Expected identifier"))
                args.append(self.curr_token)
                response.register_advancement()
                self.advance()
            if self.curr_token.type != TT_RPAR:
                return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                           self.curr_token.pos_end,
                                                           f"Expected ',' or ')'"))
        else:
            if self.curr_token.type != TT_RPAR:
                return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                           self.curr_token.pos_end,
                                                           f"Expected identifier or ')'"))
        response.register_advancement()
        self.advance()
        if self.curr_token.type == TT_ARROW:
            response.register_advancement()
            self.advance()
            body = response.register(self.expr())
            if response.error:
                return response
            return response.success(FuncDefNode(var, args, body, True))
        if self.curr_token.type != TT_EOL:
            return response.failure(InvalidSyntaxError(
                self.curr_token.pos_start, self.curr_token.pos_end,
                f"Expected '->' or NEWLINE"
            ))
        response.register_advancement()
        self.advance()
        body = response.register(self.statements())
        if response.error:
            return response
        if not self.curr_token.matches(TT_KEYWORD, 'END'):
            return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                       self.curr_token.pos_end,
                                                       f"Expected 'END'"))
        response.register_advancement()
        self.advance()
        return response.success(FuncDefNode(var, args, body, False))

    def bin_op(self, func_a, ops, func_b=None):
        if func_b is None:
            func_b = func_a
        response = ParseResult()
        left = response.register(func_a())
        if response.error:
            return response
        while self.curr_token.type in ops or (self.curr_token.type, self.curr_token.val) in ops:
            op_token = self.curr_token
            response.register_advancement()
            self.advance()
            right = response.register(func_b())
            if response.error:
                return response
            left = BinOpNode(left, op_token, right)
        return response.success(left)


class Interpreter:
    def visit(self, node, context):
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.no_visit_method)
        return method(node, context)

    def no_visit_method(self, node, context):
        raise Exception(f'No visit_{type(node).__name__} method defined')

    # noinspection PyMethodMayBeStatic
    def visit_NumberNode(self, node, context):
        return RTResult().success(
            Number(node.token.val).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    # noinspection PyMethodMayBeStatic
    def visit_StringNode(self, node, context):
        return RTResult().success(
            String(node.token.val).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_ListNode(self, node, context):
        response = RTResult()
        elements = []
        for element in node.elements:
            elements.append(response.register(self.visit(element, context)))
            if response.should_ret():
                return response
        return response.success(List(elements).set_context(context).set_pos(node.pos_start, node.pos_end))

    # noinspection PyMethodMayBeStatic
    def visit_VarAccessNode(self, node, context):
        response = RTResult()
        var_name = node.var_name_token.val
        val = context.symbol_table.get(var_name)
        if not val:
            return response.failure(RTError(node.pos_start,
                                            node.pos_end,
                                            f"'{var_name}' is not defined",
                                            context))
        val = val.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
        return response.success(val)

    def visit_VarAssignNode(self, node, context):
        response = RTResult()
        var_name = node.var_name_token.val
        val = response.register(self.visit(node.val_node, context))
        if response.should_ret():
            return response
        context.symbol_table.set(var_name, val)
        return response.success(val)

    def visit_BinOpNode(self, node, context):
        response = RTResult()
        left = response.register(self.visit(node.left_node, context))
        if response.should_ret():
            return response
        right = response.register(self.visit(node.right_node, context))
        if response.should_ret():
            return response
        result = None
        error = None
        if node.op_token.type == TT_ADD:
            result, error = left.add_to(right)
        elif node.op_token.type == TT_SUB:
            result, error = left.sub_by(right)
        elif node.op_token.type == TT_MUL:
            result, error = left.mul_by(right)
        elif node.op_token.type == TT_DIV:
            result, error = left.div_by(right)
        elif node.op_token.type == TT_MOD:
            result, error = left.mod_by(right)
        elif node.op_token.type == TT_POW:
            result, error = left.pow_by(right)
        elif node.op_token.type == TT_EEQ:
            result, error = left.get_comparison_eeq(right)
        elif node.op_token.type == TT_NEQ:
            result, error = left.get_comparison_neq(right)
        elif node.op_token.type == TT_LT:
            result, error = left.get_comparison_lt(right)
        elif node.op_token.type == TT_GT:
            result, error = left.get_comparison_gt(right)
        elif node.op_token.type == TT_LTE:
            result, error = left.get_comparison_lte(right)
        elif node.op_token.type == TT_GTE:
            result, error = left.get_comparison_gte(right)
        elif node.op_token.matches(TT_KEYWORD, 'AND'):
            result, error = left.and_with(right)
        elif node.op_token.matches(TT_KEYWORD, 'OR'):
            result, error = left.or_with(right)
        if error:
            return response.failure(error)
        else:
            return response.success(result.set_pos(node.pos_start, node.pos_end))

    def visit_UnaryOpNode(self, node, context):
        response = RTResult()
        num = response.register(self.visit(node.node, context))
        if response.should_ret():
            return response
        error = None
        if node.op_token.type == TT_SUB:
            num, error = num.mul_by(Number(-1))
        elif node.op_token.matches(TT_KEYWORD, 'NOT'):
            num, error = num.not_of()
        if error:
            return response.failure(error)
        else:
            return response.success(num.set_pos(node.pos_start, node.pos_end))

    def visit_IfNode(self, node, context):
        response = RTResult()

        for condition, expression, ret_null in node.cases:
            condition_val = response.register(self.visit(condition, context))
            if response.should_ret():
                return response
            if condition_val.is_true():
                expr_val = response.register(self.visit(expression, context))
                if response.should_ret():
                    return response
                return response.success(Number.null if ret_null else expr_val)
        if node.else_case:
            expression, ret_null = node.else_case
            expr_val = response.register(self.visit(expression, context))
            if response.should_ret():
                return response
            return response.success(Number.null if ret_null else expr_val)
        return response.success(Number.null)

    def visit_ForNode(self, node, context):
        response = RTResult()
        elements = []
        start = response.register(self.visit(node.start, context))
        if response.should_ret():
            return response
        end = response.register(self.visit(node.end, context))
        if response.should_ret():
            return response
        if node.step:
            step = response.register(self.visit(node.step, context))
            if response.should_ret():
                return response
        else:
            step = Number(1)
        i = start.val
        if step.val >= 0:
            condition = i < end.val
        else:
            condition = i > end.val

        while condition:
            context.symbol_table.set(node.var.val, Number(i))
            i += step.val
            val = response.register(self.visit(node.body, context))
            if response.should_ret() and not response.loop_continue and not response.loop_break:
                return response
            if step.val >= 0:
                condition = i < end.val
            else:
                condition = i > end.val
            if response.loop_continue:
                continue
            if response.loop_break:
                break
            elements.append(val)
        return response.success(Number.null if node.ret_null else
                                List(elements).set_context(context).set_pos(node.pos_start, node.pos_end))

    def visit_WhileNode(self, node, context):
        response = RTResult()
        elements = []
        while True:
            condition = response.register(self.visit(node.condition, context))
            if response.should_ret():
                return response
            if not condition.is_true():
                break
            val = response.register(self.visit(node.body, context))
            if response.should_ret() and not response.loop_continue and not response.loop_break:
                return response
            if response.loop_continue:
                continue
            if response.loop_break:
                break
            elements.append(val)
        return response.success(Number.null if node.ret_null else
                                List(elements).set_context(context).set_pos(node.pos_start, node.pos_end))

    # noinspection PyMethodMayBeStatic
    def visit_FuncDefNode(self, node, context):
        response = RTResult()
        func_name = node.var_name_token.val if node.var_name_token else None
        body = node.body
        arg_names = [arg_name.val for arg_name in node.args]
        func_val = Function(
            func_name, body, arg_names, node.auto_ret).set_context(context).set_pos(node.pos_start, node.pos_end)
        if node.var_name_token:
            context.symbol_table.set(func_name, func_val)
        return response.success(func_val)

    def visit_CallNode(self, node, context):
        response = RTResult()
        args = []
        call_val = response.register(self.visit(node.call_node, context))
        if response.should_ret():
            return response
        call_val = call_val.copy().set_pos(node.pos_start, node.pos_end)
        for arg in node.args:
            args.append(response.register(self.visit(arg, context)))
            if response.should_ret():
                return response
        ret_val = response.register(call_val.execute(args))
        if response.should_ret():
            return response
        ret_val = ret_val.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
        return response.success(ret_val)

    def visit_ReturnNode(self, node, context):
        response = RTResult()
        if node.ret_node:
            val = response.register(self.visit(node.ret_node, context))
            if response.should_ret():
                return response
        else:
            val = Number.null
        return response.success_ret(val)

    # noinspection PyMethodMayBeStatic
    def visit_ContinueNode(self):
        return RTResult().success_continue()

    # noinspection PyMethodMayBeStatic
    def visit_BreakNode(self):
        return RTResult().success_break()


global_symbol_table = SymbolTable()
global_symbol_table.set("TRUE", Number.true)
global_symbol_table.set("FALSE", Number.false)
global_symbol_table.set("MATH_PI", Number.math_PI)
global_symbol_table.set("PRINT", BuiltInFunction.print)
global_symbol_table.set("PRINT_RET", BuiltInFunction.print_ret)
global_symbol_table.set("INPUT", BuiltInFunction.input)
global_symbol_table.set("INPUT_INT", BuiltInFunction.input_int)
global_symbol_table.set("CLEAR", BuiltInFunction.clear)
global_symbol_table.set("CLS", BuiltInFunction.clear)
global_symbol_table.set("IS_NUM", BuiltInFunction.is_num)
global_symbol_table.set("IS_STR", BuiltInFunction.is_str)
global_symbol_table.set("IS_LIST", BuiltInFunction.is_list)
global_symbol_table.set("IS_FUN", BuiltInFunction.is_fun)
global_symbol_table.set("APPEND", BuiltInFunction.append)
global_symbol_table.set("POP", BuiltInFunction.pop)
global_symbol_table.set("EXTEND", BuiltInFunction.extend)
global_symbol_table.set("LEN", BuiltInFunction.len)
global_symbol_table.set("RUN", BuiltInFunction.run)


def run(file_name, text):
    # Generate Tokens
    lexer = Lexer(file_name, text)
    tokens, error = lexer.make_tokens()
    if error:
        return None, error

    # Generate AST
    parser = Parser(tokens)
    # print(parser.__dict__)
    ast = parser.parse()
    if ast.error:
        return None, ast.error
    # print(ast.__dict__)

    # Traverses and computes the AST
    interpreter = Interpreter()
    context = Context('<program>')
    context.symbol_table = global_symbol_table
    result = interpreter.visit(ast.node, context)
    # print(global_symbol_table.__dict__)

    return result.val, result.error
