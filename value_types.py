from interpreter import *


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

    def __repr__(self):
        return f'"{self.val}"'
