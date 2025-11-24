from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from src.state import BankState
# [ATENÇÃO] Removemos node_analise_intencao da importação
from src.nodes import (
    node_triagem, 
    node_credito, 
    node_cambio, 
    node_entrevista
)
from src.tools import (
    validar_cpf, consultar_limite, solicitar_aumento_limite, atualizar_score_entrevista
)
from langchain_community.tools.tavily_search import TavilySearchResults

# --- TOOLS ---
tool_tavily = TavilySearchResults(max_results=1)
todas_ferramentas = [validar_cpf, consultar_limite, solicitar_aumento_limite, atualizar_score_entrevista, tool_tavily]
node_ferramentas = ToolNode(todas_ferramentas)

# --- ROTEADOR DA TRIAGEM (O Cérebro das Conexões) ---
def router_triagem(state: BankState):
    # 1. Se a Triagem definiu um 'proximo_agente', siga ele!
    destino = state.get("proximo_agente")
    if destino:
        return destino
        
    # 2. Se a Triagem chamou uma Tool (Validar CPF), vá para Tools
    if tools_condition(state) == "tools":
        return "tools"
    
    # 3. Se não definiu destino e não chamou tool, é conversa -> FIM
    return END

def router_volta_tools(state: BankState):
    mensagens = state["messages"]
    last_tool_msg = mensagens[-1]
    tool_name = last_tool_msg.name
    
    if tool_name == "validar_cpf": return "triagem"
    if tool_name == "atualizar_score_entrevista": return "entrevista"
    if tool_name == "tavily_search_results_json": return "cambio"
    return "credito"

# --- GRAFO ---
workflow = StateGraph(BankState)

workflow.add_node("triagem", node_triagem)
workflow.add_node("credito", node_credito)
workflow.add_node("cambio", node_cambio)
workflow.add_node("entrevista", node_entrevista)
workflow.add_node("tools", node_ferramentas)

workflow.set_entry_point("triagem")

# --- CONEXÕES SIMPLIFICADAS ---

# Triagem decide tudo agora: Ou vai pra um agente, ou pra tool, ou para.
workflow.add_conditional_edges(
    "triagem",
    router_triagem,
    {
        "credito": "credito",
        "cambio": "cambio",
        "entrevista": "entrevista",
        "tools": "tools",
        END: END
    }
)

# Especialistas (padrão)
workflow.add_conditional_edges("credito", tools_condition, {"tools": "tools", END: END})
workflow.add_conditional_edges("cambio", tools_condition, {"tools": "tools", END: END})
workflow.add_conditional_edges("entrevista", tools_condition, {"tools": "tools", END: END})

# Volta das Tools
workflow.add_conditional_edges(
    "tools",
    router_volta_tools,
    {
        "triagem": "triagem",
        "credito": "credito",
        "cambio": "cambio",
        "entrevista": "entrevista"
    }
)

app = workflow.compile()