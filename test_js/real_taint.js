// real_taint.js - This file has a true data-flow taint!
const userInput = process.argv[2];
const code = Buffer.from(userInput, 'base64').toString();
eval(code);