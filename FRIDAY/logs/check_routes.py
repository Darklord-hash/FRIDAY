import ast

with open(r'C:\FRIDAY\ui\friday_ui.py', 'r') as f:
    tree = ast.parse(f.read())

routes = []
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if hasattr(decorator.func, 'attr') and decorator.func.attr == 'route':
                    args = []
                    for arg in decorator.args:
                        if isinstance(arg, ast.Constant):
                            args.append(arg.value)
                    for kw in decorator.keywords:
                        if kw.arg == 'methods':
                            methods = [e.value for e in kw.value.elts]
                            args.append(methods)
                    routes.append((node.name, args))

print("Routes found:")
for name, args in routes:
    print(f"  {name}: {args}")

# Check for duplicates
from collections import Counter
names = [r[0] for r in routes]
dups = {name: count for name, count in Counter(names).items() if count > 1}
if dups:
    print(f"\n❌ DUPLICATE ROUTES: {dups}")
else:
    print("\n✅ No duplicate routes")