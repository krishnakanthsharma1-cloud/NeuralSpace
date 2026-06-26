# neuralspace/ast_tokenizer.py
import hashlib
import math
from tree_sitter import Language, Parser

# --- Import specific language bindings ---
try:
    import tree_sitter_python as tspython
    PY_LANG = Language(tspython.language())
except ImportError:
    PY_LANG = None

try:
    import tree_sitter_javascript as tsjavascript
    JS_LANG = Language(tsjavascript.language())
except ImportError:
    JS_LANG = None

try:
    import tree_sitter_typescript as tstypescript
    TS_LANG = Language(tstypescript.language())
except ImportError:
    TS_LANG = None

try:
    import tree_sitter_go as tsgo
    GO_LANG = Language(tsgo.language())
except ImportError:
    GO_LANG = None

try:
    import tree_sitter_rust as tsrust
    RUST_LANG = Language(tsrust.language())
except ImportError:
    RUST_LANG = None

# Map file extensions to Tree-Sitter languages
LANGUAGE_MAP = {
    '.py': PY_LANG,
    '.js': JS_LANG,
    '.jsx': JS_LANG,
    '.ts': TS_LANG,
    '.tsx': TS_LANG,
    '.go': GO_LANG,
    '.rs': RUST_LANG,
}

# Dangerous keywords (universal across languages)
DANGEROUS_FUNCTIONS = {
    'exec', 'eval', 'system', 'Popen', 'Command', 'Function',
    'child_process.exec', 'child_process.spawn', 'os.system',
    'subprocess.Popen', 'subprocess.call', 'std::process::Command'
}
DANGEROUS_IMPORTS = {
    'os', 'subprocess', 'socket', 'requests', 'base64',
    'child_process', 'net', 'syscall', 'std::process', 'std::net'
}


class ASTTokenizer:
    def __init__(self):
        self.parsers = {}
        for ext, lang in LANGUAGE_MAP.items():
            if lang is not None:
                parser = Parser()
                parser.set_language(lang)
                self.parsers[ext] = parser
            else:
                self.parsers[ext] = None

    def tokenize(self, code_string: str, file_extension: str) -> list:
        if file_extension not in self.parsers or self.parsers[file_extension] is None:
            # Fallback to regex-based tokenizer if Tree-Sitter is missing
            from neuralspace.tokenizer import code_to_512vec
            return code_to_512vec(code_string)

        parser = self.parsers[file_extension]
        tree = parser.parse(bytes(code_string, 'utf-8'))
        root = tree.root_node

        tokens = []
        self._traverse_node(root, tokens, code_string)
        return tokens

    def _traverse_node(self, node, tokens, source_code):
        try:
            text = source_code[node.start_byte:node.end_byte]
        except:
            text = ''

        if text:
            if node.type in {'call', 'call_expression'}:
                tokens.append('CALL')
                for child in node.children:
                    if child.type in {'identifier', 'attribute', 'property_identifier', 'field_expression'}:
                        func_name = source_code[child.start_byte:child.end_byte]
                        tokens.append(func_name)
            elif node.type in {'import_statement', 'import_declaration', 'import_specifier', 'use_declaration'}:
                tokens.append('IMPORT')
                for child in node.children:
                    if child.type in {'string', 'string_literal', 'import_path', 'scoped_identifier'}:
                        import_name = source_code[child.start_byte:child.end_byte]
                        tokens.append(import_name)
            elif node.type in {'identifier', 'property_identifier', 'variable_name', 'field_identifier'}:
                tokens.append(text)

        for child in node.children:
            self._traverse_node(child, tokens, source_code)

    def get_combination_features(self, tokens: list) -> dict:
        token_set = set(tokens)
        features = {}

        has_dangerous_func = any(f in token_set for f in DANGEROUS_FUNCTIONS)
        has_dangerous_import = any(i in token_set for i in DANGEROUS_IMPORTS)

        features['has_dangerous_function'] = has_dangerous_func
        features['has_dangerous_import'] = has_dangerous_import
        features['dangerous_combination'] = has_dangerous_func and has_dangerous_import

        return features


def code_to_512vec_ast(code_string: str, file_extension: str = '.py'):
    tokenizer = ASTTokenizer()
    tokens = tokenizer.tokenize(code_string, file_extension)
    features = tokenizer.get_combination_features(tokens)

    counts = [0.0] * 512

    for token in tokens:
        h_base = int(hashlib.md5(token.encode()).hexdigest(), 16) % 120
        idx = (h_base + len(token)) % 512
        counts[idx] += 1.0

    if features['has_dangerous_function']:
        counts[490] += 3.0
    if features['has_dangerous_import']:
        counts[491] += 3.0
    if features['dangerous_combination']:
        counts[492] += 8.0

    vec = [math.log1p(c) for c in counts]
    norm = math.sqrt(sum(v * v for v in vec))
    return [v / norm for v in vec] if norm > 0 else vec