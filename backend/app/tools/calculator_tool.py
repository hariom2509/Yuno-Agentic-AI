import ast
import operator
import re


_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _safe_eval(node):
    if isinstance(node, ast.Constant):
        return node.n
    if isinstance(node, ast.BinOp):
        op = _SAFE_OPS.get(type(node.op))
        if op is None:
            raise ValueError("Unsupported operator")
        return op(_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp):
        op = _SAFE_OPS.get(type(node.op))
        if op is None:
            raise ValueError("Unsupported unary operator")
        return op(_safe_eval(node.operand))
    raise ValueError(f"Unsupported expression type: {type(node)}")


def _balance_parentheses(s: str) -> str:
    """Removes unmatched parentheses from the expression to make it syntactically clean."""
    chars = list(s)
    stack = []
    unmatched_close = []
    
    for i, char in enumerate(chars):
        if char == '(':
            stack.append(i)
        elif char == ')':
            if stack:
                stack.pop()
            else:
                unmatched_close.append(i)
                
    unmatched_open = stack
    indices_to_remove = set(unmatched_open + unmatched_close)
    return "".join(char for idx, char in enumerate(chars) if idx not in indices_to_remove)


def calculate(expression: str) -> str:
    """Safe arithmetic evaluator — no eval(), no exec(). Extracts mathematical expressions from natural language."""
    try:
        expression = expression.strip()
        
        # 1. Direct evaluation attempt
        try:
            tree = ast.parse(expression, mode="eval")
            result = _safe_eval(tree.body)
            return f"Result: {result}"
        except Exception:
            pass

        # 2. Extract math-like candidate sequences
        candidates = re.findall(r"[\d\+\-\*\/\^\(\)\.\s]+", expression)
        
        best_result = None
        best_score = -1
        
        def evaluate_candidate(cand: str):
            nonlocal best_result, best_score
            
            cand_clean = cand.strip()
            if not cand_clean:
                return
                
            # Clean invalid boundary operators
            while cand_clean and cand_clean[-1] in "+-*/^.(":
                cand_clean = cand_clean[:-1].strip()
            while cand_clean and cand_clean[0] in "*/^.)":
                cand_clean = cand_clean[1:].strip()
                
            if not cand_clean or not any(char.isdigit() for char in cand_clean):
                return
                
            # Clean unmatched parentheses
            cand_balanced = _balance_parentheses(cand_clean)
            
            try:
                tree = ast.parse(cand_balanced, mode="eval")
                res = _safe_eval(tree.body)
                
                # Scoring metric to prioritize complete expressions over simple floats/ints:
                # 1 point per digit, 5 points per arithmetic operator
                digits = sum(c.isdigit() for c in cand_balanced)
                operators = sum(c in "+-*/^" for c in cand_balanced)
                score = digits + (operators * 5)
                
                if score > best_score:
                    best_score = score
                    best_result = res
            except Exception:
                pass
                
            # If the candidate failed to parse, split by spaces/parentheses and try to evaluate sub-parts recursively
            # (only if sub-parts are actually different from the candidate to avoid infinite recursion)
            sub_parts = re.split(r"[\(\)\s]+", cand_clean)
            for part in sub_parts:
                if part != cand_clean:
                    evaluate_candidate(part)

        for candidate in candidates:
            evaluate_candidate(candidate)
            
        if best_result is not None:
            return f"Result: {best_result}"
            
        raise ValueError("No valid mathematical expression could be extracted or evaluated.")
        
    except Exception as e:
        return f"Calculation error: {e}. Input: {expression}"