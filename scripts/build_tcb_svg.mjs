import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const art = {};
const source = fs.readFileSync(path.join(root, 'plugin/nextg.elvis-unlock/TcbArt.js'), 'utf8');
vm.runInNewContext(source.replace(/^\.pragma library\s*/, ''), art);
const stops = [[0,'#775522'],[.16,'#e8cc87'],[.29,'#fff0be'],[.38,'#a67b36'],[.59,'#e5c17a'],[.74,'#75521f'],[1,'#d8b56e']];
const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 750">
<title>TCB — Taking Care of Business</title>
<desc>Gold C above T and B, with a long faceted lightning bolt, following the supplied pendant reference.</desc>
<defs><linearGradient id="gold" gradientUnits="userSpaceOnUse" x1="90" y1="15" x2="350" y2="580">${stops.map(([p,c])=>`<stop offset="${p}" stop-color="${c}"/>`).join('')}</linearGradient></defs>
${[art.bolt,...art.letters].map(d=>`<path d="${d}" fill="url(#gold)" fill-rule="evenodd" stroke="#e7c37b" stroke-width=".7"/>`).join('\n')}
${art.bevels.map(p=>`<path d="${p.d}" fill="${p.light?'#fff1bd':'#3c2914'}" opacity="${p.light?.55:.4}"/>`).join('\n')}
${art.highlights.map(d=>`<path d="${d}" fill="none" stroke="#fff3c7" stroke-width="1.3" opacity=".65"/>`).join('\n')}
</svg>\n`;
fs.writeFileSync(path.join(root,'assets/tcb-mark.svg'),svg);
console.log(path.join(root,'assets/tcb-mark.svg'));
