// Voice becomes a moving frequency landscape. No recording or upload.
const V_W = 1200, V_H = 660, V_BINS = 64, V_ROWS = 48;
let vMode = 'idle', vStream = null, vContext = null, vSource = null, vAnalyser = null;
let vHistory = [], vToken = 0, vStep = 0, vMessage = 'Click MIC to grant permission, or DEMO for a synthetic voice-like signal.';
let vHud;
function setup() { createCanvas(V_W, V_H, WEBGL); vHud = createGraphics(V_W, V_H); vHud.textFont('monospace'); frameRate(15); }
function getVoiceState() { return {mode:vMode, rows:vHistory.length, hasStream:!!vStream}; }
function stopMic() {
  vToken++;
  if (vStream) { for (const track of vStream.getTracks()) track.stop(); vStream = null; }
  if (vSource) { vSource.disconnect(); vSource = null; }
  if (vAnalyser) { vAnalyser.disconnect(); vAnalyser = null; }
  if (vContext) { vContext.close(); vContext = null; }
  vHistory = [];
  vMode = 'idle'; vMessage = 'Stopped. No microphone audio was saved.';
}
async function startMic() {
  stopMic();
  const token = vToken;
  if (!navigator.mediaDevices?.getUserMedia || !window.isSecureContext) {
    vMode = 'error'; vMessage = 'Microphone needs HTTPS or localhost. Try DEMO instead.'; return;
  }
  vMode = 'requesting'; vMessage = 'Waiting for browser microphone permission...';
  try {
    const stream = await navigator.mediaDevices.getUserMedia({audio:true});
    if (token !== vToken) { stream.getTracks().forEach(track => track.stop()); return; }
    vStream = stream;
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    vContext = ctx; await ctx.resume();
    if (token !== vToken) return;
    vSource = ctx.createMediaStreamSource(stream);
    vAnalyser = ctx.createAnalyser(); vAnalyser.fftSize = 1024; vAnalyser.smoothingTimeConstant = 0.68;
    vSource.connect(vAnalyser); // Deliberately not connected to speakers.
    stream.getTracks().forEach(track => track.addEventListener('ended', () => {
      if (vStream === stream) stopMic();
    }));
    vHistory = []; vMode = 'live'; vMessage = 'Speak to move the landscape. Visual only: your voice is not played through speakers.';
  } catch (error) {
    if (token === vToken) { stopMic(); vMode = 'error';
      vMessage = error.name === 'NotAllowedError'
        ? 'Mic blocked: allow Microphone in browser site settings, reload, then click MIC. Or use DEMO.'
        : 'Microphone unavailable. Check your input device or try DEMO.'; }
  }
}
function startDemo() {
  stopMic(); vHistory = []; vStep = 0; vMode = 'demo';
  vMessage = 'Synthetic input, not a recorded voice. Change to MIC only with consent.';
}
function voiceRow() {
  if (vMode === 'live' && vAnalyser) {
    const values = new Uint8Array(vAnalyser.frequencyBinCount);
    vAnalyser.getByteFrequencyData(values);
    return Array.from({length:V_BINS}, (_, i) => values[i * 4] / 255);
  }
  vStep++;
  return Array.from({length:V_BINS}, (_, i) => {
    const peak = 13 + 7 * Math.sin(vStep / 12);
    const spread = Math.exp(-Math.pow((i - peak) / 5, 2));
    return Math.max(0, spread * (0.5 + 0.4 * Math.sin(vStep / 6) ** 2));
  });
}
function draw() {
  background('#f5f1e8');
  if (vMode === 'live' || vMode === 'demo') {
    vHistory.push(voiceRow()); if (vHistory.length > V_ROWS) vHistory.shift();
  }
  push(); translate(10, -55, 0); rotateX(0.62); rotateY(-0.18); noFill();
  strokeWeight(1.6);
  for (let row = 0; row < vHistory.length; row++) {
    const y = (row - V_ROWS / 2) * 8;
    stroke(row % 4 === 0 ? '#cd5c2e' : '#267277');
    beginShape();
    for (let bin = 0; bin < V_BINS; bin++) {
      const height = vHistory[row][bin] * 175;
      vertex((bin - V_BINS / 2) * 11, y, height);
    }
    endShape();
  }
  pop();
  // A 2D HUD keeps labels and buttons legible over the rotating WebGL mesh.
  vHud.clear(); vHud.noStroke(); vHud.fill('#102b30');
  vHud.textSize(35); vHud.text('SPEAK AND SEE THE FREQUENCY LANDSCAPE', 42, 58);
  vHud.textSize(19);
  vHud.text('frequency →', 42, 137);
  vHud.text('time → away', 42, 167);
  vHud.text('height → energy', 42, 197);
  vHud.text(vMessage, 42, 500, 1116, 55);
  for (const [label, x, color] of [['MIC', 42, '#246e70'], ['DEMO', 290, '#102b30'], ['STOP', 538, '#b74423']]) {
    vHud.fill(color); vHud.rect(x, 558, 215, 65, 6); vHud.fill('#fff'); vHud.textSize(24); vHud.text(label, x + 35, 601);
  }
  vHud.fill('#34545a'); vHud.textSize(17); vHud.text('No sound is played, uploaded or stored. Escape/leave stops the mic.', 42, 651);
  push(); resetMatrix(); image(vHud, -V_W / 2, -V_H / 2); pop();
}
function mousePressed() {
  if (mouseY < 558 || mouseY > 623) return;
  if (mouseX >= 42 && mouseX < 257) startMic();
  else if (mouseX >= 290 && mouseX < 505) startDemo();
  else if (mouseX >= 538 && mouseX < 753) stopMic();
}
function keyPressed() { if (keyCode === 27) stopMic(); }
window.addEventListener('keydown', event => { if (event.key === 'Escape') stopMic(); }, true);
window.addEventListener('message', event => { if (event.source === window.parent && event.data === 'slide:stop') stopMic(); });
document.addEventListener('visibilitychange', () => { if (document.hidden) stopMic(); });
window.addEventListener('pagehide', stopMic);
window.week06VoiceSurface = {startMic, stopMic, startDemo, getState:getVoiceState};
