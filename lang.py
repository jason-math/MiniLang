from string_with_arrows import *

# Constants
DIGITS = '0123456789'


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


class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Invalid Syntax', details)


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
TT_ADD = 'ADD'
TT_SUB = 'SUB'
TT_MUL = 'MUL'
TT_DIV = 'DIV'
TT_MOD = 'MOD'
TT_LPAR = 'LPAR'
TT_RPAR = 'RPAR'
TT_EOF = 'EOF'


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
            elif self.curr_char == '(':
                tokens.append(Token(TT_LPAR, pos_start=self.pos))
                self.advance()
            elif self.curr_char == ')':
                tokens.append(Token(TT_RPAR, pos_start=self.pos))
                self.advance()
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


class NumberNode:
    def __init__(self, token):
        self.token = token

    def __repr__(self):
        return f'{self.token}'


class UnaryOpNode:
    def __init__(self, op_token, node):
        self.op_token = op_token
        self.node = node

    def __repr__(self):
        return f'({self.op_token}, {self.node})'


class BinOpNode:
    def __init__(self, left_node, op_token, right_node):
        self.left_node = left_node
        self.op_token = op_token
        self.right_node = right_node

    def __repr__(self):
        return f'({self.left_node}, {self.op_token}, {self.right_node})'


class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None

    def register(self, result):
        if isinstance(result, ParseResult):
            if result.error:
                self.error = result.error
            return result.node

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
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

    #############################

    def parse(self):
        res = self.expr()
        if not res.error and self.curr_token.type != TT_EOF:
            return res.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                  self.curr_token.pos_end,
                                                  "Expected '+', '-', '*', '/', or '%'"))
        return res

    def factor(self):
        response = ParseResult()
        token = self.curr_token
        if token.type in (TT_ADD, TT_SUB):
            response.register(self.advance())
            factor = response.register(self.factor())
            if response.error:
                return response
            return response.success(UnaryOpNode(token, factor))
        elif token.type in (TT_INT, TT_FLOAT):
            response.register(self.advance())
            return response.success(NumberNode(token))
        elif token.type == TT_LPAR:
            response.register(self.advance())
            expr = response.register(self.expr())
            if response.error:
                return response
            if self.curr_token.type == TT_RPAR:
                response.register(self.advance())
                return response.success(expr)
            else:
                return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                           self.curr_token.pos_end,
                                                           "Expected ')'"))

        return response.failure(InvalidSyntaxError(token.pos_start,
                                                   token.pos_end,
                                                   "Expected int or float"))

    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV, TT_MOD))

    def expr(self):
        return self.bin_op(self.term, (TT_ADD, TT_SUB))

    def bin_op(self, func, ops):
        response = ParseResult()
        left = response.register(func())
        if response.error:
            return response
        while self.curr_token.type in ops:
            op_token = self.curr_token
            response.register(self.advance())
            right = response.register(func())
            if response.error:
                return response
            left = BinOpNode(left, op_token, right)
        return response.success(left)


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

    return ast.node, ast.error
