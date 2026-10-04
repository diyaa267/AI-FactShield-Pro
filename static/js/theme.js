(function () {
  const body = document.body;
  const toggle = document.getElementById("themeToggle");
  const saved = localStorage.getItem("factshield-theme") || "dark";

  function applyTheme(theme) {
    const light = theme === "light";
    body.classList.toggle("light-mode", light);
    if (toggle) {
      toggle.setAttribute("aria-pressed", String(light));
      toggle.textContent = light ? "☀️" : "🌙";
      toggle.title = light ? "Switch to dark mode" : "Switch to light mode";
    }
  }

  applyTheme(saved);
  if (toggle) toggle.addEventListener("click", function () {
    const next = body.classList.contains("light-mode") ? "dark" : "light";
    localStorage.setItem("factshield-theme", next);
    applyTheme(next);
  });
})();
