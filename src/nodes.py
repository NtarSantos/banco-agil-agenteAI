# src/nodes.py
import re
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage
from langchain_community.tools.tavily_search import TavilySearchResults

from src.state import BankState
from src.tools import (
    validar_cpf,
    consultar_limite,
    solicitar_aumento_limite,
    atualizar_score_entrevista,
)

llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)


# ======================================================
# --- CENTRAL DE PROMPTS (Fácil de editar) ---
# ======================================================
PROMPTS = {
    "sistema_bia_sem_dados": """Você é a **Bia**, a consultora digital do **Banco Ágil**, seja simpática e atenciosa.
    **Sua Diretriz Principal:** NENHUMA informação ou serviço pode ser discutido antes da identificação do cliente.
    **Fluxo de Atendimento Obrigatório:**
    1. **Saudação e Identificação:** Apresente-se e peça o CPF.
    2. **Oferta de Serviços:** APENAS após validar o CPF, apresente o menu:
       - Consultar Limite de Crédito.
       - Entrevista para Aumento de Score.
       - Câmbio de Moedas.
    **Regra de Ouro:** Se o usuário perguntar algo antes do CPF, peça a identificação educadamente.""",

    "sistema_bia_com_dados": "Use a ferramenta 'validar_cpf' com os dados informados.",

    "classificador": """
    O usuário já está autenticado. Direcione-o para o agente correto.
    
    CONTEXTO: O Robô disse: "{contexto_anterior}"
    USUÁRIO disse: "{texto}"
    
    Responda APENAS UMA palavra:
    CAMBIO      -> Moeda, dólar, euro, cotação.
    ENTREVISTA  -> Entrevista, perguntas, sim (se foi oferecido entrevista), aumento de score.
    CREDITO     -> Limite de crédito, aumento, crédito, cartão, menu.
    
    Se for saudação ou não souber, mande para CREDITO.
    """,

    "credito": "Especialista de Crédito, seja simpática e atenciosa. CPF: {cpf}. Use tools. Sem LaTeX.",
    
    "cambio": "Especialista de Câmbio, seja simpática e atenciosa. Use Tavily.",
    
    "entrevista": """Agente de Entrevista seja simpática e atenciosa. CPF: {cpf}. Faça 5 perguntas, uma por vez de forma educada, são elas:
        Qual é a sua renda mensal atual?
        Quais são suas despesas fixas mensais?
        Você está empregado? Se sim, qual é o seu tipo de emprego (formal, autônomo ou desempregado)?
        Você tem dependentes? Se sim, quantos?
        Você possui dívidas atualmente? (Sim ou Não)
        Chame tool no final. Diga REDIRECIONANDO e pergunte se o cliente gostaria de realizar uma nova análise de crédito"""
}

# --- NÓ 1: TRIAGEM UNIFICADA (Autentica + Direciona) ---
def node_triagem(state: BankState):
    print("--- NODE: TRIAGEM (SUPER) ---")
    
    mensagens = state["messages"]
    ultima_msg = mensagens[-1]
    texto = ultima_msg.content.lower()
    
    termos_saida = ["sair", "encerrar", "tchau", "fim", "parar", "logout"]
    
    # Se o usuário disse alguma dessas palavras
    if any(termo in texto for termo in termos_saida):
        print("Usuário solicitou encerramento.")
        
        # Mensagem de despedida
        msg_tchau = AIMessage(content="Atendimento encerrado com segurança. Obrigado por usar o Banco Ágil! Se precisar, é só chamar novamente. 👋")
        
        # AQUI ACONTECE A MÁGICA:
        # Nós sobrescrevemos o estado para limpar tudo.
        # Devolvemos autenticado=False e cpf=None.
        return {
            "messages": [msg_tchau],
            "autenticado": False,  # <--- Desloga
            "cpf": None,           # <--- Esquece o CPF
            "ultimo_agente": None, # <--- Limpa o histórico
            "tentativas_falhas": 0 # <--- Reseta erros
        }

    # 1. LÓGICA DE RETORNO RÁPIDO (Sticky Routing)
    # Se o usuário estava falando com um especialista, mandamos de volta pra ele
    # sem nem pensar. Isso mantém o usuário "preso" na entrevista ou no crédito.
    ultimo_agente = state.get("ultimo_agente")
    
    if ultimo_agente == "entrevista":
        # Verifica se a entrevista acabou (pela palavra chave do agente)
        if len(mensagens) > 1:
            msg_robo_anterior = mensagens[-2].content.upper()
            if "REDIRECIONANDO" in msg_robo_anterior:
                print("-> Fim da entrevista detectado. Liberando para Crédito.")
                return {"proximo_agente": "credito"}
        
        print("-> Mantendo usuário preso na ENTREVISTA.")
        return {"proximo_agente": "entrevista"}

    # 2. LÓGICA DE AUTENTICAÇÃO 
    if not (state.get("autenticado") and state.get("cpf")):
        # -- Sub-fluxo de Autenticação --
        qtd_numeros = len(re.findall(r"\d", texto))
        
        if qtd_numeros < 3:
            # Modo Conversa (Sem dados)
            print("-> Triagem: Conversando (Sem dados).")
            llm_ativo = llm
            msg_sistema = """Você é a **Bia**, a consultora digital do **Banco Ágil**, seja simpática e atenciosa.
            **Sua Diretriz Principal:** NENHUMA informação ou serviço pode ser discutido antes da identificação do cliente.
            **Fluxo de Atendimento Obrigatório:**
            1. **Saudação e Identificação:** - Ao iniciar a conversa, apresente-se brevemente e solicite IMEDIATAMENTE o 
            CPF do cliente para acessar o ambiente seguro.
            - *Exemplo de fala:* "Olá! Sou a Bia do Banco Ágil. Para começarmos e eu acessar seus dados com segurança, 
            por favor, digite o seu CPF."
            2. **Oferta de Serviços:** - APENAS após o usuário fornecer o CPF, valide o recebimento (simule uma confirmação) 
            e apresente o menu:
                - Consultar Limite de Crédito.
                - Entrevista para Aumento de Score.
                - Câmbio de Moedas.
            **Regra de Ouro:** Se o usuário perguntar qualquer coisa ou solicitar um serviço antes de fornecer o CPF, 
            educadamente que precisa da identificação primeiro para prosseguir..
            """
        else:
            # Modo Validação (Com dados)
            print("-> Triagem: Validando CPF.")
            ferramentas = [validar_cpf]
            llm_ativo = llm.bind_tools(ferramentas)
            msg_sistema = "Use a ferramenta 'validar_cpf' com os dados informados."

        resposta = llm_ativo.invoke([SystemMessage(content=msg_sistema)] + mensagens)
        return {"messages": [resposta], "ultimo_agente": "triagem"}

    # 3. LÓGICA DE DIRECIONAMENTO 
    print("-> Usuário Autenticado. Triagem decidindo destino...")
    
    # Recupera contexto anterior para decisão melhor
    contexto_anterior = ""
    if len(mensagens) > 1 and isinstance(mensagens[-2], AIMessage):
        contexto_anterior = mensagens[-2].content

    prompt_classificacao = f"""
    O usuário já está autenticado. Direcione-o para o agente correto.
    
    CONTEXTO: O Robô disse: "{contexto_anterior}"
    USUÁRIO disse: "{texto}"
    
    Responda APENAS UMA palavra:
    CAMBIO      -> Moeda, dólar, euro, cotação.
    ENTREVISTA  -> Entrevista, perguntas, sim (se foi oferecido entrevista), aumento de score.
    CREDITO     -> Limite de crédito, aumento, crédito, cartão.
    
    Se for saudação ou não souber, mande para CREDITO (Menu Principal).
    """
    
    classificador = ChatOpenAI(model="gpt-4.1-mini", temperature=1)
    resposta_class = classificador.invoke(prompt_classificacao)
    intencao = resposta_class.content.strip().upper()
    
    print(f"Direcionando para: {intencao}")
    
    if "CAMBIO" in intencao: return {"proximo_agente": "cambio"}
    if "ENTREVISTA" in intencao: return {"proximo_agente": "entrevista"}
    return {"proximo_agente": "credito"} # Padrão

# ======================================================
# --- NÓS ESPECIALISTAS (MANTENHA IGUAL) ---
# ======================================================
def node_credito(state: BankState):
    print("--- NODE: CRÉDITO ---")
    cpf_usuario = state.get("cpf")
    msg = f"Especialista de Crédito, seja simpática e atenciosa. CPF: {cpf_usuario}. Use tools. Sem LaTeX."
    tools = [consultar_limite, solicitar_aumento_limite]
    resp = llm.bind_tools(tools).invoke([SystemMessage(content=msg)] + state["messages"])
    return {"messages": [resp], "ultimo_agente": "credito"}

def node_cambio(state: BankState):
    print("--- NODE: CÂMBIO ---")
    msg = "Especialista de Câmbio, seja simpática e atenciosa. Use Tavily."
    tool = TavilySearchResults(max_results=1)
    resp = llm.bind_tools([tool]).invoke([SystemMessage(content=msg)] + state["messages"])
    return {"messages": [resp], "ultimo_agente": "cambio"}

def node_entrevista(state: BankState):
    print("--- NODE: ENTREVISTA ---")
    cpf = state.get("cpf")
    msg = f"""Agente de Entrevista seja simpática e atenciosa. CPF: {cpf}. Faça 5 perguntas, uma por vez de forma educada, são elas:
        Qual é a sua renda mensal atual?
        Quais são suas despesas fixas mensais?
        Você está empregado? Se sim, qual é o seu tipo de emprego (formal, autônomo ou desempregado)?
        Você tem dependentes? Se sim, quantos?
        Você possui dívidas atualmente? (Sim ou Não)
        Chame tool no final. Diga REDIRECIONANDO e pergunte se o cliente gostaria de realizar uma nova análise de crédito"""
    tools = [atualizar_score_entrevista]
    resp = llm.bind_tools(tools).invoke([SystemMessage(content=msg)] + state["messages"])
    return {"messages": [resp], "ultimo_agente": "entrevista"}