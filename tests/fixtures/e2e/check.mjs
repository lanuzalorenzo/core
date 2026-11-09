// Comprueba el servicio que arranca start.sh sin abrir un navegador.
const response = await fetch("http://127.0.0.1:8099/");

if (!response.ok) {
  console.error(`Se esperaba 200 y llegó ${response.status}`);
  process.exit(1);
}

const body = await response.text();
if (!body.includes("ok")) {
  console.error(`Se esperaba «ok» en el cuerpo y llegó «${body.trim()}»`);
  process.exit(1);
}
