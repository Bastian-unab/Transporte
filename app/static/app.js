"use strict";
/* Front de la central de despacho: Prolog vs Laya.
   Sin dependencias: habla con app/servidor.py por /api/... */

// Se reemplaza por la lista del servidor (laya_agent/pregunta.py) al iniciar: si se agrega una
// acción, no hay que tocar el front.
let ACCIONES = ["despachar", "reasignar", "esperar", "inspeccionar", "alertar"];
const NOMBRES = {
  centro: "Centro", zona_norte: "Zona norte", zona_sur: "Zona sur", zona_oriente: "Zona oriente",
  zona_poniente: "Zona poniente", camioneta: "Camioneta", furgon: "Furgón",
  furgon_refrigerado: "Furgón refrigerado", camion: "Camión", general: "General",
  refrigerada: "Refrigerada", alta: "Alta", media: "Media", baja: "Baja",
  suficiente: "Suficiente", bajo: "Bajo",
};
const CAMPOS_PEDIDO = [
  { k: "pedido", label: "Id del pedido", tipo: "texto" },
  { k: "carga_kg", label: "Carga (kg)", tipo: "numero" },
  { k: "tipo_carga", label: "Tipo de carga", tipo: "opcion", opciones: ["general", "refrigerada"] },
  { k: "destino", label: "Destino", tipo: "opcion", opciones: ["centro", "zona_norte", "zona_sur", "zona_oriente", "zona_poniente"] },
  { k: "urgencia", label: "Urgencia", tipo: "opcion", opciones: ["alta", "media", "baja"] },
  { k: "ruta_despejada", label: "Ruta despejada", tipo: "bool" },
];
const CAMPOS_VEHICULO = [
  { k: "id", label: "Id", tipo: "texto" },
  { k: "tipo_vehiculo", label: "Tipo", tipo: "opcion", opciones: ["camioneta", "furgon", "furgon_refrigerado", "camion"] },
  { k: "capacidad_kg", label: "Capacidad (kg)", tipo: "numero" },
  { k: "disponible", label: "Disponible", tipo: "bool" },
  { k: "en_mantencion", label: "En mantención", tipo: "bool" },
  { k: "combustible", label: "Combustible", tipo: "opcion", opciones: ["suficiente", "bajo"] },
  { k: "conductor_disponible", label: "Conductor disponible", tipo: "bool" },
];
const ETIQUETAS_PASO = { regla: "regla", hecho: "hecho", calculo: "cálculo", negacion: "no demostrable", sin_regla: "sin regla" };
const NULO = "__nulo";

const app = {
  servidor: null,
  casos: [],
  casoId: null,          // id del caso o "NUEVO"
  original: null,
  estado: null,
  esperadaManual: "",
  cache: {},             // id -> respuesta de /api/ejecutar (solo estados sin modificar)
  mostrado: null,        // {respuesta, firma} de lo que se ve en la vista Caso
  exp: null,             // corrida de los 20 casos: {filas, terminado}
  corriendo: false,
  tab: "formulario",
  jsonValido: true,
  vista: "caso",
};

/* ------------------------------------------------------------------ utilidades */
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const copia = (o) => JSON.parse(JSON.stringify(o));
const nombre = (v) => NOMBRES[v] ?? String(v).replace(/_/g, " ");
const pct = (x, d = 1) => (x == null ? "—" : `${(x * 100).toFixed(d)} %`);
const num = (x, d = 2) => (x == null ? "—" : Number(x).toFixed(d));

function firma(o) {   // JSON con claves ordenadas: compara estados sin importar el orden
  const ordenar = (x) => Array.isArray(x) ? x.map(ordenar)
    : x && typeof x === "object" ? Object.fromEntries(Object.keys(x).sort().map((k) => [k, ordenar(x[k])])) : x;
  return JSON.stringify(ordenar(o));
}

async function api(ruta, cuerpo) {
  const opciones = cuerpo === undefined ? {} : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo),
  };
  const r = await fetch(ruta, opciones);
  const datos = await r.json().catch(() => ({ error: `Respuesta inválida (${r.status})` }));
  if (!r.ok) throw new Error(datos.error || `Error ${r.status}`);
  return datos;
}

const ICONO_BIEN = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>';
const ICONO_MAL = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7l10 10M17 7L7 17"/></svg>';

function chip(accion, clase = "") {
  if (!accion) return `<span class="accion vacia ${clase}">sin respuesta</span>`;
  return `<span class="accion ${clase}" data-a="${esc(accion)}">${esc(accion)}</span>`;
}
function veredicto(ok, textos = ["Correcto", "Incorrecto"]) {
  // Con textos vacíos (tabla compacta) queda solo el ícono, con title y texto para lectores de pantalla.
  const solo = (t) => (t ? t : "");
  const oculto = (t) => `<span class="solo-lector">${t}</span>`;
  if (ok === true) return `<span class="veredicto bien" title="Correcto">${ICONO_BIEN}${solo(textos[0]) || oculto("Correcto")}</span>`;
  if (ok === false) return `<span class="veredicto mal" title="Incorrecto">${ICONO_MAL}${solo(textos[1]) || oculto("Incorrecto")}</span>`;
  return `<span class="veredicto neutro">sin esperada</span>`;
}
function marcaAgente(letra, ok, titulo) {
  const clase = ok === true ? "bien" : ok === false ? "mal" : "";
  return `<span class="marca-agente ${clase}" title="${esc(titulo)}">${letra}${ok === true ? "✓" : ok === false ? "✗" : ""}</span>`;
}

/* ------------------------------------------------------------------ tema */
function aplicarTemaGuardado() {
  try {
    const t = localStorage.getItem("tema");
    if (t === "light" || t === "dark") document.documentElement.dataset.theme = t;
  } catch { /* sin almacenamiento: se usa el tema del sistema */ }
}
function alternarTema() {
  const actual = document.documentElement.dataset.theme
    || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  const nuevo = actual === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = nuevo;
  try { localStorage.setItem("tema", nuevo); } catch { /* ignorar */ }
}

/* ------------------------------------------------------------------ estado del servidor */
let sondeo = null;
async function actualizarServidor() {
  try {
    app.servidor = await api("/api/estado");
  } catch (e) {
    $("#pill-prolog").innerHTML = `<i class="punto error"></i>Servidor <b>sin conexión</b>`;
    return;
  }
  pintarCabecera();
  const cargando = app.servidor.laya.cargando;
  if (cargando && !sondeo) sondeo = setInterval(actualizarServidor, 1500);
  if (!cargando && sondeo) { clearInterval(sondeo); sondeo = null; }
}

function pintarCabecera() {
  const s = app.servidor;
  if (!s) return;
  const p = s.prolog;
  $("#pill-prolog").innerHTML = p.listo
    ? `<i class="punto ok"></i>Prolog <b>SWI ${esc(p.version)}</b>`
    : `<i class="punto error"></i>Prolog <b>no disponible</b>`;
  $("#pill-prolog").title = p.listo ? `Proceso abierto: ${p.ruta}` : (p.error || "");

  const m = s.laya;
  let punto = "", texto = "";
  if (m.error) { punto = "error"; texto = "error"; }
  else if (m.cargando) { punto = "cargando"; texto = "cargando…"; }
  else if (m.listo) { punto = "ok"; texto = "multilingüe"; }
  else { texto = "sin cargar"; }
  $("#pill-laya").innerHTML = `<i class="punto ${punto}"></i>Laya <b>${esc(texto)}</b>`;
  $("#pill-laya").title = m.error || (m.version ? `laya ${m.version} · checkpoint ${m.modelo}` : "Se carga en segundo plano");
}

/* ------------------------------------------------------------------ lista de casos */
function pintarLista() {
  const categorias = app.servidor?.categorias || {};
  let html = "";
  for (const [clave, titulo] of Object.entries(categorias)) {
    const casos = app.casos.filter((c) => c.categoria === clave);
    if (!casos.length) continue;
    html += `<div class="grupo-casos"><h4>${esc(titulo)}</h4>`;
    for (const c of casos) {
      const r = app.cache[c.id];
      const marcas = r ? `<span class="marcas">${marcaAgente("P", r.comparacion.prolog_correcto, "Prolog")}${marcaAgente("L", r.comparacion.laya_correcto, "Laya")}</span>` : "";
      html += `<button type="button" class="item-caso ${app.casoId === c.id ? "activo" : ""}" data-id="${esc(c.id)}">
        <span class="id">${esc(c.id)}</span><span class="desc">${esc(c.descripcion)}</span>
        <span class="pie">esperada ${chip(c.decision_esperada, "chica")}${marcas}</span></button>`;
    }
    html += `</div>`;
  }
  if (app.casoId === "NUEVO") {
    html = `<div class="grupo-casos"><h4>En edición</h4><button type="button" class="item-caso activo" data-id="NUEVO">
      <span class="id">+</span><span class="desc">Caso nuevo</span></button></div>` + html;
  }
  $("#lista").innerHTML = html;
}

function casoActual() {
  return app.casos.find((c) => c.id === app.casoId) || null;
}
function modificado() {
  return app.casoId === "NUEVO" || firma(app.estado) !== firma(app.original);
}

function seleccionarCaso(id) {
  const caso = app.casos.find((c) => c.id === id);
  if (!caso) return;
  app.casoId = id;
  app.original = copia(caso.estado);
  app.estado = copia(caso.estado);
  app.esperadaManual = "";
  history.replaceState(null, "", `${location.pathname}${location.search}#${id}`);   // enlace directo al caso
  pintarLista();
  pintarCabeceraCaso();
  pintarEstado();
  mostrarResultadoGuardado();
  pintarSugerencias();
  $("#salida-consulta").innerHTML = "";
}

function casoNuevo() {
  app.casoId = "NUEVO";
  app.original = {
    pedido: "P99", carga_kg: 500, tipo_carga: "general", destino: "zona_norte", urgencia: "media",
    ruta_despejada: true,
    vehiculo_asignado: { id: "V990", tipo_vehiculo: "camioneta", capacidad_kg: 1500, disponible: true,
      en_mantencion: false, combustible: "suficiente", conductor_disponible: true },
    vehiculos_alternativos: [],
  };
  app.estado = copia(app.original);
  app.esperadaManual = "";
  app.mostrado = null;
  pintarLista();
  pintarCabeceraCaso();
  pintarEstado();
  pintarResultadosVacios();
  pintarSugerencias();
  $("#salida-consulta").innerHTML = "";
  irAVista("caso");
}

/* ------------------------------------------------------------------ cabecera del caso */
function pintarCabeceraCaso() {
  const c = casoActual();
  const cats = app.servidor?.categorias || {};
  const mod = modificado();
  const selector = `<label>Decisión esperada (opcional):
      <select id="sel-esperada"><option value="">sin definir</option>
      ${ACCIONES.map((a) => `<option value="${a}" ${app.esperadaManual === a ? "selected" : ""}>${a}</option>`).join("")}
      </select></label>`;
  if (!c) {
    $("#cabecera-caso").innerHTML = `
      <div class="cabecera-caso-fila"><span class="etiqueta-id">NUEVO</span><span class="etiqueta-cat">caso libre</span></div>
      <h2>Caso nuevo: edita el estado y ejecuta ambos agentes</h2>
      <div class="esperada">${selector}</div>`;
  } else {
    $("#cabecera-caso").innerHTML = `
      <div class="cabecera-caso-fila"><span class="etiqueta-id">${esc(c.id)}</span>
        <span class="etiqueta-cat">${esc(cats[c.categoria] || c.categoria)}</span></div>
      <h2>${esc(c.descripcion)}</h2>
      <div class="esperada">${mod
        ? `<span>La esperada del caso original era ${chip(c.decision_esperada)}; con el estado modificado ya no aplica.</span> ${selector}`
        : `<span>Decisión esperada (definida por el grupo antes de ejecutar):</span> ${chip(c.decision_esperada)}`}</div>
      <details class="criterio"><summary>¿Por qué esa decisión?</summary><p>${esc(c.criterio_esperada)}</p></details>`;
  }
  $("#sel-esperada")?.addEventListener("change", (e) => { app.esperadaManual = e.target.value; });
}

/* ------------------------------------------------------------------ estado: formulario / JSON / texto */
function obtener(ruta) {
  return ruta.split(".").reduce((o, k) => (o == null ? undefined : o[k]), app.estado);
}
function obtenerOriginal(ruta) {
  return ruta.split(".").reduce((o, k) => (o == null ? undefined : o[k]), app.original);
}
function fijar(ruta, valor) {
  const partes = ruta.split(".");
  let o = app.estado;
  for (const k of partes.slice(0, -1)) o = o[k];
  o[partes.at(-1)] = valor;
}

function campoHTML(def, ruta) {
  const v = obtener(ruta);
  const nulo = v === null || v === undefined;
  const cambiado = app.casoId !== "NUEVO" && firma(v ?? null) !== firma(obtenerOriginal(ruta) ?? null);
  const clases = `campo ${nulo ? "nulo" : ""} ${cambiado ? "cambiado" : ""}`;
  const id = `f-${ruta.replace(/\./g, "-")}`;
  let control = "";
  if (def.tipo === "texto") {
    control = `<input id="${id}" data-ruta="${ruta}" data-tipo="texto" value="${esc(v ?? "")}">`;
  } else if (def.tipo === "numero") {
    control = `<input id="${id}" type="number" step="50" data-ruta="${ruta}" data-tipo="numero" value="${nulo ? "" : esc(v)}" placeholder="sin dato">`;
  } else if (def.tipo === "bool") {
    const sel = nulo ? NULO : v ? "true" : "false";
    control = `<select id="${id}" data-ruta="${ruta}" data-tipo="bool">
      <option value="true" ${sel === "true" ? "selected" : ""}>sí</option>
      <option value="false" ${sel === "false" ? "selected" : ""}>no</option>
      <option value="${NULO}" ${sel === NULO ? "selected" : ""}>sin dato</option></select>`;
  } else {
    const opciones = [...def.opciones];
    if (!nulo && !opciones.includes(v)) opciones.push(v);   // valor nuevo escrito en el JSON
    control = `<select id="${id}" data-ruta="${ruta}" data-tipo="opcion">
      ${opciones.map((o) => `<option value="${esc(o)}" ${o === v ? "selected" : ""}>${esc(nombre(o))}</option>`).join("")}
      <option value="${NULO}" ${nulo ? "selected" : ""}>sin dato</option></select>`;
  }
  return `<div class="${clases}"><label for="${id}">${esc(def.label)}</label>${control}</div>`;
}

function bloqueVehiculo(titulo, base, quitar) {
  const v = obtener(base);
  if (v == null) {
    return `<div class="bloque-form"><div class="bloque-form-titulo">${titulo}<span class="sutil">sin dato (null)</span></div></div>`;
  }
  return `<div class="bloque-form"><div class="bloque-form-titulo">${titulo}<span class="espacio"></span>${quitar ?? ""}</div>
    <div class="campos">${CAMPOS_VEHICULO.map((d) => campoHTML(d, `${base}.${d.k}`)).join("")}</div></div>`;
}

function pintarFormulario() {
  const e = app.estado;
  const alts = e.vehiculos_alternativos;
  let html = `<div class="bloque-form"><div class="bloque-form-titulo">Pedido</div>
    <div class="campos">${CAMPOS_PEDIDO.map((d) => campoHTML(d, d.k)).join("")}</div></div>`;
  html += bloqueVehiculo("Vehículo asignado", "vehiculo_asignado");
  html += `<div class="bloque-form"><div class="bloque-form-titulo">Vehículos alternativos
      <span class="sutil">${alts == null ? "· lista sin dato (null)" : `· ${alts.length}`}</span><span class="espacio"></span>
      <label class="check-linea"><input type="checkbox" id="alts-nulo" ${alts == null ? "checked" : ""}> lista sin dato</label>
      ${alts == null ? "" : `<button type="button" class="boton chico" id="btn-agregar-alt">+ Agregar</button>`}
    </div>`;
  if (alts != null && !alts.length) html += `<div class="alternativos-vacio">Ninguno.</div>`;
  html += `</div>`;
  if (alts) {
    alts.forEach((_, i) => {
      html += bloqueVehiculo(`Alternativo ${i + 1}`, `vehiculos_alternativos.${i}`,
        `<button type="button" class="boton chico peligro" data-quitar="${i}">Quitar</button>`);
    });
  }
  const panel = $("#panel-formulario");
  panel.innerHTML = html;
  $$("[data-ruta]", panel).forEach((el) => el.addEventListener("change", alCambiarCampo));
  $$("[data-tipo='texto'], [data-tipo='numero']", panel).forEach((el) => el.addEventListener("input", alCambiarCampo));
  $("#btn-agregar-alt", panel)?.addEventListener("click", () => {
    const n = (app.estado.vehiculos_alternativos.length + 1);
    const base = String(app.estado.vehiculo_asignado?.id || "V").replace(/\d+$/, "");
    app.estado.vehiculos_alternativos.push({ id: `${base || "V"}${900 + n}`, tipo_vehiculo: "furgon", capacidad_kg: 3500,
      disponible: true, en_mantencion: false, combustible: "suficiente", conductor_disponible: true });
    estadoCambiado(true);
  });
  $$("[data-quitar]", panel).forEach((b) => b.addEventListener("click", () => {
    app.estado.vehiculos_alternativos.splice(Number(b.dataset.quitar), 1);
    estadoCambiado(true);
  }));
  $("#alts-nulo", panel).addEventListener("change", (ev) => {
    app.estado.vehiculos_alternativos = ev.target.checked ? null : [];
    estadoCambiado(true);
  });
}

function alCambiarCampo(ev) {
  const el = ev.target;
  const tipo = el.dataset.tipo;
  let valor;
  if (tipo === "texto") valor = el.value;
  else if (tipo === "numero") valor = el.value === "" ? null : Number(el.value);
  else if (tipo === "bool") valor = el.value === NULO ? null : el.value === "true";
  else valor = el.value === NULO ? null : el.value;
  fijar(el.dataset.ruta, valor);
  // Al escribir no se redibuja el formulario (se perdería el foco); al confirmar, sí.
  estadoCambiado(ev.type === "change");
}

function estadoCambiado(redibujarFormulario) {
  if (redibujarFormulario) pintarFormulario();
  $("#editor-json").value = JSON.stringify(app.estado, null, 2);
  app.jsonValido = true;
  $("#error-json").classList.add("oculto");
  despuesDeCambio();
}

function despuesDeCambio() {
  const mod = modificado();
  $("#aviso-modificado").classList.toggle("oculto", !(mod && app.casoId !== "NUEVO"));
  $("#btn-ejecutar").disabled = !app.jsonValido;
  pintarCabeceraCaso();
  if (app.tab === "texto") actualizarTextoLaya();
  // Los resultados mostrados ya no corresponden al estado: se marcan como desactualizados.
  const res = $("#resultados");
  if (app.mostrado && app.mostrado.firma !== firma(app.estado)) {
    res.style.opacity = ".45";
    res.title = "El estado cambió: vuelve a ejecutar";
  } else {
    res.style.opacity = "";
    res.title = "";
  }
  pintarSugerencias();
}

function pintarEstado() {
  pintarFormulario();
  $("#editor-json").value = JSON.stringify(app.estado, null, 2);
  app.jsonValido = true;
  $("#error-json").classList.add("oculto");
  despuesDeCambio();
}

function alEditarJSON() {
  const texto = $("#editor-json").value;
  try {
    const obj = JSON.parse(texto);
    if (!obj || typeof obj !== "object" || Array.isArray(obj)) throw new Error("El estado debe ser un objeto JSON {…}");
    app.estado = obj;
    app.jsonValido = true;
    $("#error-json").classList.add("oculto");
  } catch (e) {
    app.jsonValido = false;
    $("#error-json").textContent = e.message;
    $("#error-json").classList.remove("oculto");
  }
  despuesDeCambio();
}

function cambiarTab(tab) {
  app.tab = tab;
  for (const b of $$("#tabs-estado button")) b.classList.toggle("activa", b.dataset.tab === tab);
  $("#panel-formulario").classList.toggle("oculto", tab !== "formulario");
  $("#panel-json").classList.toggle("oculto", tab !== "json");
  $("#panel-texto").classList.toggle("oculto", tab !== "texto");
  if (tab === "formulario" && app.jsonValido) pintarFormulario();
  if (tab === "texto") actualizarTextoLaya();
}

let temporizadorTexto = null;
function actualizarTextoLaya() {
  clearTimeout(temporizadorTexto);
  temporizadorTexto = setTimeout(async () => {
    if (!app.jsonValido) return;
    try {
      const r = await api("/api/texto_laya", { estado: app.estado });
      $("#texto-laya").textContent = r.texto;
    } catch (e) {
      $("#texto-laya").textContent = `Error: ${e.message}`;
    }
  }, 150);
}

/* ------------------------------------------------------------------ ejecutar un caso */
function idParaServidor() {
  if (app.casoId === "NUEVO") return "nuevo";
  return modificado() ? `${app.casoId}-modificado` : app.casoId;
}
function esperadaParaServidor() {
  const c = casoActual();
  if (c && !modificado()) return c.decision_esperada;
  return app.esperadaManual || null;
}

async function ejecutarCaso() {
  if (!app.jsonValido || app.corriendo) return;
  const boton = $("#btn-ejecutar");
  boton.disabled = true;
  pintarCargando();
  const estado = copia(app.estado);
  try {
    const r = await api("/api/ejecutar", { estado, id_caso: idParaServidor(),
      esperada: esperadaParaServidor() });
    if (!modificado() && app.casoId !== "NUEVO") app.cache[app.casoId] = r;
    app.mostrado = { respuesta: r, firma: firma(estado) };
    pintarResultados(r);
    pintarLista();
    pintarSugerencias();
  } catch (e) {
    $("#resultados").innerHTML = `<div class="caja-error">No se pudo ejecutar: ${esc(e.message)}</div>`;
  } finally {
    boton.disabled = !app.jsonValido;
    actualizarServidor();
  }
}

function mostrarResultadoGuardado() {
  const r = app.casoId && app.casoId !== "NUEVO" && !modificado() ? app.cache[app.casoId] : null;
  if (r) {
    app.mostrado = { respuesta: r, firma: firma(app.estado) };
    pintarResultados(r);
  } else {
    app.mostrado = null;
    pintarResultadosVacios();
  }
  despuesDeCambio();
}

function pintarResultadosVacios() {
  $("#resultados").innerHTML = `<div class="vacio-resultados">Ejecuta los agentes para ver la decisión de Prolog (con su derivación)
    y la de Laya (con sus probabilidades).<br><span class="sutil">Atajo: Ctrl + Enter</span></div>`;
}

function pintarCargando() {
  const m = app.servidor?.laya;
  const nota = m && !m.listo ? `<p class="sutil" style="margin:12px 0 0">Laya está cargando el checkpoint; la primera vez puede tardar.</p>` : "";
  const tarjeta = (t) => `<article class="tarjeta"><div class="agente-cabecera"><h3>${t}</h3></div>
    <div class="esqueleto" style="width:40%;height:28px;margin:12px 0 18px"></div>
    <div class="esqueleto"></div><div class="esqueleto" style="width:85%"></div><div class="esqueleto" style="width:70%"></div>${t === "Laya" ? nota : ""}</article>`;
  $("#resultados").style.opacity = "";
  $("#resultados").innerHTML = `<div class="agentes" style="margin-top:0">${tarjeta("Prolog")}${tarjeta("Laya")}</div>`;
}

function pintarResultados(r) {
  const c = r.comparacion;
  const p = r.prolog, l = r.laya;
  const franja = `<div class="franja">
    <div><span class="rotulo">Esperada</span><span class="valor">${c.esperada ? chip(c.esperada) : `<span class="sutil">sin definir</span>`}</span></div>
    <div><span class="rotulo">Prolog</span><span class="valor">${chip(p.accion)} ${veredicto(c.prolog_correcto)}</span></div>
    <div><span class="rotulo">Laya</span><span class="valor">${chip(l.accion)} ${veredicto(c.laya_correcto)}</span></div>
    <div><span class="rotulo">Entre agentes</span><span class="valor coinciden">${c.coinciden == null ? "—"
      : c.coinciden ? `<span class="veredicto bien">${ICONO_BIEN}Coinciden</span>` : `<span class="veredicto mal">${ICONO_MAL}Difieren</span>`}</span></div>
  </div>`;
  $("#resultados").style.opacity = "";
  $("#resultados").title = "";
  $("#resultados").innerHTML = franja + `<div class="agentes">${tarjetaProlog(p)}${tarjetaLaya(l)}</div>` + tarjetaDiagnostico(r.diagnostico);
  activarTooltips($("#resultados"));
}

function tarjetaProlog(p) {
  const avisos = p.avisos?.length ? `<div class="caja-aviso">Avisos al recargar las reglas:\n${esc(p.avisos.join("\n"))}</div>` : "";
  if (p.error) {
    return `<article class="tarjeta"><div class="agente-cabecera"><h3>Prolog</h3><span class="agente-tipo">inferencia lógica</span></div>
      ${avisos}<div class="caja-error">${esc(p.error)}</div></article>`;
  }
  const candidatas = p.candidatas.length
    ? p.candidatas.map((a, i) => `<span class="orden">${i + 1}.</span>${chip(a, i ? "atenuada" : "")}`).join(" ")
    : `<span class="sutil">ninguna: no aplica ninguna regla</span>`;
  const lista = (titulo, items) => items.length
    ? `<div class="seccion"><h4>${titulo}</h4><ul class="lista-hallazgos">${items.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>` : "";
  const pasos = (p.pasos || []).map((s) => {
    const meta = s.tipo === "negacion"
      ? `<span class="meta">\\+ ${esc(s.meta)}</span>${s.falla ? `<span class="falla">falla: ${esc(s.falla)}</span>` : ""}`
      : `<span class="meta">${esc(s.meta)}</span>`;
    return `<div class="paso" style="padding-left:${s.nivel * 18}px"><span class="etq ${esc(s.tipo)}">${esc(ETIQUETAS_PASO[s.tipo] || s.tipo)}</span>${meta}</div>`;
  }).join("");
  return `<article class="tarjeta">
    <div class="agente-cabecera"><h3>Prolog</h3><span class="agente-tipo">inferencia lógica</span><span class="tiempo">${p.tiempo_ms ?? "—"} ms</span></div>
    ${avisos}
    <div class="decision">${chip(p.accion, "grande")}</div>
    <div class="seccion"><h4>Acciones demostrables · por prioridad</h4><div class="candidatas">${candidatas}</div></div>
    ${lista("Datos críticos faltantes", p.faltantes)}
    ${lista("Contradicciones", p.contradicciones)}
    <div class="seccion"><h4>Derivación (por qué)</h4><div class="arbol">${pasos}</div>
      <div class="leyenda-arbol"><span><i class="etq regla">regla</i> se usó una regla</span><span><i class="etq hecho">hecho</i> dato del estado</span>
      <span><i class="etq calculo">cálculo</i> comparación</span><span><i class="etq negacion">no demostrable</i> negación por falla</span></div></div>
  </article>`;
}

function tarjetaLaya(l) {
  const cab = `<div class="agente-cabecera"><h3>Laya</h3><span class="agente-tipo">decisión tipada · multilingüe, sin entrenar</span>`;
  if (l.error) return `<article class="tarjeta">${cab}</div><div class="caja-error">${esc(l.error)}</div></article>`;
  const probs = l.probabilidades || {};
  const barras = ACCIONES.map((a) => {
    const v = probs[a] ?? 0;
    return `<div class="barra-fila ${a === l.accion ? "elegida" : ""}" style="--color-accion:var(--a-${a})" data-tip="${esc(a)}: ${pct(v)}${a === l.accion ? " · elegida" : ""}">
      <span class="nombre">${esc(a)}</span>
      <span class="barra-pista"><span class="barra-relleno" style="width:${(v * 100).toFixed(2)}%;display:block"></span></span>
      <span class="pct">${pct(v)}</span></div>`;
  }).join("");
  const e = l.estabilidad || { coinciden: 0, total: 0 };
  const ordenes = (l.por_orden || []).map((o) => `<tr><td>${chip(o.primera, "chica")}</td><td>${chip(o.eleccion, "chica")}</td><td class="num">${num(o.confianza)}</td></tr>`).join("");
  return `<article class="tarjeta">
    ${cab}<span class="tiempo">${l.tiempo_ms ?? "—"} ms</span></div>
    <div class="decision">${chip(l.accion, "grande")}</div>
    <div class="seccion"><h4>Probabilidad de cada acción · promedio de 5 órdenes</h4><div class="barras">${barras}</div></div>
    <div class="seccion metricas-laya">
      <div class="mini-metrica"><div class="rotulo">Confianza</div><div class="num">${num(l.confianza)}</div><div class="det">prob. de la elegida</div></div>
      <div class="mini-metrica"><div class="rotulo">Margen</div><div class="num">${num(l.margen)}</div><div class="det">vs. la 2.ª opción</div></div>
      <div class="mini-metrica"><div class="rotulo">Estabilidad</div><div class="num">${e.coinciden}<small class="sutil"> / ${e.total}</small></div><div class="det">órdenes que eligen lo mismo</div></div>
    </div>
    <p class="advertencia-laya">Resultado experimental: una probabilidad, no una demostración. Laya no ejecuta reglas: lee el texto y la descripción de cada acción.
      Con 5 acciones, una confianza cercana a 0,20 significa que prácticamente no distingue entre ellas.</p>
    <details class="plegable"><summary>Respuesta según el orden de las alternativas (sesgo de posición)</summary>
      <table class="datos estatica compacta"><thead><tr><th>Primera alternativa</th><th>Elige</th><th>Confianza</th></tr></thead><tbody>${ordenes}</tbody></table></details>
    <details class="plegable"><summary>Texto y pregunta que recibió Laya</summary>
      <pre class="texto-laya">${esc(l.texto_enviado)}</pre>
      <pre class="texto-laya" style="margin-top:8px">${esc(JSON.stringify(l.pregunta, null, 2))}</pre></details>
  </article>`;
}

function valorDiag(v) {
  if (v === null || v === undefined) return `<span class="sutil">—</span>`;
  if (v === true) return "sí";
  if (v === false) return "no";
  return esc(v);
}

function tarjetaDiagnostico(diag) {
  if (!diag || !Object.keys(diag).length) return "";
  const filas = Object.values(diag).map((d) => `<tr>
      <td>${esc(d.instruccion)}</td>
      <td><span class="etiqueta-tipo">${esc(d.tipo)}</span></td>
      <td>${valorDiag(d.laya)}${d.laya_p_si != null ? ` <span class="sutil num">P(sí) ${num(d.laya_p_si)}</span>` : ""}</td>
      <td>${valorDiag(d.prolog)} <span class="sutil mono chico">${esc(d.prolog_predicado)}</span></td>
      <td>${d.coincide == null ? `<span class="sutil">—</span>` : d.coincide ? `<span class="veredicto bien">${ICONO_BIEN}sí</span>` : `<span class="veredicto mal">${ICONO_MAL}no</span>`}</td>
    </tr>`).join("");
  return `<article class="tarjeta" style="margin-top:16px">
    <div class="tarjeta-titulo"><div><h3>Preguntas de diagnóstico <span class="sutil">· score y noul</span></h3>
      <p class="sutil">No deciden nada: muestran si Laya acierta pasos intermedios que Prolog obtiene con un hecho o una regla.</p></div></div>
    <div class="tabla-envoltura"><table class="datos estatica"><thead><tr><th>Pregunta a Laya</th><th>Tipo</th><th>Laya</th><th>Prolog</th><th>Coinciden</th></tr></thead>
    <tbody>${filas}</tbody></table></div></article>`;
}

/* ------------------------------------------------------------------ consola Prolog */
function pintarSugerencias() {
  const e = app.estado || {};
  const p = String(e.pedido ?? "p").toLowerCase();
  const v = String(e.vehiculo_asignado?.id ?? "v").toLowerCase();
  const decision = app.mostrado?.respuesta?.prolog?.accion || "despachar";
  const s = [
    `acciones_candidatas(${p}, L)`, `vehiculo_apto(${p}, V)`, `alternativa_apta(${p}, W)`,
    `por_que_no(vehiculo_apto(${p}, ${v}))`, `porque(${p}, ${decision})`, `explicar(${p})`,
    `contradiccion(${p}, Tipo)`, `falta_dato_critico(${p}, Dato)`,
  ];
  $("#sugerencias").innerHTML = s.map((q) => `<button type="button" class="sugerencia">${esc(q)}</button>`).join("");
  $("#entrada-consulta").placeholder = s[1];
}

async function consultar(texto) {
  texto = texto.trim();
  if (!texto || !app.jsonValido) return;
  $("#entrada-consulta").value = texto;
  let cuerpo;
  try {
    const r = await api("/api/consulta", { estado: app.estado, consulta: texto });
    const avisos = r.avisos?.length ? `<div class="caja-aviso">${esc(r.avisos.join("\n"))}</div>` : "";
    if (!r.ok) {
      cuerpo = `${avisos}<span class="error">${esc(r.error)}</span>`;
    } else {
      const salida = r.salida ? `${esc(r.salida)}\n` : "";
      const sols = r.soluciones || [];
      let res;
      if (!sols.length) res = `<span class="falso">false.</span>  <span class="sutil">no se puede demostrar con estos hechos y reglas</span>`;
      else if (sols.every((x) => !Object.keys(x).length)) res = `<span class="verdadero">true.</span>`;
      else {
        const vars = Object.keys(sols[0]);
        res = `<table><thead><tr>${vars.map((x) => `<th>${esc(x)}</th>`).join("")}</tr></thead><tbody>
          ${sols.map((x) => `<tr>${vars.map((k) => `<td>${esc(x[k])}</td>`).join("")}</tr>`).join("")}</tbody></table>
          <span class="sutil">${sols.length} solución${sols.length === 1 ? "" : "es"}${r.limite_alcanzado ? " (se muestran las primeras 25)" : ""}</span>`;
      }
      cuerpo = avisos + salida + res;
    }
  } catch (e) {
    cuerpo = `<span class="error">${esc(e.message)}</span>`;
  }
  const item = document.createElement("div");
  item.className = "salida-item";
  item.innerHTML = `<div class="consulta-eco">?- ${esc(texto)}.</div><div class="cuerpo">${cuerpo}</div>`;
  const salida = $("#salida-consulta");
  salida.prepend(item);
  while (salida.children.length > 6) salida.lastChild.remove();
}

/* ------------------------------------------------------------------ experimento (20 casos) */
async function ejecutarTodos() {
  if (app.corriendo) return;
  app.corriendo = true;
  irAVista("experimento");
  const corrida = { filas: app.casos.map((c) => ({ caso: c, r: null })), terminado: false };
  app.exp = corrida;
  for (const b of [$("#btn-todos"), $("#btn-todos-2")]) b.disabled = true;
  $("#btn-descargar").disabled = true;
  pintarCabecera();
  $("#progreso").classList.remove("oculto");
  pintarExperimento();
  for (const [i, fila] of corrida.filas.entries()) {
    $("#progreso-texto").textContent = `Ejecutando ${fila.caso.id} · ${i} de ${corrida.filas.length}`;
    $("#progreso-barra").style.width = `${(i / corrida.filas.length) * 100}%`;
    try {
      fila.r = await api("/api/ejecutar", { estado: fila.caso.estado, id_caso: fila.caso.id,
        esperada: fila.caso.decision_esperada });
      app.cache[fila.caso.id] = fila.r;
    } catch (e) {
      fila.error = e.message;
    }
    pintarExperimento();
    if (i === 0) actualizarServidor();
  }
  corrida.terminado = true;
  $("#progreso-barra").style.width = "100%";
  $("#progreso-texto").textContent = `Listo: ${corrida.filas.length} casos ejecutados`;
  app.corriendo = false;
  for (const b of [$("#btn-todos"), $("#btn-todos-2")]) b.disabled = false;
  $("#btn-descargar").disabled = false;
  pintarExperimento();
  pintarLista();
  mostrarResultadoGuardado();
  actualizarServidor();
}

function resumen(filas) {
  const hechas = filas.filter((f) => f.r);
  const n = hechas.length;
  const aciertosP = hechas.filter((f) => f.r.comparacion.prolog_correcto).length;
  const aciertosL = hechas.filter((f) => f.r.comparacion.laya_correcto).length;
  const acuerdo = hechas.filter((f) => f.r.comparacion.coinciden).length;
  const conf = (ok) => {
    const v = hechas.filter((f) => f.r.comparacion.laya_correcto === ok && f.r.laya.confianza != null).map((f) => f.r.laya.confianza);
    return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null;
  };
  return { n, aciertosP, aciertosL, acuerdo, confBien: conf(true), confMal: conf(false) };
}

function pintarExperimento() {
  const corrida = app.exp;
  if (!corrida) {
    $("#exp-metricas").innerHTML = `<div class="exp-vacio">Todavía no se ejecutan los 20 casos.
      Pulsa <b>Ejecutar los 20 casos</b>: cada caso se envía a Prolog y a Laya, y la tabla se llena a medida que responden.</div>`;
    $("#exp-tablas").innerHTML = "";
    $("#btn-descargar").disabled = true;
    return;
  }
  const s = resumen(corrida.filas);
  const pctDe = (a, n) => (n ? Math.round((a / n) * 100) : 0);
  $("#exp-metricas").innerHTML = `<div class="tiles">
    <div class="tile"><div class="rotulo">Prolog · aciertos</div><div class="num">${s.aciertosP}<small> / ${s.n}</small></div><div class="det">${pctDe(s.aciertosP, s.n)} % de los casos ejecutados</div></div>
    <div class="tile"><div class="rotulo">Laya · aciertos</div><div class="num">${s.aciertosL}<small> / ${s.n}</small></div><div class="det">${pctDe(s.aciertosL, s.n)} % · al azar: 20 %</div></div>
    <div class="tile"><div class="rotulo">Acuerdo entre agentes</div><div class="num">${s.acuerdo}<small> / ${s.n}</small></div><div class="det">misma acción en ambos</div></div>
    <div class="tile"><div class="rotulo">Confianza media de Laya</div><div class="num">${num(s.confBien)}</div>
      <div class="det">cuando acierta · cuando falla: ${num(s.confMal)}</div></div>
  </div>`;
  $("#btn-descargar").disabled = !corrida.terminado;

  const cats = app.servidor?.categorias || {};
  const filasCat = Object.entries(cats).map(([k, titulo]) => {
    const f = corrida.filas.filter((x) => x.caso.categoria === k && x.r);
    const total = corrida.filas.filter((x) => x.caso.categoria === k).length;
    const ap = f.filter((x) => x.r.comparacion.prolog_correcto).length;
    const al = f.filter((x) => x.r.comparacion.laya_correcto).length;
    const celda = (a) => `<span class="mini-barra"><i style="width:${total ? (a / total) * 100 : 0}%"></i></span><span class="num">${a} / ${total}</span>`;
    return `<tr><td>${esc(titulo)}</td><td>${celda(ap)}</td><td>${celda(al)}</td></tr>`;
  }).join("");

  const diagInfo = app.servidor?.diagnostico || {};
  const filasDiag = Object.entries(diagInfo).map(([qid, info]) => {
    const con = corrida.filas.filter((x) => x.r && x.r.diagnostico?.[qid]?.coincide != null);
    const ok = con.filter((x) => x.r.diagnostico[qid].coincide).length;
    return `<tr><td>${esc(info.pregunta.instructions)}<div class="sutil mono chico">${esc(info.prolog)}</div></td>
      <td><span class="etiqueta-tipo">${esc(info.pregunta.type)}</span></td>
      <td><span class="mini-barra"><i style="width:${con.length ? (ok / con.length) * 100 : 0}%"></i></span><span class="num">${ok} / ${con.length}</span></td></tr>`;
  }).join("");

  const filas = corrida.filas.map((f) => {
    const c = f.caso;
    if (!f.r) {
      return `<tr class="pendiente" data-id="${esc(c.id)}"><td class="num">${esc(c.id)}</td><td>${esc(cats[c.categoria] || c.categoria)}</td>
        <td>${chip(c.decision_esperada)}</td><td colspan="5">${f.error ? `<span class="veredicto mal">${esc(f.error)}</span>` : "…"}</td></tr>`;
    }
    const k = f.r.comparacion, e = f.r.laya.estabilidad;
    return `<tr data-id="${esc(c.id)}"><td class="num">${esc(c.id)}</td><td>${esc(cats[c.categoria] || c.categoria)}</td>
      <td>${chip(c.decision_esperada)}</td>
      <td><span class="celda-agente">${chip(f.r.prolog.accion)}${veredicto(k.prolog_correcto, ["", ""])}</span></td>
      <td><span class="celda-agente">${chip(f.r.laya.accion)}${veredicto(k.laya_correcto, ["", ""])}</span></td>
      <td class="num">${num(f.r.laya.confianza)}</td>
      <td class="num">${e ? `${e.coinciden}/${e.total}` : "—"}</td>
      <td>${k.coinciden ? `<span class="veredicto bien">${ICONO_BIEN}sí</span>` : `<span class="veredicto mal">${ICONO_MAL}no</span>`}</td></tr>`;
  }).join("");

  $("#exp-tablas").innerHTML = `<div class="dos-columnas">
    <div class="columna">
      <article class="tarjeta"><div class="tarjeta-titulo"><h3>Aciertos por categoría</h3></div>
        <div class="tabla-envoltura"><table class="datos estatica"><thead><tr><th>Categoría</th><th>Prolog</th><th>Laya</th></tr></thead><tbody>${filasCat}</tbody></table></div></article>
      <article class="tarjeta"><div class="tarjeta-titulo"><div><h3>Diagnóstico de Laya</h3><p class="sutil">Preguntas score y noul frente al hecho o la regla de Prolog</p></div></div>
        <div class="tabla-envoltura"><table class="datos estatica"><thead><tr><th>Pregunta</th><th>Tipo</th><th>Coinciden</th></tr></thead><tbody>${filasDiag}</tbody></table></div></article>
    </div>
    <article class="tarjeta"><div class="tarjeta-titulo"><h3>Resultados por caso</h3><span class="sutil">Clic en una fila para abrir el caso</span></div>
      <div class="tabla-envoltura"><table class="datos" id="tabla-resultados"><thead><tr><th>Caso</th><th>Categoría</th><th>Esperada</th><th>Prolog</th><th>Laya</th><th>Confianza</th><th title="Órdenes de las alternativas que eligen la misma acción">Estab.</th><th>Coinciden</th></tr></thead>
      <tbody>${filas}</tbody></table></div></article></div>`;
  $$("#tabla-resultados tbody tr").forEach((tr) => tr.addEventListener("click", () => {
    seleccionarCaso(tr.dataset.id);
    irAVista("caso");
  }));
}

function descargarCSV() {
  const corrida = app.exp;
  if (!corrida) return;
  const diagIds = Object.keys(app.servidor?.diagnostico || {});
  const columnas = ["id", "categoria", "descripcion", "esperada", "prolog", "prolog_correcto", "laya", "laya_correcto",
    "laya_confianza", "laya_estabilidad", ...ACCIONES.map((a) => `p_${a}`), "coinciden", ...diagIds.map((q) => `diag_${q}_coincide`)];
  const csv = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const lineas = [columnas.join(",")];
  for (const f of corrida.filas) {
    if (!f.r) continue;
    const c = f.caso, r = f.r;
    lineas.push([c.id, c.categoria, c.descripcion, c.decision_esperada, r.prolog.accion, r.comparacion.prolog_correcto,
      r.laya.accion, r.comparacion.laya_correcto, r.laya.confianza,
      r.laya.estabilidad ? `${r.laya.estabilidad.coinciden}/${r.laya.estabilidad.total}` : "",
      ...ACCIONES.map((a) => r.laya.probabilidades?.[a]), r.comparacion.coinciden,
      ...diagIds.map((q) => r.diagnostico?.[q]?.coincide)].map(csv).join(","));
  }
  const blob = new Blob(["﻿" + lineas.join("\n")], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "resultados_20_casos.csv";
  a.click();
  URL.revokeObjectURL(a.href);
}

/* ------------------------------------------------------------------ vistas, tooltips, inicio */
function irAVista(vista) {
  app.vista = vista;
  for (const b of $$(".pestana")) b.classList.toggle("activa", b.dataset.vista === vista);
  $("#vista-caso").classList.toggle("oculto", vista !== "caso");
  $("#vista-experimento").classList.toggle("oculto", vista !== "experimento");
  if (vista === "experimento") pintarExperimento();
}

function activarTooltips(raiz) {
  const tip = $("#tooltip");
  $$("[data-tip]", raiz).forEach((el) => {
    el.addEventListener("mousemove", (ev) => {
      tip.textContent = el.dataset.tip;
      tip.classList.remove("oculto");
      const x = Math.min(ev.clientX + 14, innerWidth - tip.offsetWidth - 8);
      tip.style.left = `${x}px`;
      tip.style.top = `${ev.clientY + 16}px`;
    });
    el.addEventListener("mouseleave", () => tip.classList.add("oculto"));
  });
}

async function iniciar() {
  aplicarTemaGuardado();
  $("#btn-tema").addEventListener("click", alternarTema);
  $$(".pestana").forEach((b) => b.addEventListener("click", () => irAVista(b.dataset.vista)));
  $$("#tabs-estado button").forEach((b) => b.addEventListener("click", () => cambiarTab(b.dataset.tab)));
  $("#lista").addEventListener("click", (ev) => {
    const b = ev.target.closest(".item-caso");
    if (b && b.dataset.id !== "NUEVO") seleccionarCaso(b.dataset.id);
  });
  $("#btn-nuevo").addEventListener("click", casoNuevo);
  $("#btn-restaurar").addEventListener("click", () => {
    app.estado = copia(app.original);
    app.esperadaManual = "";
    pintarEstado();
    mostrarResultadoGuardado();
  });
  $("#btn-ejecutar").addEventListener("click", ejecutarCaso);
  $("#btn-todos").addEventListener("click", ejecutarTodos);
  $("#btn-todos-2").addEventListener("click", ejecutarTodos);
  $("#btn-descargar").addEventListener("click", descargarCSV);
  $("#editor-json").addEventListener("input", alEditarJSON);
  $("#form-consulta").addEventListener("submit", (ev) => { ev.preventDefault(); consultar($("#entrada-consulta").value); });
  $("#sugerencias").addEventListener("click", (ev) => {
    const b = ev.target.closest(".sugerencia");
    if (b) consultar(b.textContent);
  });
  document.addEventListener("keydown", (ev) => {
    if ((ev.ctrlKey || ev.metaKey) && ev.key === "Enter" && app.vista === "caso") { ev.preventDefault(); ejecutarCaso(); }
  });

  // Enlaces directos:  /#C09  abre un caso · ?ejecutar lo ejecuta · ?todos corre los 20
  //                    ?tema=light|dark · ?vista=experimento
  const params = new URLSearchParams(location.search);
  if (["light", "dark"].includes(params.get("tema"))) document.documentElement.dataset.theme = params.get("tema");

  await actualizarServidor();
  if (app.servidor) {
    ACCIONES = app.servidor.acciones;
  }
  pintarCabecera();
  try {
    app.casos = await api("/api/casos");
  } catch (e) {
    $("#lista").innerHTML = `<div class="caja-error" style="margin:12px">${esc(e.message)}</div>`;
    return;
  }
  const desdeUrl = decodeURIComponent(location.hash.slice(1)).toUpperCase();
  seleccionarCaso(app.casos.some((c) => c.id === desdeUrl) ? desdeUrl : app.casos[0].id);
  if (params.get("vista") === "experimento") irAVista("experimento");
  if (params.has("todos")) ejecutarTodos();
  else if (params.has("ejecutar")) ejecutarCaso();
}

iniciar();
