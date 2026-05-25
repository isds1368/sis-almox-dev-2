"""pages/entrada.py"""
import datetime, streamlit as st
from utils.database import buscar_produto_por_ean,buscar_produtos_por_nome,criar_produto,registrar_movimentacao,criar_documento,upload_pdf,listar_categorias,listar_movimentacoes
from utils.auth import sessao
from utils.ui import badge
from utils.fmt import datahora_br,qtd_br
UNS=["UN","CX","KG","LT","MT","PC","RL","FR","GL","DZ","CT","SC","FD","BL"]
TIPOS=["Nota Fiscal","FL","Entrada Interna","Ajuste Manual"]

def tela_entrada():
    st.markdown('<div class="pg">', unsafe_allow_html=True)
    st.markdown('<div class="pg-title">📥 Entrada de Produtos</div><div class="pg-sub">Registre entradas por EAN, nome ou cadastro avulso</div>', unsafe_allow_html=True)
    t1,t2 = st.tabs(["Nova Entrada","Histórico"])
    with t1: _form()
    with t2: _hist()
    st.markdown("</div>", unsafe_allow_html=True)

def _form():
    u = sessao(); cats = listar_categorias(); cm = {c["nome"]:c["id"] for c in cats}
    st.markdown('<div class="card"><div class="card-h">🔍 Identificar Produto</div>', unsafe_allow_html=True)
    c1,c2,c3 = st.columns([3,1,1])
    with c1: termo = st.text_input("EAN ou nome",placeholder="Bipe ou digite",key="eb")
    with c2:
        st.markdown("<div style='height:27px'></div>",unsafe_allow_html=True)
        be = st.button("Buscar EAN",use_container_width=True)
    with c3:
        st.markdown("<div style='height:27px'></div>",unsafe_allow_html=True)
        bn = st.button("Buscar Nome",use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    prod = st.session_state.get("ps")
    if be and termo.strip():
        p = buscar_produto_por_ean(termo.strip())
        if p: st.session_state["ps"]=p; st.session_state.pop("en",None); prod=p; st.success(f"✅ {p['nome']} — {p['codigo_interno']}")
        else: st.warning("EAN não encontrado. Cadastre abaixo."); st.session_state.pop("ps",None); st.session_state["en"]=termo.strip()
    if bn and termo.strip():
        res = buscar_produtos_por_nome(termo.strip())
        if res:
            opts = {f"{r['nome']} ({r['codigo_interno']})":r for r in res}
            sel = st.selectbox("Selecione",list(opts.keys()),key="snr")
            if st.button("Usar este →"): st.session_state["ps"]=opts[sel]; st.session_state.pop("en",None); st.rerun()
        else: st.warning("Não encontrado."); st.session_state.pop("ps",None)
    if st.session_state.get("en") and not prod:
        st.markdown('<div class="card"><div class="card-h">📋 Cadastrar Novo Produto</div>', unsafe_allow_html=True)
        with st.form("fnp"):
            c1,c2 = st.columns(2)
            with c1: nm=st.text_input("Nome *"); cat=st.selectbox("Categoria",list(cm.keys())); up=st.selectbox("Un. primária",UNS,index=1); us=st.selectbox("Un. secundária",UNS)
            with c2: fat=st.number_input("Fator (1 prim=? sec)",value=1.0,min_value=0.001,step=1.0); em=st.number_input("Est. mínimo",value=0.0,min_value=0.0); ean=st.text_input("EAN",value=st.session_state.get("en",""))
            desc=st.text_area("Descrição",height=60)
            if st.form_submit_button("Cadastrar →",type="primary"):
                if not nm.strip(): st.error("Nome obrigatório.")
                else:
                    novo=criar_produto({"nome":nm.strip(),"ean":ean.strip() or None,"categoria_id":cm.get(cat),"unidade_primaria":up,"unidade_secundaria":us,"fator_conversao":fat,"estoque_minimo_primario":em,"descricao":desc.strip() or None})
                    st.session_state["ps"]=novo; st.session_state.pop("en",None)
                    st.success(f"✅ {novo['nome']} — {novo['codigo_interno']}"); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    if not prod and not st.session_state.get("en"):
        with st.expander("➕ Criar produto sem EAN"):
            with st.form("fav"):
                c1,c2=st.columns(2)
                with c1: nav=st.text_input("Nome *"); cav=st.selectbox("Cat",list(cm.keys()),key="cav"); upav=st.selectbox("Un. prim",UNS,index=1,key="upav"); usav=st.selectbox("Un. sec",UNS,key="usav")
                with c2: ftav=st.number_input("Fator",value=1.0,min_value=0.001); emav=st.number_input("Est. mín",value=0.0,min_value=0.0)
                if st.form_submit_button("Criar →",type="primary"):
                    if nav.strip():
                        novo=criar_produto({"nome":nav.strip(),"categoria_id":cm.get(cav),"unidade_primaria":upav,"unidade_secundaria":usav,"fator_conversao":ftav,"estoque_minimo_primario":emav})
                        st.session_state["ps"]=novo; st.rerun()
    if prod:
        est=float(prod.get("quantidade_total_secundaria",0)); fat=float(prod.get("fator_conversao",1))
        up=prod.get("unidade_primaria","UN"); us=prod.get("unidade_secundaria","UN")
        st.markdown('<div class="card"><div class="card-h">📥 Registrar Entrada</div>', unsafe_allow_html=True)
        c1,c2,c3=st.columns(3); c1.metric("Produto",prod["nome"][:22]); c2.metric("Código",prod["codigo_interno"]); c3.metric("Estoque",f"{qtd_br(est)} {us}")
        st.markdown('<div class="div"></div>', unsafe_allow_html=True)
        with st.form("fer"):
            c1,c2=st.columns(2)
            with c1: te=st.selectbox("Tipo *",TIPOS); qtd=st.number_input("Qtd *",min_value=0.001,value=1.0,step=1.0); ui=st.selectbox("Unidade",UNS,index=UNS.index(up) if up in UNS else 0)
            with c2: nfn=st.text_input("NF",placeholder="Opcional"); forn=st.text_input("Fornecedor",placeholder="Opcional"); obs=st.text_area("Obs",height=60)
            qc=qtd*fat
            st.markdown(f'<div style="background:var(--bg2);border:1px solid var(--bdr);border-radius:7px;padding:.65rem .9rem;margin:.4rem 0;font-size:.8rem;">📦 <strong>{qtd_br(qtd)} {ui}</strong> <span style="color:var(--t3);">=</span> <strong style="color:var(--red);">{qtd_br(qc)} {us}</strong> adicionados</div>', unsafe_allow_html=True)
            pdf=st.file_uploader("Anexar (opcional)",type=["pdf","png","jpg"])
            if st.form_submit_button("✅ Registrar Entrada",type="primary",use_container_width=True):
                did=None
                if pdf:
                    ts=datetime.datetime.now().strftime("%Y%m%d%H%M%S"); nm=f"{ts}_{pdf.name}"
                    url=upload_pdf(pdf.read(),nm) if pdf.type=="application/pdf" else None
                    doc=criar_documento({"nome_arquivo":pdf.name,"caminho_arquivo":url,"status_envio":"pendente" if te=="Nota Fiscal" else "nao_requer"})
                    did=doc["id"]
                registrar_movimentacao({"produto_id":prod["id"],"tipo":"entrada","tipo_entrada":te,"status":"concluido","quantidade_informada":qtd,"unidade_informada":ui,"quantidade_convertida":qc,"envio_financeiro":te!="Nota Fiscal","fornecedor":forn.strip() or None,"numero_nf":nfn.strip() or None,"observacao":obs.strip() or None,"documento_id":did,"usuario_executor":u["id"],"data_movimentacao":datetime.datetime.utcnow().isoformat()})
                st.success(f"✅ +{qtd_br(qc)} {us} em **{prod['nome']}**!")
                if te=="Nota Fiscal": st.info("📎 NF registrada — acesse Notas Fiscais para enviar.")
                for k in ["ps","en","eb"]: st.session_state.pop(k,None)
                st.rerun()
        if st.button("🔄 Nova busca"): st.session_state.pop("ps",None); st.session_state.pop("en",None); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

def _hist():
    movs=listar_movimentacoes(tipo="entrada",limite=100)
    if not movs: st.info("Nenhuma entrada."); return
    st.markdown('<div class="card"><div class="card-h">Histórico</div>', unsafe_allow_html=True)
    rows=""
    for m in movs:
        prod=(m.get("produto") or {}).get("nome","—"); cod=(m.get("produto") or {}).get("codigo_interno","—")
        eu=(m.get("exe") or {}).get("nick","—"); tp=badge(m.get("tipo_entrada","—"),"manual" if m.get("tipo_entrada")=="FL" else "concluido")
        rows+=f'<tr><td style="color:var(--t3);font-size:.73rem;">{datahora_br(m["criado_em"])}</td><td><strong>{prod}</strong></td><td class="mono">{cod}</td><td style="font-weight:600;">{qtd_br(m["quantidade_informada"])} {m["unidade_informada"]}</td><td>{tp}</td><td style="color:var(--t3);">{m.get("numero_nf") or "—"}</td><td style="color:var(--t3);">{eu}</td></tr>'
    st.markdown(f'<table class="tbl"><thead><tr><th>Data</th><th>Produto</th><th>Código</th><th>Qtd</th><th>Tipo</th><th>NF</th><th>Executor</th></tr></thead><tbody>{rows}</tbody></table>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
