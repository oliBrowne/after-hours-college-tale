// Native-only deterministic additive/material/formant synthesis. No recordings,
// external samples, speech models, reference-game tunes, or runtime generation.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const source=path.dirname(fileURLToPath(import.meta.url));
const runtime=path.resolve(source,'../../assets/audio');
const workspace=path.resolve(source,'../../..');
const SR=48000, TAU=Math.PI*2, ledger=[];
fs.mkdirSync(runtime,{recursive:true});fs.mkdirSync(path.join(source,'masters'),{recursive:true});
const midi=n=>440*2**((n-69)/12);
let seed=91929;
function rand(){seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/2147483648-1;}
function voice(kind,hz,t){
 const p=TAU*hz*t;
 if(kind==='felt')return .7*Math.sin(p)+.16*Math.sin(p*2.002)*Math.exp(-t*4)+.07*Math.sin(p*3.003);
 if(kind==='glass')return .65*Math.sin(p)+.22*Math.sin(p*2)+.09*Math.sin(p*5);
 if(kind==='lead')return .64*Math.sin(p)+.2*Math.sin(p*3)+.09*Math.sin(p*5)+.04*Math.sin(p*7);
 if(kind==='bass')return Math.tanh((Math.sin(p)+.22*Math.sin(p*2)+.12*Math.sin(p*3))*1.4)*.8;
 if(kind==='organ')return .5*Math.sin(p)+.17*Math.sin(p*2)+.16*Math.sin(p*3)+.07*Math.sin(p*4);
 if(kind==='metal')return .5*Math.sin(p)+.24*Math.sin(p*2.73)+.17*Math.sin(p*5.41);
 if(kind==='kick')return Math.sin(TAU*(42*t+4.2*(1-Math.exp(-t*30))));
 return Math.sin(p);
}
function tone(buf,at,dur,hz,gain,kind='felt',decay=3,slide=0,loop=false){
 const start=Math.round(at*SR),count=Math.round(dur*SR),attack=kind==='organ'?.025:.003;
 for(let i=0;i<count;i++){
  const t=i/SR,fade=Math.min(1,t/attack)*Math.max(0,Math.min(1,(dur-t)/.05));
  const index=loop?(start+i)%buf.length:start+i;
  if(index>=buf.length)break;
  // Integrated linear frequency slide, not a clicky discontinuous frequency swap.
  const effectiveHz=hz+slide*t/2;
  buf[index]+=voice(kind,effectiveHz,t)*fade*Math.exp(-t*decay)*gain;
 }
}
function noise(buf,at,dur,gain,cutoff=1500,decay=16,loop=false){
 const start=Math.round(at*SR),count=Math.round(dur*SR),alpha=Math.min(.95,TAU*cutoff/SR);let low=0;
 for(let i=0;i<count;i++){
  const t=i/SR;low+=alpha*(rand()-low);
  const env=Math.min(1,t/.004)*Math.max(0,Math.min(1,(dur-t)/.035))*Math.exp(-t*decay);
  const index=loop?(start+i)%buf.length:start+i;if(index>=buf.length)break;
  buf[index]+=low*gain*env;
 }
}
function room(buf,delay=.035,amount=.2){
 const count=Math.round(delay*SR);for(let i=buf.length-1;i>=count;i--)buf[i]+=buf[i-count]*amount;
}
function wave(id,buf,type,extra={}){
 let peak=0,sum=0;for(const x of buf){peak=Math.max(peak,Math.abs(x));sum+=x*x;}
 const limit=type==='music'?.4:.6,scale=peak>limit?limit/peak:1;
 const file=Buffer.alloc(44+buf.length*2);file.write('RIFF');file.writeUInt32LE(file.length-8,4);file.write('WAVE',8);file.write('fmt ',12);file.writeUInt32LE(16,16);file.writeUInt16LE(1,20);file.writeUInt16LE(1,22);file.writeUInt32LE(SR,24);file.writeUInt32LE(SR*2,28);file.writeUInt16LE(2,32);file.writeUInt16LE(16,34);file.write('data',36);file.writeUInt32LE(buf.length*2,40);
 for(let i=0;i<buf.length;i++)file.writeInt16LE(Math.round(buf[i]*scale*32767),44+i*2);
 const destination=type==='music'?path.join(source,'masters',id+'.wav'):path.join(runtime,id+'.wav');fs.writeFileSync(destination,file);
 const record={id,type,path:type==='music'?`masters/${id}.wav`:`res://assets/audio/${id}.wav`,sampleRate:SR,channels:1,frames:buf.length,duration:buf.length/SR,peak:peak*scale,rms:Math.sqrt(sum/buf.length)*scale,seamDelta:Math.abs(buf[0]-buf.at(-1))*scale,sha256:crypto.createHash('sha256').update(file).digest('hex'),source:'export-native-audio.mjs; original additive/material/formant synthesis; no external samples',status:'numerical checks passed; integrated listening pending',...extra};
 ledger.push(record);if(record.peak>=1||type==='music'&&record.seamDelta>.01)throw Error('Clip/seam '+id);
 return buf;
}
const rendered={};
function effect(id,duration,compose){const b=new Float32Array(Math.round(duration*SR));compose(b);rendered[id]=wave(id,b,'effect');}
effect('swing-whoosh',.34,b=>{noise(b,0,.25,.55,2200,6);tone(b,.07,.21,260,.18,'lead',12,-850);noise(b,.13,.09,.25,9000,25);});
effect('body-hit',.38,b=>{noise(b,0,.08,.7,1600,24);tone(b,0,.22,72,.37,'kick',16);tone(b,.018,.22,130,.15,'bass',20,-150);room(b,.028,.22);});
effect('guard-metal',.62,b=>{noise(b,0,.035,.45,11000,22);tone(b,0,.53,920,.25,'metal',9);tone(b,.005,.5,1410,.14,'metal',7);room(b,.038,.25);});
effect('shield-pop',.4,b=>{tone(b,0,.2,480,.25,'glass',13,-1900);noise(b,.05,.22,.32,5000,12);tone(b,.01,.15,90,.18,'kick',18);});
effect('foot-wood',.23,b=>{tone(b,0,.12,165,.18,'bass',28);tone(b,.008,.12,420,.14,'metal',30);noise(b,0,.11,.36,1700,30);room(b,.021,.15);});
effect('door-hinge',.76,b=>{tone(b,0,.62,310,.15,'metal',2,190);noise(b,.05,.54,.11,2300,2);tone(b,.23,.34,550,.08,'metal',5,-280);});
effect('door-latch',.3,b=>{noise(b,0,.035,.3,8500,40);tone(b,0,.12,1240,.14,'metal',24);noise(b,.055,.07,.45,1100,30);tone(b,.055,.12,96,.19,'bass',28);});
effect('ring-warning',.8,b=>{for(const at of [0,.27,.54]){tone(b,at,.2,1050,.21,'metal',13);tone(b,at,.2,1580,.11,'glass',14);} });
effect('confetti',.62,b=>{for(let i=0;i<9;i++){noise(b,i*.045,.08,.15,2400+i*450,24);tone(b,i*.045,.12,720+i*170,.07,'glass',20);}});
effect('football-whistle',.67,b=>{tone(b,0,.22,2100,.19,'glass',2,180);tone(b,.25,.32,2250,.2,'glass',2,-150);noise(b,0,.6,.025,7500,1);});
effect('audit-stamp',.4,b=>{tone(b,0,.14,60,.25,'kick',23);noise(b,0,.06,.56,1450,26);tone(b,.065,.14,195,.17,'bass',25);noise(b,.17,.1,.14,3800,24);});
effect('release-warm',1.2,b=>{for(const [i,n]of[62,65,69,74].entries()){tone(b,i*.12,.7,midi(n),.11,'felt',3);tone(b,.3+i*.12,.65,midi(n+12),.045,'glass',3);}room(b,.081,.22);});
effect('enemy-hurt',.42,b=>{tone(b,0,.27,225,.24,'organ',12,-450);noise(b,0,.1,.22,3100,19);tone(b,.025,.2,410,.1,'metal',18,-700);});
effect('enemy-defeat',1.1,b=>{for(const [i,n]of[62,57,53,50].entries())tone(b,i*.14,.43,midi(n),.15,'organ',6,-25);noise(b,.07,.78,.24,1600,5);room(b,.047,.22);});
effect('ui-pick',.22,b=>{tone(b,0,.09,740,.13,'felt',14);tone(b,.04,.14,1100,.1,'glass',15);noise(b,0,.018,.1,5300,35);});
effect('timing-perfect',.6,b=>{tone(b,0,.13,880,.16,'metal',14);for(const[i,n]of[74,81,86].entries())tone(b,.065+i*.075,.31,midi(n),.09,'glass',7);room(b,.032,.15);});
effect('bird-chirp',.65,b=>{for(const[i,at]of[0,.15,.32].entries())tone(b,at,.14,2600+i*180,.11,'glass',12,6000-i*1700);});
effect('squirrel-chirp',.42,b=>{for(const at of [0,.07,.15])tone(b,at,.08,1450,.085,'lead',18,2300);noise(b,.2,.1,.12,3100,26);});
effect('leaf-rustle',.7,b=>{noise(b,0,.42,.2,3400,3);noise(b,.2,.4,.14,4800,4);noise(b,.43,.2,.07,6300,8);});
effect('foot-stone-rich',.24,b=>{noise(b,0,.09,.31,5300,35);tone(b,0,.1,205,.12,'metal',30);tone(b,.012,.14,80,.13,'bass',25);});
effect('foot-carpet-rich',.21,b=>{noise(b,0,.14,.14,800,23);tone(b,0,.11,67,.1,'bass',25);});
effect('foot-grass',.25,b=>{noise(b,0,.16,.23,2300,20);noise(b,.03,.15,.08,7200,24);tone(b,0,.1,62,.065,'bass',25);});
effect('boss-release',2.4,b=>{for(const[i,n]of[62,69,65,64,67,74].entries()){tone(b,i*.18,.9,midi(n),.12,'felt',2);tone(b,.07+i*.18,.85,midi(n+12),.045,'glass',2.5);}tone(b,.95,1.1,midi(50),.12,'bass',2);room(b,.094,.25);});
effect('boss-force',2.1,b=>{for(const[i,n]of[50,53,49,50].entries()){tone(b,i*.23,.5,midi(n),.16,'bass',4);noise(b,i*.23,.15,.15,1400,16);tone(b,i*.23,.3,36,.13,'kick',15);}tone(b,.94,.95,midi(62),.09,'organ',4);tone(b,.94,.95,midi(69),.045,'metal',5);room(b,.07,.2);});

// Glottal harmonic source shaped through three moving formant bands. These are
// expressive nonverbal vowel/hum textures, never synthesised words or actors.
const characters={
 jules:{hz:155,formants:[550,1250,2500],breath:.055,rasp:.015},
 imani:{hz:205,formants:[720,1550,2900],breath:.1,rasp:.007},
 cal:{hz:108,formants:[430,1040,2350],breath:.028,rasp:.015},
 mags:{hz:167,formants:[630,1380,2400],breath:.035,rasp:.09},
 todd:{hz:188,formants:[400,1950,2950],breath:.022,rasp:.03},
 deion:{hz:122,formants:[750,1100,2600],breath:.035,rasp:.02},
 chip:{hz:248,formants:[370,1850,3200],breath:.018,rasp:.012}
};
for(const [speaker,c]of Object.entries(characters))for(const mood of ['neutral','warm','concern'])for(let variant=1;variant<=3;variant++){
 const duration=.105+(variant-1)*.008,b=new Float32Array(Math.round(duration*SR));
 let phase=0,filtered=0;const moodPitch=mood==='warm'?1.09:mood==='concern'?.94:1;
 for(let i=0;i<b.length;i++){
  const t=i/SR,u=t/duration,curve=mood==='warm'?1+.12*u:mood==='concern'?1-.16*u:1+.045*Math.sin(u*Math.PI);
  const hz=c.hz*moodPitch*(1+(variant-2)*.035)*curve*(1+.007*Math.sin(t*TAU*6));phase+=TAU*hz/SR;
  let sample=0;
  for(let h=1;h<=32;h++){
   const frequency=hz*h;let shape=.085/h;
   for(const [j,f]of c.formants.entries()){
    const center=f*(1+.075*Math.sin(u*Math.PI+(variant-1)*.4)),width=[130,200,310][j];
    shape+=Math.exp(-.5*((frequency-center)/width)**2)*[.5,.25,.14][j]/Math.sqrt(h);
   }
   sample+=Math.sin(phase*h)*shape;
  }
  filtered+=.28*(rand()-filtered);
  const envelope=Math.min(1,t/.012)*Math.min(1,(duration-t)/.025)*Math.sin(Math.PI*u)**.45;
  b[i]=(sample*.32+filtered*c.breath+Math.sin(phase*.5)*c.rasp)*envelope;
 }
 rendered[`vocal-${speaker}-${mood}-${variant}`]=wave(`vocal-${speaker}-${mood}-${variant}`,b,'nonverbal-voice',{speaker,mood,variant,performedSpeech:false,description:'Original glottal/formant vowel-hum phonation with breath and expressive pitch curve; no intelligible words'});
}

const nextYear=[57,60,64,62,60,64,67,62],lastBus=[62,62,69,67,65,64,62,57];
for(const boss of [false,true]){
 const id=boss?'boss-dark':'battle-rich',bars=boss?48:32,beat=.5,buf=new Float32Array(SR*bars*4*beat);
 const rootCycle=boss?[38,41,46,45,38,43,46,45]:[50,58,55,57];
 for(let bar=0;bar<bars;bar++){
  const at=bar*4*beat,section=Math.floor(bar/8),phase=Math.floor(bar/16),root=rootCycle[Math.floor(bar/2)%rootCycle.length],bridge=boss?false:section===2;
  const motif=boss?nextYear:lastBus;
  for(const [j,n]of[root+12,root+19,root+(boss?24:26)].entries())tone(buf,at+j*.02,bridge?1.8:.8,midi(n),boss?[.035,.055,.075][phase]:.05,boss?(phase===0?'felt':'organ'):'felt',bridge?1.4:3,0,true);
  for(let b=0;b<4;b+=.5){
   if(!bridge||b%1===0)tone(buf,at+b*beat,.16,midi(root+(b%1?7:0)-(boss?0:12)),boss?[.09,.12,.15][phase]:.1,'bass',11,0,true);
   noise(buf,at+(b+.25)*beat,.04,boss?[.017,.03,.047][phase]:.023,8500,38,true);
  }
  for(const b of bridge?[0,2]:boss&&phase===2?[0,.75,1.5,2,2.75,3.25]:[0,1.5,2,3.25])tone(buf,at+b*beat,.17,36,boss?[.075,.105,.13][phase]:.09,'kick',20,0,true);
  for(const b of [1,3]){noise(buf,at+b*beat,.12,boss?[.085,.125,.175][phase]:.105,3000,25,true);tone(buf,at+b*beat,.09,190,.03,'metal',24,0,true);}
  const rhythm=bridge?[.5,2.5]:boss?[0,.75,1.5,2.75,3.5]:[0,.5,1.25,2.5];
  for(const[k,b]of rhythm.entries())tone(buf,at+b*beat,bridge?.5:.21,midi(motif[(bar*2+k)%8]+(bridge?12:section%3===2?12:0)),boss?[.055,.085,.115][phase]:.095,bridge?'felt':'lead',bridge?2.8:3.5,0,true);
  if(bar%2===1)tone(buf,at+2.5*beat,.55,midi(motif[(bar*2+4)%8]+12),.055,'glass',4,0,true);
  // Every four-bar ending contains authored descending tom/snare fills.
  if(bar%4===3)for(let k=0;k<4;k++){
   tone(buf,at+(3+k*.25)*beat,.11,180-k*26,boss?[.045,.065,.085][phase]:.07,'bass',22,0,true);
   noise(buf,at+(3+k*.25)*beat,.055,boss?[.035,.06,.085][phase]:.06,2400,32,true);
  }
  if(boss&&section>=4)for(let k=0;k<4;k++)tone(buf,at+(k+.25)*beat,.16,midi(root+24+[0,7,3,10][k]),.04,'glass',7,0,true);
  if(boss&&phase===1)for(const b of [.5,2.5])tone(buf,at+b*beat,.35,midi(root+31),.035,'organ',4,0,true);
  if(boss&&phase===2)for(const b of [0,2])tone(buf,at+b*beat,.3,midi(root+36),.035,'glass',5,0,true);
 }
 const phaseRMS=boss?[0,1,2].map(phase=>{let sum=0;for(let i=phase*SR*32;i<(phase+1)*SR*32;i++)sum+=buf[i]*buf[i];return Math.sqrt(sum/(SR*32));}):null;
 wave(id,buf,'music',{bpm:120,beatsPerBar:4,bars,loopStartFrame:0,loopEndFrame:buf.length,phaseRMS,sections:boss?[{phase:0,startSeconds:0,endSeconds:32,orchestration:'restrained felt/chip, low dry bass, sparse hats'},{phase:1,startSeconds:32,endSeconds:64,orchestration:'new upper organ response, stronger bass/snare, eighth-note hats'},{phase:2,startSeconds:64,endSeconds:96,orchestration:'new glass counterline/octave accents, extra kick subdivisions, heavier tom fills'}]:null,description:boss?'Original dark Next Year score with three escalating 32-second authored orchestration sections; dry layered drum fills':'Original Last Bus motif, plucked bass pulse, piano/glass response, layered drums and quiet bridge'});
}
// Quiet environmental beds have no melody or intelligible recorded speech.
for(const id of ['campus-air','quiet-birds','umc-room','hall-clock']){
 const duration=24,b=new Float32Array(duration*SR);
 if(id==='campus-air'||id==='quiet-birds'){
  noise(b,0,duration,id==='campus-air'?.09:.032,270,.0);
  noise(b,0,duration,id==='campus-air'?.016:.01,3400,.0);
  if(id==='quiet-birds')for(const at of [2.1,7.4,15.3,19.8])for(const [k,offset]of[0,.17,.34].entries())tone(b,at+offset,.13,2400+k*310,.033,'glass',13,5000, true);
  if(id==='campus-air')for(const at of [4.2,12.3,18.5])noise(b,at,1.5,.032,1300,1.3,true);
 }
 if(id==='umc-room'){
  noise(b,0,duration,.027,900,0);
  for(let t=.7;t<duration;t+=1.43){
   tone(b,t,.34,105+(t*17)%130,.015,'organ',5,85,true);
   tone(b,t+.17,.23,150+(t*11)%130,.012,'organ',6,-50,true);
   noise(b,t,.39,.026,1600,4,true);
  }
  for(const at of [5.8,16.7]){noise(b,at,.05,.02,5000,24,true);tone(b,at,.17,610,.014,'metal',18,0,true);}
 }
 if(id==='hall-clock'){
  noise(b,0,duration,.013,480,0);
  for(let second=0;second<duration;second++){
   tone(b,second,.06,second%2?1200:1500,.031,'metal',30,0,true);
   noise(b,second,.04,.027,2900,30,true);
  }
 }
 wave(id,b,'music',{type:'ambience',bpm:null,loopStartFrame:0,loopEndFrame:b.length,description:'Original synthesized room tone; no melody or intelligible words; 24-second local ambience loop'});
}
fs.writeFileSync(path.join(source,'native-audio-ledger.json'),JSON.stringify({version:1,assets:ledger},null,2)+'\n');
// Short user-facing review reel of effects and three neutral voice examples.
const previewIDs=['swing-whoosh','body-hit','guard-metal','shield-pop','ring-warning','audit-stamp','release-warm','enemy-defeat','timing-perfect','vocal-jules-neutral-1','vocal-imani-warm-1','vocal-cal-neutral-1','vocal-mags-concern-1','vocal-todd-neutral-1','vocal-deion-neutral-1','vocal-chip-warm-1','bird-chirp','squirrel-chirp','leaf-rustle'];
const length=previewIDs.reduce((sum,id)=>sum+rendered[id].length+Math.round(.3*SR),0),preview=new Float32Array(length);let offset=0;
for(const id of previewIDs){preview.set(rendered[id],offset);offset+=rendered[id].length+Math.round(.3*SR);}
const previewDir=path.join(workspace,'outputs');fs.mkdirSync(previewDir,{recursive:true});
// Export preview outside runtime so it is never bundled or used as an effect.
const previewFile=Buffer.alloc(44+preview.length*2);previewFile.write('RIFF');previewFile.writeUInt32LE(previewFile.length-8,4);previewFile.write('WAVE',8);previewFile.write('fmt ',12);previewFile.writeUInt32LE(16,16);previewFile.writeUInt16LE(1,20);previewFile.writeUInt16LE(1,22);previewFile.writeUInt32LE(SR,24);previewFile.writeUInt32LE(SR*2,28);previewFile.writeUInt16LE(2,32);previewFile.writeUInt16LE(16,34);previewFile.write('data',36);previewFile.writeUInt32LE(preview.length*2,40);for(let i=0;i<preview.length;i++)previewFile.writeInt16LE(Math.round(Math.max(-.95,Math.min(.95,preview[i]))*32767),44+i*2);fs.writeFileSync(path.join(previewDir,'sound-design-preview.wav'),previewFile);
console.log(`Exported ${ledger.length} assets: 24 layered FX/stingers, 63 nonverbal voiced fragments, 2 music and 4 ambience masters; all peak/seam checks passed.`);
