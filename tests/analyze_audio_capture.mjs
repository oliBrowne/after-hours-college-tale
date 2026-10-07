import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const folder=process.argv[2]||path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../outputs/audio-qa');
const filename=path.join(folder,'chip-native-master-mix.wav'),reportPath=path.join(folder,'chip-native-master-mix.json');
const wave=fs.readFileSync(filename),report=JSON.parse(fs.readFileSync(reportPath,'utf8'));
let offset=12,data,rate=0,channels=0,bits=0;
while(offset+8<=wave.length){
 const id=wave.toString('ascii',offset,offset+4),length=wave.readUInt32LE(offset+4);
 if(id==='fmt '){channels=wave.readUInt16LE(offset+10);rate=wave.readUInt32LE(offset+12);bits=wave.readUInt16LE(offset+22);}
 if(id==='data')data=wave.subarray(offset+8,offset+8+length);
 offset+=8+length+(length%2);
}
if(!data||bits!==16||rate<=0||channels<=0)throw Error('Unsupported or empty native recording');
function measure(from=0,to=data.length/(rate*channels*2)){
 const start=Math.max(0,Math.floor(from*rate*channels))*2,end=Math.min(data.length,Math.floor(to*rate*channels)*2);
 let peak=0,sum=0,nonzero=0,count=0;
 for(let i=start;i<end;i+=2){const n=data.readInt16LE(i)/32768;peak=Math.max(peak,Math.abs(n));sum+=n*n;if(n!==0)nonzero++;count++;}
 return {peak,rms:Math.sqrt(sum/Math.max(1,count)),nonzeroSamples:nonzero};
}
const drift=[];
for(let i=0;i<report.phasesSeen.length;i++){
 const start=report.phasesSeen[i];if(start.mode!==7)continue;
 const end=report.phasesSeen.slice(i+1).find(x=>x.mode===4||x.mode===8);if(!end)continue;
 const expectedBeats=(480+start.stage*60)/30,actualBeats=end.beat-start.beat;
 drift.push({stage:start.stage,dodgeStartBeat:start.beat,nearestBar:Math.round(start.beat/4)*4,onsetLatenessSeconds:(start.beat-Math.round(start.beat/4)*4)/2,expectedPhaseBeats:expectedBeats,observedPhaseBeats:actualBeats,endpointDriftSeconds:(actualBeats-expectedBeats)/2,mixWindowSeconds:[start.seconds,end.seconds],mix:measure(start.seconds,end.seconds)});
}
const stats={sampleRate:rate,channels,bits,duration:data.length/(rate*channels*2),...measure(),sha256:crypto.createHash('sha256').update(wave).digest('hex')};stats.clipped=stats.peak>=.999;
if(stats.clipped||stats.nonzeroSamples<1000||report.outcome!=='peaceful'||drift.length!==3)throw Error('Incomplete or clipped actual encounter capture');
report.audioSyncEvidence=drift;report.maxEndpointDriftSeconds=Math.max(...drift.map(x=>Math.abs(x.endpointDriftSeconds)));
fs.writeFileSync(reportPath,JSON.stringify(report,null,2)+'\n');
fs.writeFileSync(path.join(folder,'chip-native-master-mix-stats.json'),JSON.stringify(stats,null,2)+'\n');
console.log(JSON.stringify({stats,phases:drift},null,2));
