from lexer import *
from node_types import *


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
        response = self.expr()
        if not response.error and self.curr_token.type != TT_EOF:
            return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                       self.curr_token.pos_end,
                                                       "Expected '+', '-', '*', '/', '%', '^', '==', '!=', "
                                                       "'<', '>', '<=', '>=', 'AND', or 'OR'"))
        return response

    def if_expr(self):
        response = ParseResult()
        cases = []
        else_case = None

        if not self.curr_token.matches(TT_KEYWORD, 'IF'):
            return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                       self.curr_token.pos_end,
                                                       f"Expected 'IF'"))
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
        expr = response.register(self.expr())
        if response.error:
            return response
        cases.append((condition, expr))

        while self.curr_token.matches(TT_KEYWORD, 'ELIF'):
            response.register_advancement()
            self.advance()
            condition = response.register(self.expr())
            if response.error:
                return response
            if not self.curr_token.matches(TT_KEYWORD, 'THEN'):
                return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                           self.curr_token.pos_end,
                                                           f"Expected 'THEN'"))
            response.register_advancement()
            self.advance()
            expr = response.register(self.expr())
            if response.error:
                return response
            cases.append((condition, expr))
        if self.curr_token.matches(TT_KEYWORD, 'ELSE'):
            response.register_advancement()
            self.advance()
            else_case = response.register(self.expr())
            if response.error:
                return response
        return response.success(IfNode(cases, else_case))

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
        body = response.register(self.expr())
        if response.error:
            return response
        return response.success(ForNode(var, start, end, step, body))

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
        body = response.register(self.expr())
        if response.error:
            return response
        return response.success(WhileNode(condition, body))

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
                                                               "Expected ')', 'VAR', 'If', 'FOR', 'WHILE', 'FUN', "
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
            expr = response.register(self.expr())
            if response.error:
                return response
            return response.success(VarAssignNode(var_name, expr))
        node = response.register(self.bin_op(self.comp_expr, ((TT_KEYWORD, "AND"), (TT_KEYWORD, "OR"))))
        if response.error:
            return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                       self.curr_token.pos_end,
                                                       "Expected 'VAR', 'IF', 'FOR', 'WHILE', 'FUN', "
                                                       "int, float, identifier, '+', '-' or '('"))
        return response.success(node)

    def func_def(self):
        response = ParseResult()
        if not self.curr_token.matches(TT_KEYWORD, 'FUN'):
            return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                       self.curr_token.pos_end,
                                                       f"Expected 'FUN"))
        response.register_advancement()
        self.advance()
        if self.curr_token == TT_IDENTIFIER:
            var = self.curr_token
            response.register_advancement()
            self.advance()
            if self.curr_token != TT_LPAR:
                return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                           self.curr_token.pos_end,
                                                           f"Expected '('"))
        else:
            var = None
            if self.curr_token != TT_LPAR:
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
        if self.curr_token.type != TT_ARROW:
            return response.failure(InvalidSyntaxError(self.curr_token.pos_start,
                                                       self.curr_token.pos_end,
                                                       f"Expected '->'"))
        response.register_advancement()
        self.advance()
        return_node = response.register(self.expr())
        if response.error:
            return response
        return response.success(FuncDefNode(var, args, return_node))

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
