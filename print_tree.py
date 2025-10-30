from pathlib import Path

IGNORE = {'.git', '__pycache__', 'node_modules', 'bin', 'obj', 'venv'}
MAX_DEPTH = 2

def build_tree(path: Path, prefix: str = '', level: int = 0) -> str:
    if level > MAX_DEPTH:
        return ''
    lines = []
    entries = [e for e in sorted(path.iterdir()) if e.name not in IGNORE]
    for i, entry in enumerate(entries):
        connector = '├── ' if i < len(entries) - 1 else '└── '
        lines.append(prefix + connector + entry.name)
        if entry.is_dir():
            extension = '│   ' if i < len(entries) - 1 else '    '
            lines.append(build_tree(entry, prefix + extension, level + 1))
    return '\n'.join(lines)

if __name__ == '__main__':
    tree = build_tree(Path('.'))
    with open('structure.txt', 'w', encoding='utf-8') as f:
        f.write(tree)
    print('✅ structure.txt generated successfully!')
