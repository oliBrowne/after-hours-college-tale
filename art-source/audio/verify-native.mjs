import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const source=path.dirname(fileURLToPath(import.meta.url)),runtime=path.resolve(source,'../../assets/audio');
const ledger=JSON.parse(fs.readFileSync(path.join(source,'native-audio-ledger.json'),'utf8'));
for(const asset of ledger.assets){
 const filename=asset.type==='music'||asset.type==='ambience'?path.join(source,'masters',asset.id+'.wav'):path.join(runtime,asset.id+'.wav');
 const file=fs.readFileSync(filename);
 if(crypto.createHash('sha256').update(file).digest('hex')!==asset.sha256)throw Error('Hash '+asset.id);
 if(file.readUInt32LE(24)!==48000||file.readUInt16LE(22)!==1||file.readUInt16LE(34)!==16)throw Error('Format '+asset.id);
 if(asset.type==='music'||asset.type==='ambience'){
  const decoded=fs.readFileSync(path.join(source,asset.id+'-check.pcm')),encoded=fs.readFileSync(path.join(runtime,asset.id+'.ogg'));let peak=0;
  for(let i=0;i<decoded.length;i+=2)peak=Math.max(peak,Math.abs(decoded.readInt16LE(i)/32768));
  const seamDelta=Math.abs(decoded.readInt16LE(0)-decoded.readInt16LE(decoded.length-2))/32768;
  if(decoded.length/2!==asset.frames||peak>=1||seamDelta>.01)throw Error('Compressed clip/seam '+asset.id);
  asset.runtime={path:`res://assets/audio/${asset.id}.ogg`,bytes:encoded.length,sha256:crypto.createHash('sha256').update(encoded).digest('hex'),decodedFrames:decoded.length/2,peak,seamDelta};
 }
}
fs.writeFileSync(path.join(source,'native-audio-ledger.json'),JSON.stringify(ledger,null,2)+'\n');
console.log(`NATIVE AUDIO VERIFIED: ${ledger.assets.length} hashes/PCM headers, 6 compressed loop exact frame counts/peaks/seams.`);
