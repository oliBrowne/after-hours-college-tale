import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
const dir = process.argv[2];
if (!dir) throw new Error('Pass native capture directory');
function read(name) {
  const bytes = fs.readFileSync(path.join(dir, name + '.wav'));
  let rate, channels, data;
  for (let at = 12; at + 8 < bytes.length;) {
    const kind = bytes.toString('ascii', at, at + 4), size = bytes.readUInt32LE(at + 4);
    if (kind === 'fmt ') { channels = bytes.readUInt16LE(at + 10); rate = bytes.readUInt32LE(at + 12); if (bytes.readUInt16LE(at + 22) !== 16) throw new Error('Expected PCM16'); }
    if (kind === 'data') data = bytes.subarray(at + 8, at + 8 + size);
    at += 8 + size + (size & 1);
  }
  const mono = Float64Array.from({ length: data.length / channels / 2 }, (_, i) => data.readInt16LE(i * channels * 2) / 32768);
  function stats(start = 0, end = mono.length / rate) {
    let peak = 0, sum = 0, count = 0, clips = 0;
    for (let i = Math.floor(start * rate); i < Math.min(mono.length, end * rate); i++) { peak = Math.max(peak, Math.abs(mono[i])); sum += mono[i] ** 2; count++; if (Math.abs(mono[i]) >= .9999) clips++; }
    return { peak, rms: Math.sqrt(sum / count), clips };
  }
  return { rate, mono, stats, summary: { seconds: mono.length / rate, rate, channels, ...stats(), sha256: crypto.createHash('sha256').update(bytes).digest('hex') } };
}
const hold = read('result-hold-10s-native-api'), immediate = read('result-immediate-continue-native-api'), pitch = read('native-pitch-compensation-proof');
function frequency(start) {
  const samples = pitch.mono.subarray(Math.floor(start * pitch.rate), Math.floor((start + .25) * pitch.rate));
  let best = { hz: 0, power: 0 };
  for (let hz = 220; hz <= 470; hz += .5) {
    let re = 0, im = 0;
    for (let i = 0; i < samples.length; i++) { const phase = 2 * Math.PI * hz * i / pitch.rate; re += samples[i] * Math.cos(phase); im += samples[i] * Math.sin(phase); }
    const power = re * re + im * im;
    if (power > best.power) best = { hz, power };
  }
  return best.hz;
}
const frequencies = { normal: frequency(.7), rawSlow: frequency(2.7), compensatedSlow: frequency(4.7) };
if (Math.abs(frequencies.normal - 440) > 1 || Math.abs(frequencies.rawSlow - 246.4) > 2 || Math.abs(frequencies.compensatedSlow - 440) > 6) throw new Error('Pitch compensation failed: ' + JSON.stringify(frequencies));
const report = { source: 'Native WASAPI AudioServer Master API fixtures, not actual Main playthrough or human listening approval', performedSpeech: false, hold: { ...hold.summary, fighting: hold.stats(.2,.8), quietResult: hold.stats(5,9), world: hold.stats(11.5,12) }, immediate: immediate.summary, pitch: { ...pitch.summary, dominantHz: frequencies }, limits: '512 sample FFT trades low latency for reduced stability; complex music quality and seams need listening. Root records actual normal-speed conversation separately.' };
if (fs.existsSync(path.join(dir, 'dialogue-normal-effects-muted.wav'))) {
  report.dialogue = {};
  for (const name of ['dialogue-normal-effects-muted', 'dialogue-normal-full-mix']) {
    const audio = read(name);
    if (audio.summary.rms < .0001 || audio.summary.clips > 0) throw new Error('Silent/clipped dialogue capture: ' + name);
    report.dialogue[name] = audio.summary;
  }
  report.dialogue.source = 'Production Main dialogue/reveal/punctuation through viewport action events; explicit authored QA lines. Voices-only recording mutes music/effects/ambience, so its nonzero signal establishes independent voice output.';
  report.limits = '512 sample FFT trades low latency for reduced stability; complex music quality and seams need listening. Actual Main dialogue is an authored fixture, not discovery or a complete route. Performed speech remains missing.';
}
fs.writeFileSync(path.join(dir, 'resolution-native-api-analysis.json'), JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
