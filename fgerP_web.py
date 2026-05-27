import streamlit as st
from datetime import datetime

# 1. Configuração da página web
st.set_page_config(page_title="FgERP - Análise de Crédito Inteligente", layout="centered")

# =========================================================================
# 2. INICIALIZAÇÃO FIXA DO BANCO DE DADOS (Com suporte a Limite de Crédito)
# =========================================================================
if "estoque" not in st.session_state:
    st.session_state.estoque = {}
if "clientes" not in st.session_state:
    st.session_state.clientes = {}
if "vendas" not in st.session_state:
    st.session_state.vendas = []
if "financeiro" not in st.session_state:
    st.session_state.financeiro = []

if "proximo_id_prod" not in st.session_state:
    st.session_state.proximo_id_prod = 1
if "proximo_id_cli" not in st.session_state:
    st.session_state.proximo_id_cli = 1
if "menu_atual" not in st.session_state:
    st.session_state.menu_atual = "Início"
if "logado" not in st.session_state:
    st.session_state.logado = False

# =========================================================================
# FUNÇÃO DA REGRA DE NEGÓCIO: RECALCULAR LIMITE DE CRÉDITO DINAMICAMENTE
# =========================================================================
def atualizar_limite_cliente(id_cliente):
    cliente = st.session_state.clientes[id_cliente]
    
    # 1. Base inicial: 30% da renda informada
    limite_calculado = cliente["renda"] * 0.30
    
    # 2. Analisar histórico de parcelas/vendas a prazo no financeiro
    nome_cliente = cliente["nome"]
    parcelas_pagas_no_prazo = 0
    parcelas_pagas_com_atraso = 0
    inadimplencias = 0 # Contas em aberto que passaram da data (simulado por status)
    
    for item in st.session_state.financeiro:
        # Verifica se o lançamento pertence a este cliente no contas a receber
        if item["tipo"] == "Receber" and nome_cliente in item["descricao"]:
            if item["status"] == "Pago":
                # Regra de bônus por bom comportamento
                parcelas_pagas_no_prazo += 1
            elif item["status"] == "Aberto":
                # Regra de penalidade (se o usuário clicar no botão de atraso/inadimplência na tela)
                if item.get("atrasado", False):
                    inadimplencias += 1

    # Aplicando os fatores multiplicadores/restritivos:
    # Cada parcela paga corretamente aumenta o limite em +5% do valor da renda
    limite_calculado += (parcelas_pagas_no_prazo * (cliente["renda"] * 0.05))
    
    # Se houver inadimplência ativa/atraso, o limite é severamente restringido (reduz 50% por ocorrência)
    if inadimplencias > 0:
        limite_calculado = limite_calculado * 0.00  # Bloqueia o crédito totalmente se estiver inadimplente
        cliente["status_credito"] = "Bloqueado por Inadimplência"
    else:
        cliente["status_credito"] = "Regular"

    # Garante que o limite nunca seja menor que zero
    cliente["limite_credito"] = max(0.0, limite_calculado)

# =========================================================================
# 3. VALIDAÇÃO DE ACESSO (TELA DE LOGIN)
# =========================================================================
if not st.session_state.logado:
    st.title("🔒 FgERP - Acesso Restrito")
    st.subheader("Análise de Risco de Crédito Ativa")
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
opcoes_menu = ["Início", "Módulo de Estoque", "Módulo de Clientes", "Registrar Venda", "Contas a Pagar / Receber"]
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
    st.write("Bem-vindo ao Sistema de Gestão Inteligente com Score de Crédito!")
    st.info("O sistema agora calcula e restringe riscos financeiros automaticamente com base no comportamento do cliente.")

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
        
        if st.button("Gravar Entrada", key="btn_gravar_produto"):
            if nome.strip() != "":
                id_atual = st.session_state.proximo_id_prod
                st.session_state.estoque[id_atual] = {"nome": nome, "preco": preco, "qtd": qtd}
                st.session_state.financeiro.append({
                    "id_lancamento": len(st.session_state.financeiro) + 1, "tipo": "Pagar",
                    "descricao": f"Compra de Estoque: {nome}", "valor": custo_unitario * qtd,
                    "forma": forma_pag_custo, "status": "Pago" if "À Vista" in forma_pag_custo else "Aberto", "data": datetime.now().strftime("%d/%m/%Y")
                })
                st.success(f"✅ Produto cadastrado!")
                st.session_state.proximo_id_prod += 1
                st.rerun()
    with aba2:
        if not st.session_state.estoque: st.info("Vazio.")
        else: st.table([{"ID": id_p, "Produto": info["nome"], "Preço Venda": f"R$ {info['preco']:.2f}", "Quantidade": f"{info['qtd']} un"} for id_p, info in st.session_state.estoque.items()])

# ==========================================
# TELA 2: MÓDULO DE CLIENTES (NOVOS CAMPOS E RENDIMENTO)
# ==========================================
elif st.session_state.menu_atual == "Módulo de Clientes":
    st.title("👥 Gestão de Clientes e Crédito")
    aba1, aba2 = st.tabs(["➕ Cadastrar Novo Cliente", "📋 Listar Fichas de Crédito"])
    
    with aba1:
        st.subheader("Informações Pessoais e Financeiras")
        nome_cli = st.text_input("Nome do cliente", key="cli_nome_input")
        tel = st.text_input("Telefone", key="cli_tel_input")
        endereco = st.text_input("Endereço (Rua, Nº)", key="cli_end_input")
        bairro = st.text_input("Bairro", key="cli_bairro_input")
        cidade = st.text_input("Cidade", key="cli_cid_input")
        renda = st.number_input("Renda Mensal Comprovada (R$)", min_value=0.0, step=100.0, format="%.2f", key="cli_renda_input")
        
        if st.button("Gravar e Analisar Crédito Inicial", key="btn_gravar_cliente"):
            if nome_cli.strip() != "":
                id_atual = st.session_state.proximo_id_cli
                # Regra dos 30% sem histórico
                limite_inicial = renda * 0.30
                
                st.session_state.clientes[id_atual] = {
                    "nome": nome_cli, "telefone": tel, "endereco": endereco,
                    "bairro": bairro, "cidade": cidade, "renda": renda,
                    "limite_credito": limite_inicial, "status_credito": "Regular (Sem histórico)"
                }
                st.success(f"✅ Cliente '{nome_cli}' gravado! Limite de Crédito Inicial aprovado: R$ {limite_inicial:.2f}")
                st.session_state.proximo_id_cli += 1
                st.rerun()
            else:
                st.error("Digite o nome do cliente.")
                
    with aba2:
        st.subheader("Análise do Score de Crédito dos Clientes")
        if not st.session_state.clientes:
            st.info("Nenhum cliente cadastrado.")
        else:
            dados_clientes = []
            for id_c, info in st.session_state.clientes.items():
                dados_clientes.append({
                    "ID": id_c, "Nome": info["nome"], "Cidade/Bairro": f"{info['cidade']} - {info['bairro']}",
                    "Renda Comprovada": f"R$ {info['renda']:.2f}",
                    "LIMITE DISPONÍVEL": f"R$ {info['limite_credito']:.2f}",
                    "Status do Crédito": info["status_credito"]
                })
            st.table(dados_clientes)

# ==========================================
# TELA 3: REGISTRAR VENDA (BLOQUEIA CASO PASSE DO LIMITE)
# ==========================================
elif st.session_state.menu_atual == "Registrar Venda":
    st.title("🛒 Registrar Venda (Validação de Crédito)")
    
    if not st.session_state.clientes or not st.session_state.estoque:
        st.warning("⚠️ Cadastre clientes e produtos antes.")
    else:
        opcoes_clientes = {id_c: f"{id_c} - {info['nome']} (Limite: R$ {info['limite_credito']:.2f})" for id_c, info in st.session_state.clientes.items()}
        opcoes_produtos = {id_p: f"{id_p} - {info['nome']} (Preço: R$ {info['preco']:.2f})" for id_p, info in st.session_state.estoque.items()}
        
        id_cli = st.selectbox("Selecione o Cliente:", options=list(opcoes_clientes.keys()), format_func=lambda x: opcoes_clientes[x], key="venda_cli_select")
        id_prod = st.selectbox("Selecione o Produto:", options=list(opcoes_produtos.keys()), format_func=lambda x: opcoes_produtos[x], key="venda_prod_select")
        qtd_venda = st.number_input("Quantidade", min_value=1, step=1, key="venda_qtd_input")
        tipo_pagamento = st.selectbox("Forma de Recebimento:", ["À Vista", "Crediário", "Boleto bancário"], key="venda_forma_input")
        
        valor_total = st.session_state.estoque[id_prod]["preco"] * qtd_venda
        st.metric("Total do Pedido", f"R$ {valor_total:.2f}")
        
        if st.button("Finalizar Venda", key="btn_finalizar_venda"):
            cliente = st.session_state.clientes[id_cli]
            estoque_atual = st.session_state.estoque[id_prod]["qtd"]
            
            if estoque_atual < qtd_venda:
                st.error("❌ Estoque insuficiente!")
            # VALIDAÇÃO CRUCIAL: Se for a prazo, impede a venda caso o valor estoure o limite disponível do cliente
            elif tipo_pagamento in ["Crediário", "Boleto bancário"] and valor_total > cliente["limite_credito"]:
                st.error(f"❌ VENDA RECUSADA! O cliente não possui limite de crédito suficiente. Limite atual: R$ {cliente['limite_credito']:.2f}")
            else:
                # Deduz estoque
                st.session_state.estoque[id_prod]["qtd"] -= qtd_venda
                st.session_state.vendas.append({"cliente": cliente["nome"], "produto": st.session_state.estoque[id_prod]["nome"], "qtd": qtd_venda, "total": valor_total})
                
                st.session_state.financeiro.append({
                    "id_lancamento": len(st.session_state.financeiro) + 1, "tipo": "Receber",
                    "descricao": f"Venda para {cliente['nome']}", "valor": valor_total,
                    "forma": tipo_pagamento, "status": "Pago" if tipo_pagamento == "À Vista" else "Aberto",
                    "atrasado": False, "data": datetime.now().strftime("%d/%m/%Y")
                })
                
                st.success("🎉 Venda autorizada com sucesso!")
                st.rerun()

# ==========================================
# TELA 4: CONTAS (COM SIMULAÇÃO DE INADIMPLÊNCIA / ATRASOS)
# ==========================================
elif st.session_state.menu_atual == "Contas a Pagar / Receber":
    st.title("💸 Módulo Financeiro & Cobrança")
    aba_fin1, aba_fin2, aba_fin3 = st.tabs(["📊 Fluxo Geral", "📉 Contas a Pagar", "📈 Contas a Receber (Ações de Crédito)"])
    
    with aba_fin1:
        total_recebido = sum(item["valor"] for item in st.session_state.financeiro if item["tipo"] == "Receber" and item["status"] == "Pago")
        total_a_receber = sum(item["valor"] for item in st.session_state.financeiro if item["tipo"] == "Receber" and item["status"] == "Aberto")
        st.columns(2)[0].metric("Em Caixa", f"R$ {total_recebido:.2f}")
        st.columns(2)[1].metric("A Receber Geral", f"R$ {total_a_receber:.2f}")
        
    with aba_fin2:
        st.write("Controle de fornecedores...")
        
    with aba_fin3:
        st.subheader("📌 Carteira de Cobrança (A prazo)")
        receber_list = [item for item in st.session_state.financeiro if item["tipo"] == "Receber" and item["forma"] != "À Vista"]
        
        if not receber_list: st.info("Nenhuma conta a prazo.")
        else:
            for item in receber_list:
                cor_status = "🟢" if item["status"] == "Pago" else ("🔴" if item["atrasado"] else "🟡")
                txt_atraso = " (INADIMPLENTE/ATRASADO)" if item["atrasado"] else ""
                
                st.markdown(f"**{cor_status} {item['descricao']}{txt_atraso}**")
                st.write(f"Valor: R$ {item['valor']:.2f} | Forma: {item['forma']} | Status: {item['status']}")
                
                if item["status"] == "Aberto":
                    col_b1, col_b2 = st.columns(2)
                    
                    # Ação 1: Receber em dia (Aumenta o score do cliente)
                    if col_b1.button(f"Liquidar (Receber em dia) ID: {item['id_lancamento']}", key=f"rec_ok_{item['id_lancamento']}"):
                        item["status"] = "Pago"
                        # Encontra o cliente para atualizar o score dele
                        for id_c, cli in st.session_state.clientes.items():
                            if cli["nome"] in item["descricao"]:
                                atualizar_limite_cliente(id_c)
                        st.success("Recebido! O limite do cliente aumentou devido ao bom histórico.")
                        st.rerun()
                        
                    # Ação 2: Marcar como Atraso/Inadimplência (Bloqueia o crédito do cliente)
                    if not item["atrasado"]:
                        if col_b2.button(f"⚠️ Marcar Inadimplência ID: {item['id_lancamento']}", key=f"rec_bad_{item['id_lancamento']}"):
                            item["atrasado"] = True
                            for id_c, cli in st.session_state.clientes.items():
                                if cli["nome"] in item["descricao"]:
                                    atualizar_limite_cliente(id_c)
                            st.error("Inadimplência registrada! O crédito deste cliente foi bloqueado.")
                            st.rerun()
                st.divider()
