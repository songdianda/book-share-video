/* Executable scaffold only. Author original, content-specific scenes before delivery. */
(function(){
'use strict';
const TL=window.BOOK_TIMELINE,{text,caption}=BookVisual;
function scene(f,t){
  // Draw the book's actual objects, actions and visual metaphor here.
  // Pick materials, composition and motion from this project's style.json.
  text(f,TL.title,f.w/2,f.h*.4,90,'#304354','serifm','c',f.w*.8);
}
VK.film({dur:TL.end,fps:TL.fps,theme:'flat',bloom:0,grain:0,meta:{title:TL.title},draw(f,t){
  f.look.bg='flat';f.look.bgo={color:'#F4F0E6'};f.look.bloom=0;f.look.grain=0;
  scene(f,t);
  caption(f,t,TL,{color:'#304354',size:46,width:f.w*.78});
}});
})();
