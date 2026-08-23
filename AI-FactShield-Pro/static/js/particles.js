const canvas = document.getElementById("particleCanvas");
if (canvas) {
  const ctx = canvas.getContext("2d");
  let w, h, dots=[];
  function resize(){w=canvas.width=innerWidth;h=canvas.height=innerHeight;}
  function init(){dots=Array.from({length:90},()=>({x:Math.random()*w,y:Math.random()*h,r:Math.random()*1.8+.4,vx:(Math.random()-.5)*.18,vy:(Math.random()-.5)*.18}));}
  function draw(){
    ctx.clearRect(0,0,w,h);
    dots.forEach((p,i)=>{
      p.x+=p.vx;p.y+=p.vy;
      if(p.x<0)p.x=w;if(p.x>w)p.x=0;if(p.y<0)p.y=h;if(p.y>h)p.y=0;
      ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);ctx.fillStyle="rgba(150,220,255,.72)";ctx.fill();
      for(let j=i+1;j<dots.length;j++){let q=dots[j],dx=p.x-q.x,dy=p.y-q.y,d=Math.hypot(dx,dy);if(d<110){ctx.strokeStyle=`rgba(70,180,255,${.08*(1-d/110)})`;ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(q.x,q.y);ctx.stroke();}}
    });
    requestAnimationFrame(draw);
  }
  addEventListener("resize",()=>{resize();init()});resize();init();draw();
}
