import string
from error_handling import *

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

TT_EOF = 'EOF'

KEYWORDS = [
    'VAR',
    'AND',
    'OR',
    'NOT',
    'IF',
    'THEN',
    'ELIF',
    'ELSE',
    'FOR',
    'TO',
    'STEP',
    'WHILE',
    'FUN'
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
