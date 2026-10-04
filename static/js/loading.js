document.querySelectorAll("form").forEach(form=>{
  form.addEventListener("submit",()=>{
    const btn=form.querySelector("button[type=submit]");
    if(btn){btn.dataset.original=btn.innerHTML;btn.innerHTML="Analyzing…";btn.disabled=true;}
  });
});
