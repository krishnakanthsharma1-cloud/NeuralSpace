// evil.ts
import { exec } from 'child_process';
import * as base64 from 'base64-js';
const code = 'aW1wb3J0IG9zOyBvcy5zeXN0ZW0oImNhbGMuZXhlIik=';
eval(Buffer.from(code, 'base64').toString());