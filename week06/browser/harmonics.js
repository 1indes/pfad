// Week 6 harmonics: set a base, multiply it, then hear the sum.
const H_W = 1200, H_H = 650;
let baseControl, multipleControl, hContext = null, hSources = [], hToken = 0;
let hMessage = 'Predict: what happens when 220 Hz is multiplied by 2?';
function validateHarmonic(base, multiple) {
  const b = Number(base), n = Number(multiple);
  if (!Number.isFinite(b) || b < 110 || b > 880 || !Number.isInteger(n) || n < 1 || n > 12 || b * n > 4000) return null;
  return {baseHz:b, multiple:n, harmonicHz:b * n};
}
function setup() {
  createCanvas(H_W, H_H); textFont('monospace');
  baseControl = createSlider(110, 880, 220, 10, 'Base Hz');
  multipleControl = createSlider(1, 12, 2, 1, 'Multiple');
}
function draw() {
  background('#f5f1e8'); noStroke(); fill('#102b30');
  textSize(35); text('Build a timbre from a base and its harmonic', 45, 57);
  const current = validateHarmonic(baseControl.value(), multipleControl.value());
  textSize(24);
  text(current ? `${current.baseHz} Hz  x  ${current.multiple}  =  ${current.harmonicHz} Hz` : 'Lower the base or the multiple: keep the result below 4,000 Hz.', 45, 107);
  if (!current) return;
  const b = current.baseHz, n = current.multiple;
  const lines = [['BASE', '#246e70', 195, t => Math.sin(t)],
    ['HARMONIC', '#d75c28', 335, t => Math.sin(n * t)],
    ['SUM (HALF + HALF)', '#102b30', 475, t => (Math.sin(t) + Math.sin(n * t)) / 2]];
  for (const [label, color, y, rule] of lines) {
    stroke('#c0cccc'); strokeWeight(1); line(245, y, 1150, y);
    noStroke(); fill(color); textSize(19); text(label, 42, y + 7);
    stroke(color); strokeWeight(3); noFill(); beginShape();
    for (let x = 245; x <= 1150; x += 4) vertex(x, y - rule((x - 245) / 905 * Math.PI * 4) * 50);
    endShape();
  }
  noStroke(); fill('#34545a'); textSize(18);
  const clock = hContext ? `${hContext.sampleRate.toLocaleString()} samples/s` : 'set by the browser';
  text(`Browser clock: ${clock}. Peaks: ${b} Hz and ${b * n} Hz.`, 45, 555);
  text(hMessage, 45, 595);
  const buttons = [['BASE', 45, '#246e70'], ['HARMONIC', 280, '#d75c28'], ['TOGETHER', 515, '#102b30'], ['STOP', 750, '#b74423']];
  for (const [label, x, color] of buttons) {
    fill(color); rect(x, 605, 210, 39, 4); fill('#fff'); textSize(19); text(label, x + 19, 633);
  }
}
async function harmonicPlay(kind) {
  const current = validateHarmonic(baseControl.value(), multipleControl.value());
  if (!current) { hMessage = 'That product is too high. Lower the base or multiple.'; return; }
  stopAudio(); const token = hToken;
  try {
    hContext = new (window.AudioContext || window.webkitAudioContext)();
    const ctx = hContext; await ctx.resume();
    if (token !== hToken || ctx !== hContext) return;
    const frequencies = kind === 'base' ? [current.baseHz] : kind === 'harmonic' ? [current.harmonicHz] : [current.baseHz, current.harmonicHz];
    for (const hz of frequencies) {
      const osc = ctx.createOscillator(), gain = ctx.createGain(), now = ctx.currentTime;
      osc.type = 'sine'; osc.frequency.value = hz;
      gain.gain.setValueAtTime(0, now);
      gain.gain.linearRampToValueAtTime(0.03 / frequencies.length, now + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.75);
      osc.connect(gain); gain.connect(ctx.destination); hSources.push(osc);
      osc.start(now); osc.stop(now + 0.78);
    }
    hMessage = `Listening: ${frequencies.join(' + ')} Hz. What changed about the sound?`;
  } catch (error) { console.warn('Harmonic audio unavailable', error); stopAudio(); hMessage = 'Audio unavailable; compare the three drawn waves.'; }
}
function stopAudio() {
  hToken++;
  for (const osc of hSources) { try { osc.stop(); } catch (_) {} }
  hSources = [];
  if (hContext) { hContext.close(); hContext = null; }
}
function mousePressed() {
  if (mouseY < 605 || mouseY > 645) return;
  if (mouseX >= 45 && mouseX < 255) harmonicPlay('base');
  else if (mouseX >= 280 && mouseX < 490) harmonicPlay('harmonic');
  else if (mouseX >= 515 && mouseX < 725) harmonicPlay('together');
  else if (mouseX >= 750 && mouseX < 960) stopAudio();
}
function keyPressed() { if (keyCode === 27) stopAudio(); }
window.addEventListener('keydown', event => { if (event.key === 'Escape') stopAudio(); }, true);
window.addEventListener('message', event => { if (event.source === window.parent && event.data === 'slide:stop') stopAudio(); });
document.addEventListener('visibilitychange', () => { if (document.hidden) stopAudio(); });
window.addEventListener('pagehide', stopAudio);
window.week06Harmonics = {validate: validateHarmonic, stopAudio};
