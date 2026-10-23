(function(){
'use strict';
function path(f,d,fill,stroke=null,w=4){const p=new Path2D(d),x=f.x;if(fill){x.fillStyle=fill;x.fill(p);}if(stroke){x.strokeStyle=stroke;x.lineWidth=w;x.lineCap='round';x.lineJoin='round';x.stroke(p);}}
function text(f,s,x,y,size=70,color='#304354',font='sansm',align='c',max=860){while(f.measure(s,{font,size})>max&&size>28)size-=2;f.text(s,x,y,{size,color,font,align});}
function lines(f,s,size=46,width=840,font='sansm'){
 if(f.measure(s,{font,size})<=width)return [s];
 const candidates=[];for(let i=2;i<s.length-2;i++){if('，；：。！？'.includes(s[i])){const a=s.slice(0,i+1),b=s.slice(i+1),wa=f.measure(a,{font,size}),wb=f.measure(b,{font,size});if(wa<=width&&wb<=width&&a.length>=5&&b.length>=5)candidates.push({a,b,score:Math.abs(wa-wb)});}}
 if(candidates.length){candidates.sort((a,b)=>a.score-b.score);return [candidates[0].a,candidates[0].b];}
 const out=[];let line='';for(const c of s){const punct='，。！？；：、）》”’'.includes(c);if(f.measure(line+c,{font,size})>width&&line&&!punct){out.push(line);line=c;}else line+=c;}if(line)out.push(line);if(out.length>1&&out.at(-1).length<5){const tail=out.pop();let prior=out.pop(),moved='';while((moved+tail).length<6&&prior.length>7){moved=prior.at(-1)+moved;prior=prior.slice(0,-1);}out.push(prior,moved+tail);}return out;
}
function caption(f,t,tl,o={}){const e=tl.segments.find(s=>t>=s.a&&t<s.b);if(!e)return;const size=o.size||46,font=o.font||'sansm',ls=lines(f,e.text,size,o.width||840,font),y=(o.y||f.h*.854)-(ls.length-1)*38;f.g({a:Math.min(VK.ss(t,e.a,e.a+.1),1-VK.ss(t,e.b-.1,e.b))},()=>{ls.forEach((s,i)=>text(f,s,f.w/2,y+i*76,size,o.color||'#304354',font,'c',o.width||840));});}
window.BookVisual={path,text,lines,caption};
})();
