import os, re
for f in os.listdir('alembic/versions'):
    if not f.endswith('.py'): continue
    with open(f'alembic/versions/{f}') as fh:
        content = fh.read()
    rev = re.search(r"revision:\s*str\s*=\s*['\"]([^'\"]+)['\"]", content)
    down = re.search(r"down_revision[^=]*=\s*['\"]([^'\"]+)['\"]", content)
    
    if not down:
        down_match = re.search(r"down_revision[^=]*=\s*(\([^\)]+\)|\[[^\]]+\]|None)", content)
        if down_match:
            down_val = down_match.group(1)
        else:
            down_val = 'None'
    else:
        down_val = down.group(1)
        
    rev_val = rev.group(1) if rev else 'None'
    print(f'{rev_val} -> {down_val} ({f})')
