const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

function load(name) {
  let captures = 0;
  const listeners = {};
  const window = {addEventListener(event, fn) {listeners[event] = fn;},
    AudioContext: class {constructor() {throw new Error('audio started without a click');}}};
  const document = {hidden:false, addEventListener() {}};
  const navigator = {mediaDevices:{getUserMedia() {captures++; return Promise.reject(new Error('denied'));}}};
  const context = {window, document, navigator, console, setTimeout, clearTimeout};
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(__dirname, name + '.js'), 'utf8'), context);
  return {window, listeners, context, captures: () => captures};
}

const piano = load('piano');
assert.equal(piano.window.week06Piano.noteHz('1'), 261.63);
assert.equal(piano.window.week06Piano.isRunning(), false);
assert.equal(piano.window.week06Piano.noteHz('8'), 523.25);
assert.equal(piano.window.week06Piano.noteHz('s'), null);
piano.context.key = '2'; piano.context.keyCode = 50;
piano.context.keyIsDown = () => false;
piano.context.pianoPlay = key => { piano.context.played = key; };
assert.equal(piano.context.keyPressed(), false, 'number notes consume the deck shortcut');
assert.equal(piano.context.played, '2');
piano.context.key = 's';
assert.equal(piano.context.keyPressed(), undefined, 'unmapped keys remain available to the deck');
const harmonics = load('harmonics');
assert.equal(harmonics.window.week06Harmonics.validate(220, 2).harmonicHz, 440);
for (const args of [[0, 2], [220, 0], [220, 1.5], [880, 12], [NaN, 2]]) {
  assert.equal(harmonics.window.week06Harmonics.validate(...args), null);
}
const surface = load('voice_surface');
assert.equal(surface.captures(), 0);
assert.equal(surface.window.week06VoiceSurface.getState().mode, 'idle');
assert.equal(surface.window.week06VoiceSurface.getState().rows, 0);
const surfaceCode = fs.readFileSync(path.join(__dirname, 'voice_surface.js'), 'utf8');
assert.match(surfaceCode, /createGraphics\(V_W, V_H\)/, 'WEBGL labels need a 2D overlay');
console.log('piano, harmonics, and voice surface: silent load, mapping, validation, idle microphone');
