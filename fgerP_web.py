import streamlit as st
from datetime import datetime, timedelta

# 1. Configuração da página web
st.set_page_config(page_title="FgERP - Fluxo de Caixa Avançado", layout="centered")

# =========================================================================
# 2. INICIALIZAÇÃO FIXA DO BANCO DE DADOS (Com suporte a Datas de Vencimento)
# =========================================================================
if "estoque" not in st.session_state:
    st.session_state.estoque = {}
if "clientes" not in st.session_state:
    st.session_state.clientes = {}
if "vendas" not in st.session_state:
    st.session_state.vendas = []
if "financeiro" not in st.session_state:
    # Estrutura atualizada: adicionado 'data_vencimento' no formato YYYY-MM-DD para ordenação correta
    st.session_state.financeiro = []

if "proximo_id_prod" not in st.session_state:
    st.session_state.proximo_id_prod = 1
if "proximo_id_cli" not in st.session_state:
    st.session_state.proximo_id_cli = 1
if "menu_atual" not in st.session_state:
    st.session_state.menu_atual = "Início"
if "logado" not in st.session_state:
    st.session_state.logado = False

# Função auxiliar para recalcular limites (mantida do módulo anterior)
def atualizar_limite_cliente(id_cliente):
    cliente = st.session_state.clientes[id_cliente]
    limite_calculado = cliente["renda"] * 0.30
    nome_cliente = cliente["nome"]
    parcelas_pagas_no_prazo = 0
    inadimplencias = 0
    
    for item in st.session_state.financeiro:
        if item["tipo"] == "Receber" and nome_cliente in item["descricao"]:
            if item["status"] == "Pago":
                parcelas_pagas_no_prazo += 1
            elif item["status"] == "Aberto" and item.get("atrasado", False):
                inadimplencias += 1

    limite_calculado += (parcelas_pagas_no_prazo * (cliente["renda"] * 0.05))
    if inadimplencias > 0:
        limite_calculado = 0.0
        cliente["status_credito"] = "Bloqueado por Inadimplência"
    else:
        cliente["status_credito"] = "Regular"
    cliente["limite_credito"] = max(0.0, limite_calculado)

# =========================================================================
# 3. VALIDAÇÃO DE ACESSO (LOGIN)
# =========================================================================
if not st.session_state.logado:
    st.title("🔒 FgERP - Acesso Restrito")
    usuario = st.text_input("Usuário:", key="login_usuario")
    senha = st.text_input("Senha:", type="password", key="login_senha")
    if st.button("Iniciar Sistema (Start)"):
        if usuario == "admin" and senha == "1234":
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")
    st.stop()

# --- MENU LATERAL ---
st.sidebar.title("=== FgERP ===")
opcoes_menu = ["Início", "Módulo de Estoque", "Módulo de Clientes", "Registrar Venda", "Contas a Pagar / Receber", "📊 Fluxo de Caixa Diário"]
if st.session_state.menu_atual not in opcoes_menu:
    st.session_state.menu_atual = "Início"
escolha = st.sidebar.radio("Escolha um Módulo:", opcoes_menu, index=opcoes_menu.index(st.session_state.menu_atual))
st.session_state.menu_atual = escolha

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Sair do Sistema"):
    st.session_state.logado = False
    st.rerun()

# ==========================================
# TELA 0: INÍCIO
# ==========================================
if st.session_state.menu_atual == "Início":
    st.title("📊 Painel Principal - FgERP")
    st.write("Bem-vindo ao Sistema de Gestão Financeira Avançado!")
    st.info("Acesse o novo módulo lateral 'Fluxo de Caixa Diário' para acompanhar a saúde financeira dia a dia.")

# ==========================================
# TELA 1: MÓDULO DE ESTOQUE
# ==========================================
elif st.session_state.menu_atual == "Módulo de Estoque":
    st.title("📦 Gestão de Estoque")
    aba1, aba2 = st.tabs(["➕ Entrada de Estoque", "📋 Listar Produtos"])
    with aba1:
        nome = st.text_input("Nome do produto", key="prod_nome_input")
        preco = st.number_input("Preço de venda (R$)", min_value=0.0, step=0.01, format="%.2f", key="prod_preco_input")
        qtd = st.number_input("Quantidade de entrada", min_value=0, step=1, key="prod_qtd_input")
        custo_unitario = st.number_input("Custo Unitário de Compra (R$)", min_value=0.0, step=0.01, format="%.2f", key="prod_custo_input")
        forma_pag_custo = st.selectbox("Forma de Pagamento:", ["Boleto bancário", "À Vista", "Prazo Fornecedor"], key="prod_forma_input")
        vencimento_custo = st.date_input("Data de Vencimento do Custo:", datetime.now(), key="prod_venc_input")
        
        if st.button("Gravar Entrada", key="btn_gravar_produto"):
            if nome.strip() != "":
                id_atual = st.session_state.proximo_id_prod
                st.session_state.estoque[id_atual] = {"nome": nome, "preco": preco, "qtd": qtd}
                st.session_state.financeiro.append({
                    "id_lancamento": len(st.session_state.financeiro) + 1, "tipo": "Pagar",
                    "descricao": f"Compra Estoque: {nome}", "valor": custo_unitario * qtd,
                    "forma": forma_pag_custo, "status": "Pago" if "À Vista" in forma_pag_custo else "Aberto",
                    "data_vencimento": vencimento_custo.strftime("%Y-%m-%d")
                })
                st.success(f"✅ Produto cadastrado!")
                st.session_state.proximo_id_prod += 1
                st.rerun()

# ==========================================
# TELA 2: MÓDULO DE CLIENTES
# ==========================================
elif st.session_state.menu_atual == "Módulo de Clientes":
    st.title("👥 Gestão de Clientes e Crédito")
    aba1, aba2 = st.tabs(["➕ Cadastrar Novo Cliente", "📋 Listar Fichas de Crédito"])
    with aba1:
        nome_cli = st.text_input("Nome do cliente", key="cli_nome_input")
        tel = st.text_input("Telefone", key="cli_tel_input")
        endereco = st.text_input("Endereço", key="cli_end_input")
        bairro = st.text_input("Bairro", key="cli_bairro_input")
        cidade = st.text_input("Cidade", key="cli_cid_input")
        renda = st.number_input("Renda Mensal (R$)", min_value=0.0, step=100.0, format="%.2f", key="cli_renda_input")
        if st.button("Gravar Cliente", key="btn_gravar_cliente"):
            if nome_cli.strip() != "":
                id_atual = st.session_state.proximo_id_cli
                st.session_state.clientes[id_atual] = {
                    "nome": nome_cli, "telefone": tel, "endereco": endereco, "bairro": bairro, "cidade": city,
                    "renda": renda, "limite_credito": renda * 0.30, "status_credito": "Regular (Sem histórico)"
                }
                st.success("✅ Cliente gravado!")
                st.session_state.proximo_id_cli += 1
                st.rerun()

# ==========================================
# TELA 3: REGISTRAR VENDA
# ==========================================
elif st.session_state.menu_atual == "Registrar Venda":
    st.title("🛒 Registrar Venda")
    if not st.session_state.clientes or not st.session_state.estoque:
        st.warning("⚠️ Cadastre clientes e produtos antes.")
    else:
        opcoes_clientes = {id_c: f"{info['nome']}" for id_c, info in st.session_state.clientes.items()}
        opcoes_produtos = {id_p: f"{info['nome']}" for id_p, info in st.session_state.estoque.items()}
        id_cli = st.selectbox("Cliente:", options=list(opcoes_clientes.keys()), format_func=lambda x: opcoes_clientes[x])
        id_prod = st.selectbox("Produto:", options=list(opcoes_produtos.keys()), format_func=lambda x: opcoes_produtos[x])
        qtd_venda = st.number_input("Quantidade", min_value=1, step=1)
        tipo_pagamento = st.selectbox("Forma:", ["À Vista", "Crediário", "Boleto bancário"])
        vencimento_venda = st.date_input("Data de Vencimento da Parcela:", datetime.now())
        
        valor_total = st.session_state.estoque[id_prod]["preco"] * qtd_venda
        st.metric("Total do Pedido", f"R$ {valor_total:.2f}")
        
        if st.button("Finalizar Venda"):
            cliente = st.session_state.clientes[id_cli]
            if st.session_state.estoque[id_prod]["qtd"] < qtd_venda: st.error("Sem estoque!")
            elif tipo_pagamento in ["Crediário", "Boleto bancário"] and valor_total > cliente["limite_credito"]:
                st.error("❌ VENDA RECUSADA! Sem limite de crédito.")
            else:
                st.session_state.estoque[id_prod]["qtd"] -= qtd_venda
                st.session_state.financeiro.append({
                    "id_lancamento": len(st.session_state.financeiro) + 1, "tipo": "Receber",
                    "descricao": f"Venda: {cliente['nome']}", "valor": valor_total,
                    "forma": tipo_pagamento, "status": "Pago" if tipo_pagamento == "À Vista" else "Aberto",
                    "atrasado": False, "data_vencimento": vencimento_venda.strftime("%Y-%m-%d")
                })
                st.success("🎉 Venda processada!")
                st.rerun()

# ==========================================
# TELA 4: CONTAS A PAGAR / RECEBER (COM LANÇAMENTO MANUAL DE BOLETOS)
# ==========================================
elif st.session_state.menu_atual == "Contas a Pagar / Receber":
    st.title("💸 Central de Obrigações e Direitos")
    aba_fin1, aba_fin2, aba_fin3 = st.tabs(["➕ Lançar Boleto Manual", "📉 Contas a Pagar", "📈 Contas a Receber"])
    
    with aba_fin1:
        st.subheader("Cadastro Manual de Contas / Despesas Fixas")
        tipo_manual = st.selectbox("Tipo de Lançamento:", ["Pagar (Despesa/Boleto)", "Receber (Outras Receitas)"])
        desc_manual = st.text_input("Descrição do Boleto (Ex: Boleto Água, Aluguel, Luz):")
        valor_manual = st.number_input("Valor Nominal (R$):", min_value=0.0, step=10.0, format="%.2f")
        forma_manual = st.selectbox("Forma de Operação:", ["Boleto bancário", "Dinheiro/Pix", "Cartão"])
        venc_manual = st.date_input("Data de Vencimento:", datetime.now())
        status_manual = st.selectbox("Status Inicial:", ["Aberto", "Pago"])
        
        if st.button("Salvar Lançamento Financeiro"):
            if desc_manual.strip() != "":
                st.session_state.financeiro.append({
                    "id_lancamento": len(st.session_state.financeiro) + 1,
                    "tipo": "Pagar" if "Pagar" in tipo_manual else "Receber",
                    "descricao": desc_manual,
                    "valor": valor_manual,
                    "forma": forma_manual,
                    "status": status_manual,
                    "atrasado": False,
                    "data_vencimento": venc_manual.strftime("%Y-%m-%d")
                })
                st.success("✅ Conta cadastrada e provisionada no Fluxo de Caixa!")
                st.rerun()
            else:
                st.error("Preencha a descrição.")
                
    with aba_fin2:
        st.subheader("📌 Obrigações (Contas a Pagar)")
        pagar_list = [item for item in st.session_state.financeiro if item["tipo"] == "Pagar"]
        if not pagar_list: st.info("Nenhum registro.")
        else:
            for item in pagar_list:
                cor = "🔴" if item["status"] == "Aberto" else "🟢"
                venc_formatado = datetime.strptime(item["data_vencimento"], "%Y-%m-%d").strftime("%d/%m/%Y")
                st.markdown(f"**{cor} {item['descricao']}**")
                st.write(f"Valor: R$ {item['valor']:.2f} | Vencimento: {venc_formatado} | Status: {item['status']}")
                if item["status"] == "Aberto" and st.button(f"Confirmar Pagamento ID: {item['id_lancamento']}"):
                    item["status"] = "Pago"
                    st.rerun()
                st.divider()

    with aba_fin3:
        st.subheader("📌 Direitos (Contas a Receber)")
        receber_list = [item for item in st.session_state.financeiro if item["tipo"] == "Receber"]
        if not receber_list: st.info("Nenhum registro.")
        else:
            for item in receber_list:
                cor = "🔴" if item["status"] == "Aberto" else "🟢"
                venc_formatado = datetime.strptime(item["data_vencimento"], "%Y-%m-%d").strftime("%d/%m/%Y")
                st.markdown(f"**{cor} {item['descricao']}**")
                st.write(f"Valor: R$ {item['valor']:.2f} | Vencimento: {venc_formatado} | Status: {item['status']}")
                if item["status"] == "Aberto" and st.button(f"Liquidar ID: {item['id_lancamento']}"):
                    item["status"] = "Pago"
                    st.rerun()
                st.divider()

# ==========================================
# TELA 5: NOVO RELATÓRIO - FLUXO DE CAIXA DIÁRIO
# ==========================================
elif st.session_state.menu_atual == "📊 Fluxo de Caixa Diário":
    st.title("📊 Relatório: Fluxo de Caixa Diário")
    st.write("Visão cronológica de Entradas, Saídas e Saldos baseados nas datas de vencimento.")
    
    if not st.session_state.financeiro:
        st.info("Sem movimentações financeiras para gerar o relatório.")
    else:
        # Agrupar todas as datas únicas de movimentação para montar o calendário ordenado
        datas_encontradas = sorted(list(set(item["data_vencimento"] for item in st.session_state.financeiro)))
        
        saldo_acumulado = 0.0
        
        for data_venc in datas_encontradas:
            data_formatada = datetime.strptime(data_venc, "%Y-%m-%d").strftime("%d/%m/%Y")
            
            # Filtrar o que vence nesse dia específico
            itens_do_dia = [item for item in st.session_state.financeiro if item["data_vencimento"] == data_venc]
            
            entradas_dia = sum(item["valor"] for item in itens_do_dia if item["tipo"] == "Receber")
            saidas_dia = sum(item["valor"] for item in itens_do_dia if item["tipo"] == "Pagar")
            saldo_dia = entradas_dia - saidas_dia
            saldo_acumulado += saldo_dia
            
            # Container visual para o dia
            with st.expander(f"📅 Dia {data_formatada} | Saldo do Dia: R$ {saldo_dia:.2f}"):
                # Mostrar tabelinha de movimentações do dia
                dados_dia_tabela = []
                for item in itens_do_dia:
                    seta = "🟩 (+)" if item["tipo"] == "Receber" else "🟥 (-)"
                    dados_dia_tabela.append({
                        "Fluxo": seta,
                        "Descrição": item["descricao"],
                        "Forma": item["forma"],
                        "Valor": f"R$ {item['valor']:.2f}",
                        "Situação": item["status"]
                    })
                st.table(dados_dia_tabela)
                
                # Métricas do dia
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Entradas", f"R$ {entradas_dia:.2f}")
                c2.metric("Total Saídas", f"R$ {saidas_dia:.2f}")
                c3.metric("Saldo Acumulado Geral", f"R$ {saldo_acumulado:.2f}")
