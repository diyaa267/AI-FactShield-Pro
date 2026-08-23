const navToggle=document.getElementById('navToggle');
if(navToggle) navToggle.addEventListener('click',()=>document.querySelector('.navbar')?.classList.toggle('menu-open'));
