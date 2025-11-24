import pandas as pd
import os

# Garantir que a pasta data existe
os.makedirs("data", exist_ok=True)

# 1. Criar clientes.csv
# Colunas sugeridas pelo desafio + colunas necessárias para lógica
data_clientes = {
    "cpf": ["12345678900", "98765432100", "11122233344"],
    "nome": ["João Silva", "Maria Oliveira", "Carlos Souza"],
    "data_nascimento": ["1990-01-01", "1985-05-15", "2000-12-10"],
    "score_atual": [500, 800, 300],
    "renda_mensal": [3000.0, 8000.0, 1500.0],
    "limite_atual": [1000.0, 5000.0, 200.0]
}
df_clientes = pd.DataFrame(data_clientes)
df_clientes.to_csv("data/clientes.csv", index=False)
print("✅ data/clientes.csv criado.")

# 2. Criar score_limite.csv
# Tabela para definir se o score permite X limite
data_score = {
    "score_min": [0, 300, 500, 700, 900],
    "score_max": [299, 499, 699, 899, 1000],
    "limite_maximo": [0.0, 500.0, 2000.0, 10000.0, 50000.0]
}
df_score = pd.DataFrame(data_score)
df_score.to_csv("data/score_limite.csv", index=False)
print("✅ data/score_limite.csv criado.")

# 3. Criar arquivo de solicitações vazio (apenas cabeçalho)
colunas_solicitacao = ["cpf_cliente", "data_hora_solicitacao", "limite_atual", "novo_limite_solicitado", "status_pedido"]
df_solicitacoes = pd.DataFrame(columns=colunas_solicitacao)
df_solicitacoes.to_csv("data/solicitacoes_aumento_limite.csv", index=False)
print("✅ data/solicitacoes_aumento_limite.csv criado.")