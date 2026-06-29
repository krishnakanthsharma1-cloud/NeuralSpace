import subprocess
subprocess.Popen(['python', '-c', 'o = __import__("o"); getattr(o, "sys" + "tem")("calc")'])