import streamlit as st
from datetime import datetime

# 1. Configuração da página web 
st.set_page_config(page_title="FgERP - Demonstrativo Negócios", layout="centered")

# =========================================================================
# 2. INICIALIZAÇÃO FIXA DO BANCO DE DADOS 
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
# 3. VALIDAÇÃO DE ACESSO (TELA DE LOGIN)
# =========================================================================
if not st.session_state.logado:
    st.title("🔒 FgERP - Acesso Restrito")
    st.subheader("Área de Demonstração Comercial")
    
    usuario = st.text_input("Usuário:", key="login_usuario")
    senha = st.text_input("Senha:", type="password", key="login_senha")
    
    if st.button("Iniciar Sistema (Start)"):
        if usuario == "admin" and senha == "1234":
            st.session_state.logado = True
            st.success("Acesso concedido! Carregando...")
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")
    
    # Trava o sistema aqui caso não esteja logado
    st.stop()

# =========================================================================
# 4. SISTEMA LIBERADO (Só roda se st.session_state.logado for True)
# =========================================================================

# --- MENU LATERAL DE NAVEGAÇÃO ---
st.sidebar.title("=== FgERP ===")
st.sidebar.subheader("SISTEMA DE GESTÃO")

opcoes_menu = ["Início", "Estoque", "Clientes", "Registrar Venda", "Contas a Pagar / Receber"]
# Controla o menu de forma reativa 
if st.session_state.menu_atual not in opcoes_menu:
    st.session_state.menu_atual = "Início"
# Agora o rádio roda 100% 
escolha = st.sidebar.radio(
    "Escolha um Módulo:", 
    opcoes_menu, 
    index=opcoes_menu.index(st.session_state.menu_atual)
)
st.session_state.menu_atual = escolha

# Botão de Logout no final do menu lateral
st.sidebar.markdown("---")
if st.sidebar.button("🚪 Sair do Sistema"):
    st.session_state.logado = False
    st.rerun()

# ==========================================
# TELA 0: INÍCIO
# ==========================================
if st.session_state.menu_atual == "Início":
    st.title("📊 Painel Principal - FgERP")
    st.write("Bem-vindo ao seu Sistema de Gestão Web Integrado!")
    st.info("Utilize o menu na barra lateral esquerda para navegar entre os módulos.")

# ==========================================
# TELA 1: ESTOQUE
# ==========================================
elif st.session_state.menu_atual == "Estoque":
    st.title("📦 Gestão de Estoque")
    aba1, aba2 = st.tabs(["➕ Entrada de Estoque", "📋 Listar Produtos"])
    
    with aba1:
        st.subheader("Entrada de Novo Produto")
        nome = st.text_input("Nome do produto", key="prod_nome_input")
        preco = st.number_input("Preço de venda (R$)", min_value=0.0, step=0.01, format="%.2f", key="prod_preco_input")
        qtd = st.number_input("Quantidade de entrada", min_value=0, step=1, key="prod_qtd_input")
        
        st.markdown("---")
        st.subheader("💳 Dados de Custo (Financeiro)")
        custo_unitario = st.number_input("Custo Unitário de Compra (R$)", min_value=0.0, step=0.01, format="%.2f", key="prod_custo_input")
        forma_pag_custo = st.selectbox("Forma de Pagamento do Fornecedor:", ["Boleto bancário", "À Vista (Dinheiro/Pix)", "Prazo Fornecedor"], key="prod_forma_input")
        
        if st.button("Gravar Entrada e Gerar Custo", key="btn_gravar_produto"):
            if nome.strip() != "":
                id_atual = st.session_state.proximo_id_prod
                st.session_state.estoque[id_atual] = {"nome": nome, "preco": preco, "qtd": qtd}
                
                valor_custo_total = custo_unitario * qtd
                status_inicial = "Pago" if "À Vista" in forma_pag_custo else "Aberto"
                
                st.session_state.financeiro.append({
                    "id_lancamento": len(st.session_state.financeiro) + 1,
                    "tipo": "Pagar",
                    "descricao": f"Compra de Estoque: {nome} (Qtd: {qtd})",
                    "valor": valor_custo_total,
                    "forma": forma_pag_custo,
                    "status": status_inicial,
                    "data": datetime.now().strftime("%d/%m/%Y")
                })
                
                st.success(f"✅ Produto '{nome}' cadastrado com ID {id_atual}!")
                st.session_state.proximo_id_prod += 1
                st.rerun() # Força o Streamlit a atualizar as listas imediatamente
            else:
                st.error("❌ Erro: O nome do produto não pode ficar em branco.")
                
    with aba2:
        st.subheader("Produtos em Estoque")
        if not st.session_state.estoque:
            st.info("Nenhum produto cadastrado até o momento.")
        else:
            dados_tabela = [{"ID": id_p, "Produto": info["nome"], "Preço Venda": f"R$ {info['preco']:.2f}", "Quantidade": f"{info['qtd']} un"} for id_p, info in st.session_state.estoque.items()]
            st.table(dados_tabela)

# ==========================================
# TELA 2: CLIENTES
# ==========================================
elif st.session_state.menu_atual == "Clientes":
    st.title("👥 Gestão de Clientes")
    aba1, aba2 = st.tabs(["➕ Cadastrar Cliente", "📋 Listar Clientes"])
    
    with aba1:
        st.subheader("Novo Cliente")
        nome_cli = st.text_input("Nome do cliente", key="cli_nome_input")
        tel = st.text_input("Telefone (com DDD)", key="cli_tel_input")
        
        if st.button("Gravar Cliente no Sistema", key="btn_gravar_cliente"):
            if nome_cli.strip() != "":
                id_atual = st.session_state.proximo_id_cli
                st.session_state.clientes[id_atual] = {"nome": nome_cli, "telefone": tel}
                st.success(f"✅ Cliente '{nome_cli}' cadastrado com ID {id_atual}!")
                st.session_state.proximo_id_cli += 1
                st.rerun() # Força a atualização imediata da aba de listagem
            else:
                st.error("❌ Erro: O nome do cliente não pode ficar em branco.")
                
    with aba2:
        st.subheader("Clientes Cadastrados")
        if not st.session_state.clientes:
            st.info("Nenhum cliente cadastrado até o momento.")
        else:
            dados_clientes = [{"ID": id_c, "Nome": info["nome"], "Telefone": info["telefone"]} for id_c, info in st.session_state.clientes.items()]
            st.table(dados_clientes)

# ==========================================
# TELA 3: REGISTRAR VENDA
# ==========================================
elif st.session_state.menu_atual == "Registrar Venda":
    st.title("🛒 Registrar Venda (Faturamento)")
    
    if not st.session_state.clientes or not st.session_state.estoque:
        st.warning("⚠️ Atenção: Cadastre pelo menos 1 cliente e 1 produto antes de realizar uma venda.")
    else:
        opcoes_clientes = {id_c: f"{id_c} - {info['nome']}" for id_c, info in st.session_state.clientes.items()}
        opcoes_produtos = {id_p: f"{id_p} - {info['nome']} (Disponível: {info['qtd']})" for id_p, info in st.session_state.estoque.items()}
        
        id_cli = st.selectbox("Selecione o Cliente:", options=list(opcoes_clientes.keys()), format_func=lambda x: opcoes_clientes[x], key="venda_cli_select")
        id_prod = st.selectbox("Selecione o Produto:", options=list(opcoes_produtos.keys()), format_func=lambda x: opcoes_produtos[x], key="venda_prod_select")
        qtd_venda = st.number_input("Quantidade a vender", min_value=1, step=1, key="venda_qtd_input")
        tipo_pagamento = st.selectbox("Forma de Recebimento:", ["À Vista (Dinheiro/Pix)", "Crediário (Conta Corrente Cliente)", "Boleto bancário"], key="venda_forma_input")
        
        if st.button("Finalizar Venda", key="btn_finalizar_venda"):
            estoque_atual = st.session_state.estoque[id_prod]["qtd"]
            if estoque_atual < qtd_venda:
                st.error(f"❌ Estoque insuficiente! Quantidade atual em estoque: {estoque_atual}")
            else:
                st.session_state.estoque[id_prod]["qtd"] -= qtd_venda
                valor_total = st.session_state.estoque[id_prod]["preco"] * qtd_venda
                
                st.session_state.vendas.append({
                    "cliente": st.session_state.clientes[id_cli]["nome"],
                    "produto": st.session_state.estoque[id_prod]["nome"],
                    "qtd": qtd_venda,
                    "total": valor_total
                })
                
                status_venda = "Pago" if tipo_pagamento == "À Vista (Dinheiro/Pix)" else "Aberto"
                
                st.session_state.financeiro.append({
                    "id_lancamento": len(st.session_state.financeiro) + 1,
                    "tipo": "Receber",
                    "descricao": f"Venda para {st.session_state.clientes[id_cli]['nome']} ({st.session_state.estoque[id_prod]['nome']})",
                    "valor": valor_total,
                    "forma": tipo_pagamento,
                    "status": status_venda,
                    "data": datetime.now().strftime("%d/%m/%Y")
                })
                
                st.success(f"🎉 Venda processada!")
                st.metric(label="Total da Venda Atual", value=f"R$ {valor_total:.2f}")
                st.rerun()

# ==========================================
# TELA 4: CONTAS A PAGAR / RECEBER
# ==========================================
elif st.session_state.menu_atual == "Contas a Pagar / Receber":
    st.title("💸 Módulo Financeiro")
    
    aba_fin1, aba_fin2, aba_fin3 = st.tabs(["📊 Fluxo Geral", "📉 Contas a Pagar", "📈 Contas a Receber"])
    
    with aba_fin1:
        st.subheader("Resumo de Caixa")
        total_pago = sum(item["valor"] for item in st.session_state.financeiro if item["tipo"] == "Pagar" and item["status"] == "Pago")
        total_a_pagar = sum(item["valor"] for item in st.session_state.financeiro if item["tipo"] == "Pagar" and item["status"] == "Aberto")
        total_recebido = sum(item["valor"] for item in st.session_state.financeiro if item["tipo"] == "Receber" and item["status"] == "Pago")
        total_a_receber = sum(item["valor"] for item in st.session_state.financeiro if item["tipo"] == "Receber" and item["status"] == "Aberto")
        
        col1, col2 = st.columns(2)
        col1.metric("Total em Caixa (Recebido)", f"R$ {total_recebido:.2f}")
        col1.metric("Contas a Receber", f"R$ {total_a_receber:.2f}")
        
        col2.metric("Total Despendido", f"R$ {total_pago:.2f}")
        col2.metric("Contas a Pagar Pendentes", f"R$ {total_a_pagar:.2f}")
        
    with aba_fin2:
        st.subheader("📌 Obrigações (Contas a Pagar)")
        pagar_list = [item for item in st.session_state.financeiro if item["tipo"] == "Pagar"]
        
        if not pagar_list:
            st.info("Nenhuma conta a pagar registrada.")
        else:
            for item in pagar_list:
                cor_status = "🔴" if item["status"] == "Aberto" else "🟢"
                st.markdown(f"**{cor_status} {item['descricao']}**")
                st.write(f"Valor: R$ {item['valor']:.2f} | Forma: {item['forma']} | Data: {item['data']}")
                
                if item["status"] == "Aberto":
                    if st.button(f"Confirmar Pagamento ID: {item['id_lancamento']}", key=f"pag_btn_{item['id_lancamento']}"):
                        item["status"] = "Pago"
                        st.success("Conta marcada como PAGA!")
                        st.rerun()
                st.divider()
                
    with aba_fin3:
        st.subheader("📌 Direitos (Contas a Receber)")
        receber_list = [item for item in st.session_state.financeiro if item["tipo"] == "Receber"]
        
        if not receber_list:
            st.info("Nenhuma conta a receber registrada.")
        else:
            for item in receber_list:
                cor_status = "🔴" if item["status"] == "Aberto" else "🟢"
                st.markdown(f"**{cor_status} {item['descricao']}**")
                st.write(f"Valor: R$ {item['valor']:.2f} | Forma: {item['forma']} | Data: {item['data']}")
                
                if item["status"] == "Aberto":
                    if st.button(f"Receber Valor ID: {item['id_lancamento']}", key=f"rec_btn_{item['id_lancamento']}"):
                        item["status"] = "Pago"
                        st.success("Saldo recebido!")
                        st.rerun()
                st.divider()
