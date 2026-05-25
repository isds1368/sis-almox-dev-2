"""pages/saidas.py"""
import datetime, streamlit as st
from utils.database import listar_produtos,listar_setores,registrar_movimentacao,listar_solicitacoes,atualizar_movimentacao,buscar_produto_por_id,listar_movimentacoes
from utils.auth import sessao,is_admin
from utils.ui import badge
from utils.fmt import datahora_br,qtd_br
UNS=["UN","CX","KG","LT","MT","PC","RL","FR","GL","DZ","CT","SC","FD","BL"]

def tela_solicitacoes():
    st.markdown('<div class="pg">', unsafe_allow_html=True)
    st.markdown('<div class="pg-title">📋 Solicitações</div><div class="pg-sub">Solicite retiradas — passam por aprovação do administrador</div>', unsafe_allow_html=True)
    tabs=["Nova Solicitação","Aprovar / Rejeitar","Histórico"] if is_admin() else ["Nova Solicitação","Minhas Solicitações"]
    tl=st.tabs(tabs)
    with tl[0]: _form_sol()
    if is_admin():
        with tl[1]: _aprovar()
        with tl[2]: _hist_sol()
    else:
        with tl[1]: _hist_sol(apenas_meu=True)
    st.markdown("</div>", unsafe_allow_html=True)

def _form_sol():
    u=sessao(); prods=listar_produtos(); sets=listar_setores()
    if not prods: st.warning("Nenhum produto cadastrado."); return
    pm={f"{p['nome']} ({p['codigo_interno']})":p for p in prods}
    sn=[s["nome"] for s in sets] or ["Sem setor"]
    st.markdown('<div class="card"><div class="card-h">📝 Nova Solicitação</div>', unsafe_allow_html=True)
    with st.form("ffs"):
        c1,c2=st.columns(2)
        with c1:
            sel=st.selectbox("Produto *",list(pm.keys())); prod=pm[sel]
            qtd=st.number_input("Quantidade *",min_value=0.001,value=1.0,step=1.0)
            ui=st.selectbox("Unidade",UNS,index=UNS.index(prod["unidade_secundaria"]) if prod["unidade_secundaria"] in UNS else 0)
        with c2:
            setor=st.selectbox("Setor *",sn)
            nome_s=st.text_input("Nome do solicitante *",value=u.get("nome") or u.get("nick",""))
            obs=st.text_area("Obs",height=60)
        est=float(prod["quantidade_total_secundaria"]); cor="var(--ok)" if est>0 else "var(--err)"
        st.markdown(f'<div style="background:var(--bg2);border:1px solid var(--bdr);border-radius:7px;padding:.55rem .9rem;font-size:.79rem;margin:.3rem 0;">Saldo: <strong style="color:{cor};">{qtd_br(est)} {prod["unidade_secundaria"]}</strong></div>', unsafe_allow_html=True)
        if st.form_submit_button("Enviar Solicitação →",type="primary",use_container_width=True):
            if not nome_s.strip(): st.error("Nome obrigatório.")
            else:
                registrar_movimentacao({"produto_id":prod["id"],"tipo":"saida","tipo_saida":"SOLICITADA","status":"pendente","quantidade_informada":qtd,"unidade_informada":ui,"quantidade_convertida":qtd,"setor_solicitante":setor,"nome_solicitante":nome_s.strip(),"nick_solicitante":u["nick"],"observacao":obs.strip() or None,"usuario_solicitante":u["id"]})
                st.success("✅ Solicitação enviada! Aguardando aprovação."); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def _aprovar():
    u=sessao(); pend=listar_solicitacoes("pendente")
    st.markdown('<div class="card"><div class="card-h">🔐 Pendentes de Aprovação</div>', unsafe_allow_html=True)
    if not pend:
        st.markdown('<p style="color:var(--t3);font-size:.82rem;">Nenhuma pendente.</p>', unsafe_allow_html=True)
    else:
        for s in pend:
            prod=s.get("produto") or {}; sol=s.get("sol") or {}
            c1,c2,c3,c4=st.columns([4,2,1,1])
            with c1:
                st.markdown(f"**{prod.get('nome','—')}**")
                st.caption(f"{sol.get('nick','—')} | {s.get('setor_solicitante','—')} | {datahora_br(s['criado_em'])}")
            with c2: st.markdown(f"**{qtd_br(s['quantidade_informada'])} {s['unidade_informada']}**")
            with c3:
                if st.button("✅",key=f"a_{s['id']}",help="Aprovar"):
                    atualizar_movimentacao(s["id"],{"status":"aprovado","usuario_autorizador":u["id"],"data_autorizacao":datetime.datetime.utcnow().isoformat()}); st.rerun()
            with c4:
                if st.button("❌",key=f"r_{s['id']}",help="Rejeitar"):
                    atualizar_movimentacao(s["id"],{"status":"rejeitado"}); st.rerun()
            st.markdown('<div class="div"></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def _hist_sol(apenas_meu=False):
    u=sessao(); todas=listar_solicitacoes()
    if apenas_meu: todas=[s for s in todas if s.get("nick_solicitante")==u["nick"]]
    _tbl(todas)

def tela_saida_manual():
    st.markdown('<div class="pg">', unsafe_allow_html=True)
    st.markdown('<div class="pg-title">📤 Saída Manual</div><div class="pg-sub">Saída direta — sem aprovação prévia</div>', unsafe_allow_html=True)
    t1,t2=st.tabs(["Executar","Histórico"])
    with t1: _form_manual()
    with t2: _tbl(listar_movimentacoes(tipo="saida",tipo_saida="MANUAL"))
    st.markdown("</div>", unsafe_allow_html=True)

def _form_manual():
    u=sessao(); prods=listar_produtos(); sets=listar_setores()
    if not prods: st.warning("Nenhum produto cadastrado."); return
    pm={f"{p['nome']} ({p['codigo_interno']})":p for p in prods}
    sn=[s["nome"] for s in sets] or ["Sem setor"]
    st.markdown('<div class="card"><div class="card-h">⚡ Saída Direta</div>', unsafe_allow_html=True)
    with st.form("ffm"):
        c1,c2=st.columns(2)
        with c1:
            sel=st.selectbox("Produto *",list(pm.keys())); prod=pm[sel]
            qtd=st.number_input("Qtd *",min_value=0.001,value=1.0,step=1.0)
            ui=st.selectbox("Unidade",UNS,index=UNS.index(prod["unidade_secundaria"]) if prod["unidade_secundaria"] in UNS else 0)
        with c2: setor=st.selectbox("Setor *",sn); nome_r=st.text_input("Retirante *"); motivo=st.text_area("Motivo *",height=60)
        est=float(prod["quantidade_total_secundaria"]); cor="var(--ok)" if est>=qtd else "var(--err)"
        st.markdown(f'<div style="background:var(--bg2);border:1px solid var(--bdr);border-radius:7px;padding:.55rem .9rem;font-size:.79rem;margin:.3rem 0;">Saldo: <strong style="color:{cor};">{qtd_br(est)} {prod["unidade_secundaria"]}</strong>{"&nbsp;⚠️ <span style=color:var(--err)>Insuficiente</span>" if est<qtd else ""}</div>', unsafe_allow_html=True)
        if st.form_submit_button("⬇️ Executar Saída",type="primary",use_container_width=True):
            erros=[]
            if not nome_r.strip(): erros.append("Nome obrigatório.")
            if not motivo.strip(): erros.append("Motivo obrigatório.")
            if est<qtd: erros.append("Estoque insuficiente.")
            if erros:
                for e in erros: st.error(e)
            else:
                registrar_movimentacao({"produto_id":prod["id"],"tipo":"saida","tipo_saida":"MANUAL","status":"concluido","quantidade_informada":qtd,"unidade_informada":ui,"quantidade_convertida":qtd,"setor_solicitante":setor,"nome_solicitante":nome_r.strip(),"nick_solicitante":u["nick"],"motivo_saida":motivo.strip(),"usuario_executor":u["id"],"data_movimentacao":datetime.datetime.utcnow().isoformat()})
                st.success(f"✅ Saída de {qtd_br(qtd)} {ui} de **{prod['nome']}** concluída!"); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def tela_saida_aprovada():
    st.markdown('<div class="pg">', unsafe_allow_html=True)
    st.markdown('<div class="pg-title">✅ Saída Aprovada</div><div class="pg-sub">Execute baixas de solicitações aprovadas</div>', unsafe_allow_html=True)
    u=sessao(); aprov=listar_solicitacoes("aprovado")
    st.markdown('<div class="card"><div class="card-h">📋 Aguardando Execução</div>', unsafe_allow_html=True)
    if not aprov:
        st.markdown('<p style="color:var(--t3);font-size:.82rem;">Nenhuma saída aprovada pendente.</p>', unsafe_allow_html=True)
    else:
        for s in aprov:
            prod=s.get("produto") or {}; autor=s.get("aut") or {}
            c1,c2,c3=st.columns([4,3,2])
            with c1:
                st.markdown(f"**{prod.get('nome','—')}**")
                st.caption(f"Setor: {s.get('setor_solicitante','—')} | {s.get('nome_solicitante','—')}")
                st.caption(f"Aprovado por: {autor.get('nick','—')}")
            with c2: st.markdown(f"**{qtd_br(s['quantidade_informada'])} {s['unidade_informada']}**")
            with c3:
                if st.button("⬇️ Executar",key=f"ex_{s['id']}",type="primary",use_container_width=True):
                    p=buscar_produto_por_id(prod.get("id",""))
                    if p and float(p["quantidade_total_secundaria"])>=float(s["quantidade_convertida"]):
                        atualizar_movimentacao(s["id"],{"status":"concluido","usuario_executor":u["id"],"data_movimentacao":datetime.datetime.utcnow().isoformat()})
                        st.success("Baixa executada!"); st.rerun()
                    else: st.error("Estoque insuficiente.")
            st.markdown('<div class="div"></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    with st.expander("Histórico"): _tbl(listar_solicitacoes("concluido"))
    st.markdown("</div>", unsafe_allow_html=True)

def _tbl(movs):
    if not movs: st.info("Nenhum registro."); return
    st.markdown('<div class="card">', unsafe_allow_html=True)
    rows=""
    for m in movs:
        prod=m.get("produto") or {}; b=badge(m["status"].capitalize(),m["status"])
        rows+=f'<tr><td style="color:var(--t3);font-size:.73rem;">{datahora_br(m["criado_em"])}</td><td><strong>{prod.get("nome","—")}</strong></td><td>{qtd_br(m["quantidade_informada"])} {m["unidade_informada"]}</td><td>{m.get("setor_solicitante","—")}</td><td>{m.get("nome_solicitante","—")}</td><td>{b}</td></tr>'
    st.markdown(f'<table class="tbl"><thead><tr><th>Data</th><th>Produto</th><th>Qtd</th><th>Setor</th><th>Solicitante</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
