async function consultar() {
  const rut = document.getElementById("rut").value;
  const resultado = document.getElementById("resultado");
  resultado.innerHTML = "Consultando...";

  try {
    const res = await fetch("/consultar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rut })
    });

    const data = await res.json();

    if (!res.ok) {
      resultado.innerHTML = data.error || "Error en la consulta";
      return;
    }

    resultado.innerHTML = `
      <strong>Nombre:</strong> ${data.nombre}<br>
      <strong>RUT:</strong> ${data.rut}<br>
      <strong>Páginas restantes:</strong> ${data.paginas_restantes}
    `;
  } catch (error) {
    resultado.innerHTML = "Error al conectar con el servidor";
  }
}
