# data_flow.py
import ast
import sys
from typing import Set, List, Dict, Tuple, Any

class DataFlowAnalyzer:
    """
    Perform AST-based taint analysis to determine if tainted data reaches a dangerous sink.
    Tracks variable assignments, function calls, and control flow.
    """
    
    # Sources: functions that return tainted (user-controlled) data
    SOURCE_FUNCTIONS = {
        'input', 'raw_input',
        'sys.stdin', 'sys.argv',
        'os.environ', 'os.getenv',
        'requests.get', 'requests.post',
        'urllib.request.urlopen',
        'open',
        'getattr',  # Can fetch attributes dynamically
    }
    
    # Sinks: dangerous functions that execute code
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
        """Run the analysis and return results."""
        self._walk_ast(self.tree)
        return {
            "has_tainted_sink": len(self.taint_flow) > 0,
            "tainted_vars": list(self.tainted_vars),
            "sink_calls": self.sink_calls,
            "taint_flow": self.taint_flow,
            "sources_found": self.sources_found,
        }
    
    def _walk_ast(self, node):
        """Recursively walk AST."""
        if isinstance(node, ast.Assign):
            self._handle_assignment(node)
        elif isinstance(node, ast.Call):
            self._handle_call(node)
        elif isinstance(node, ast.FunctionDef):
            # Recursively walk function body
            for child in ast.iter_child_nodes(node):
                self._walk_ast(child)
        else:
            for child in ast.iter_child_nodes(node):
                self._walk_ast(child)
    
    def _handle_assignment(self, node):
        """Handle variable assignment: track tainted values."""
        # Check if the value is a source call
        if isinstance(node.value, ast.Call):
            if self._is_source_call(node.value):
                # Mark the target variable as tainted
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.tainted_vars.add(target.id)
                        self.sources_found.append(f"{target.id} = {self._call_name(node.value)}")
                        self.taint_flow.append((f"Source: {self._call_name(node.value)}", f"Variable: {target.id}"))
        # Also check if the value is a variable that is tainted
        elif isinstance(node.value, ast.Name):
            if node.value.id in self.tainted_vars:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.tainted_vars.add(target.id)
                        self.taint_flow.append((f"Variable: {node.value.id}", f"Variable: {target.id}"))
        # Check if the value is a function call that returns tainted data (like getattr)
        elif isinstance(node.value, ast.Call) and self._is_taint_retaining_call(node.value):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.tainted_vars.add(target.id)
                    self.taint_flow.append((f"Call: {self._call_name(node.value)}", f"Variable: {target.id}"))
    
    def _handle_call(self, node):
        """Handle function calls: check if it's a sink with tainted args."""
        call_name = self._call_name(node)
        if call_name in self.SINK_FUNCTIONS:
            self.sink_calls.append({"function": call_name, "line": node.lineno})
            # Check arguments for tainted variables
            for arg in node.args:
                if self._is_tainted_arg(arg):
                    self.taint_flow.append((f"Sink: {call_name}", f"Arg: {ast.unparse(arg)}"))
        elif call_name in self.SOURCE_FUNCTIONS:
            # Mark any return value as tainted? Not directly, but assignments handle it.
            pass
    
    def _is_source_call(self, call_node) -> bool:
        """Check if a call is a source."""
        return self._call_name(call_node) in self.SOURCE_FUNCTIONS
    
    def _is_taint_retaining_call(self, call_node) -> bool:
        """Check if a call returns tainted data (e.g., getattr)."""
        # getattr can return tainted data if its object is tainted
        return self._call_name(call_node) == 'getattr'
    
    def _call_name(self, call_node) -> str:
        """Get the full name of a function call."""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            # e.g., os.system -> 'os.system'
            return self._attr_chain(call_node.func)
        return "unknown"
    
    def _attr_chain(self, attr_node) -> str:
        """Recursively build attribute chain."""
        if isinstance(attr_node, ast.Name):
            return attr_node.id
        elif isinstance(attr_node, ast.Attribute):
            return f"{self._attr_chain(attr_node.value)}.{attr_node.attr}"
        return ""
    
    def _is_tainted_arg(self, arg_node) -> bool:
        """Check if an argument is tainted."""
        if isinstance(arg_node, ast.Name):
            return arg_node.id in self.tainted_vars
        elif isinstance(arg_node, ast.Attribute):
            # e.g., obj.attr, check if base is tainted
            if isinstance(arg_node.value, ast.Name):
                return arg_node.value.id in self.tainted_vars
        elif isinstance(arg_node, ast.Subscript):
            # e.g., dict['key'], check if base is tainted
            if isinstance(arg_node.value, ast.Name):
                return arg_node.value.id in self.tainted_vars
        return False

def analyze_taint(code_string: str) -> Dict:
    """Public API to run data-flow analysis."""
    try:
        analyzer = DataFlowAnalyzer(code_string)
        return analyzer.analyze()
    except Exception as e:
        print(f"[!] Data-flow analysis error: {e}")
        return {
            "has_tainted_sink": False,
            "tainted_vars": [],
            "sink_calls": [],
            "taint_flow": [],
            "sources_found": [],
        }