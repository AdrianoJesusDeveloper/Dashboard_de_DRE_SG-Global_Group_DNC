from pathlib import Path
p=Path('app.py')
s=p.read_text(encoding='utf-8')
s=s.replace('BR Brasil', 'Brasil').replace('US EUA', 'EUA').replace('BR — Brasil', 'Brasil').replace('US — EUA', 'EUA')
p.write_text(s, encoding='utf-8')
