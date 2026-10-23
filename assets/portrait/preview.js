(function(){
if(!new URLSearchParams(location.search).has('preview'))return;
const audio=document.createElement('audio');audio.src='audio/score.wav';audio.controls=true;
audio.style.cssText='position:fixed;bottom:12px;left:25%;width:50%;z-index:2';document.body.append(audio);
function sync(){if(window.READY)window.seek(Math.min(audio.currentTime,window.END));requestAnimationFrame(sync);}
requestAnimationFrame(sync);
})();
