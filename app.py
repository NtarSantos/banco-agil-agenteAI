import streamlit as st
import os
import re
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from src.graph import app as graph_app

# ... imports ...
import os
import pandas as pd

# --- [SOLUÇÃO] GARANTIR DADOS NO DEPLOY ---
def garantir_dados():
    if not os.path.exists("data"):
        os.makedirs("data")
    
    # Se o cliente.csv não existe, cria ele agora
    if not os.path.exists("data/clientes.csv"):
        print("⚠️ CSVs não encontrados. Criando base de dados inicial...")
        
        # 1. Clientes
        data_clientes = {
            "cpf": ["12345678900", "98765432100", "11122233344"],
            "nome": ["João Silva", "Maria Oliveira", "Carlos Souza"],
            "data_nascimento": ["1990-01-01", "1985-05-15", "2000-12-10"],
            "score_atual": [500, 800, 300],
            "renda_mensal": [3000.0, 8000.0, 1500.0],
            "limite_atual": [1000.0, 5000.0, 200.0]
        }
        pd.DataFrame(data_clientes).to_csv("data/clientes.csv", index=False)

        # 2. Score
        data_score = {
            "score_min": [0, 300, 500, 700, 900],
            "score_max": [299, 499, 699, 899, 1000],
            "limite_maximo": [0.0, 500.0, 2000.0, 10000.0, 50000.0]
        }
        pd.DataFrame(data_score).to_csv("data/score_limite.csv", index=False)

        # 3. Solicitações
        cols = ["cpf_cliente", "data_hora_solicitacao", "limite_atual", "novo_limite_solicitado", "status_pedido"]
        pd.DataFrame(columns=cols).to_csv("data/solicitacoes_aumento_limite.csv", index=False)
        
        print("✅ Base de dados recriada com sucesso!")

# Chama a função antes de qualquer coisa
garantir_dados()

load_dotenv()

st.set_page_config(page_title="Banco Ágil - Atendimento IA", page_icon="🏦")
st.title("🏦 Banco Ágil - Atendimento Inteligente")
st.markdown("---")

# --- MEMÓRIA DO STREAMLIT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if "cpf" not in st.session_state:
    st.session_state.cpf = None

if "ultimo_agente" not in st.session_state:
    st.session_state.ultimo_agente = None

if "tentativas" not in st.session_state:
    st.session_state.tentativas = 0

# Mostra histórico
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.markdown(msg.content)
    elif isinstance(msg, AIMessage):
        with st.chat_message("assistant"):
            st.markdown(msg.content)

# Input do usuário
if prompt := st.chat_input("Digite sua mensagem..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append(HumanMessage(content=prompt))
    
    # --- [LÓGICA NOVA] CAPTURAR CPF ---
    # Se ainda não logou e o usuário digitou 11 números, assumimos que é o CPF.
    if not st.session_state.autenticado:
        # Remove tudo que não é número
        apenas_numeros = re.sub(r'\D', '', prompt)
        if len(apenas_numeros) == 11:
            st.session_state.cpf = apenas_numeros
            # Dica: Em um app real, validaríamos mais coisas, mas aqui serve!

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("⏳ *Processando...*")
        full_response = ""
        
        # PREPARA O INPUT PARA O GRAFO
        inputs = {
            "messages": st.session_state.messages,
            "autenticado": st.session_state.autenticado,
            "cpf": st.session_state.cpf ,
            "ultimo_agente": st.session_state.ultimo_agente,
            "tentativas_falhas": st.session_state.tentativas #Envia contagem atual
        }
        
        try:
            output = graph_app.invoke(inputs, config={"recursion_limit": 50})
            
            if "ultimo_agente" in output:
                novo_agente = output["ultimo_agente"]
                # Só atualizamos se vier algo válido (não vazio)
                if novo_agente:
                    st.session_state.ultimo_agente = novo_agente
                    print(f"MEMÓRIA ATUALIZADA: Fixado em -> {novo_agente}")

                # [NOVO] Pega a contagem atualizada do robô
                if "tentativas_falhas" in output:
                    st.session_state.tentativas = output["tentativas_falhas"]

            ultima_msg = output["messages"][-1]
            full_response = ultima_msg.content

            full_response = full_response.replace("$", " ")
            
            # Verifica se autenticou
            if "autenticado" in full_response.lower() or "bem-vindo" in full_response.lower() or "prazer" in full_response.lower():
                 st.session_state.autenticado = True
            
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            st.error(f"Erro no sistema: {e}")
            full_response = "Desculpe, tive um erro interno."

    st.session_state.messages.append(AIMessage(content=full_response))