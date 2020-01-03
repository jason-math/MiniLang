from parser import *
from value_types import *

global_symbol_table = SymbolTable()
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
    print(parser.__dict__)
    ast = parser.parse()
    if ast.error:
        return None, ast.error
    print(ast.__dict__)

    # Traverses and computes the AST
    interpreter = Interpreter()
    context = Context('<program>')
    context.symbol_table = global_symbol_table
    result = interpreter.visit(ast.node, context)
    print(global_symbol_table.__dict__)

    return result.val, result.error
