// Front-end mínimo que consome a API. Usa textContent (nunca innerHTML com dados) -> evita XSS.
const API = "/api/registros";
const NOMES = { agua: "Água", energia: "Energia", alimento: "Alimento" };
const $ = (id) => document.getElementById(id);

function mostrarMensagem(texto, ok) {
  const p = $("mensagem");
  p.textContent = texto;
  p.className = ok ? "ok" : "falha";
}

async function chamarApi(url, opcoes = {}) {
  const resp = await fetch(url, { headers: { "Content-Type": "application/json" }, ...opcoes });
  if (resp.status === 204) return null;
  const dados = await resp.json();
  if (!resp.ok) throw new Error(dados.erro || "Erro inesperado.");
  return dados;
}

function celula(texto, classe) {
  const td = document.createElement("td");
  td.textContent = texto;
  if (classe) td.className = classe;
  return td;
}

function botao(texto, classe, acao) {
  const b = document.createElement("button");
  b.textContent = texto;
  b.className = "pequeno " + classe;
  b.addEventListener("click", acao);
  return b;
}

async function carregarRegistros() {
  const filtro = $("filtro").value;
  const url = filtro ? `${API}?categoria=${encodeURIComponent(filtro)}` : API;
  const corpo = $("corpo-tabela");
  try {
    const registros = await chamarApi(url);
    corpo.replaceChildren();
    if (registros.length === 0) {
      const tr = document.createElement("tr");
      tr.appendChild(celula("Nenhum registro ainda."));
      corpo.appendChild(tr);
    }
    for (const r of registros) {
      const tr = document.createElement("tr");
      const a = r.analise;
      tr.appendChild(celula(r.apelido));
      tr.appendChild(celula(NOMES[r.categoria]));
      tr.appendChild(celula(`${r.quantidade} ${r.unidade}`));
      tr.appendChild(celula(r.mes_referencia));
      tr.appendChild(celula(r.pessoas));
      tr.appendChild(celula(`${a.percentual_da_referencia}% (ref. ${a.referencia})`, a.acima ? "acima" : "dentro"));
      tr.appendChild(celula(a.dica));
      const acoes = document.createElement("td");
      acoes.appendChild(botao("Editar", "secundario", () => editar(r)));
      acoes.appendChild(document.createTextNode(" "));
      acoes.appendChild(botao("Excluir", "perigo", () => excluir(r.id)));
      tr.appendChild(acoes);
      corpo.appendChild(tr);
    }
  } catch (e) {
    mostrarMensagem(e.message, false);
  }
}

async function carregarResumo() {
  try {
    const resumo = await chamarApi("/api/resumo");
    const caixa = $("resumo");
    caixa.replaceChildren();
    for (const [cat, info] of Object.entries(resumo)) {
      const div = document.createElement("div");
      const titulo = document.createElement("span");
      titulo.textContent = NOMES[cat];
      const total = document.createElement("strong");
      total.textContent = `${info.total} ${info.unidade}`;
      const detalhe = document.createElement("small");
      detalhe.textContent = `${info.registros} registro(s), ${info.acima_da_referencia} acima da referência`;
      div.append(titulo, total, detalhe);
      caixa.appendChild(div);
    }
  } catch (e) {
    mostrarMensagem(e.message, false);
  }
}

async function carregarClima() {
  const lista = $("alertas-clima");
  try {
    const clima = await chamarApi("/api/clima");
    lista.replaceChildren();
    for (const alerta of clima.alertas) {
      const li = document.createElement("li");
      li.textContent = alerta;
      lista.appendChild(li);
    }
  } catch (e) {
    lista.replaceChildren();
    const li = document.createElement("li");
    li.textContent = e.message;
    lista.appendChild(li);
  }
}

function lerFormulario() {
  return {
    apelido: $("apelido").value.trim(),
    categoria: $("categoria").value,
    quantidade: parseFloat($("quantidade").value),
    mes_referencia: $("mes").value,
    pessoas: parseInt($("pessoas").value, 10),
  };
}

function editar(r) {
  $("id-edicao").value = r.id;
  $("apelido").value = r.apelido;
  $("categoria").value = r.categoria;
  $("quantidade").value = r.quantidade;
  $("mes").value = r.mes_referencia;
  $("pessoas").value = r.pessoas;
  $("titulo-form").textContent = "Editar registro";
  $("btn-cancelar").hidden = false;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function limparFormulario() {
  $("form-registro").reset();
  $("id-edicao").value = "";
  $("titulo-form").textContent = "Novo registro";
  $("btn-cancelar").hidden = true;
}

async function excluir(id) {
  if (!confirm("Excluir este registro?")) return;
  try {
    await chamarApi(`${API}/${id}`, { method: "DELETE" });
    mostrarMensagem("Registro excluído.", true);
    atualizarTela();
  } catch (e) {
    mostrarMensagem(e.message, false);
  }
}

$("form-registro").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const id = $("id-edicao").value;
  try {
    const r = await chamarApi(id ? `${API}/${id}` : API, {
      method: id ? "PUT" : "POST",
      body: JSON.stringify(lerFormulario()),
    });
    const aviso = r.analise.acima ? " Atenção: acima da referência!" : "";
    mostrarMensagem((id ? "Registro atualizado." : "Registro criado.") + aviso, !r.analise.acima);
    limparFormulario();
    atualizarTela();
  } catch (e) {
    mostrarMensagem(e.message, false);
  }
});

$("btn-cancelar").addEventListener("click", limparFormulario);
$("filtro").addEventListener("change", carregarRegistros);

function atualizarTela() {
  carregarRegistros();
  carregarResumo();
}

atualizarTela();
carregarClima();
