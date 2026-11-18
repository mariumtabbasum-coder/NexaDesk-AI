import ast, operator, re
OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.Pow:operator.pow,ast.Mod:operator.mod,ast.USub:operator.neg,ast.UAdd:operator.pos}
def calculate(text):
    expr=text.lower().replace("calculate","").replace("what is","").replace("how much is","").replace("×","*").replace("÷","/").replace("^","**").strip().rstrip("?")
    expr=re.sub(r"[^0-9+\-*/().% ]","",expr)
    try:
        node=ast.parse(expr,mode="eval")
        def ev(n):
            if isinstance(n,ast.Expression): return ev(n.body)
            if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)): return n.value
            if isinstance(n,ast.BinOp) and type(n.op) in OPS: return OPS[type(n.op)](ev(n.left),ev(n.right))
            if isinstance(n,ast.UnaryOp) and type(n.op) in OPS: return OPS[type(n.op)](ev(n.operand))
            raise ValueError("Unsupported expression")
        result=ev(node)
        if abs(result)>1e100: return None
        return result
    except Exception: return None
