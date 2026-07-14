import ast

class FormulaEngine:
    """
    Computes derived columns safely in Python using an AST-based parser.
    Prevents execution of malicious code while allowing arithmetic operations on record fields.
    """

    class SafeEval(ast.NodeVisitor):
        def __init__(self, variables):
            self.variables = variables

        def visit_Num(self, node):
            return node.n

        def visit_Constant(self, node):
            return node.value

        def visit_Name(self, node):
            if node.id in self.variables:
                val = self.variables[node.id]
                try:
                    return float(val) if val is not None else 0.0
                except (ValueError, TypeError):
                    return 0.0
            raise ValueError(f"Unregistered variable: {node.id}")

        def visit_BinOp(self, node):
            left = self.visit(node.left)
            right = self.visit(node.right)
            
            if isinstance(node.op, ast.Add):
                return left + right
            elif isinstance(node.op, ast.Sub):
                return left - right
            elif isinstance(node.op, ast.Mult):
                return left * right
            elif isinstance(node.op, ast.Div):
                return left / right if right != 0 else 0.0
            raise ValueError(f"Unsupported operator: {type(node.op)}")

        def visit_UnaryOp(self, node):
            operand = self.visit(node.operand)
            if isinstance(node.op, ast.USub):
                return -operand
            elif isinstance(node.op, ast.UAdd):
                return operand
            raise ValueError(f"Unsupported unary operator: {type(node.op)}")

    @classmethod
    def evaluate_expression(cls, expr, row):
        try:
            tree = ast.parse(expr, mode='eval')

            # Extract fields from model instances
            if not isinstance(row, dict):
                row_dict = {}
                for field in row._meta.fields:
                    row_dict[field.name] = getattr(row, field.name)
                # Include annotated fields / properties
                for k in dir(row):
                    if not k.startswith('_') and not callable(getattr(row, k)):
                        row_dict[k] = getattr(row, k)
                row = row_dict

            visitor = cls.SafeEval(row)
            return visitor.visit(tree.body)
        except Exception:
            return 0.0

    @classmethod
    def apply_formulas(cls, data, formulas_config):
        """
        data: list of dicts or list of model instances
        formulas_config: dict of { 'alias': 'expression' }
        """
        if not formulas_config:
            return data

        processed_data = []
        for row in data:
            if not isinstance(row, dict):
                row_dict = {}
                for field in row.__class__._meta.fields:
                    row_dict[field.name] = getattr(row, field.name)
                for k in dir(row):
                    if not k.startswith('_') and not callable(getattr(row, k)):
                        row_dict[k] = getattr(row, k)
                row = row_dict
            else:
                row = dict(row)

            for alias, expr in formulas_config.items():
                row[alias] = cls.evaluate_expression(expr, row)
            processed_data.append(row)

        return processed_data
