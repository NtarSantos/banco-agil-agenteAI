# 🏦 Banco Ágil - Agente Bancário Inteligente com LangGraph

> Uma solução de atendimento bancário baseada em **Multi-Agent Systems**, utilizando **LangGraph** para orquestração de estado, persistência de memória e ferramentas dinâmicas.

---

## 📋 Visão Geral

Este projeto simula um sistema de atendimento bancário digital completo. Diferente de chatbots tradicionais, ele utiliza uma arquitetura de **Grafos de Estado (StateGraph)**. Isso permite que o assistente mantenha o contexto, gerencie permissões de acesso e execute fluxos complexos (como entrevistas passo a passo) sem "alucinar" ou perder o fio da meada.

### 🎯 Principais Diferenciais Técnicos
* **Arquitetura Stateful:** O sistema lembra quem é o usuário, se está logado e qual foi a última interação.
* **Roteamento "Sticky" (Grudento):** Se o usuário está numa entrevista, o sistema bloqueia saídas acidentais até o fim do fluxo.
* **Triagem Inteligente:** O agente de entrada atua como um "porteiro" que decide dinamicamente se deve conversar, validar dados ou direcionar para especialistas.
* **Prevenção de Alucinação:** Ferramentas sensíveis (como validar CPF) só são ativadas se o input do usuário contiver padrões numéricos.

---

## 🏗️ Arquitetura do Sistema

O sistema é composto por nós (Nodes) especializados que compartilham um estado global (`BankState`).

### 🧠 O Estado (Memory Schema)
O "cérebro" da aplicação armazena:
* `messages`: Histórico da conversa.
* `autenticado` & `cpf`: Controle de sessão.
* `ultimo_agente`: Memória de curto prazo para manter o contexto (Sticky Routing).
* `tentativas_falhas`: Contador para bloqueio de segurança.

### 👥 Os Agentes (Nodes)

1.  **Agente de Triagem (Super Node):**
    * Atua como recepcionista e roteador.
    * **Funil de Vendas:** Apresenta serviços antes de pedir dados.
    * **Segurança:** Bloqueia o usuário após 3 tentativas falhas de autenticação.
    * **Classificador:** Analisa a intenção (Crédito, Câmbio, Entrevista) com base no histórico da conversa.

2.  **Agente de Crédito:**
    * Consulta limites em tempo real (CSV).
    * Processa solicitações de aumento.
    * Aplica regras de negócio rígidas baseadas em Score.

3.  **Agente de Entrevista:**
    * Conduz um questionário interativo (Renda, Despesas, etc.).
    * Utiliza lógica de persistência para não perder o foco entre as perguntas.
    * **Cálculo Real:** Executa uma fórmula matemática ponderada para atualizar o Score no banco de dados.

4.  **Agente de Câmbio:**
    * Conectado à API **Tavily** para buscar cotações de moedas em tempo real na web.

---

## ✨ Funcionalidades Detalhadas

### 🔐 Autenticação & Segurança
* Validação de CPF e Data de Nascimento contra base de dados (`data/clientes.csv`).
* **Lockout:** Bloqueio automático após 3 erros consecutivos.
* **Logout:** Comando "Sair" ou "Encerrar" limpa a sessão e o estado.

### 💳 Gestão de Crédito
* Consulta de limite disponível.
* Solicitação de aumento com verificação automática de regras de Score.
* Registro de auditoria: Todas as tentativas (aprovadas ou negadas) são salvas em `data/solicitacoes_aumento_limite.csv`.

### 📝 Entrevista de Perfil (Fluxo Complexo)
* Se o crédito for negado, o sistema oferece uma reanálise.
* O fluxo de entrevista é "blindado": o roteador prioriza as respostas da entrevista sobre qualquer outra intenção até que o processo finalize.
* Atualização física do Score do cliente no arquivo CSV após a conclusão.

### 💰 Câmbio em Tempo Real
* Busca ativa na internet para trazer valores atualizados de Dólar, Euro, etc.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.12+
* **Orquestração:** [LangGraph](https://langchain-ai.github.io/langgraph/) (Stateful Multi-Agent orchestration)
* **LLM:** LangChain + OpenAI (`gpt-4o-mini`)
* **Interface:** Streamlit (Chat UI com gestão de Session State)
* **Dados:** Pandas (Manipulação de CSV)
* **Web Search:** Tavily API

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
* Python instalado.
* Chaves de API da **OpenAI** e **Tavily**.

### Passo a Passo

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/NtarSantos/banco-agil-bot.git](https://github.com/NtarSantos/banco-agil-agenteAI.git)
    cd banco-agil-bot
    ```

2.  **Crie o ambiente virtual e instale as dependências:**
    ```bash
    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # Linux/Mac:
    source venv/bin/activate
    
    pip install -r requirements.txt
    ```

3.  **Configure as Variáveis de Ambiente:**
    Crie um arquivo `.env` na raiz do projeto:
    ```env
    OPENAI_API_KEY="sua-chave-aqui"
    TAVILY_API_KEY="sua-chave-aqui"
    ```

4.  **Gere os dados iniciais (Mock):**
    ```bash
    python setup_data.py
    ```
    *(Isso criará a pasta `data/` com clientes e regras fictícias).*

5.  **Execute a aplicação:**
    ```bash
    streamlit run app.py
    ```

---

## 🧪 Roteiro de Testes (Sugestão)

1.  **Saudação:** Digite "Olá". (O sistema deve apresentar o menu sem pedir CPF).
2.  **Interesse:** Digite "Quero ver meu limite". (O sistema pedirá o CPF).
3.  **Login:** Use CPF `12345678900` e Data `1990-01-01`.
4.  **Crédito (Reprovação):** Peça um aumento para `5000` (O sistema negará e oferecerá entrevista).
5.  **Entrevista:** Aceite a entrevista ("Sim"). Responda as perguntas (Renda alta, sem dívidas).
6.  **Sucesso:** Ao final, o sistema atualizará seu Score e redirecionará ao crédito.
7.  **Câmbio:** Pergunte "Quanto está o dólar?".
8.  **Logout:** Digite "Sair" para encerrar.

---

## 📂 Estrutura de Arquivos

```text
banco-agil-bot/
├── app.py              # Interface Frontend (Streamlit)
├── setup_data.py       # Script gerador de dados mock
├── requirements.txt    # Dependências
├── .env                # Chaves de API (Não comitado)
├── data/               # Banco de dados (CSV)
│   ├── clientes.csv
│   └── solicitacoes...
└── src/                # Lógica do Backend
    ├── graph.py        # Definição do Grafo e Roteamento
    ├── nodes.py        # Inteligência dos Agentes (Prompts)
    ├── tools.py        # Ferramentas (Cálculos, Pandas, API)
    └── state.py        # Schema de Memória
