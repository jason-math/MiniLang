from function import *
from lexer import *


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
        val = val.copy().set_pos(node.pos_start, node.pos_end)
        return response.success(val)

    def visit_VarAssignNode(self, node, context):
        response = RTResult()
        var_name = node.var_name_token.val
        val = response.register(self.visit(node.val_node, context))
        if response.error:
            return response
        context.symbol_table.set(var_name, val)
        return response.success(val)

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

    def visit_IfNode(self, node, context):
        response = RTResult()

        for condition, expression in node.cases:
            condition_val = response.register(self.visit(condition, context))
            if response.error:
                return response
            if condition_val.is_true():
                expr_val = response.register(self.visit(expression, context))
                if response.error:
                    return response
                return response.success(expr_val)
        if node.else_case:
            else_val = response.register(self.visit(node.else_case, context))
            if response.error:
                return response
            return response.success(else_val)
        return response.success(None)

    def visit_ForNode(self, node, context):
        response = RTResult()
        start = response.register(self.visit(node.start, context))
        if response.error:
            return response
        end = response.register(self.visit(node.end, context))
        if response.error:
            return response
        if node.step:
            step = response.register(self.visit(node.step, context))
            if response.error:
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
            response.register(self.visit(node.body, context))
            if response.error:
                return response
            if step.val >= 0:
                condition = i < end.val
            else:
                condition = i > end.val
        return response.success(None)

    def visit_WhileNode(self, node, context):
        response = RTResult()
        while True:
            condition = response.register(self.visit(node.condition, context))
            if response.error:
                return response
            if not condition.is_true():
                break
            response.register(self.visit(node.body, context))
            if response.error:
                return response
        return response.success(None)

    # noinspection PyMethodMayBeStatic
    def visit_FuncDefNode(self, node, context):
        response = RTResult()
        func_name = node.var_name_token.val if node.var_name_token else None
        body = node.body
        arg_names = [arg_name.val for arg_name in node.args]
        func_val = Function(func_name, body, arg_names).set_context(context).set_pos(node.pos_start, node.pos_end)
        if node.var_name_token:
            context.symbol_table.set(func_name, func_val)
        return response.success(func_val)

    def visit_CallNode(self, node, context):
        response = RTResult()
        args = []
        call_val = response.register(self.visit(node.call_node, context))
        if response.error:
            return response
        call_val = call_val.copy().set_pos(node.pos_start, node.pos_end)
        for arg in node.args:
            args.append(response.register(self.visit(arg, context)))
            if response.error:
                return response
        ret_val = response.register(call_val.execute(args))
        if response.error:
            return response
        return response.success(ret_val)
