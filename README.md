# 🏦 Banco Ágil - Agente Bancário Inteligente

Solução desenvolvida para o desafio técnico de Agente Bancário com IA. O sistema utiliza uma arquitetura baseada em grafos (**LangGraph**) para orquestrar múltiplos agentes especializados, garantindo persistência de estado e execução de ferramentas complexas.

## 📋 Visão Geral
O projeto simula um atendimento bancário digital onde um cliente interage com uma Inteligência Artificial capaz de:
- Autenticar usuários via base de dados (CSV).
- Consultar cotações de moedas em tempo real (API externa).
- Analisar e conceder crédito baseado em regras de negócio.
- Conduzir entrevistas para recalculo de Score financeiro.

## 🏗️ Arquitetura do Sistema

O sistema foi construído utilizando o padrão **Multi-Agent System** orquestrado pelo **LangGraph**.

### Os Agentes (Nós do Grafo)
1.  **Agente de Triagem:** Responsável pela segurança. Identifica se o usuário já está autenticado e direciona o fluxo. Implementa lógica de "Sondagem" vs "Validação".
2.  **Roteador de Intenção:** Um classificador semântico que analisa a linguagem natural do usuário para encaminhá-lo ao departamento correto (Câmbio, Crédito ou Entrevista).
3.  **Agente de Crédito:** Especialista financeiro. Possui acesso às ferramentas de leitura de CSV e escrita de solicitações. Segue regras rígidas de Score para aprovação.
4.  **Agente de Entrevista:** Responsável pela reanálise. Coleta dados (Renda, Dívidas, etc.) e executa o algoritmo de recálculo de Score.
5.  **Agente de Câmbio:** Conectado à internet (Tavily API) para buscar dados financeiros em tempo real.

### Fluxo de Dados
- **Estado (State):** Mantido em memória durante a sessão (Streamlit Session State + LangGraph State), armazenando histórico de chat, CPF autenticado e contexto.
- **Persistência:**
    - `data/clientes.csv`: Base de usuários e scores.
    - `data/score_limite.csv`: Regras de negócio para concessão de crédito.
    - `data/solicitacoes_aumento_limite.csv`: Log de auditoria de todas as solicitações.

## ✨ Funcionalidades Implementadas
- ✅ Autenticação de usuário (CPF/Data) contra base CSV.
- ✅ Persistência de sessão (usuário não precisa logar a cada mensagem).
- ✅ Consulta de limites e Score em tempo real.
- ✅ Solicitação de aumento de limite com validação automática de regras.
- ✅ Entrevista interativa para atualização de Score (Algoritmo ponderado).
- ✅ Consulta de cotação do Dólar/Euro via API externa.
- ✅ Interface de Chat amigável via Streamlit.

## 🛠️ Tecnologias e Escolhas Técnicas

- **Python 3.12**: Linguagem base.
- **LangGraph**: Escolhido ao invés de Chains simples do LangChain para permitir fluxos cíclicos e manutenção de estado robusta (Stateful), essencial para a lógica de "entrevista" e "autenticação".
- **LangChain + OpenAI (GPT-4o-mini)**: Para o raciocínio dos agentes. O modelo `mini` foi escolhido por ser rápido e eficiente em custos, suficiente para classificação e uso de ferramentas.
- **Pandas**: Para manipulação eficiente dos arquivos CSV (Leitura/Escrita).
- **Streamlit**: Para criar uma interface de chat rápida e funcional para testes.
- **Tavily API**: Para buscas na internet (Câmbio) sem alucinações.

## 🚀 Como Executar

### Pré-requisitos
- Python 3.10+
- Chave da OpenAI
- Chave da Tavily (opcional, para câmbio)

### Instalação

1. Clone o repositório:
```bash
git clone [https://github.com/ntar-santos/banco-agil-agenteAI.git]
](https://github.com/NtarSantos/banco-agil-agenteAI.git)
