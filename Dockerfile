# 1. Imagem base do Python (Leve e rápida)
FROM python:3.12-slim

# 2. Define o diretório de trabalho dentro do container
WORKDIR /app

# 3. Copia os arquivos de requisitos primeiro (para cachear as bibliotecas)
COPY requirements.txt .

# 4. Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copia todo o resto do código para dentro do container
COPY . .

# 6. Roda o script de setup para gerar os CSVs iniciais (Importante!)
RUN python setup_data.py

# 7. Expõe a porta padrão do Streamlit
EXPOSE 8501

# 8. Comando para rodar a aplicação
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]