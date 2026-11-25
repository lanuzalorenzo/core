// Menú de la cabecera compartida. Sin dependencias y sin estado propio.
(() => {
  const boton = document.querySelector(".menu-toggle");
  const nav = document.getElementById("site-nav");
  if (!boton || !nav) return;

  const abierto = () => boton.getAttribute("aria-expanded") === "true";
  const cerrar = () => {
    boton.setAttribute("aria-expanded", "false");
    nav.classList.remove("is-open");
    document.documentElement.classList.remove("menu-open");
  };
  const abrir = () => {
    boton.setAttribute("aria-expanded", "true");
    nav.classList.add("is-open");
    document.documentElement.classList.add("menu-open");
  };

  boton.addEventListener("click", () => (abierto() ? cerrar() : abrir()));
  nav.addEventListener("click", (evento) => {
    if (evento.target.closest("a")) cerrar();
  });
  document.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape" && abierto()) {
      cerrar();
      boton.focus();
    }
  });
  window.addEventListener("resize", () => {
    if (window.innerWidth > 850) cerrar();
  });
})();
