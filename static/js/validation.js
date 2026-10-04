document.querySelectorAll("input[type=email]").forEach(input=>{
  input.addEventListener("blur",()=>{input.setCustomValidity(input.value && !input.value.includes("@")?"Enter a valid email.":"");});
});
