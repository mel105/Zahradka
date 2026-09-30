"use strict";
/* Záhradka – webové rozhranie (bez knižníc) */
const APP_VERZIA = "1.1.0";
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const app = $("#app");
let I = null;               // /api/init
let PL = {};                // plodiny podľa id
const S = { datum: null, planRok: new Date().getFullYear(), sel: null, kresli: false, typObj: "zahon",
            vysRok: new Date().getFullYear(), dnFilter: {}, fotoFilter: {}, plodinaFilter: "", plodinaTyp: "", navod: null };

const TABS = [
  ["nastenka", "Nástenka"], ["plan", "Plán"], ["striedanie", "Striedanie"], ["pestujem", "Čo pestujem"], ["dennik", "Denník"],
  ["fotky", "Fotky"], ["plodiny", "Plodiny"], ["navody", "Návody"], ["nastavenia", "Nastavenia"],
];
const MESIACE = ["január", "február", "marec", "apríl", "máj", "jún", "júl", "august", "september", "október", "november", "december"];
const MES_KR = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"];
const DNI = ["ne", "po", "ut", "st", "št", "pi", "so"];
const TYP_IKONA = { sejba: "🌱", vysadba: "🪴", nakup: "🛒", priprava: "🧰", hnojenie: "💩", ochrana: "🛡️",
  rez: "✂️", starostlivost: "🤲", zber: "🧺", info: "ℹ️", polievanie: "💧", praca: "🧰", pozorovanie: "👀" };
const TYP_PLODINY = { zelenina: "Zelenina", ovocie: "Ovocie", bylinka: "Bylinky", zelene_hnojenie: "Zelené hnojenie" };

// ---------------------------------------------------------------- pomocné
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
function fmtD(iso, rok = true) {
  if (!iso) return "";
  const [y, m, d] = iso.slice(0, 10).split("-").map(Number);
  return rok ? `${d}. ${m}. ${y}` : `${d}. ${m}.`;
}
function isoDate(d) { return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; }
function dnes() { return isoDate(new Date()); }
function addDays(iso, n) { const d = new Date(iso + "T12:00:00"); d.setDate(d.getDate() + n); return isoDate(d); }
function toast(msg, err = false) {
  const el = document.createElement("div");
  el.textContent = msg; if (err) el.className = "err";
  $("#toast").appendChild(el);
  setTimeout(() => el.remove(), err ? 7000 : 3000);
}
async function api(path, body) {
  const opt = body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  let r;
  try { r = await fetch(path, opt); } catch (e) { toast("Server neodpovedá – beží Záhradka?", true); throw e; }
  const j = await r.json().catch(() => ({}));
  if (!r.ok) { toast(j.chyba || `Chyba ${r.status}`, true); throw new Error(j.chyba || r.status); }
  return j;
}
function modal(html, wide = false) {
  $("#modal-body").innerHTML = html;
  $(".modal-box").classList.toggle("wide", wide);
  $("#modal").classList.remove("hidden");
}
function zavri() { $("#modal").classList.add("hidden"); $("#modal-body").innerHTML = ""; }
$("#modal").addEventListener("click", (e) => { if (e.target.id === "modal" || e.target.classList.contains("modal-x")) zavri(); });
document.addEventListener("keydown", (e) => { if (e.key === "Escape") zavri(); });
function formData(form) {
  const o = {};
  for (const el of form.elements) {
    if (!el.name) continue;
    o[el.name] = el.type === "checkbox" ? (el.checked ? "1" : "0") : el.value;
  }
  return o;
}
function md(text) {
  const inl = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
  let html = "", ul = false, p = [];
  const flushP = () => { if (p.length) { html += `<p>${inl(p.join(" "))}</p>`; p = []; } };
  const flushUl = () => { if (ul) { html += "</ul>"; ul = false; } };
  for (const raw of text.trim().split("\n")) {
    const l = raw.trim();
    if (l.startsWith("## ")) { flushP(); flushUl(); html += `<h3>${inl(l.slice(3))}</h3>`; }
    else if (l.startsWith("- ")) { flushP(); if (!ul) { html += "<ul>"; ul = true; } html += `<li>${inl(l.slice(2))}</li>`; }
    else if (!l) { flushP(); flushUl(); }
    else { flushUl(); p.push(l); }
  }
  flushP(); flushUl();
  return html;
}
function wxIkona(k) {
  if (k === 0) return "☀️"; if (k <= 2) return "🌤️"; if (k === 3) return "☁️"; if (k <= 48) return "🌫️";
  if (k <= 57) return "🌦️"; if (k <= 67) return "🌧️"; if (k <= 77) return "🌨️"; if (k <= 82) return "🌦️";
  if (k <= 86) return "🌨️"; return "⛈️";
}
const zamknute = () => { try { return JSON.parse(I.nastavenia.uzamknute || "[]").map(Number); } catch { return []; } };
const jeZamknuty = (rok) => zamknute().includes(+rok);
const zahonMeno = (id) => (I.zahony.find((z) => z.id == id) || {}).nazov || "";
const plodinaMeno = (id) => (PL[id] || {}).nazov || id || "";
const kratko = (id) => plodinaMeno(id).split(" (")[0];
const platiVRoku = (z, rok) => !rok || ((!z.od_roku || z.od_roku <= rok) && (!z.do_roku || z.do_roku >= rok));
function optZahony(sel, prazdne = "— bez záhona —", len = true, rok = null) {
  const zz = I.zahony.filter((z) => (!len || ["zahon", "ker", "ine", "trava"].includes(z.typ)) && (platiVRoku(z, rok) || z.id == sel));
  return `<option value="">${prazdne}</option>` + zz.map((z) => `<option value="${z.id}" ${z.id == sel ? "selected" : ""}>${esc(z.nazov)}</option>`).join("");
}
function optPlodiny(sel, prazdne = "— vyber plodinu —") {
  let h = `<option value="">${prazdne}</option>`;
  for (const [t, n] of Object.entries(TYP_PLODINY)) {
    h += `<optgroup label="${n}">` + I.plodiny.filter((p) => p.typ === t)
      .map((p) => `<option value="${p.id}" ${p.id === sel ? "selected" : ""}>${esc(p.nazov)}</option>`).join("") + "</optgroup>";
  }
  return h;
}
const opts = (obj, sel) => Object.entries(obj).map(([k, v]) => `<option value="${k}" ${k === sel ? "selected" : ""}>${esc(v)}</option>`).join("");

async function reloadInit() {
  I = await api("/api/init");
  PL = Object.fromEntries(I.plodiny.map((p) => [p.id, p]));
  $("#nazov").textContent = I.nastavenia.nazov || "Záhradka";
  document.title = I.nastavenia.nazov || "Záhradka";
  if (I.verzia !== APP_VERZIA) {
    app.insertAdjacentHTML("beforebegin", `<div class="alert alarm" style="max-width:1200px;margin:10px auto">Beží iná verzia servera (${esc(I.verzia)}) ako stránky (${APP_VERZIA}). Klikni znova na ikonu Záhradka a potom Ctrl+F5.</div>`);
  }
}

// ---------------------------------------------------------------- router
function route() {
  zavri();
  const tab = (location.hash.slice(1).split("/")[0]) || "nastenka";
  $("#nav").innerHTML = TABS.map(([id, n]) => `<a href="#${id}" class="${id === tab ? "on" : ""}">${n}</a>`).join("");
  const f = { nastenka: rNastenka, plan: rPlan, striedanie: rStriedanie, pestujem: rPestujem, dennik: rDennik, fotky: rFotky,
              plodiny: rPlodiny, navody: rNavody, nastavenia: rNastavenia }[tab] || rNastenka;
  f().catch((e) => { console.error(e); app.innerHTML = `<div class="alert alarm">Chyba: ${esc(e.message)}</div>`; });
}
window.addEventListener("hashchange", route);

// ================================================================ NÁSTENKA
async function rNastenka() {
  const d = S.datum || dnes();
  const n = await api("/api/nastenka?datum=" + d);
  const dt0 = new Date(n.datum + "T12:00:00");
  const jeDnes = n.datum === dnes();
  let h = `<div class="row between"><h1>${jeDnes ? "Dnes" : DNI[dt0.getDay()]} ${fmtD(n.datum)} · ${n.iso_tyzden}. týždeň · ${MESIACE[n.mesiac - 1]}</h1>
    <div class="row"><button data-w="-7">◀ týždeň</button><button data-w="0">Dnes</button><button data-w="7">týždeň ▶</button></div></div>`;

  if (!n.pestujem && !I.zahony.length) {
    h += `<div class="alert info">👋 Začni tu: <b>1.</b> v <a href="#plan">Pláne</a> nakresli záhony, <b>2.</b> v <a href="#pestujem">Čo pestujem</a> pridaj plodiny (aj tie, ktoré len plánuješ). Úlohy sa potom vyberú podľa nich. Kým nič nepridáš, vidíš len všeobecné úlohy.</div>`;
  } else if (!n.pestujem) {
    h += `<div class="alert info">Pridaj plodiny v <a href="#pestujem">Čo pestujem</a> – úlohy sa vyberú podľa nich.</div>`;
  }

  // počasie
  const wx = n.pocasie || {};
  const dni = (wx.dni || []).filter((x) => x.datum >= dnes()).slice(0, 7);
  h += `<div class="card"><div class="row between"><h2>Počasie · ${esc(I.nastavenia.miesto)}</h2>
        <button class="link" id="wx-ref" title="Obnoviť predpoveď">↻ obnoviť</button></div>`;
  if (wx.chyba) h += `<div class="alert varovanie">${esc(wx.chyba)}</div>`;
  if (dni.length) {
    h += `<div class="wx">` + dni.map((x) => {
      const dd = new Date(x.datum + "T12:00:00");
      return `<div class="${x.datum === dnes() ? "today" : ""}"><b>${x.datum === dnes() ? "dnes" : DNI[dd.getDay()]}</b> ${dd.getDate()}.${dd.getMonth() + 1}.
        <div class="e">${wxIkona(x.kod)}</div><div>${Math.round(x.tmax)}° / <span class="tmin ${x.tmin <= 2 ? "frost" : ""}">${Math.round(x.tmin)}°</span></div>
        <div class="muted">${x.zrazky ? x.zrazky.toFixed(1) + " mm" : "—"}${x.pravd ? " · " + x.pravd + " %" : ""}</div></div>`;
    }).join("") + `</div>`;
  }
  if (wx.ts) h += `<div class="muted small" style="margin-top:6px">Open-Meteo · aktualizované ${esc(wx.ts.replace("T", " ").slice(0, 16))}</div>`;
  h += (n.upozornenia || []).map((u) => `<div class="alert ${u.uroven}"><span>${u.ikona}</span><span>${esc(u.text)}</span></div>`).join("");
  h += `</div>`;

  h += `<div class="grid2"><div>`;
  h += `<div class="card"><h2>Tento týždeň <span class="muted small">${fmtD(n.tyzden_od, false)} – ${fmtD(n.tyzden_do)}</span></h2>${ulohy(n.ulohy_tyzden, "Tento týždeň nič konkrétne – ideálny čas pozrieť Návody alebo si oddýchnuť 🙂")}</div>`;
  h += `<div class="card"><h2>Tento mesiac a priebežne</h2>${ulohy(n.ulohy_mesiac, "Nič ďalšie.")}</div>`;
  h += `</div><div>`;
  h += `<div class="card"><h2>🛒 Kúpiť a pripraviť <span class="muted small">najbližšie 4 týždne</span></h2>`;
  h += n.nakup.length ? `<ul class="tasks">` + n.nakup.map((x) => `<li><span class="ic">▫️</span><span class="t">${esc(x.vec)} <span class="muted small">– ${x.pre.map(esc).join(", ")}</span></span></li>`).join("") + `</ul>` : `<div class="empty">Nič netreba.</div>`;
  h += `</div>`;
  h += `<div class="card"><h2>Čo príde <span class="muted small">ďalších ~5 týždňov</span></h2>${ulohy(n.ulohy_buduce, "Nič naplánované.", false)}</div>`;
  h += `<div class="card"><div class="row between"><h2>Denník</h2><button class="primary" id="dn-add">+ Zápis</button></div>`;
  h += n.dennik.length ? dennikTab(n.dennik, false) : `<div class="empty">Zatiaľ prázdny. Odškrtnuté úlohy sa sem zapíšu samy.</div>`;
  h += `</div></div></div>`;
  app.innerHTML = h;

  $$("[data-w]").forEach((b) => b.onclick = () => { const w = +b.dataset.w; S.datum = w ? addDays(n.datum, w) : null; rNastenka(); });
  $("#wx-ref").onclick = async () => { $("#wx-ref").innerHTML = `<span class="spin"></span>`; await api("/api/pocasie?refresh=1"); rNastenka(); };
  $("#dn-add").onclick = () => dennikForm({}, rNastenka);
  bindUlohy([...n.ulohy_tyzden, ...n.ulohy_mesiac], rNastenka);
}

function ulohy(list, prazdne, checkable = true) {
  if (!list.length) return `<div class="empty">${prazdne}</div>`;
  return `<ul class="tasks">` + list.map((u) => {
    const meta = [];
    if (u.meskanie) meta.push(`<span class="tag warn">zmeškané? do ${u.do_txt}</span>`);
    else if (u.opak === "tyzden") meta.push(`<span class="tag">každý týždeň do ${u.do_txt}</span>`);
    else if (u.opak === "14dni") meta.push(`<span class="tag">každé 2 týždne do ${u.do_txt}</span>`);
    else meta.push(`<span class="tag">${u.od_txt} – ${u.do_txt}</span>`);
    (u.zahony || []).filter(Boolean).forEach((z) => meta.push(`<span class="tag green">${esc(z)}</span>`));
    if (u.pid) meta.push(`<a href="#plodiny/${u.pid}" class="small">o plodine</a>`);
    const cb = checkable && u.checkable !== false ? `<input type="checkbox" data-k="${esc(u.key)}" ${u.hotovo ? "checked" : ""}>` : "";
    return `<li class="${u.hotovo ? "done" : ""}">${cb}<span class="ic">${TYP_IKONA[u.typ] || "•"}</span><div class="t"><div class="txt">${esc(u.text)}</div><div class="meta">${meta.join(" ")}</div></div></li>`;
  }).join("") + `</ul>`;
}
function bindUlohy(list, po) {
  const m = Object.fromEntries(list.map((u) => [u.key, u]));
  $$("input[data-k]").forEach((cb) => cb.onchange = async () => {
    const u = m[cb.dataset.k];
    await api("/api/hotovo", { key: u.key, hotovo: cb.checked, text: u.text, typ: u.typ, pid: u.pid, nastav: u.nastav, zahon: (u.zahony || [])[0] || "" });
    if (cb.checked && u.nastav) toast(`Výsadba prepnutá na „${I.stavy[u.nastav]}“ s dnešným dátumom.`);
    po();
  });
}

// ================================================================ PLÁN
async function rPlan() {
  const d = await api("/api/plan?rok=" + S.planRok);
  I.zahony = d.vsetky;
  const W = +I.nastavenia.sirka || 10, H = +I.nastavenia.dlzka || 20;
  const roky = [S.planRok - 2, S.planRok - 1, S.planRok, S.planRok + 1];
  const rokOpt = roky.map((r) => `<option ${r === S.planRok ? "selected" : ""}>${r}${jeZamknuty(r) ? " 🔒" : ""}</option>`).join("");
  const cmpOpt = `<option value="">—</option>` + [S.planRok - 3, ...roky].filter((r) => r !== S.planRok)
    .map((r) => `<option value="${r}" ${r === S.porovnaj ? "selected" : ""}>${r}</option>`).join("");
  const zam = d.zamknute;
  if (zam) S.kresli = false;
  let h = `<div class="row between"><h1>Plán záhrady</h1><div class="row">
      <label style="margin:0">Rok</label><select id="p-rok">${rokOpt}</select>
      <label style="margin:0">porovnať s</label><select id="p-cmp">${cmpOpt}</select>
      ${zam ? "" : `<select id="p-typ">${opts(I.typy_zahonov, S.typObj)}</select>
      <button id="p-kresli" class="${S.kresli ? "primary" : ""}">${S.kresli ? "Ťahaj myšou na pláne…" : "+ Nakresliť"}</button>`}
      <button id="p-lock" title="${zam ? "Odomknúť rok" : "Uzamknúť rok – plán a výsadby sa už nebudú meniť"}">${zam ? "🔓 Odomknúť" : "🔒 Uzamknúť"} ${S.planRok}</button></div></div>
    ${zam ? `<div class="alert info small">🔒 Rok ${S.planRok} je uzamknutý: plán je snímka z času uzamknutia, výsadby sa nedajú pridávať ani presúvať (stav, množstvo a poznámku zmeniť môžeš).</div>` : ""}`;
  if (S.porovnaj) {
    const d2 = await api("/api/plan?rok=" + S.porovnaj);
    h += `<div class="grid2"><div class="plan-wrap"><h2 style="text-align:center">${S.planRok}${zam ? " 🔒" : ""}</h2>${planSvg(d, W, H, "p-svg")}</div>
      <div class="plan-wrap"><h2 style="text-align:center">${S.porovnaj}${d2.zamknute ? " 🔒" : ""}</h2>${planSvg(d2, W, H, "p-svg2", false)}</div></div>
      <div id="p-side" class="grid2" style="margin-top:14px"></div>`;
  } else {
    h += `<div class="grid-side"><div class="plan-wrap">${planSvg(d, W, H, "p-svg")}</div><div id="p-side"></div></div>`;
  }
  app.innerHTML = h;
  $("#p-rok").onchange = (e) => { S.planRok = +e.target.value; if (S.porovnaj === S.planRok) S.porovnaj = null; rPlan(); };
  $("#p-cmp").onchange = (e) => { S.porovnaj = e.target.value ? +e.target.value : null; rPlan(); };
  if (!zam) {
    $("#p-typ").onchange = (e) => { S.typObj = e.target.value; };
    $("#p-kresli").onclick = () => { S.kresli = !S.kresli; S.sel = null; rPlan(); };
  }
  $("#p-lock").onclick = async () => {
    const msg = zam ? `Odomknúť rok ${S.planRok}? Plán sa znova bude zobrazovať podľa aktuálnych objektov.`
                    : `Uzamknúť rok ${S.planRok}? Uloží sa snímka plánu a výsadby roka sa už nebudú dať presúvať.`;
    if (!confirm(msg)) return;
    await api("/api/zamknut", { rok: S.planRok, zamknut: !zam });
    await reloadInit(); rPlan();
  };
  planInterakcia(d, W, H, zam);
  planSide(d, zam);
}

function planSvg(d, W, H, id = "p-svg", hlavny = true) {
  const pad = 0.8;
  const pod = {};
  d.vysadby.filter((v) => v.stav !== "ukoncene").forEach((v) => { (pod[v.zahon_id] = pod[v.zahon_id] || []).push(kratko(v.plodina)); });
  let s = `<svg id="${id}" class="plan ${hlavny && S.kresli ? "draw" : ""}" viewBox="${-pad} ${-pad} ${W + 2 * pad} ${H + 2 * pad}" xmlns="http://www.w3.org/2000/svg">`;
  s += `<rect x="0" y="0" width="${W}" height="${H}" fill="var(--soil)" stroke="var(--muted)" stroke-width="0.04"/>`;
  for (let x = 1; x < W; x++) s += `<line x1="${x}" y1="0" x2="${x}" y2="${H}" stroke="var(--grid)" stroke-width="0.02"/>`;
  for (let y = 1; y < H; y++) s += `<line x1="0" y1="${y}" x2="${W}" y2="${y}" stroke="var(--grid)" stroke-width="0.02"/>`;
  s += `<text x="${W / 2}" y="${-0.25}" font-size="0.3" text-anchor="middle" fill="var(--muted)">${W} m</text>`;
  s += `<text x="${-0.25}" y="${H / 2}" font-size="0.3" text-anchor="middle" transform="rotate(-90 ${-0.25} ${H / 2})">${H} m</text>`;
  const juh = I.nastavenia.juh;
  const jp = { dole: [W / 2, H + 0.55], hore: [W / 2, -0.5], vlavo: [-0.55, 0.4], vpravo: [W + 0.55, 0.4] }[juh] || [W / 2, H + 0.55];
  s += `<text x="${jp[0]}" y="${jp[1]}" font-size="0.35" text-anchor="middle" font-weight="700">☀ juh</text>`;
  for (const z of d.zahony) {
    const sel = hlavny && S.sel == z.id ? "sel" : "";
    s += `<g data-id="${z.id}"><rect class="obj ${sel}" data-id="${z.id}" x="${z.x}" y="${z.y}" width="${z.w}" height="${z.h}" rx="0.08" fill="var(--z-${z.typ})"/>`;
    const lines = [z.nazov, ...(pod[z.id] || [])];
    const najdlhsi = Math.max(...lines.map((t) => String(t).length));
    const fs = Math.max(0.14, Math.min(0.4, Math.min(z.w, z.h) / 3.2, (z.w - 0.1) / (najdlhsi * 0.6)));
    const maxL = Math.max(1, Math.floor((z.h - 0.1) / (fs * 1.2)));
    const show = lines.length > maxL ? [...lines.slice(0, maxL - 1), `+${lines.length - maxL + 1}`] : lines;
    show.forEach((t, i) => {
      s += `<text x="${z.x + z.w / 2}" y="${z.y + fs * 1.1 + i * fs * 1.2}" font-size="${i ? fs * 0.85 : fs}" text-anchor="middle" font-weight="${i ? 400 : 700}">${esc(t)}</text>`;
    });
    s += `</g>`;
  }
  if (hlavny) s += `<rect id="p-new" x="0" y="0" width="0" height="0" fill="none" stroke="var(--alarm)" stroke-width="0.06" stroke-dasharray="0.15 0.1" visibility="hidden"/>`;
  return s + `</svg>`;
}

function planInterakcia(d, W, H, zam = false) {
  const svg = $("#p-svg");
  const pt = (e) => { const p = svg.createSVGPoint(); p.x = e.clientX; p.y = e.clientY; return p.matrixTransform(svg.getScreenCTM().inverse()); };
  const snap = (v) => Math.round(v * 10) / 10;
  let drag = null;
  svg.addEventListener("pointerdown", (e) => {
    const p = pt(e);
    if (S.kresli) {
      drag = { mode: "new", x0: snap(p.x), y0: snap(p.y) };
    } else {
      const id = e.target.dataset && e.target.dataset.id;
      if (!id) { S.sel = null; rPlan(); return; }
      const z = d.zahony.find((q) => q.id == id);
      S.sel = z.id;
      $$("rect.obj", svg).forEach((r) => r.classList.toggle("sel", r.dataset.id == id));
      planSide(d, zam);
      if (zam) return;
      drag = { mode: "move", z, dx: p.x - z.x, dy: p.y - z.y, moved: false, g: e.target.parentNode };
    }
    svg.setPointerCapture(e.pointerId);
  });
  svg.addEventListener("pointermove", (e) => {
    if (!drag) return;
    const p = pt(e);
    if (drag.mode === "new") {
      const r = $("#p-new");
      const x = Math.min(drag.x0, snap(p.x)), y = Math.min(drag.y0, snap(p.y));
      r.setAttribute("x", x); r.setAttribute("y", y);
      r.setAttribute("width", Math.abs(snap(p.x) - drag.x0)); r.setAttribute("height", Math.abs(snap(p.y) - drag.y0));
      r.setAttribute("visibility", "visible");
    } else {
      const nx = Math.max(0, Math.min(W - drag.z.w, snap(p.x - drag.dx)));
      const ny = Math.max(0, Math.min(H - drag.z.h, snap(p.y - drag.dy)));
      if (nx !== drag.z.x || ny !== drag.z.y) {
        drag.g.setAttribute("transform", `translate(${nx - drag.z.x} ${ny - drag.z.y})`);
        drag.nx = nx; drag.ny = ny; drag.moved = true;
      }
    }
  });
  svg.addEventListener("pointerup", async () => {
    if (!drag) return;
    const dd = drag; drag = null;
    if (dd.mode === "new") {
      const r = $("#p-new");
      const w = +r.getAttribute("width"), h = +r.getAttribute("height");
      if (w < 0.2 || h < 0.2) { r.setAttribute("visibility", "hidden"); return; }
      const x = Math.max(0, +r.getAttribute("x")), y = Math.max(0, +r.getAttribute("y"));
      const pocet = d.zahony.filter((z) => z.typ === S.typObj).length + 1;
      const meno = S.typObj === "zahon" ? `Záhon ${pocet}` : I.typy_zahonov[S.typObj].split(" /")[0].replace(/^./, (c) => c.toUpperCase());
      const res = await api("/api/zahon", { nazov: meno, typ: S.typObj, x, y, w: Math.min(w, W - x), h: Math.min(h, H - y), od_roku: S.planRok });
      S.kresli = false; S.sel = res.id;
      await rPlan();
      const inp = $("#z-nazov"); if (inp) { inp.focus(); inp.select(); }
    } else if (dd.moved) {
      await api("/api/zahon", { ...dd.z, x: dd.nx, y: dd.ny });
      rPlan();
    }
  });
}

async function planSide(d, zam = false) {
  const side = $("#p-side");
  const W = +I.nastavenia.sirka, H = +I.nastavenia.dlzka;
  if (!S.sel) {
    side.innerHTML = `<div class="card"><h2>Ako na to</h2>
      <p class="small">Parcela má ${W} × ${H} m (zmeníš v <a href="#nastavenia">Nastaveniach</a>). Mriežka = 1 m.</p>
      <ul class="small"><li><b>+ Nakresliť</b> → vyber typ (záhon, ker, chodník…) a ťahaj obdĺžnik myšou.</li>
      <li>Klik na objekt = detail vpravo, ťahaním ho presunieš.</li>
      <li>Presné rozmery (m) zadáš v detaile.</li>
      <li>V záhone sa zobrazujú plodiny zvoleného roka – striedanie a návrh na ďalší rok nájdeš v detaile.</li>
      <li><b>Plán na budúci rok:</b> prepni Rok hore. Čo nakreslíš, platí od toho roka; čo odstrániš, zmizne od toho roka, staršie roky ostanú.</li></ul>
      ${d.zahony.length ? `<h3>Objekty</h3>` + d.zahony.map((z) => `<div><a href="#" data-z="${z.id}">${esc(z.nazov)}</a> <span class="muted small">${esc(I.typy_zahonov[z.typ])}, ${z.w} × ${z.h} m${z.od_roku ? `, od ${z.od_roku}` : ""}${z.do_roku ? `, do ${z.do_roku}` : ""}</span></div>`).join("") : ""}</div>`;
    $$("[data-z]", side).forEach((a) => a.onclick = (e) => { e.preventDefault(); S.sel = +a.dataset.z; rPlan(); });
    return;
  }
  const z = d.zahony.find((q) => q.id == S.sel);
  if (!z) { S.sel = null; return planSide(d); }
  const vys = d.vysadby.filter((v) => v.zahon_id == z.id);
  const vysHtml = vys.length ? vys.map((v) => `<div>${esc(plodinaMeno(v.plodina))}${v.odroda ? " – " + esc(v.odroda) : ""} <span class="tag">${esc(I.stavy[v.stav])}</span>${v.z_minula ? `<span class="tag">od ${v.rok}</span>` : ""}</div>`).join("") : `<div class="empty">Nič.</div>`;
  if (zam) {
    side.innerHTML = `<div class="card"><h2>${esc(z.nazov)} 🔒</h2><div class="muted small">${esc(I.typy_zahonov[z.typ])}, ${z.w} × ${z.h} m</div>${z.poznamka ? `<p>${esc(z.poznamka)}</p>` : ""}</div>
      <div class="card"><h2>${S.planRok}</h2>${vysHtml}</div><div id="z-det"></div>`;
  } else {
  side.innerHTML = `<div class="card"><form id="z-form" class="form-grid">
      <div class="full"><label>Názov</label><input id="z-nazov" name="nazov" value="${esc(z.nazov)}"></div>
      <div><label>Typ</label><select name="typ">${opts(I.typy_zahonov, z.typ)}</select></div><div></div>
      <div><label>X od ľavého okraja (m)</label><input name="x" type="number" step="0.1" value="${z.x}"></div>
      <div><label>Y od horného okraja (m)</label><input name="y" type="number" step="0.1" value="${z.y}"></div>
      <div><label>Šírka (m)</label><input name="w" type="number" step="0.1" min="0.1" value="${z.w}"></div>
      <div><label>Dĺžka (m)</label><input name="h" type="number" step="0.1" min="0.1" value="${z.h}"></div>
      <div class="full"><label>Poznámka</label><input name="poznamka" value="${esc(z.poznamka)}"></div>
      <div><label>Existuje od roku (prázdne = vždy)</label><input name="od_roku" type="number" value="${z.od_roku ?? ""}"></div>
      <div><label>do roku (prázdne = stále)</label><input name="do_roku" type="number" value="${z.do_roku ?? ""}"></div>
      <div class="full muted small">Posun a rozmery platia vo všetkých rokoch, kde objekt existuje. Keď sa objekt v novom roku mení (presun kompostu), odstráň ho v novom roku a nakresli nový – v starších rokoch ostane.</div>
      <div class="full row" style="margin-top:10px"><button class="primary">Uložiť</button><span class="muted small">${(z.w * z.h).toFixed(1)} m²</span><span class="spacer"></span><button type="button" class="danger" id="z-del">Odstrániť</button></div>
    </form></div>
    <div class="card"><div class="row between"><h2>${S.planRok}</h2><button id="z-add">+ Plodina sem</button></div>
      ${vysHtml}
    </div><div id="z-det"><div class="card muted"><span class="spin"></span></div></div>`;
  $("#z-form").onsubmit = async (e) => { e.preventDefault(); await api("/api/zahon", { id: z.id, ...formData(e.target) }); toast("Uložené"); rPlan(); };
  $("#z-del").onclick = async () => {
    const starsi = !z.od_roku || z.od_roku < S.planRok;
    const otazka = starsi ? `Odstrániť „${z.nazov}“ z plánu od roku ${S.planRok}? V rokoch do ${S.planRok - 1} ostane.`
                          : `Odstrániť „${z.nazov}“ z plánu? História (výsadby, denník, fotky) ostane.`;
    if (!confirm(otazka)) return;
    await api("/api/zahon/zmazat", { id: z.id, rok: S.planRok }); S.sel = null; rPlan();
  };
  $("#z-add").onclick = () => vysadbaForm({ zahon_id: z.id, rok: S.planRok }, rPlan);
  }
  const det = await api(`/api/zahon?id=${z.id}&rok=${S.planRok}`);
  if (S.sel != z.id) return;
  const nv = det.navrh;
  let h = z.typ !== "zahon" ? "" : `<div class="card"><h2>Na rok ${S.planRok + 1}</h2>` + (nv.obsadene ? `<p class="small">${esc(nv.preco)}</p></div>` : `
    <p class="small">Odporúčam <b>${esc(nv.naroky_text)}</b> plodiny – ${esc(nv.preco)}.</p>
    ${nv.vyhnut.length ? `<p class="small">Vyhni sa čeľadiam: ${nv.vyhnut.map((x) => `<span class="tag warn">${esc(x)}</span>`).join(" ")}</p>` : ""}
    ${nv.kandidati.length ? `<p class="small">Napríklad: ${nv.kandidati.map(esc).join(", ")}</p>` : ""}</div>`);
  h += `<div class="card"><h2>História záhona</h2>` + (det.historia.length ? det.historia.map((r) => `<div><b>${r.rok}</b>: ${r.vysadby.map((v) => `${esc(v.nazov)} <span class="muted small">(${esc(v.rodina)})</span>`).join(", ")}</div>`).join("") : `<div class="empty">Zatiaľ nič.</div>`) + `</div>`;
  if (det.fotky.length) h += `<div class="card"><h2>Fotky</h2><div class="thumbs">` + det.fotky.map((f) => `<img src="/fotky/${esc(f.subor)}" data-f="${f.id}" title="${fmtD(f.datum)}">`).join("") + `</div></div>`;
  if (det.dennik.length) h += `<div class="card"><h2>Denník</h2>${dennikTab(det.dennik.slice(0, 10), false)}</div>`;
  $("#z-det").innerHTML = h;
  $$("[data-f]", $("#z-det")).forEach((img) => img.onclick = () => fotkaDetail(det.fotky.find((f) => f.id == img.dataset.f), rPlan));
}

// ================================================================ ČO PESTUJEM
async function rPestujem() {
  const d = await api("/api/vysadby?rok=" + S.vysRok);
  const roky = [...new Set([...d.roky, new Date().getFullYear() + 1])].sort();
  let h = `<div class="row between"><h1>Čo pestujem</h1><div class="row">
    <select id="v-rok">${roky.map((r) => `<option ${r === S.vysRok ? "selected" : ""}>${r}</option>`).join("")}</select>
    ${jeZamknuty(S.vysRok) ? `<span class="tag">🔒 uzamknutý</span>` : `<button class="primary" id="v-add">+ Pridať plodinu</button>`}</div></div>
    <p class="muted small">Pridaj aj to, čo len plánuješ (stav „plánujem“) – nástenka ti potom včas pripomenie sejbu, výsadbu aj nákup. Trvalky (jahody, ríbezle…) a cesnak ostávajú aj v ďalších rokoch, kým ich neukončíš.</p>`;
  const zm = d.vysadby.filter((v) => v.z_minula), tento = d.vysadby.filter((v) => !v.z_minula);
  h += `<div class="card"><h2>${S.vysRok}</h2>${vysTab(tento, "Zatiaľ nič. Klikni na + Pridať plodinu.")}</div>`;
  if (zm.length) h += `<div class="card"><h2>Z minulých rokov (trvalky, prezimujúce)</h2>${vysTab(zm)}</div>`;
  app.innerHTML = h;
  $("#v-rok").onchange = (e) => { S.vysRok = +e.target.value; rPestujem(); };
  if ($("#v-add")) $("#v-add").onclick = () => vysadbaForm({ rok: S.vysRok }, rPestujem);
  const all = Object.fromEntries(d.vysadby.map((v) => [v.id, v]));
  $$("[data-ve]").forEach((b) => b.onclick = () => vysadbaForm(all[b.dataset.ve], rPestujem));
  $$("[data-vs]").forEach((s) => s.onchange = async () => {
    const v = all[s.dataset.vs];
    const datum = v.datum || (["zasiate", "vysadene"].includes(s.value) ? dnes() : null);
    await api("/api/vysadba", { ...v, stav: s.value, datum });
    toast("Uložené"); rPestujem();
  });
}
function vysTab(list, prazdne = "") {
  if (!list.length) return `<div class="empty">${prazdne}</div>`;
  return `<div style="overflow-x:auto"><table><tr><th>Plodina</th><th>Záhon</th><th>Spôsob</th><th>Stav</th><th>Dátum</th><th>Množstvo</th><th>Poznámka</th><th></th></tr>` +
    list.map((v) => `<tr class="${v.stav === "ukoncene" ? "dim" : ""}"><td><a href="#plodiny/${v.plodina}">${esc(plodinaMeno(v.plodina))}</a>${v.odroda ? `<div class="muted small">${esc(v.odroda)}</div>` : ""}</td>
      <td>${esc(zahonMeno(v.zahon_id))}</td><td class="small">${esc(I.sposoby[v.sposob] || v.sposob)}</td>
      <td><select data-vs="${v.id}">${opts(I.stavy, v.stav)}</select></td><td>${fmtD(v.datum)}</td>
      <td>${esc(v.mnozstvo)}</td><td class="small">${esc(v.poznamka)}</td><td><button class="link" data-ve="${v.id}">upraviť</button></td></tr>`).join("") + `</table></div>`;
}

function vysadbaForm(v, po) {
  const nova = !v.id;
  modal(`<h2>${nova ? "Pridať plodinu" : "Upraviť výsadbu"}</h2><form id="vf" class="form-grid">
    <div class="full"><label>Plodina</label><select name="plodina" required>${optPlodiny(v.plodina)}</select></div>
    <div><label>Odroda (voliteľné)</label><input name="odroda" value="${esc(v.odroda)}"></div>
    <div><label>Záhon</label><select name="zahon_id">${optZahony(v.zahon_id, undefined, true, v.rok || S.vysRok)}</select></div>
    <div><label>Spôsob</label><select name="sposob"></select></div>
    <div><label>Stav</label><select name="stav">${opts(I.stavy, v.stav || "plan")}</select></div>
    <div><label>Dátum sejby / výsadby</label><input type="date" name="datum" value="${esc(v.datum || "")}"></div>
    <div><label>Rok</label><input type="number" name="rok" value="${v.rok || S.vysRok}"></div>
    <div><label>Množstvo (napr. 12 ks, 2 riadky)</label><input name="mnozstvo" value="${esc(v.mnozstvo)}"></div>
    <div><label>Poznámka</label><input name="poznamka" value="${esc(v.poznamka)}"></div>
    <div class="full" id="vf-info"></div>
    <div class="full row" style="margin-top:12px"><button class="primary">Uložiť</button><button type="button" onclick="zavri()">Zrušiť</button>
      <span class="spacer"></span>${nova ? "" : `<button type="button" class="danger" id="vf-del">Zmazať</button>`}</div></form>`);
  const f = $("#vf");
  const upd = async () => {
    const p = PL[f.plodina.value];
    const sp = p ? p.sposoby : Object.keys(I.sposoby);
    const cur = f.sposob.value || v.sposob;
    f.sposob.innerHTML = sp.map((k) => `<option value="${k}" ${k === cur ? "selected" : ""}>${esc(I.sposoby[k])}</option>`).join("");
    let h = "";
    if (p) {
      const m = (a) => a.length ? a.map((x) => MES_KR[x - 1]).join(", ") : "—";
      h += `<div class="alert info small"><div>${p.kal.pred.length ? `Predpestovanie: <b>${m(p.kal.pred)}</b> · ` : ""}Sejba/výsadba von: <b>${m(p.kal.von)}</b> · Zber: <b>${m(p.kal.zber)}</b><br>
        Spon: ${esc(p.spon)}<br>Hĺbka: ${esc(p.hlbka)}<br>Čeľaď: ${esc(p.rodina)} · ${esc(I.naroky[p.naroky])}</div></div>`;
      if (f.zahon_id.value) {
        const w = await api(`/api/striedanie?zahon_id=${f.zahon_id.value}&plodina=${p.id}&rok=${f.rok.value}&id=${v.id || 0}`);
        h += w.map((x) => `<div class="alert ${x.uroven} small">${esc(x.text)}</div>`).join("");
      }
    }
    $("#vf-info").innerHTML = h;
  };
  f.plodina.onchange = upd; f.zahon_id.onchange = upd; f.rok.onchange = upd;
  upd();
  f.onsubmit = async (e) => {
    e.preventDefault();
    const b = formData(f);
    if ((b.stav === "zasiate" || b.stav === "vysadene") && !b.datum) b.datum = dnes();
    const r = await api("/api/vysadba", { ...v, ...b });
    zavri();
    if (r.varovania && r.varovania.some((x) => x.uroven === "varovanie")) toast("Uložené – pozor na striedanie plodín v tomto záhone.");
    else toast("Uložené");
    po();
  };
  if (!nova) $("#vf-del").onclick = async () => { if (!confirm("Zmazať túto výsadbu?")) return; await api("/api/vysadba/zmazat", { id: v.id }); zavri(); po(); };
}

// ================================================================ DENNÍK
async function rDennik() {
  const F = S.dnFilter;
  const q = new URLSearchParams(Object.entries(F).filter(([, v]) => v)).toString();
  const d = await api("/api/dennik?" + q);
  let h = `<div class="row between"><h1>Denník záhrady</h1><div class="row">
    <select id="f-rok"><option value="">všetky roky</option>${d.roky.map((r) => `<option ${r == F.rok ? "selected" : ""}>${r}</option>`).join("")}</select>
    <select id="f-zahon">${optZahony(F.zahon_id, "všetky záhony", false)}</select>
    <select id="f-plodina">${optPlodiny(F.plodina, "všetky plodiny")}</select>
    <a class="btn" href="/api/export/dennik.csv">Export CSV</a>
    <button class="primary" id="dn-add">+ Zápis</button></div></div>`;
  if (d.zber.length) {
    h += `<div class="card"><h2>Úroda ${esc(F.rok || new Date().getFullYear())}</h2><div class="row">` +
      d.zber.map((z) => `<span class="tag green">🧺 ${esc(z.plodina_nazov)}: ${z.s != null ? (+z.s).toLocaleString("sk") + " " + esc(z.jednotka || "") : z.n + "× zber"}</span>`).join("") + `</div></div>`;
  }
  h += `<div class="card">${d.dennik.length ? dennikTab(d.dennik, true) : `<div class="empty">Nič. Odškrtnuté úlohy z nástenky sa zapisujú samy, alebo pridaj zápis ručne.</div>`}</div>`;
  app.innerHTML = h;
  $("#f-rok").onchange = (e) => { F.rok = e.target.value; rDennik(); };
  $("#f-zahon").onchange = (e) => { F.zahon_id = e.target.value; rDennik(); };
  $("#f-plodina").onchange = (e) => { F.plodina = e.target.value; rDennik(); };
  $("#dn-add").onclick = () => dennikForm({}, rDennik);
  const m = Object.fromEntries(d.dennik.map((x) => [x.id, x]));
  $$("[data-de]").forEach((b) => b.onclick = () => dennikForm(m[b.dataset.de], rDennik));
}
function dennikTab(list, akcie) {
  return `<table>` + list.map((r) => `<tr><td style="white-space:nowrap">${fmtD(r.datum, akcie)}</td><td>${TYP_IKONA[r.typ] || "•"}</td>
    <td>${esc(r.text)}${r.mnozstvo != null ? ` <b>${(+r.mnozstvo).toLocaleString("sk")} ${esc(r.jednotka || "")}</b>` : ""}
      <div class="small muted">${[r.zahon, r.plodina_nazov].filter(Boolean).map(esc).join(" · ")}</div></td>
    ${akcie ? `<td><button class="link" data-de="${r.id}">upraviť</button></td>` : ""}</tr>`).join("") + `</table>`;
}
function dennikForm(r, po) {
  const nova = !r.id;
  modal(`<h2>${nova ? "Nový zápis" : "Upraviť zápis"}</h2><form id="df" class="form-grid">
    <div><label>Dátum</label><input type="date" name="datum" value="${esc(r.datum || dnes())}" required></div>
    <div><label>Typ</label><select name="typ">${opts(I.typy_dennik, r.typ || "praca")}</select></div>
    <div><label>Záhon</label><select name="zahon_id">${optZahony(r.zahon_id, "—", false)}</select></div>
    <div><label>Plodina</label><select name="plodina">${optPlodiny(r.plodina, "—")}</select></div>
    <div class="full"><label>Čo sa robilo / pozorovanie</label><textarea name="text">${esc(r.text)}</textarea></div>
    <div id="df-zber" class="full form-grid" style="padding:0"><div><label>Množstvo</label><input name="mnozstvo" value="${r.mnozstvo ?? ""}" inputmode="decimal"></div>
      <div><label>Jednotka</label><select name="jednotka">${["kg", "ks", "l", "g"].map((j) => `<option ${j === (r.jednotka || "kg") ? "selected" : ""}>${j}</option>`).join("")}</select></div></div>
    <div class="full row" style="margin-top:12px"><button class="primary">Uložiť</button><button type="button" onclick="zavri()">Zrušiť</button>
      <span class="spacer"></span>${nova ? "" : `<button type="button" class="danger" id="df-del">Zmazať</button>`}</div></form>`);
  const f = $("#df");
  const t = () => { $("#df-zber").style.display = f.typ.value === "zber" ? "" : "none"; };
  f.typ.onchange = t; t();
  f.onsubmit = async (e) => {
    e.preventDefault();
    const b = formData(f);
    if (b.typ !== "zber") { b.mnozstvo = ""; b.jednotka = ""; }
    await api("/api/dennik", { id: r.id, ...b }); zavri(); toast("Zapísané"); po();
  };
  if (!nova) $("#df-del").onclick = async () => { if (!confirm("Zmazať zápis?")) return; await api("/api/dennik/zmazat", { id: r.id }); zavri(); po(); };
}

// ================================================================ FOTKY
async function rFotky() {
  const F = S.fotoFilter;
  const q = new URLSearchParams(Object.entries(F).filter(([, v]) => v)).toString();
  const fotky = await api("/api/fotky?" + q);
  let h = `<h1>Fotky a diagnostika</h1>
    <div class="card"><h2>Nahrať fotky</h2><form id="up" class="form-grid">
      <div class="full"><label>Fotky (z mobilu si ich najprv prenes do PC)</label><input type="file" name="subory" accept="image/*" multiple required></div>
      <div><label>Záhon</label><select name="zahon_id">${optZahony("", "—", false)}</select></div>
      <div><label>Plodina</label><select name="plodina">${optPlodiny("", "—")}</select></div>
      <div class="full"><label>Popis (čo vidíš, čo ťa trápi)</label><input name="popis"></div>
      <div class="full row" style="margin-top:10px"><button class="primary">Nahrať</button><span id="up-stav" class="muted small">Fotky sa zmenšia na max. 1600 px. Dátum sa vezme zo súboru.</span></div>
    </form></div>
    <div class="row" style="margin-bottom:10px"><select id="ff-zahon">${optZahony(F.zahon_id, "všetky záhony", false)}</select>
      <select id="ff-plodina">${optPlodiny(F.plodina, "všetky plodiny")}</select><span class="muted small">${fotky.length} fotiek</span></div>
    <div class="photos">${fotky.map((f) => `<div class="photo" data-f="${f.id}"><img src="/fotky/${esc(f.subor)}" loading="lazy">
      <div>${fmtD(f.datum)} ${f.hodnotenie ? `<span class="tag green">hodnotené</span>` : ""}<div class="muted">${[f.plodina_nazov, f.zahon].filter(Boolean).map(esc).join(" · ")}</div></div></div>`).join("")}</div>
    ${fotky.length ? "" : `<div class="empty">Zatiaľ žiadne fotky.</div>`}`;
  app.innerHTML = h;
  $("#ff-zahon").onchange = (e) => { F.zahon_id = e.target.value; rFotky(); };
  $("#ff-plodina").onchange = (e) => { F.plodina = e.target.value; rFotky(); };
  const m = Object.fromEntries(fotky.map((f) => [f.id, f]));
  $$("[data-f]").forEach((el) => el.onclick = () => fotkaDetail(m[el.dataset.f], rFotky));
  $("#up").onsubmit = async (e) => {
    e.preventDefault();
    const f = e.target, files = [...f.subory.files], meta = formData(f);
    const stav = $("#up-stav");
    for (let i = 0; i < files.length; i++) {
      stav.innerHTML = `<span class="spin"></span> ${i + 1} / ${files.length}`;
      const data = await zmensi(files[i]);
      await api("/api/fotka", { data, datum: isoDate(new Date(files[i].lastModified || Date.now())),
                                zahon_id: meta.zahon_id, plodina: meta.plodina, popis: meta.popis });
    }
    toast(`Nahraté: ${files.length}`); rFotky();
  };
}
function zmensi(file, max = 1600) {
  return new Promise((ok, err) => {
    const img = new Image(), url = URL.createObjectURL(file);
    img.onload = () => {
      const k = Math.min(1, max / Math.max(img.width, img.height));
      const c = document.createElement("canvas");
      c.width = Math.round(img.width * k); c.height = Math.round(img.height * k);
      c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
      URL.revokeObjectURL(url);
      ok(c.toDataURL("image/jpeg", 0.85));
    };
    img.onerror = () => { URL.revokeObjectURL(url); toast(`Súbor ${file.name} sa nedá načítať ako obrázok.`, true); err(new Error("img")); };
    img.src = url;
  });
}
function fotkaDetail(f, po) {
  const key = I.nastavenia.api_key_nastaveny;
  modal(`<img class="big-photo" src="/fotky/${esc(f.subor)}">
    <form id="ff" class="form-grid">
      <div><label>Dátum</label><input type="date" name="datum" value="${esc(f.datum)}"></div>
      <div><label>Záhon</label><select name="zahon_id">${optZahony(f.zahon_id, "—", false)}</select></div>
      <div><label>Plodina</label><select name="plodina">${optPlodiny(f.plodina, "—")}</select></div>
      <div><label>Popis</label><input name="popis" value="${esc(f.popis)}"></div>
      <div class="full row" style="margin-top:8px"><button class="primary">Uložiť údaje</button>
        <a class="btn" href="/fotky/${esc(f.subor)}" download>Stiahnuť</a><span class="spacer"></span><button type="button" class="danger" id="ff-del">Zmazať fotku</button></div>
    </form>
    <h3>Hodnotenie stavu rastliny</h3>
    ${f.hodnotenie ? `<div class="pre">${esc(f.hodnotenie)}</div><div class="muted small">${esc(f.hodnotenie_zdroj)} · ${fmtD(f.hodnotenie_datum)}</div>` : `<div class="empty">Zatiaľ nehodnotené.</div>`}
    <label>Doplňujúca poznámka k diagnostike (voliteľné)</label><input id="dg-pozn" style="width:100%" placeholder="napr. listy žltnú odspodu, polievam každý druhý deň">
    <div class="row" style="margin-top:8px">
      <button id="dg-api" ${key ? "" : "disabled"} title="${key ? "" : "Nastav API kľúč v Nastaveniach"}">🤖 Diagnostikovať cez API</button>
      <button id="dg-chat">💬 Otázka pre chat (zadarmo)</button>
      <button id="dg-vloz">✍️ Vložiť odpoveď ručne</button></div>
    <div id="dg-box"></div>`, true);
  $("#ff").onsubmit = async (e) => { e.preventDefault(); await api("/api/fotka/upravit", { id: f.id, ...formData(e.target) }); toast("Uložené"); zavri(); po(); };
  $("#ff-del").onclick = async () => { if (!confirm("Zmazať fotku aj súbor?")) return; await api("/api/fotka/zmazat", { id: f.id }); zavri(); po(); };
  $("#dg-api").onclick = async () => {
    const b = $("#dg-api"); b.disabled = true; b.innerHTML = `<span class="spin"></span> Claude sa pozerá…`;
    try {
      const r = await api("/api/diagnostika", { id: f.id, poznamka: $("#dg-pozn").value });
      f.hodnotenie = r.hodnotenie; f.hodnotenie_zdroj = r.zdroj; f.hodnotenie_datum = dnes();
      fotkaDetail(f, po);
    } catch (e) { b.disabled = false; b.textContent = "🤖 Diagnostikovať cez API"; }
  };
  $("#dg-chat").onclick = async () => {
    const r = await api(`/api/prompt?id=${f.id}&poznamka=${encodeURIComponent($("#dg-pozn").value)}`);
    $("#dg-box").innerHTML = `<div class="alert info small">1. Stiahni fotku (tlačidlo hore). 2. Otvor chat s Claude a vlož fotku. 3. Skopíruj a vlož tento text. 4. Odpoveď vlož späť cez „Vložiť odpoveď ručne“.</div>
      <textarea id="dg-prompt" style="min-height:220px">${esc(r.prompt)}</textarea><button id="dg-copy">Kopírovať text</button>`;
    $("#dg-copy").onclick = async () => {
      try { await navigator.clipboard.writeText($("#dg-prompt").value); } catch { $("#dg-prompt").select(); document.execCommand("copy"); }
      toast("Skopírované");
    };
  };
  $("#dg-vloz").onclick = () => {
    $("#dg-box").innerHTML = `<label>Odpoveď (hodnotenie)</label><textarea id="dg-text" style="min-height:180px">${esc(f.hodnotenie)}</textarea>
      <button class="primary" id="dg-save">Uložiť hodnotenie</button>`;
    $("#dg-save").onclick = async () => {
      await api("/api/fotka/upravit", { ...f, hodnotenie: $("#dg-text").value, hodnotenie_zdroj: "vložené z chatu" });
      f.hodnotenie = $("#dg-text").value; f.hodnotenie_zdroj = "vložené z chatu"; f.hodnotenie_datum = dnes();
      toast("Uložené"); fotkaDetail(f, po);
    };
  };
}

// ================================================================ PLODINY
async function rPlodiny() {
  const pid = location.hash.split("/")[1];
  if (pid) return plodinaDetail(pid);
  const q = S.plodinaFilter.toLowerCase();
  const list = I.plodiny.filter((p) => (!S.plodinaTyp || p.typ === S.plodinaTyp) && (!q || p.nazov.toLowerCase().includes(q) || p.rodina.toLowerCase().includes(q)));
  app.innerHTML = `<div class="row between"><h1>Plodiny</h1><div class="row">
      <input id="pf" placeholder="Hľadať…" value="${esc(S.plodinaFilter)}">
      <select id="pt"><option value="">všetky</option>${opts(TYP_PLODINY, S.plodinaTyp)}</select></div></div>
    <div class="legend" style="margin-bottom:10px"><span><i style="background:#f0c36d"></i>predpestovanie</span><span><i style="background:#7cb66f"></i>sejba / výsadba von</span><span><i style="background:#d9825b"></i>zber</span></div>
    <div class="crops">${list.map((p) => `<div class="crop" data-p="${p.id}"><b>${esc(p.nazov)}</b>
      <div class="small muted">${esc(p.rodina)} · ${esc(p.naroky)}${p.trvalka ? " · trvalka" : ""}</div>${kalendar(p.kal, true)}</div>`).join("")}</div>`;
  $("#pf").oninput = (e) => { S.plodinaFilter = e.target.value; const pos = e.target.selectionStart; rPlodiny().then(() => { const i = $("#pf"); i.focus(); i.setSelectionRange(pos, pos); }); };
  $("#pt").onchange = (e) => { S.plodinaTyp = e.target.value; rPlodiny(); };
  $$("[data-p]").forEach((el) => el.onclick = () => { location.hash = "plodiny/" + el.dataset.p; });
}
function kalendar(kal, mini = false) {
  const riadky = [["pred", "Predpestovanie"], ["von", "Sejba / výsadba"], ["zber", "Zber"]].filter(([k]) => !mini || kal[k].length);
  let h = `<div class="cal" style="${mini ? "grid-template-columns:repeat(12,1fr)" : ""}">`;
  if (!mini) h += `<div></div>` + MES_KR.map((m) => `<div class="h">${m}</div>`).join("");
  for (const [k, n] of riadky) {
    if (!mini) h += `<div class="small">${n}</div>`;
    for (let m = 1; m <= 12; m++) h += `<div class="c ${kal[k].includes(m) ? k : ""}" title="${n} – ${MESIACE[m - 1]}"></div>`;
  }
  return h + `</div>`;
}
async function plodinaDetail(pid) {
  const p = await api("/api/plodina?id=" + pid);
  const u = p.ulohy.map((x) => `<li><span class="ic">${TYP_IKONA[x.typ] || "•"}</span><div class="t">${esc(x.text)}<div class="meta"><span class="tag">${fmtMD(x.od)} – ${fmtMD(x.do)}</span>${x.opak !== "raz" ? `<span class="tag">opakovane</span>` : ""}</div></div></li>`).join("");
  app.innerHTML = `<p><a href="#plodiny">← všetky plodiny</a></p>
    <div class="row between"><h1>${esc(p.nazov)}</h1><button class="primary" id="pd-add">+ Pridať do záhrady</button></div>
    <div class="grid2"><div>
      <div class="card"><div class="small muted">${esc(p.rodina)} · ${esc(I.naroky[p.naroky])}${p.trvalka ? " · trvalka" : ""}${p.prezimuje ? " · sadí sa na jeseň" : ""}</div>
        ${kalendar(p.kal)}
        <div class="legend"><span><i style="background:#f0c36d"></i>predpestovanie</span><span><i style="background:#7cb66f"></i>sejba / výsadba</span><span><i style="background:#d9825b"></i>zber</span></div>
        <h3>Spon</h3><div>${esc(p.spon)}</div><h3>Hĺbka</h3><div>${esc(p.hlbka)}</div>
        ${p.dobri.length ? `<h3>Dobrí susedia</h3><div>${p.dobri.map(esc).join(", ")}</div>` : ""}
        ${p.zli.length ? `<h3>Zlí susedia</h3><div>${p.zli.map(esc).join(", ")}</div>` : ""}</div>
      <div class="card"><h2>Tipy</h2><ul>${p.tipy.map((t) => `<li>${esc(t)}</li>`).join("")}</ul></div>
      ${p.problemy.length ? `<div class="card"><h2>Časté problémy</h2>${p.problemy.map((x) => `<h3>${esc(x.nazov)}</h3><div>${esc(x.text)}</div>`).join("")}</div>` : ""}
    </div><div><div class="card"><h2>Úlohy v kalendári</h2><ul class="tasks">${u}</ul>
      <p class="muted small">Na nástenke sa ukážu len tie, ktoré sedia na tvoj spôsob pestovania a stav výsadby.</p></div></div></div>`;
  $("#pd-add").onclick = () => vysadbaForm({ plodina: pid, rok: new Date().getFullYear() }, () => { location.hash = "pestujem"; });
}
function fmtMD(s) { const [m, d] = s.split("-").map(Number); return `${d}. ${m}.`; }

// ================================================================ NÁVODY
async function rNavody() {
  const id = location.hash.split("/")[1] || I.navody[0].id;
  const n = await api("/api/navod?id=" + id);
  app.innerHTML = `<h1>Návody</h1><div class="grid-side" style="grid-template-columns:260px minmax(0,1fr)">
    <div class="card navlist">${I.navody.map((x) => `<a href="#navody/${x.id}" class="${x.id === id ? "on" : ""}">${esc(x.nazov)}</a>`).join("")}</div>
    <div class="card article"><h2>${esc(n.nazov)}</h2>${md(n.text)}</div></div>`;
}

// ================================================================ STRIEDANIE
async function rStriedanie() {
  const d = await api("/api/striedanie_plan");
  const cfg = d.cfg, SK = Object.fromEntries(d.skupiny.map((s) => [s.id, s]));
  const vStried = Object.fromEntries(cfg.zahony.map((z) => [z.id, z.skupina]));
  const navrh = Object.fromEntries(d.navrh.map((z) => [z.id, z.skupina]));
  const bg = (s) => `background:${SK[s].farba}33;border-left:4px solid ${SK[s].farba}`;
  let h = `<h1>Striedanie plodín</h1>
    <div class="card"><p class="small">Záhony v striedaní sa každý rok posunú o jednu skupinu ďalej (1 → 2 → 3 → 4 → 1). Každá čeľaď je len v jednej skupine,
      takže sa na ten istý záhon vráti až po 4 rokoch. Poradie strieda aj nároky: plodová zelenina s kompostom → strukoviny pôdu obohatia o dusík → kapustoviny ho využijú → koreňová zelenina bez hnoja → znova kompost.
      Trvalky (jahody, kríky) do striedania nepatria. Úlohy na prípravu záhonov (jar, jeseň) sa objavia na nástenke.</p>
      <div style="overflow-x:auto"><table><tr><th>Skupina</th><th>Plodiny</th><th>Na jar</th><th>Po zbere</th></tr>` +
    d.skupiny.map((s) => `<tr><td style="${bg(s.id)}"><b>${s.id}. ${esc(s.nazov)}</b><div class="small muted">${esc(I.naroky[s.naroky])}</div></td>
      <td class="small">${s.plodiny.filter((p) => PL[p]).map(kratko).join(", ")}</td><td class="small">${esc(s.jar)}</td><td class="small">${esc(s.po)}</td></tr>`).join("") +
    `</table></div></div>`;

  h += `<div class="card"><h2>Záhony v striedaní</h2><form id="st-f">
    <div class="row"><label style="margin:0">Skupina platí pre rok</label><input name="rok" type="number" value="${cfg.rok}" style="width:90px">
      <button type="button" id="st-navrh">Navrhnúť podľa roka ${cfg.rok - 1}</button></div>
    <table style="margin-top:8px"><tr><th>V striedaní</th><th>Záhon</th><th>Skupina v roku ${cfg.rok}</th></tr>` +
    d.zahony.map((z) => `<tr><td><input type="checkbox" name="z${z.id}" ${vStried[z.id] ? "checked" : ""}></td><td>${esc(z.nazov)} <span class="muted small">${z.w} × ${z.h} m</span></td>
      <td><select name="s${z.id}">${d.skupiny.map((s) => `<option value="${s.id}" ${(vStried[z.id] || navrh[z.id]) == s.id ? "selected" : ""}>${s.id}. ${esc(s.nazov)}</option>`).join("")}</select></td></tr>`).join("") +
    `</table>${d.zahony.length ? "" : `<div class="empty">Najprv nakresli záhony v Pláne.</div>`}
    <div style="margin-top:10px"><button class="primary">Uložiť</button> <span class="muted small">Pri 4 záhonoch daj každému inú skupinu.</span></div></form></div>`;

  if (d.riadky.length) {
    const roky = []; for (let r = d.od; r <= d.do; r++) roky.push(r);
    h += `<div class="card"><h2>Plán po rokoch</h2><div style="overflow-x:auto"><table><tr><th>Záhon</th>${roky.map((r) => `<th>${r}${jeZamknuty(r) ? " 🔒" : ""}</th>`).join("")}</tr>` +
      d.riadky.map((row) => `<tr><td><b>${esc(row.nazov)}</b></td>` + row.bunky.map((b) => {
        if (b.neexistuje) return `<td class="small muted">záhon ešte / už neexistuje</td>`;
        if (!b.skupina) return `<td class="small">${b.vysadby.map((v) => esc(kratko(v.plodina))).join(", ") || `<span class="muted">nič</span>`}
          ${b.minulost || jeZamknuty(b.rok) ? "" : `<br><button class="link" data-add="${row.id}:${b.rok}">+ plodina</button>`}</td>`;
        const s = SK[b.skupina];
        const pl = b.vysadby.length ? b.vysadby.map((v) => esc(kratko(v.plodina))).join(", ")
          : `<span class="muted">napr. ${s.plodiny.filter((p) => PL[p]).slice(0, 4).map(kratko).join(", ")}</span>`;
        const warn = [...b.mimo.map((m) => `${m} nepatrí do skupiny`), ...b.varovania];
        return `<td class="small" style="${bg(b.skupina)};min-width:150px"><b>${esc(s.kratko)}</b>${b.minulost ? ` <span class="muted">(skutočnosť)</span>` : ""}<div>${pl}</div>
          ${warn.length ? `<div title="${esc(warn.join("\n"))}" style="color:var(--warn)">⚠ ${warn.length === 1 ? esc(warn[0]).slice(0, 60) : warn.length + " upozornenia"}</div>` : ""}
          ${jeZamknuty(b.rok) ? "" : `<button class="link" data-add="${row.id}:${b.rok}">+ plodina</button>`}</td>`;
      }).join("") + `</tr>`).join("") + `</table></div>
      <p class="muted small">Sivý text = návrh zo skupiny. Plodiny pridané cez „+ plodina“ sa uložia ako „plánujem“ a nástenka ti ich pripomenie.</p></div>`;
  }
  app.innerHTML = h;
  const f = $("#st-f");
  $("#st-navrh").onclick = () => { d.navrh.forEach((z) => { const s = f["s" + z.id]; if (s) s.value = z.skupina; if (f["z" + z.id]) f["z" + z.id].checked = true; }); toast("Návrh vyplnený – skontroluj a Ulož."); };
  f.onsubmit = async (e) => {
    e.preventDefault();
    const zz = d.zahony.filter((z) => f["z" + z.id].checked).map((z) => ({ id: z.id, skupina: +f["s" + z.id].value }));
    await api("/api/striedanie", { rok: +f.rok.value, zahony: zz });
    toast("Uložené"); rStriedanie();
  };
  $$("[data-add]").forEach((b) => b.onclick = () => {
    const [zid, rok] = b.dataset.add.split(":").map(Number);
    vysadbaForm({ zahon_id: zid, rok }, rStriedanie);
  });
}

// ================================================================ NASTAVENIA
async function rNastavenia() {
  const s = I.nastavenia;
  app.innerHTML = `<h1>Nastavenia</h1><div class="grid2"><div>
    <form id="ns" class="card"><h2>Záhrada</h2><div class="form-grid">
      <div class="full"><label>Názov</label><input name="nazov" value="${esc(s.nazov)}"></div>
      <div class="full"><label>Miesto (pre počasie)</label><div class="row"><input name="miesto" value="${esc(s.miesto)}" style="flex:1"><button type="button" id="geo">Hľadať</button></div><div id="geo-res"></div></div>
      <div><label>Zemepisná šírka</label><input name="lat" value="${esc(s.lat)}"></div>
      <div><label>Zemepisná dĺžka</label><input name="lon" value="${esc(s.lon)}"></div>
      <div><label>Pôda</label><select name="poda">${opts(I.pody, s.poda)}</select></div>
      <div><label>Juh na pláne je</label><select name="juh">${opts({ dole: "dole", hore: "hore", vlavo: "vľavo", vpravo: "vpravo" }, s.juh)}</select></div>
      <div><label>Šírka parcely (m)</label><input name="sirka" type="number" step="0.5" value="${esc(s.sirka)}"></div>
      <div><label>Dĺžka parcely (m)</label><input name="dlzka" type="number" step="0.5" value="${esc(s.dlzka)}"></div>
      <div class="full"><label><input type="checkbox" name="dennik_auto" ${s.dennik_auto === "1" ? "checked" : ""}> Odškrtnuté úlohy zapisovať do denníka</label></div>
    </div><div style="margin-top:12px"><button class="primary">Uložiť</button></div></form>
    </div><div>
    <form id="nk" class="card"><h2>Fotodiagnostika cez Claude API</h2>
      <p class="small">Voliteľné. Bez kľúča funguje „Otázka pre chat“ (zadarmo v rámci predplatného, odpoveď vložíš ručne).
      S kľúčom apka pošle fotku priamo na <b>api.anthropic.com</b> a odpoveď uloží k fotke. API sa platí zvlášť od predplatného podľa spotrebovaných tokenov –
      aktuálne ceny sú na stránke cien Claude API. Pri každom hodnotení apka uloží počet tokenov, takže vidíš reálnu spotrebu.</p>
      <p class="small">Kľúč vytvoríš v Claude Console (sekcia API keys), návod je na docs.claude.com. Ukladá sa len do lokálnej databázy (<code>data/zahradka.db</code>).</p>
      <div class="form-grid"><div class="full"><label>API kľúč</label><input name="api_key" type="password" value="${esc(s.api_key)}" placeholder="sk-ant-…" autocomplete="off"></div>
      <div class="full"><label>Model</label><input name="model" value="${esc(s.model)}"></div></div>
      <div class="row" style="margin-top:12px"><button class="primary">Uložiť</button>${s.api_key_nastaveny ? `<button type="button" id="nk-del" class="danger">Odstrániť kľúč</button>` : ""}</div></form>
    <div class="card"><h2>Dáta</h2>
      <p class="small">Databáza: <code>data/zahradka.db</code>, fotky: <code>data/fotky/</code>, denné zálohy (30 dní): <code>data/backups/</code>.</p>
      <div class="row"><a class="btn" href="/api/export/dennik.csv">Export denníka (CSV)</a></div></div>
    <div class="card"><h2>Vypnutie</h2><p class="small">Server beží na pozadí, kým ho nevypneš. Ikona na ploche ho znova spustí.</p>
      <button id="off" class="danger">Vypnúť Záhradku</button><p class="muted small">Verzia ${esc(I.verzia)}</p></div>
  </div></div>`;
  $("#ns").onsubmit = async (e) => { e.preventDefault(); await api("/api/nastavenia", formData(e.target)); await reloadInit(); toast("Uložené"); rNastavenia(); };
  $("#nk").onsubmit = async (e) => { e.preventDefault(); await api("/api/nastavenia", formData(e.target)); await reloadInit(); toast("Uložené"); rNastavenia(); };
  if ($("#nk-del")) $("#nk-del").onclick = async () => { await api("/api/nastavenia", { api_key: "" }); await reloadInit(); toast("Kľúč odstránený"); rNastavenia(); };
  $("#geo").onclick = async () => {
    const f = $("#ns");
    const r = await api("/api/geokod?q=" + encodeURIComponent(f.miesto.value));
    $("#geo-res").innerHTML = r.length ? r.map((x, i) => `<div><a href="#" data-g="${i}">${esc(x.nazov)}</a> <span class="muted small">${esc(x.kraj)}, ${esc(x.stat)}</span></div>`).join("") : `<div class="muted small">Nič sa nenašlo.</div>`;
    $$("[data-g]").forEach((a) => a.onclick = (e) => { e.preventDefault(); const x = r[a.dataset.g]; f.miesto.value = x.nazov; f.lat.value = x.lat; f.lon.value = x.lon; $("#geo-res").innerHTML = `<div class="muted small">Nastavené – nezabudni Uložiť.</div>`; });
  };
  $("#off").onclick = async () => {
    if (!confirm("Vypnúť server Záhradky?")) return;
    await api("/api/vypnut", {});
    document.body.innerHTML = `<main><div class="card"><h2>Záhradka je vypnutá</h2><p>Znova ju spustíš ikonou na ploche.</p></div></main>`;
  };
}

// ---------------------------------------------------------------- štart
reloadInit().then(route).catch((e) => { app.innerHTML = `<div class="alert alarm">Server neodpovedá: ${esc(e.message)}</div>`; });
