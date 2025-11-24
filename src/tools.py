import pandas as pd
import datetime
import os
from langchain_core.tools import tool

# Caminhos dos arquivos (garantindo que funciona em qualquer SO)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CLIENTES_CSV = os.path.join(DATA_DIR, "clientes.csv")
SOLICITACOES_CSV = os.path.join(DATA_DIR, "solicitacoes_aumento_limite.csv")
SCORE_CSV = os.path.join(DATA_DIR, "score_limite.csv")

@tool
def validar_cpf(cpf: str, data_nascimento: str) -> dict:
    """
    Valida se o CPF e a data de nascimento correspondem a um cliente na base.
    Retorna um dicionário com sucesso (bool) e dados do cliente se encontrado.
    """
    try:
        df = pd.read_csv(CLIENTES_CSV, dtype=str)
        
        # Limpeza básica
        cpf_limpo = cpf.replace(".", "").replace("-", "").strip()
        
        cliente = df[
            (df['cpf'] == cpf_limpo) & 
            (df['data_nascimento'] == data_nascimento)
        ]
        
        if not cliente.empty:
            dados = cliente.iloc[0].to_dict()
            return {"sucesso": True, "dados": dados, "msg": "Autenticado com sucesso."}
        
        return {"sucesso": False, "msg": "CPF ou Data de Nascimento incorretos."}
    except Exception as e:
        return {"sucesso": False, "msg": f"Erro no sistema: {str(e)}"}

@tool
def consultar_limite(cpf: str) -> str:
    """Consulta o limite atual e o score do cliente."""
    try:
        df = pd.read_csv(CLIENTES_CSV, dtype={'cpf': str})
        cpf_limpo = cpf.replace(".", "").replace("-", "").strip()
        cliente = df[df['cpf'] == cpf_limpo]
        
        if cliente.empty:
            return "Cliente não encontrado."
            
        row = cliente.iloc[0]
        return f"Seu limite atual é R$ {row['limite_atual']} e seu Score é {row['score_atual']}."
    except Exception as e:
        return "Erro ao consultar dados."

@tool
def solicitar_aumento_limite(cpf: str, novo_limite: float) -> str:
    """
    Registra um pedido de aumento de limite.
    Verifica na tabela de score se o aumento é permitido.
    """
    try:
        # 1. Carregar dados
        df_clientes = pd.read_csv(CLIENTES_CSV, dtype={'cpf': str})
        df_score = pd.read_csv(SCORE_CSV)
        
        cpf_limpo = cpf.replace(".", "").replace("-", "").strip()
        cliente = df_clientes[df_clientes['cpf'] == cpf_limpo]
        
        if cliente.empty:
            return "Erro: Cliente não identificado na base."
            
        score_atual = float(cliente.iloc[0]['score_atual'])
        limite_atual = float(cliente.iloc[0]['limite_atual'])
        
        # 2. Verificar regra de Score
        # Busca qual a faixa de limite permitida para esse score
        regra = df_score[
            (df_score['score_min'] <= score_atual) & 
            (df_score['score_max'] >= score_atual)
        ]
        
        limite_max_permitido = 0.0
        if not regra.empty:
            limite_max_permitido = float(regra.iloc[0]['limite_maximo'])
            
        status = "rejeitado"
        if novo_limite <= limite_max_permitido:
            status = "aprovado"
            
        # 3. Salvar solicitação no CSV
        nova_solicitacao = {
            "cpf_cliente": cpf_limpo,
            "data_hora_solicitacao": datetime.datetime.now().isoformat(),
            "limite_atual": limite_atual,
            "novo_limite_solicitado": novo_limite,
            "status_pedido": status
        }
        
        df_solicitacoes = pd.read_csv(SOLICITACOES_CSV)
        df_solicitacoes = pd.concat([df_solicitacoes, pd.DataFrame([nova_solicitacao])], ignore_index=True)
        df_solicitacoes.to_csv(SOLICITACOES_CSV, index=False)
        
        if status == "aprovado":
            return f"Parabéns! Seu aumento para R$ {novo_limite} foi APROVADO."
        else:
            return (f"Pedido REPROVADO. Seu score ({score_atual}) permite no máximo R$ {limite_max_permitido}. "
                    "Gostaria de fazer uma entrevista para tentar aumentar seu score?")
                    
    except Exception as e:
        return f"Erro ao processar solicitação: {str(e)}"


# --- ATUALIZAÇÃO NO FINAL DO ARQUIVO src/tools.py ---
@tool
def atualizar_score_entrevista(cpf: str, renda_mensal: float, despesas_fixas: float, tipo_emprego: str, dependentes: int, tem_dividas: bool) -> str:
    """
    Calcula o novo score baseado na fórmula financeira e atualiza o CSV.
    Argumentos:
    - cpf: CPF do cliente
    - renda_mensal: Valor numérico (float)
    - despesas_fixas: Valor numérico (float)
    - tipo_emprego: 'formal', 'autônomo' ou 'desempregado'
    - dependentes: Número inteiro (0, 1, 2, 3...)
    - tem_dividas: True (sim) ou False (não)
    """
    try:
        # 1. Definição dos Pesos (Conforme solicitado)
        PESO_RENDA = 30
        
        PESO_EMPREGO = {
            "formal": 300,
            "autônomo": 200,
            "desempregado": 0
        }
        
        # Lógica para dependentes (3 ou mais vale 30)
        def get_peso_dependentes(num):
            if num == 0: return 100
            if num == 1: return 80
            if num == 2: return 60
            return 30 # Para 3+
            
        PESO_DIVIDAS = {
            True: -100,  # Sim, tem dívidas
            False: 100   # Não tem dívidas
        }

        # 2. Cálculo Matemático (A Fórmula)
        # score = ((renda / (despesas + 1)) * peso_renda) + emprego + dependentes + dividas
        
        # Tratamento de strings para evitar erro
        emprego_normalizado = tipo_emprego.lower().replace("autonomo", "autônomo")
        if emprego_normalizado not in PESO_EMPREGO:
            emprego_normalizado = "desempregado" # Fallback seguro
            
        score_renda = (renda_mensal / (despesas_fixas + 1)) * PESO_RENDA
        score_emprego = PESO_EMPREGO[emprego_normalizado]
        score_dependentes = get_peso_dependentes(dependentes)
        score_dividas = PESO_DIVIDAS[tem_dividas]
        
        novo_score = score_renda + score_emprego + score_dependentes + score_dividas
        
        # Trava o score entre 0 e 1000
        novo_score = max(0, min(1000, int(novo_score)))
        
        # 3. Atualização no Banco de Dados (CSV)
        df = pd.read_csv(CLIENTES_CSV, dtype={'cpf': str})
        cpf_limpo = cpf.replace(".", "").replace("-", "").strip()
        
        # Verifica se cliente existe
        if cpf_limpo not in df['cpf'].values:
            return "Erro: Cliente não encontrado no banco de dados."
            
        # Atualiza a linha correspondente
        df.loc[df['cpf'] == cpf_limpo, 'score_atual'] = novo_score
        df.to_csv(CLIENTES_CSV, index=False)
        
        return f"SUCESSO! Score recalculado para {novo_score}. O cadastro foi atualizado."
        
    except Exception as e:
        return f"Erro ao calcular score: {str(e)}"