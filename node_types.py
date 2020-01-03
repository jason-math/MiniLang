class NumberNode:
    def __init__(self, token):
        self.token = token
        self.pos_start = self.token.pos_start
        self.pos_end = self.token.pos_end

    def __repr__(self):
        return f'{self.token}'


class StringNode:
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
    def __init__(self, var_name_token, val_node):
        self.var_name_token = var_name_token
        self.val_node = val_node
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


class IfNode:
    def __init__(self, cases, else_case):
        self.cases = cases
        self.else_case = else_case
        self.pos_start = self.cases[0][0].pos_start
        self.pos_end = self.else_case or (self.cases[len(self.cases) - 1][0]).pos_end


class ForNode:
    def __init__(self, var, start, end, step, body):
        self.var = var
        self.start = start
        self.end = end
        self.step = step
        self.body = body
        self.pos_start = self.var.pos_start
        self.pos_end = self.body.pos_end


class FuncDefNode:
    def __init__(self, var_name_token, args, body):
        self.var_name_token = var_name_token
        self.args = args
        self.body = body
        if self.var_name_token:
            self.pos_start = self.var_name_token.pos_start
        elif len(self.args) > 0:
            self.pos_start = self.args[0].pos_start
        else:
            self.pos_start = self.body.pos_start
        self.pos_end = self.body.pos_end


class CallNode:
    def __init__(self, call_node, args):
        self.call_node = call_node
        self.args = args
        self.pos_start = self.call_node.pos_start
        if len(self.args) > 0:
            self.pos_end = self.args[len(self.args) - 1].pos_end
        else:
            self.pos_end = self.call_node.pos_end


class WhileNode:
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body
        self.pos_start = self.condition.pos_start
        self.pos_end = self.body.pos_end
