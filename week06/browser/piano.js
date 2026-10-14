// Week 6 piano: p5 draws; Web Audio plays only after a key/click.
const PIANO_W = 1200, PIANO_H = 620;
const PIANO_KEYS = [
  ['1', 'C4', 261.63], ['2', 'D4', 293.66], ['3', 'E4', 329.63],
  ['4', 'F4', 349.23], ['5', 'G4', 392.00], ['6', 'A4', 440.00],
  ['7', 'B4', 493.88], ['8', 'C5', 523.25],
];
let pianoContext = null, pianoVoices = [], pianoLast = null, pianoToken = 0;
function pianoNoteHz(key) { return PIANO_KEYS.find(note => note[0] === String(key).toLowerCase())?.[2] || null; }
function setup() { createCanvas(PIANO_W, PIANO_H); textFont('monospace'); }
function draw() {
  background('#f5f1e8'); noStroke(); fill('#102b30');
  textSize(35); text('A keyboard is a rule for choosing frequencies', 42, 64);
  textSize(21); text('Click a key or press 1 2 3 4 5 6 7 8. Sound starts only when you play.', 42, 108);
  for (let i = 0; i < PIANO_KEYS.length; i++) {
    const x = 42 + 138 * i, active = pianoLast && pianoLast[0] === PIANO_KEYS[i][0];
    fill(active ? '#e98040' : '#ffffff'); stroke('#17373b'); strokeWeight(3);
    rect(x, 156, 128, 300, 8); noStroke(); fill('#102b30');
    textSize(23); text(PIANO_KEYS[i][1], x + 32, 395);
    textSize(19); text(PIANO_KEYS[i][0].toUpperCase(), x + 53, 434);
  }
  fill('#102b30'); textSize(27);
  text(pianoLast ? `${pianoLast[1]}  =  ${pianoLast[2].toFixed(2)} Hz` : 'Which note would be an octave above C4?', 42, 510);
  fill('#b74423'); rect(930, 490, 220, 70, 6); fill('#fff'); text('STOP', 995, 535);
  fill('#34545a'); textSize(18); text('Short, quiet notes. Escape, Stop, or leaving the slide silences them.', 42, 585);
}
async function pianoPlay(key) {
  const note = PIANO_KEYS.find(item => item[0] === String(key).toLowerCase());
  if (!note) return;
  const token = pianoToken;
  try {
    if (!pianoContext) pianoContext = new (window.AudioContext || window.webkitAudioContext)();
    const ctx = pianoContext;
    await ctx.resume();
    if (token !== pianoToken || ctx !== pianoContext) return;
    const osc = ctx.createOscillator(), gain = ctx.createGain(), now = ctx.currentTime;
    osc.type = 'sine'; osc.frequency.value = note[2];
    gain.gain.setValueAtTime(0, now);
    gain.gain.linearRampToValueAtTime(0.025, now + 0.015);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.55);
    osc.connect(gain); gain.connect(ctx.destination);
    osc.onended = () => { pianoVoices = pianoVoices.filter(voice => voice !== osc); };
    pianoVoices.push(osc); osc.start(now); osc.stop(now + 0.57);
    if (pianoVoices.length > 4) { try { pianoVoices.shift().stop(); } catch (_) {} }
    pianoLast = note;
  } catch (error) { console.warn('Piano audio unavailable', error); stopAudio(); }
}
function stopAudio() {
  pianoToken++;
  for (const voice of pianoVoices) { try { voice.stop(); } catch (_) {} }
  pianoVoices = []; pianoLast = null;
  if (pianoContext) { pianoContext.close(); pianoContext = null; }
}
function mousePressed() {
  if (mouseX >= 930 && mouseX <= 1150 && mouseY >= 490 && mouseY <= 560) return stopAudio();
  if (mouseX >= 42 && mouseX < 1146 && mouseY >= 156 && mouseY <= 456) {
    const index = Math.floor((mouseX - 42) / 138);
    if (PIANO_KEYS[index] && mouseX - (42 + 138 * index) < 128) pianoPlay(PIANO_KEYS[index][0]);
  }
}
function keyPressed() {
  if (keyCode === 27) { stopAudio(); return false; }
  if (pianoNoteHz(key) && !keyIsDown(17) && !keyIsDown(91)) { pianoPlay(key); return false; }
}
window.addEventListener('keydown', event => { if (event.key === 'Escape') stopAudio(); }, true);
window.addEventListener('message', event => { if (event.source === window.parent && event.data === 'slide:stop') stopAudio(); });
document.addEventListener('visibilitychange', () => { if (document.hidden) stopAudio(); });
window.addEventListener('pagehide', stopAudio);
window.week06Piano = {noteHz: pianoNoteHz, isRunning: () => pianoVoices.length > 0, stopAudio};
