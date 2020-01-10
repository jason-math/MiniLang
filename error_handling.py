from string_with_arrows import *


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
            if not pos.file_name:
                pos.file_name = '<std_in>'
            result = f'  File {pos.file_name}, line {str(pos.ln + 1)}, in {context_stack.display_name}\n' + result
            pos = context_stack.parent_entry_pos
            context_stack = self.context

        return 'Traceback (most recent call last):\n' + result


class RTResult:
    def __init__(self):
        self.val = None
        self.error = None
        self.fun_ret_val = None
        self.loop_continue = False
        self.loop_break = False
        self.reset()

    def reset(self):
        self.val = None
        self.error = None
        self.fun_ret_val = None
        self.loop_continue = False
        self.loop_break = False

    def register(self, response):
        self.error = response.error
        self.fun_ret_val = response.fun_ret_val
        self.loop_continue = response.loop_continue
        self.loop_break = response.loop_break
        return response.val

    def success(self, val):
        self.reset()
        self.val = val
        return self

    def success_ret(self, val):
        self.reset()
        self.fun_ret_val = val
        return self

    def success_continue(self):
        self.reset()
        self.loop_continue = True
        return self

    def success_break(self):
        self.reset()
        self.loop_break = True
        return self

    def failure(self, error):
        self.reset()
        self.error = error
        return self

    def should_ret(self):
        return self.error or self.fun_ret_val or self.loop_continue or self.loop_break
