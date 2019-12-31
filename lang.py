from string_with_arrows import *
import string

# Constants
DIGITS = '0123456789'
LETTERS = string.ascii_letters
LETTERS_DIGITS = LETTERS + DIGITS


# Error Class
class Error:
    def __init__(self, pos_start, pos_end, error_type, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_type = error_type
        self.details = details

    def to_string(self):
        result = f'{self.error_type}: {self.details} \n'
        result += f'File {self.pos_start.file_name}, line {self.pos_start.ln + 1}, col {self.pos_start.col + 1}'
        result += '\n\n' + string_with_arrows(self.pos_start.file_txt, self.pos_start, self.pos_end)
        return result


class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Illegal Character', details)


class ExpectedCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Expected Character', details)


class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details=''):
        super().__init__(pos_start, pos_end, 'Invalid Syntax', details)


class RTError(Error):
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, 'Runtime Error', details)
        self.context = context

    def to_string(self):
        result = self.generate_traceback()
        result += f'{self.error_type}: {self.details} \n'
        result += '\n\n' + string_with_arrows(self.pos_start.file_txt, self.pos_start, self.pos_end)
        return result

    def generate_traceback(self):
        result = ''
        pos = self.pos_start
        context_stack = self.context

        while context_stack:
            result = f'  File {pos.file_name}, line {str(pos.ln + 1)}, in {context_stack.display_name}\n' + result
            pos = context_stack.parent_entry_pos
            context_stack = self.context

        return 'Traceback (most recent call last):\n' + result


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


# Token Types
TT_INT = 'INT'
TT_FLOAT = 'FLOAT'
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

TT_EOF = 'EOF'

KEYWORDS = [
    'VAR',
    'AND',
    'OR',
    'NOT'
]


# Token Class
class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value

        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance()
        if pos_end:
            self.pos_end = pos_end

    def matches(self, type_, value):
        return self.type == type_ and self.value == value

    # String representation
    def __repr__(self):
        if self.value:
            return f'{self.type}:{self.value}'
        else:
            return f'{self.type}'


# Lexer Class
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
            elif self.curr_char in DIGITS:
                tokens.append(self.make_num())
            elif self.curr_char in LETTERS:
                tokens.append(self.make_identifier())
            elif self.curr_char == '+':
                tokens.append(Token(TT_ADD, pos_start=self.pos))
                self.advance()
            elif self.curr_char == '-':
                tokens.append(Token(TT_SUB, pos_start=self.pos))
                self.advance()
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

    def make_identifier(self):
        id_str = ''
        pos_start = self.pos.copy()

        while self.curr_char is not None and self.curr_char in LETTERS_DIGITS + '_':
            id_str += self.curr_char
            self.advance()

        token_type = TT_KEYWORD if id_str in KEYWORDS else TT_IDENTIFIER
        return Token(token_type, id_str, pos_start, self.pos)

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


class NumberNode:
    def __init__(self, token):
        self.token = token
        self.pos_start = self.token.pos_start
        self.pos_end = self.token.pos_end

    def __repr__(self):
        return f'{self.token}'


class VarAccessNode:
    def __init__(self, var_name_token):
        self.var_name_token = var_name_token
        self.pos_start = self.var_name_token.pos_start
        self.pos_end = self.var_name_token.pos_end


class VarAssignNode:
    def __init__(self, var_name_token, value_node):
        self.var_name_token = var_name_token
        self.value_node = value_node
        self.pos_start = self.var_name_token.pos_start
        self.pos_end = self.var_name_token.pos_end


class UnaryOpNode:
    def __init__(self, op_token, node):
        self.op_token = op_token
        self.node = node
        self.pos_start = self.op_token.pos_start
        self.pos_end = node.pos_end

    def __repr__(self):
        return f'({self.op_token}, {self.node})'


class BinOpNode:
    def __init__(self, left_node, op_token, right_node):
        self.left_node = left_node
        self.op_token = op_token
        self.right_node = right_node
        self.pos_start = self.left_node.pos_start
        self.pos_end = self.right_node.pos_end

    def __repr__(self):
        return f'({self.left_node}, {self.op_token}, {self.right_node})'


class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None
        self.advance_count = 0

    def register(self, response):
        self.advance_count += response.advance_count
        if response.error:
            self.error = response.error
        return response.node

    def register_advancement(self):
        self.advance_count += 1

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        if not self.error or self.advance_count == 0:
            self.error = error
        return self


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.token_index = -1
        self.advance()
        self.curr_token = self.tokens[self.token_index]

    def advance(self):
        self.token_index += 1
        if self.token_index < len(self.tokens):
            self.curr_token = self.tokens[self.token_index]
        return self.curr_token

    def parse(self):
        res = self.expr()
        if not res.error and self.curr_token.type != TT_EOF:
            return res.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                  self.curr_token.pos_end,
                                                  "Expected '+', '-', '*', '/', '%', '^', '==', '!=', "
                                                  "'<', '>', '<=', '>=', 'AND', or 'OR'"))
        return res

    def atom(self):
        response = ParseResult()
        token = self.curr_token
        if token.type in (TT_INT, TT_FLOAT):
            response.register_advancement()
            self.advance()
            return response.success(NumberNode(token))
        elif token.type == TT_IDENTIFIER:
            response.register_advancement()
            self.advance()
            return response.success(VarAccessNode(token))
        elif token.type == TT_LPAR:
            response.register_advancement()
            self.advance()
            expr = response.register(self.expr())
            if response.error:
                return response
            if self.curr_token.type == TT_RPAR:
                response.register_advancement()
                self.advance()
                return response.success(expr)
            else:
                return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                           self.curr_token.pos_end,
                                                           "Expected ')'"))
        return response.failure(InvalidSyntaxError(token.pos_start,
                                                   token.pos_end,
                                                   "Expected int, float, identifier, '+', '-' or '('"))

    def power(self):
        return self.bin_op(self.atom, (TT_POW, ), self.factor)

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
            expr = response.register(self.expr())
            if response.error:
                return response
            return response.success(VarAssignNode(var_name, expr))
        node = response.register(self.bin_op(self.comp_expr, ((TT_KEYWORD, "AND"), (TT_KEYWORD, "OR"))))
        if response.error:
            return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                       self.curr_token.pos_end,
                                                       "Expected 'VAR', int, float, identifier, '+', '-' or '('"))
        return response.success(node)

    def bin_op(self, func_a, ops, func_b=None):
        if func_b is None:
            func_b = func_a
        response = ParseResult()
        left = response.register(func_a())
        if response.error:
            return response
        while self.curr_token.type in ops or (self.curr_token.type, self.curr_token.value) in ops:
            op_token = self.curr_token
            response.register_advancement()
            self.advance()
            right = response.register(func_b())
            if response.error:
                return response
            left = BinOpNode(left, op_token, right)
        return response.success(left)


class RTResult:
    def __init__(self):
        self.value = None
        self.error = None

    def register(self, result):
        if result.error:
            self.error = result.error
        return result.value

    def success(self, value):
        self.value = value
        return self

    def failure(self, error):
        self.error = error
        return self


class Number:
    def __init__(self, value):
        self.value = value
        self.set_pos()
        self.pos_start = None
        self.pos_end = None
        self.context = None
        self.set_context()

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def add_to(self, other):
        if isinstance(other, Number):
            return Number(self.value + other.value).set_context(self.context), None

    def sub_by(self, other):
        if isinstance(other, Number):
            return Number(self.value - other.value).set_context(self.context), None

    def mul_by(self, other):
        if isinstance(other, Number):
            return Number(self.value * other.value).set_context(self.context), None

    def div_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RTError(other.pos_start, other.pos_end,
                                     'Division by Zero', self.context)
            return Number(self.value / other.value).set_context(self.context), None

    def mod_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RTError(other.pos_start, other.pos_end,
                                     'Division by Zero', self.context)
            return Number(self.value % other.value).set_context(self.context), None

    def pow_by(self, other):
        if isinstance(other, Number):
            return Number(self.value ** other.value).set_context(self.context), None

    def get_comparison_eeq(self, other):
        if isinstance(other, Number):
            return Number(int(self.value == other.value)).set_context(self.context), None

    def get_comparison_neq(self, other):
        if isinstance(other, Number):
            return Number(int(self.value != other.value)).set_context(self.context), None

    def get_comparison_lt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value < other.value)).set_context(self.context), None

    def get_comparison_gt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value > other.value)).set_context(self.context), None

    def get_comparison_lte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value <= other.value)).set_context(self.context), None

    def get_comparison_gte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value >= other.value)).set_context(self.context), None

    def and_with(self, other):
        if isinstance(other, Number):
            return Number(int(self.value and other.value)).set_context(self.context), None

    def or_with(self, other):
        if isinstance(other, Number):
            return Number(int(self.value or other.value)).set_context(self.context), None

    def not_of(self):
        return Number(1 if self.value == 0 else 0).set_context(self.context), None

    def copy(self):
        copy = Number(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __repr__(self):
        return str(self.value)


class Context:
    def __init__(self, display_name, parent=None, parent_entry_pos=None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos
        self.symbol_table = None


class SymbolTable:
    def __init__(self):
        self.symbols = {}
        self.parent = None

    def get(self, name):
        value = self.symbols.get(name, None)
        if value is None and self.parent:
            return self.parent.get(name)
        return value

    def set(self, name, value):
        self.symbols[name] = value

    def remove(self, name):
        del self.symbols[name]


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
            Number(node.token.value).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    # noinspection PyMethodMayBeStatic
    def visit_VarAccessNode(self, node, context):
        response = RTResult()
        var_name = node.var_name_token.value
        value = context.symbol_table.get(var_name)
        if not value:
            return response.failure(RTError(node.pos_start,
                                            node.pos_end,
                                            f"'{var_name}' is not defined",
                                            context))
        value = value.copy().set_pos(node.pos_start, node.pos_end)
        return response.success(value)

    def visit_VarAssignNode(self, node, context):
        response = RTResult()
        var_name = node.var_name_token.value
        value = response.register(self.visit(node.value_node, context))
        if response.error:
            return response
        context.symbol_table.set(var_name, value)
        return response.success(value)

    def visit_BinOpNode(self, node, context):
        response = RTResult()
        left = response.register(self.visit(node.left_node, context))
        if response.error:
            return response
        right = response.register(self.visit(node.right_node, context))
        if response.error:
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
        if response.error:
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


global_symbol_table = SymbolTable()
global_symbol_table.set("NULL", Number(0))
global_symbol_table.set("TRUE", Number(1))
global_symbol_table.set("FALSE", Number(0))


# Run function
def run(file_name, text):
    # Generate Tokens
    lexer = Lexer(file_name, text)
    tokens, error = lexer.make_tokens()
    if error:
        return None, error

    # Generate AST
    parser = Parser(tokens)
    ast = parser.parse()
    if ast.error:
        return None, ast.error

    # Traverses and computes the AST
    interpreter = Interpreter()
    context = Context('<program>')
    context.symbol_table = global_symbol_table
    result = interpreter.visit(ast.node, context)

    return result.value, result.error
