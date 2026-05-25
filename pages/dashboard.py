"""pages/dashboard.py"""
import plotly.graph_objects as go
import streamlit as st
from utils.database import stats_dashboard
from utils.ui import badge, kpi_html, status_estoque
from utils.fmt import qtd_br, datahora_br

_PL = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
           font=dict(family="Plus Jakarta Sans", size=11),
           margin=dict(l=0,r=0,t=20,b=0), showlegend=True,
           legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)))

def tela_dashboard():
    st.markdown('<div class="pg">', unsafe_allow_html=True)
    st.markdown('<div class="pg-title">Dashboard</div><div class="pg-sub">Visão geral em tempo real</div>', unsafe_allow_html=True)
    s = stats_dashboard()
    st.markdown(f"""<div class="kpis">
        {kpi_html("Produtos", s["total_produtos"], "ativos", "var(--red)")}
        {kpi_html("OK", s["ok"], "acima do mínimo", "var(--ok)")}
        {kpi_html("Baixo", s["baixos"], "abaixo do mínimo", "var(--warn)")}
        {kpi_html("Crítico", s["criticos"], "sem estoque", "var(--err)")}
        {kpi_html("Solicitações", s["pend_solicitacoes"], "pendentes", "#7C3AED")}
        {kpi_html("Notas NF", s["pend_notas"], "aguardando envio", "var(--info)")}
        {kpi_html("Parados 30d", s["parados"], "sem movimentação", "var(--t3)")}
        {kpi_html("Movimentações", s["total_movimentacoes"], "total", "var(--t2)")}
    </div>""", unsafe_allow_html=True)
    if s["criticos"]: st.error(f"🔴 **{s['criticos']} produto(s) com estoque zerado.**")
    if s["pend_solicitacoes"]: st.warning(f"🟡 **{s['pend_solicitacoes']} solicitação(ões)** aguardando aprovação.")
    if s["pend_notas"]: st.info(f"🔵 **{s['pend_notas']} nota(s)** pendentes de envio ao financeiro.")
    c1, c2 = st.columns([1.4, 1])
    with c1: _consumo(s["consumo_setor"])
    with c2: _pie(s)
    c3, c4 = st.columns(2)
    with c3: _recentes(s["recentes"])
    with c4: _atencao(s["produtos"])
    st.markdown("</div>", unsafe_allow_html=True)

def _consumo(consumo):
    st.markdown('<div class="card"><div class="card-h">📊 Consumo por Setor</div>', unsafe_allow_html=True)
    if not consumo:
        st.markdown('<p style="color:var(--t3);font-size:.82rem;text-align:center;padding:1rem">Sem dados.</p>', unsafe_allow_html=True)
    else:
        cores = ["#CC0000","#E53535","#FF6666","#FF9999","#8B0000","#B22222","#DC143C","#F08080"]
        fig = go.Figure(go.Bar(x=list(consumo.keys()), y=list(consumo.values()),
            marker=dict(color=cores[:len(consumo)], line=dict(width=0)),
            hovertemplate="<b>%{x}</b><br>%{y:.0f}<extra></extra>"))
        fig.update_layout(**_PL, height=220,
            xaxis=dict(gridcolor="rgba(0,0,0,.05)", tickfont=dict(size=10)),
            yaxis=dict(gridcolor="rgba(0,0,0,.05)"))
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

def _pie(s):
    st.markdown('<div class="card"><div class="card-h">📦 Status Inventário</div>', unsafe_allow_html=True)
    fig = go.Figure(go.Pie(labels=["OK","Baixo","Crítico"], values=[s["ok"],s["baixos"],s["criticos"]],
        hole=0.65, marker=dict(colors=["#16A34A","#D97706","#DC2626"], line=dict(color="rgba(255,255,255,.15)",width=2)),
        hovertemplate="<b>%{label}</b>: %{value}<extra></extra>"))
    fig.update_layout(**_PL, height=220,
        annotations=[dict(text=f"<b>{s['total_produtos']}</b>", x=.5, y=.5, font_size=22, showarrow=False)])
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

def _recentes(r):
    st.markdown('<div class="card"><div class="card-h">🔄 Movimentações Recentes</div>', unsafe_allow_html=True)
    if not r:
        st.markdown('<p style="color:var(--t3);font-size:.82rem;">Nenhuma.</p>', unsafe_allow_html=True)
    else:
        rows = ""
        for m in r:
            prod = (m.get("produtos") or {}).get("nome","—")
            cor = "var(--ok)" if m["tipo"]=="entrada" else "var(--err)"
            sinal = "+" if m["tipo"]=="entrada" else "-"
            rows += f'<tr><td style="color:var(--t3);font-size:.73rem;">{datahora_br(m["criado_em"])}</td><td>{prod[:28]}{"…" if len(prod)>28 else ""}</td><td style="color:{cor};font-weight:700;font-family:var(--mono);">{sinal}{qtd_br(m["quantidade_informada"])} {m["unidade_informada"]}</td></tr>'
        st.markdown(f'<table class="tbl"><thead><tr><th>Data</th><th>Produto</th><th>Qtd</th></tr></thead><tbody>{rows}</tbody></table>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def _atencao(produtos):
    st.markdown('<div class="card"><div class="card-h">🚨 Produtos em Atenção</div>', unsafe_allow_html=True)
    at = [(p, *status_estoque(float(p["quantidade_total_secundaria"]), float(p["estoque_minimo_primario"]), float(p["fator_conversao"]))) for p in produtos]
    at = [x for x in at if x[2] != "ok"]
    if not at:
        st.markdown('<p style="color:var(--ok);font-size:.82rem;">✅ Todos OK.</p>', unsafe_allow_html=True)
    else:
        rows = ""
        for p, txt, cls in sorted(at, key=lambda x: float(x[0]["quantidade_total_secundaria"]))[:8]:
            rows += f'<tr><td>{p["nome"][:28]}{"…" if len(p["nome"])>28 else ""}</td><td class="mono">{qtd_br(p["quantidade_total_secundaria"])} {p["unidade_secundaria"]}</td><td>{badge(txt,cls)}</td></tr>'
        st.markdown(f'<table class="tbl"><thead><tr><th>Produto</th><th>Estoque</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
