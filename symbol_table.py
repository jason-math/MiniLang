class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent

    def get(self, name):
        val = self.symbols.get(name, None)
        if val is None and self.parent:
            return self.parent.get(name)
        return val

    def set(self, name, val):
        self.symbols[name] = val

    def remove(self, name):
        del self.symbols[name]

    def to_string(self):
        return self.symbols
