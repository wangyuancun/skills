"""Photo mockups for the Studio.

Eight photographs of blank surfaces (generated for FontWorks, shipped in
mockups/). The design for each surface is set live in the font as SVG,
warped onto the surface with a projective mesh and multiplied into the photo,
so the paper's folds, the fabric weave and the shadows fall across the type
the way they would on a real print. Each scene exports as a PNG.
"""
import base64
import json
import os

HERE = os.path.join(os.path.dirname(__file__), "..", "mockups")

# surface corners in the 1280 x 853 photos: TL, TR, BR, BL
SCENES = [
    ("poster", "Street poster", [[[388, 87], [875, 87], [877, 767], [388, 767]]], "paper"),
    ("cards", "Business cards", [[[191, 297], [612, 297], [611, 543], [185, 543]],
                                 [[671, 295], [1092, 296], [1095, 543], [670, 543]]], "paper"),
    ("store", "Storefront", [[[163, 67], [1133, 65], [1133, 212], [157, 212]]], "paper"),
    ("bag", "Coffee bag", [[[400, 208], [871, 208], [863, 683], [410, 683]]], "paper"),
    ("billboard", "Billboard", [[[156, 181], [1130, 178], [1136, 531], [147, 531]]], "flat"),
    ("tote", "Tote bag", [[[456, 400], [844, 400], [844, 756], [456, 756]]], "ink"),
    ("book", "Book cover", [[[389, 83], [869, 83], [869, 709], [389, 709]]], "paper"),
    ("phone", "App", [[[507, 80], [797, 80], [797, 705], [507, 705]]], "screen"),
]


def data():
    out = []
    for key, name, quads, mode in SCENES:
        with open(os.path.join(HERE, key + ".jpg"), "rb") as f:
            src = base64.b64encode(f.read()).decode()
        out.append(dict(k=key, n=name, q=quads, m=mode, src=src))
    return json.dumps(out, separators=(",", ":"))


SECTION = r"""<section id="mockups"><div class="sh"><div><div class="kicker">In use</div><h2>See it in the real world.</h2><p class="lede">Eight photographs, set live in this font. The type is mapped onto each surface in perspective and printed into the photo, so folds, weave and shadows fall across it. Change the name, line and colours, then download any scene.</p></div></div>
<div class="mkbar"><label>Name <input id="mkn" maxlength="28"></label><label>Line <input id="mkt" maxlength="60"></label><label>Weight <select id="mkw"></select></label><span class="mkpal" id="mkpal"></span></div>
<div class="mkgrid" id="mkgrid"></div></section>"""

CSS = r"""
.mkbar{display:flex;flex-wrap:wrap;gap:10px 18px;align-items:center;padding:12px 14px;background:var(--card);border:1px solid var(--line);border-radius:18px;font-size:13px;color:var(--mute);margin-bottom:16px}
.mkbar label{display:flex;align-items:center;gap:8px}.mkbar input,.mkbar select{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:6px 10px;color:var(--fg)}
.mkbar input{width:200px}.mkpal{display:flex;gap:8px;margin-left:auto}.mkpal button{width:30px;height:30px;border-radius:50%;border:2px solid var(--line);cursor:pointer;padding:0;overflow:hidden;display:flex}
.mkpal button i{flex:1}.mkpal button.on{outline:2px solid var(--acc);outline-offset:2px}
.mkgrid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}.mk{position:relative;border-radius:var(--r);overflow:hidden;background:#222;aspect-ratio:1280/853}
.mk:first-child{grid-column:span 2}.mk canvas{display:block;width:100%;height:100%}
.mk .mkf{position:absolute;left:12px;right:12px;bottom:12px;display:flex;justify-content:space-between;align-items:center;opacity:0;transition:opacity .15s}
.mk:hover .mkf,.mk:focus-within .mkf{opacity:1}.mk .mkf span{background:rgba(0,0,0,.55);color:#fff;border-radius:999px;padding:5px 11px;font-size:12px;backdrop-filter:blur(6px)}
@media(max-width:860px){.mkgrid{grid-template-columns:1fr}.mk:first-child{grid-column:auto}.mk .mkf{opacity:1}}
"""

JS = r"""
// ---------------------------------------------------------------- photo mockups
{
const MK=__MOCKS__;
const PAL=[['Ink','#191815','#f5f0e6','#c4573b'],['Forest','#1f2a17','#f2ecdc','#b9c45c'],['Ocean','#0e2536','#eef3f2','#ff8a5c'],
 ['Rose','#3d1020','#fbeae5','#e0475e'],['Sun','#1d1a10','#fff3cc','#ff5b23'],['Mono','#111111','#ffffff','#111111']];
const mk={n:D.family,t:'Made with care, set in '+D.family+'.',w:topW,p:0};
const nI=$('#mkn'),tI=$('#mkt'),wS=$('#mkw');nI.value=mk.n;tI.value=mk.t;
D.weights.forEach(([w,n])=>{const o=el('option','',n);o.value=w;if(w===mk.w)o.selected=true;wS.append(o)});
PAL.forEach((p,i)=>{const b=el('button',i?'':'on','<i style="background:'+p[1]+'"></i><i style="background:'+p[2]+'"></i><i style="background:'+p[3]+'"></i>');b.title=p[0];
 b.onclick=()=>{mk.p=i;$$('#mkpal button').forEach(x=>x.classList.toggle('on',x===b));draw()};$('#mkpal').append(b)});
let FACE='';for(const sh of document.styleSheets){try{for(const r of sh.cssRules){if(r.type===5&&/PCX/.test(r.cssText))FACE+=r.cssText}}catch(e){}}
const mc=document.createElement('canvas').getContext('2d');
// font size that fits txt in max px at weight w, capped at cap
function fs(txt,max,cap,w){mc.font=(w||mk.w)+' 100px PCX';const wd=mc.measureText(txt).width||1;return Math.min(cap,100*max/wd)}
const E=s=>esc(s);
const T=(x,y,s,txt,fill,o={})=>`<text x="${x}" y="${y}" font-size="${s.toFixed(1)}" fill="${fill}" font-weight="${o.w||mk.w}"${o.a?' text-anchor="'+o.a+'"':''}${o.ls?' letter-spacing="'+o.ls+'"':''}${o.op?' opacity="'+o.op+'"':''}>${E(txt)}</text>`;
function two(s){const w=s.split(/\s+/);if(w.length<2)return[s,''];const h=Math.ceil(w.length/2);return[w.slice(0,h).join(' '),w.slice(h).join(' ')]}
const L=()=>W[0],yr=new Date().getFullYear();
// one design per surface: (w,h,P,n,t,i) -> svg body; P = [name, ink, paper, accent]
const DES={
 poster:(w,h,P,n,t)=>{const [a,b]=two(n),m=w*.08,s1=fs(a,w-2*m,h*.24),s2=b?fs(b,w-2*m,h*.24):0,s=Math.min(s1,s2||s1);
  return`<rect width="${w}" height="${h}" fill="${P[1]}"/>${T(m,m+h*.03,h*.026,'No. 01 — '+yr,P[2],{w:L(),ls:1})}${T(w-m,m+h*.03,h*.026,'Spring edition',P[2],{w:L(),a:'end'})}
  ${T(m,h*.52,s,a,P[2])}${b?T(m,h*.52+s*.95,s,b,P[3]):''}<rect x="${m}" y="${h*.8}" width="${w-2*m}" height="${h*.004}" fill="${P[2]}"/>
  ${T(m,h*.85,fs(t,w-2*m,h*.032,L()),t,P[2],{w:L()})}${T(m,h-m,h*.022,'Set in '+D.family,P[2],{w:L(),op:.7})}`},
 cards:(w,h,P,n,t,i)=>i?`<rect width="${w}" height="${h}" fill="#fff" opacity="0"/>${T(w*.08,h*.2,fs(n,w*.5,h*.1),n,P[1])}
  ${T(w*.08,h*.66,h*.065,'hello@studio.example',P[1],{w:L()})}${T(w*.08,h*.76,h*.065,'+00 000 000 000',P[1],{w:L()})}${T(w*.08,h*.86,h*.065,'studio.example',P[3],{w:L()})}<circle cx="${w*.88}" cy="${h*.18}" r="${h*.06}" fill="${P[3]}"/>`
  :`<rect width="${w}" height="${h}" fill="${P[1]}"/>${T(w/2,h*.56,fs(n,w*.8,h*.28),n,P[2],{a:'middle'})}${T(w/2,h*.72,fs(t,w*.7,h*.06,L()),t,P[2],{a:'middle',w:L(),op:.75})}`,
 store:(w,h,P,n,t)=>`<rect width="${w}" height="${h}" fill="${P[1]}"/>${T(w/2,h*.66,fs(n,w*.8,h*.6),n,P[2],{a:'middle'})}`,
 bag:(w,h,P,n,t)=>`<rect width="${w}" height="${h}" fill="#fff" opacity="0"/>${T(w/2,h*.22,h*.034,'SINGLE ORIGIN · '+yr,P[1],{a:'middle',w:L(),ls:3})}
  ${T(w/2,h*.47,fs(n,w*.82,h*.17),n,P[1],{a:'middle'})}${T(w/2,h*.56,fs(t,w*.8,h*.04,L()),t,P[1],{a:'middle',w:L(),op:.8})}
  <rect y="${h*.72}" width="${w}" height="${h*.28}" fill="${P[3]}"/>${T(w/2,h*.88,h*.06,'250 g · whole bean',P[2],{a:'middle',w:L()})}`,
 billboard:(w,h,P,n,t)=>`<rect width="${w}" height="${h}" fill="${P[3]}"/>${T(w*.06,h*.58,fs(n,w*.86,h*.42),n,P[1])}${T(w*.06,h*.82,fs(t,w*.86,h*.08,L()),t,P[1],{w:L()})}`,
 tote:(w,h,P,n,t)=>{const [a,b]=two(n),s=Math.min(fs(a,w*.82,h*.26),b?fs(b,w*.82,h*.26):99);
  return`${T(w/2,h*.42,s,a,P[1],{a:'middle'})}${b?T(w/2,h*.42+s,s,b,P[1],{a:'middle'}):''}${T(w/2,h*.88,fs(t,w*.8,h*.045,L()),t,P[1],{a:'middle',w:L(),op:.85})}`},
 book:(w,h,P,n,t)=>{const [a,b]=two(n),m=w*.1,s=Math.min(fs(a,w-2*m,h*.17),b?fs(b,w-2*m,h*.17):99);
  return`<rect width="${w}" height="${h}" fill="${P[3]}"/>${T(m,m+h*.03,h*.026,'A NOVEL',P[1],{w:L(),ls:4})}${T(m,h*.5,s,a,P[1])}${b?T(m,h*.5+s*.95,s,b,P[1]):''}
  <rect x="${m}" y="${h*.72}" width="${w*.12}" height="${h*.007}" fill="${P[1]}"/>${T(m,h-m,fs(t,w-2*m,h*.03,L()),t,P[1],{w:L()})}`},
 phone:(w,h,P,n,t)=>{const m=w*.08,cw=w-2*m;let r=`<rect width="${w}" height="${h}" fill="${P[2]}"/>${T(m,h*.16,fs(n,cw,h*.07),n,P[1])}${T(m,h*.2,fs(t,cw,h*.024,L()),t,P[1],{w:L(),op:.65})}`;
  ['Today','Saved','Inbox'].forEach((k,i)=>{const y=h*.25+i*h*.19,dk=!i;r+=`<rect x="${m}" y="${y}" width="${cw}" height="${h*.16}" rx="${w*.06}" fill="${dk?P[1]:'#fff'}"/>${T(m+w*.07,y+h*.07,h*.04,k,dk?P[2]:P[1])}${T(m+w*.07,y+h*.115,h*.024,['3 new things','12 items','All caught up'][i],dk?P[2]:P[1],{w:L(),op:.7})}`});
  return r+`<rect x="${m}" y="${h*.86}" width="${cw}" height="${h*.075}" rx="${h*.0375}" fill="${P[3]}"/>${T(w/2,h*.908,h*.03,'Get started',P[2],{a:'middle'})}`}};
// projective texture mapping in WebGL: each surface pixel looks up its own point on the design, so no seams
function hmat(q){const [[x0,y0],[x1,y1],[x2,y2],[x3,y3]]=q;const dx1=x1-x2,dx2=x3-x2,dy1=y1-y2,dy2=y3-y2,sx=x0-x1+x2-x3,sy=y0-y1+y2-y3;
 const den=dx1*dy2-dx2*dy1,g=(sx*dy2-dx2*sy)/den,h=(dx1*sy-sx*dy1)/den;
 const M=[x1-x0+g*x1,x3-x0+h*x3,x0, y1-y0+g*y1,y3-y0+h*y3,y0, g,h,1];
 const [a,b,c,d,e,f,gg,hh,i]=M,A=e*i-f*hh,B=-(d*i-f*gg),C=d*hh-e*gg,det=a*A+b*B+c*C;
 return[A/det,-(b*i-c*hh)/det,(b*f-c*e)/det, B/det,(a*i-c*gg)/det,-(a*f-c*d)/det, C/det,-(a*hh-b*gg)/det,(a*e-b*d)/det]}
const GL=(()=>{const c=document.createElement('canvas');c.width=1280;c.height=853;const gl=c.getContext('webgl',{premultipliedAlpha:true,preserveDrawingBuffer:true});if(!gl)return null;
 const sh=(t,src)=>{const o=gl.createShader(t);gl.shaderSource(o,src);gl.compileShader(o);return o};const pr=gl.createProgram();
 gl.attachShader(pr,sh(gl.VERTEX_SHADER,'attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}'));
 gl.attachShader(pr,sh(gl.FRAGMENT_SHADER,'precision highp float;uniform mat3 H;uniform sampler2D T;void main(){vec2 xy=vec2(gl_FragCoord.x,853.-gl_FragCoord.y);vec3 u=H*vec3(xy,1.);vec2 uv=u.xy/u.z;'+
  'if(uv.x<0.||uv.y<0.||uv.x>1.||uv.y>1.)discard;vec2 e=min(uv,1.-uv)*vec2(900.);float a=clamp(min(e.x,e.y),0.,1.);gl_FragColor=texture2D(T,uv)*a;}'));
 gl.linkProgram(pr);gl.useProgram(pr);const bf=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,bf);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
 const lp=gl.getAttribLocation(pr,'p');gl.enableVertexAttribArray(lp);gl.vertexAttribPointer(lp,2,gl.FLOAT,false,0,0);
 const tx=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,tx);[gl.TEXTURE_WRAP_S,gl.TEXTURE_WRAP_T].forEach(k=>gl.texParameteri(gl.TEXTURE_2D,k,gl.CLAMP_TO_EDGE));
 gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL,true);
 gl.enable(gl.BLEND);gl.blendFunc(gl.ONE,gl.ONE_MINUS_SRC_ALPHA);
 return{c,clear(){gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT)},draw(im,q){gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,im);
  const m=hmat(q);gl.uniformMatrix3fv(gl.getUniformLocation(pr,'H'),false,[m[0],m[3],m[6],m[1],m[4],m[7],m[2],m[5],m[8]]);gl.drawArrays(gl.TRIANGLE_STRIP,0,4)}}})();
// 2D fallback: one affine per surface (fine for near-rectangular surfaces)
function warp(ctx,im,q){const [[x0,y0],[x1,y1],,[x3,y3]]=q;ctx.save();ctx.beginPath();q.forEach((p,j)=>j?ctx.lineTo(...p):ctx.moveTo(...p));ctx.closePath();ctx.clip();
 ctx.transform((x1-x0)/im.width,(y1-y0)/im.width,(x3-x0)/im.height,(y3-y0)/im.height,x0,y0);ctx.drawImage(im,0,0);ctx.restore()}
const svgImg=(w,h,body)=>new Promise(res=>{const S=2,svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${w*S}" height="${h*S}" viewBox="0 0 ${w} ${h}" font-family="PCX"><style>${FACE}</style>${body}</svg>`;
 const im=new Image();im.onload=()=>res(im);im.onerror=()=>res(null);im.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg)});
const photos=MK.map(s=>{const im=new Image();im.src='data:image/jpeg;base64,'+s.src;return im});
const cvs=[];const g=$('#mkgrid');
MK.forEach((s,i)=>{const d=el('div','mk');const c=document.createElement('canvas');c.width=1280;c.height=853;cvs.push(c);d.append(c);
 d.insertAdjacentHTML('beforeend',`<div class="mkf"><span>${E(s.n)}</span><button class="btn sm">Download PNG</button></div>`);
 d.querySelector('button').onclick=()=>{window.pcTrack&&pcTrack('mockup_download',{scene:s.k})};d.querySelector('button').addEventListener('click',()=>c.toBlob(b=>{const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=D.id+'-'+s.k+'.png';a.click();toast('Mockup saved')}));g.append(d)});
async function scene(i,tok){const s=MK[i],c=cvs[i],ctx=c.getContext('2d'),P=PAL[mk.p],ph=photos[i];
 if(!ph.complete)await new Promise(r=>ph.onload=r);
 const layer=document.createElement('canvas');layer.width=1280;layer.height=853;const lx=layer.getContext('2d');
 const ims=[];for(let k=0;k<s.q.length;k++){const q=s.q[k],w=Math.hypot(q[1][0]-q[0][0],q[1][1]-q[0][1]),h=Math.hypot(q[3][0]-q[0][0],q[3][1]-q[0][1]);
  ims.push(await svgImg(Math.round(w),Math.round(h),DES[s.k](Math.round(w),Math.round(h),P,mk.n||' ',mk.t||' ',k)))}
 if(tok!==drawTok)return;
 if(GL){GL.clear();ims.forEach((im,k)=>im&&GL.draw(im,s.q[k]));lx.drawImage(GL.c,0,0)}else ims.forEach((im,k)=>im&&warp(lx,im,s.q[k]));
 ctx.globalCompositeOperation='source-over';ctx.globalAlpha=1;ctx.drawImage(ph,0,0,1280,853);
 ctx.globalCompositeOperation='multiply';ctx.globalAlpha=s.m==='ink'?.93:1;ctx.drawImage(layer,0,0);
 if(s.m==='paper'||s.m==='ink'){ // bring the paper's folds and texture back over dark ink
  ctx.save();ctx.beginPath();s.q.forEach(q=>{q.forEach((p,j)=>j?ctx.lineTo(...p):ctx.moveTo(...p));ctx.closePath()});ctx.clip();
  ctx.globalCompositeOperation='soft-light';ctx.globalAlpha=.45;ctx.drawImage(ph,0,0,1280,853);ctx.restore()}
 if(s.m==='flat'){ctx.globalCompositeOperation='screen';ctx.globalAlpha=.06;ctx.drawImage(ph,0,0,1280,853)}
 ctx.globalCompositeOperation='source-over';ctx.globalAlpha=1}
let drawTok=0,deb;
function draw(){clearTimeout(deb);deb=setTimeout(()=>{const tok=++drawTok;MK.forEach((_,i)=>scene(i,tok))},90)}
nI.oninput=()=>{mk.n=nI.value;draw()};tI.oninput=()=>{mk.t=tI.value;draw()};wS.onchange=()=>{mk.w=+wS.value;draw()};
document.fonts.ready.then(draw);
}
"""
