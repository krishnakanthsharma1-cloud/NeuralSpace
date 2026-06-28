# data_flow.py
import ast
import sys
from typing import Set, List, Dict, Tuple, Any

class DataFlowAnalyzer:
    """
    Perform AST-based taint analysis to determine if tainted data reaches a dangerous sink.
    Tracks variable assignments, function calls, and control flow.
    """
    
    SOURCE_FUNCTIONS = {
        'input', 'raw_input',
        'sys.stdin', 'sys.argv',
        'os.environ', 'os.getenv',
        'requests.get', 'requests.post',
        'urllib.request.urlopen',
        'open',
        'getattr',
    }
    
    SINK_FUNCTIONS = {
        'exec', 'eval', 'compile',
        'os.system', 'os.popen',
        'subprocess.Popen', 'subprocess.call', 'subprocess.check_output',
        'eval', 'execfile',
        '__import__',
    }
    
    def __init__(self, code_string: str):
        self.code = code_string
        self.tree = ast.parse(code_string)
        self.tainted_vars: Set[str] = set()
        self.sink_calls: List[Dict] = []
        self.taint_flow: List[Tuple[str, str]] = []
        self.sources_found: List[str] = []
    
    def analyze(self) -> Dict:
        self._walk_ast(self.tree)
        return {
            "has_tainted_sink": len(self.taint_flow) > 0,
            "tainted_vars": list(self.tainted_vars),
            "sink_calls": self.sink_calls,
            "taint_flow": self.taint_flow,
            "sources_found": self.sources_found,
        }
    
    def _walk_ast(self, node):
        if isinstance(node, ast.Assign):
            self._handle_assignment(node)
        elif isinstance(node, ast.Call):
            self._handle_call(node)
        elif isinstance(node, ast.FunctionDef):
            for child in ast.iter_child_nodes(node):
                self._walk_ast(child)
        else:
            for child in ast.iter_child_nodes(node):
                self._walk_ast(child)
    
    def _handle_assignment(self, node):
        if isinstance(node.value, ast.Call):
            if self._is_source_call(node.value):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.tainted_vars.add(target.id)
                        self.sources_found.append(f"{target.id} = {self._call_name(node.value)}")
                        self.taint_flow.append((f"Source: {self._call_name(node.value)}", f"Variable: {target.id}"))
        elif isinstance(node.value, ast.Name):
            if node.value.id in self.tainted_vars:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.tainted_vars.add(target.id)
                        self.taint_flow.append((f"Variable: {node.value.id}", f"Variable: {target.id}"))
        elif isinstance(node.value, ast.Call) and self._is_taint_retaining_call(node.value):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.tainted_vars.add(target.id)
                    self.taint_flow.append((f"Call: {self._call_name(node.value)}", f"Variable: {target.id}"))
    
    def _handle_call(self, node):
        call_name = self._call_name(node)
        
        # --- FIX: Check if the call is through a tainted variable (e.g., f(...) where f is tainted) ---
        if isinstance(node.func, ast.Name):
            if node.func.id in self.tainted_vars:
                self.sink_calls.append({"function": "tainted_callable", "line": node.lineno})
                self.taint_flow.append((f"Tainted callable: {node.func.id}", f"Call: {ast.unparse(node)}"))
                return

        if call_name in self.SINK_FUNCTIONS:
            self.sink_calls.append({"function": call_name, "line": node.lineno})
            for arg in node.args:
                if self._is_tainted_arg(arg):
                    self.taint_flow.append((f"Sink: {call_name}", f"Arg: {ast.unparse(arg)}"))
        elif call_name in self.SOURCE_FUNCTIONS:
            pass
    
    def _is_source_call(self, call_node) -> bool:
        return self._call_name(call_node) in self.SOURCE_FUNCTIONS
    
    def _is_taint_retaining_call(self, call_node) -> bool:
        return self._call_name(call_node) == 'getattr'
    
    def _call_name(self, call_node) -> str:
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            return self._attr_chain(call_node.func)
        return "unknown"
    
    def _attr_chain(self, attr_node) -> str:
        if isinstance(attr_node, ast.Name):
            return attr_node.id
        elif isinstance(attr_node, ast.Attribute):
            return f"{self._attr_chain(attr_node.value)}.{attr_node.attr}"
        return ""
    
    def _is_tainted_arg(self, arg_node) -> bool:
        if isinstance(arg_node, ast.Name):
            return arg_node.id in self.tainted_vars
        elif isinstance(arg_node, ast.Attribute):
            if isinstance(arg_node.value, ast.Name):
                return arg_node.value.id in self.tainted_vars
        elif isinstance(arg_node, ast.Subscript):
            if isinstance(arg_node.value, ast.Name):
                return arg_node.value.id in self.tainted_vars
        return False

def analyze_taint(code_string: str) -> Dict:
    try:
        analyzer = DataFlowAnalyzer(code_string)
        return analyzer.analyze()
    except Exception as e:
        return {
            "has_tainted_sink": False,
            "tainted_vars": [],
            "sink_calls": [],
            "taint_flow": [],
            "sources_found": [],
        }