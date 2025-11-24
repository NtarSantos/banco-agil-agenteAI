from typing import Annotated, List, Optional, Dict, Any
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
import operator

class BankState(TypedDict):
    # Histórico da conversa (append-only)
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Dados do Usuário Logado
    cpf: Optional[str]
    nome: Optional[str]
    dados_cliente: Optional[Dict[str, Any]]  # Guarda infos do CSV aqui
    
    # Controle de Fluxo
    autenticado: bool
    tentativas_falhas: int
    ultimo_agente: Optional[str]
    proximo_agente: Optional[str] # Para o roteador saber pra onde mandar
    
    # Contexto Temporário (ex: dados da entrevista)
    temp_entrevista: Optional[Dict[str, Any]]