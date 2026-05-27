import streamlit as st
from datetime import datetime
import json
import os

# 1. Configuração da página web
st.set_page_config(page_title="FgERP - Banco de Dados Permanente", layout="centered")

# =========================================================================
# 2. SISTEMA DE ARMAZENAMENTO PERMANENTE (ARQUIVOS JSON)
# =========================================================================
ARQUIVO_ESTOQUE = "banco_estoque.json"
ARQUIVO_CLIENTES = "banco_clientes.json"
ARQUIVO_VENDAS = "banco_vendas.json"
ARQUIVO_FINANCEIRO = "banco_financeiro.json"

# Função para carregar dados do arquivo de texto para a memória do sistema
def carregar_dados_arquivo(nome_arquivo):
    if os.path.exists(nome_arquivo):
        try:
            with open(nome_arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {} if "banco_vendas" not in nome_arquivo and "banco_financeiro" not in nome_arquivo else []
    # Retorna dicionário ou lista vazia dependendo do arquivo se ele não existir
    if "banco_vendas" in nome_arquivo or "banco_financeiro" in nome_arquivo:
        return []
    return {}

# Função para salvar os dados da memória de volta para o arquivo de texto
def salvar_dados_arquivo(dados, nome_arquivo):
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# --- INICIALIZAÇÃO INTEGRADA (Lê os arquivos salvos ao invés de começar do zero) ---
if "estoque" not in st.session_state:
    # Como o JSON transforma chaves de dicionário em texto, convertemos de volta para número (ID)
    dados_carregados = carregar_dados_arquivo(ARQUIVO_ESTOQUE)
    st.session_state.estoque = {int(k): v for k, v in dados_carregados.items()}

if "clientes" not in st.session_state:
    dados_carregados = carregar_dados_arquivo(ARQUIVO_CLIENTES)
    st.session_state.clientes = {int(k): v for k, v in dados_carregados.items()}

if "vendas" not in st.session_state:
    st.session_state.vendas = carregar_dados_arquivo(ARQUIVO_VENDAS)

if "financeiro" not in st.session_state:
    st.session_state.financeiro = carregar_dados_arquivo(ARQUIVO_FINANCEIRO)

# Define os próximos IDs com base no que já está cadastrado para não duplicar
if "proximo_id_prod" not in st.session_state:
    st.session_state.proximo_id_prod = max(st.session_state.estoque.keys()) + 1 if st.session_state.estoque else 1
if "proximo_id_cli" not in st.session_state:
    st.session_state.proximo_id_cli = max(st.session_state.clientes.keys()) + 1 if st.session_state.clientes else 1

if "menu_atual" not in st.session_state:
    st.session_state.menu_atual = "Início"
if "logado" not in st.session_state:
    st.session_state.logado = False

# Função auxiliar para recalcular limites (Mantida e integrada para salvar as mudanças)
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
    # Salva a alteração do limite no arquivo
    salvar_dados_arquivo(st.session_state.clientes, ARQUIVO_CLIENTES)

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
    st.write("Sistema de Gestão Comercial com Banco de Dados Local Ativo!")
    st.success("💾 Todos os dados cadastrados nesta sessão estão sendo salvos permanentemente em arquivos JSON.")

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
                    "atrasado": False, "data_vencimento": vencimento_custo.strftime("%Y-%m-%d")
                })
                st.session_state.proximo_id_prod += 1
                
                # SALVAMENTO EM ARQUIVO REAL
                salvar_dados_arquivo(st.session_state.estoque, ARQUIVO_ESTOQUE)
                salvar_dados_arquivo(st.session_state.financeiro, ARQUIVO_FINANCEIRO)
                
                st.success(f"✅ Produto '{nome}' cadastrado e salvo no arquivo!")
                st.rerun()

    with aba2:
        if not st.session_state.estoque: st.info("Nenhum produto cadastrado.")
        else: st.table([{"ID": id_p, "Produto": info["nome"], "Preço Venda": f"R$ {info['preco']:.2f}", "Quantidade": f"{info['qtd']} un"} for id_p, info in st.session_state.estoque.items()])

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
                    "nome": nome_cli, "telefone": tel, "endereco": endereco, "bairro": bairro, "cidade": cidade,
                    "renda": renda, "limite_credito": renda * 0.30, "status_credito": "Regular (Sem histórico)"
                }
                st.session_state.proximo_id_cli += 1
                
                # SALVAMENTO EM ARQUIVO REAL
                salvar_dados_arquivo(st.session_state.clientes, ARQUIVO_CLIENTES)
                
                st.success("✅ Cliente gravado e salvo no arquivo!")
                st.rerun()

    with aba2:
        if not st.session_state.clientes: st.info("Nenhum cliente cadastrado.")
        else: st.table([{"ID": id_c, "Nome": info["nome"], "Cidade/Bairro": f"{info['cidade']} - {info['bairro']}", "Renda": f"R$ {info['renda']:.2f}", "LIMITE DISPONÍVEL": f"R$ {info['limite_credito']:.2f}", "Status": info["status_credito"]} for id_c, info in st.session_state.clientes.items()])

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
                st.session_state.vendas.append({"cliente": cliente["nome"], "produto": st.session_state.estoque[id_prod]["nome"], "qtd": qtd_venda, "total": valor_total})
                
                st.session_state.financeiro.append({
                    "id_lancamento": len(st.session_state.financeiro) + 1, "tipo": "Receber",
                    "descricao": f"Venda: {cliente['nome']}", "valor": valor_total,
                    "forma": tipo_pagamento, "status": "Pago" if tipo_pagamento == "À Vista" else "Aberto",
                    "atrasado": False, "data_vencimento": vencimento_venda.strftime("%Y-%m-%d")
                })
                
                # SALVAMENTO EM ARQUIVO REAL (Atualiza estoque, vendas e financeiro de uma vez)
                salvar_dados_arquivo(st.session_state.estoque, ARQUIVO_ESTOQUE)
                salvar_dados_arquivo(st.session_state.vendas, ARQUIVO_VENDAS)
                salvar_dados_arquivo(st.session_state.financeiro, ARQUIVO_FINANCEIRO)
                
                st.success("🎉 Venda processada e gravada com sucesso!")
                st.rerun()

# ==========================================
# TELA 4: CONTAS A PAGAR / RECEBER
# ==========================================
elif st.session_state.menu_atual == "Contas a Pagar / Receber":
    st.title("💸 Central de Obrigações e Direitos")
    aba_fin1, aba_fin2, aba_fin3 = st.tabs(["➕ Lançar Boleto Manual", "📉 Contas a Pagar", "📈 Contas a Receber"])
    
    with aba_fin1:
        st.subheader("Cadastro Manual de Contas")
        tipo_manual = st.selectbox("Tipo de Lançamento:", ["Pagar (Despesa/Boleto)", "Receber (Outras Receitas)"])
        desc_manual = st.text_input("Descrição do Boleto (Ex: Boleto Água, Aluguel):")
        valor_manual = st.number_input("Valor Nominal (R$):", min_value=0.0, step=10.0, format="%.2f")
        forma_manual = st.selectbox("Forma de Operação:", ["Boleto bancário", "Dinheiro/Pix", "Cartão"])
        venc_manual = st.date_input("Data de Vencimento:", datetime.now())
        status_manual = st.selectbox("Status Inicial:", ["Aberto", "Pago"])
        
        if st.button("Salvar Lançamento Financeiro"):
            if desc_manual.strip() != "":
                st.session_state.financeiro.append({
                    "id_lancamento": len(st.session_state.financeiro) + 1,
                    "tipo": "Pagar" if "Pagar" in tipo_manual else "Receber",
                    "descricao": desc_manual, "valor": valor_manual, "forma": forma_manual,
                    "status": status_manual, "atrasado": False, "data_vencimento": venc_manual.strftime("%Y-%m-%d")
                })
                # SALVAMENTO EM ARQUIVO REAL
                salvar_dados_arquivo(st.session_state.financeiro, ARQUIVO_FINANCEIRO)
                st.success("✅ Conta cadastrada!")
                st.rerun()
                
    with aba_fin2:
        st.subheader("📌 Obrigações (Contas a Pagar)")
        pagar_list = [item for item in st.session_state.financeiro if item["tipo"] == "Pagar"]
        
        if not pagar_list:
            st.info("Nenhum registro de conta a pagar.")
        else:
            dados_pagar = []
            contas_abertas_id = []
            
            for item in pagar_list:
                status_sinal = "🔴 Aberto" if item["status"] == "Aberto" else "🟢 Pago"
                dados_pagar.append({
                    "ID": item["id_lancamento"],
                    "Descrição": item["descricao"],
                    "Valor": f"R$ {item['valor']:.2f}",
                    "Vencimento": item["data_vencimento"],
                    "Forma": item["forma"],
                    "Situação": status_sinal
                })
                if item["status"] == "Aberto":
                    contas_abertas_id.append(item["id_lancamento"])
            
            st.dataframe(dados_pagar, use_container_width=True, hide_index=True)
            
            if contas_abertas_id:
                st.markdown("---")
                id_para_pagar = st.selectbox("Selecione o ID da conta para dar Baixa (Pagar):", contas_abertas_id, key="sel_id_pagar")
                if st.button("Confirmar Pagamento da Conta Selecionada", key="btn_confirmar_pagamento"):
                    for item in st.session_state.financeiro:
                        if item["id_lancamento"] == id_para_pagar:
                            item["status"] = "Pago"
                    salvar_dados_arquivo(st.session_state.financeiro, ARQUIVO_FINANCEIRO)
                    st.success(f"✅ Conta ID {id_para_pagar} marcada como PAGA!")
                    st.rerun()
            else:
                st.success("🎉 Excelente! Não há contas pendentes de pagamento.")

    with aba_fin3:
        st.subheader("📌 Direitos (Contas a Receber)")
        receber_list = [item for item in st.session_state.financeiro if item["tipo"] == "Receber"]
        
        if not receber_list:
            st.info("Nenhum registro de conta a receber.")
        else:
            dados_receber = []
            contas_receber_id = []
            
            for item in receber_list:
                status_sinal = "🔴 Aberto" if item["status"] == "Aberto" else "🟢 Pago"
                if item.get("atrasado", False):
                    status_sinal = "⚠️ Inadimplente"
                    
                dados_receber.append({
                    "ID": item["id_lancamento"],
                    "Descrição": item["descricao"],
                    "Valor": f"R$ {item['valor']:.2f}",
                    "Vencimento": item["data_vencimento"],
                    "Forma": item["forma"],
                    "Situação": status_sinal
                })
                if item["status"] == "Aberto":
                    contas_receber_id.append(item["id_lancamento"])
            
            st.dataframe(dados_receber, use_container_width=True, hide_index=True)
            
            if contas_receber_id:
                st.markdown("---")
                id_para_receber = st.selectbox("Selecione o ID da conta para receber/ações:", contas_receber_id, key="sel_id_receber")
                
                col_c1, col_c2 = st.columns(2)
                
                if col_c1.button("Liquidar (Receber Valor)", key="btn_liq_receber"):
                    for item in st.session_state.financeiro:
                        if item["id_lancamento"] == id_para_receber:
                            item["status"] = "Pago"
                            for id_c, cli in st.session_state.clientes.items():
                                if cli["nome"] in item["descricao"]:
                                    atualizar_limite_cliente(id_c)
                    salvar_dados_arquivo(st.session_state.financeiro, ARQUIVO_FINANCEIRO)
                    st.success(f"✅ Saldo do ID {id_para_receber} recebido!")
                    st.rerun()
                    
                if col_c2.button("⚠️ Marcar como Inadimplente", key="btn_inad_receber"):
                    for item in st.session_state.financeiro:
                        if item["id_lancamento"] == id_para_receber:
                            item["atrasado"] = True
                            for id_c, cli in st.session_state.clientes.items():
                                if cli["nome"] in item["descricao"]:
                                    atualizar_limite_cliente(id_c)
                    salvar_dados_arquivo(st.session_state.financeiro, ARQUIVO_FINANCEIRO)
                    st.error(f"🔴 ID {id_para_receber} marcado como inadimplente. Crédito do cliente bloqueado!")
                    st.rerun()
            else:
                st.success("🎉 Nenhuma pendência de recebimento dos clientes.")

# ==========================================
# TELA 5: FLUXO DE CAIXA DIÁRIO
# ==========================================
elif st.session_state.menu_atual == "📊 Fluxo de Caixa Diário":
    st.title("📊 Relatório: Fluxo de Caixa Diário")
    
    if not st.session_state.financeiro:
        st.info("Sem movimentações financeiras para gerar o relatório.")
    else:
        datas_encontradas = sorted(list(set(item["data_vencimento"] for item in st.session_state.financeiro)))
        saldo_acumulado = 0.0
        
        for data_venc in datas_encontradas:
            data_formatada = datetime.strptime(data_venc, "%Y-%m-%d").strftime("%d/%m/%Y")
            itens_do_dia = [item for item in st.session_state.financeiro if item["data_vencimento"] == data_venc]
            
            entradas_dia = sum(item["valor"] for item in itens_do_dia if item["tipo"] == "Receber")
            saidas_dia = sum(item["valor"] for item in itens_do_dia if item["tipo"] == "Pagar")
            saldo_dia = entradas_dia - saidas_dia
            saldo_acumulado += saldo_dia
            
            with st.expander(f"📅 Dia {data_formatada} | Saldo do Dia: R$ {saldo_dia:.2f}"):
                dados_dia_tabela = [{"Fluxo": "🟩 (+)" if item["tipo"] == "Receber" else "🟥 (-)", "Descrição": item["descricao"], "Forma": item["forma"], "Valor": f"R$ {item['valor']:.2f}", "Situação": item["status"]} for item in itens_do_dia]
                st.table(dados_dia_tabela)
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Entradas", f"R$ {entradas_dia:.2f}")
                c2.metric("Total Saídas", f"R$ {saidas_dia:.2f}")
                c3.metric("Saldo Acumulado", f"R$ {saldo_acumulado:.2f}")
