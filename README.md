# Bot de Relatórios Comerciais via Telegram

Este é um sistema de automação via bot do Telegram, utilizado oficialmente por uma empresa para geração de relatórios comerciais, como:

- Rentabilidade por loja e período;
- Notas fiscais sem recebimento.

Ele conecta-se tanto a um banco SQL Server (dados operacionais) quanto a um SQLite local (dados de usuários e permissões).

## Funcionalidades principais

- /rentabilidade: Permite ao usuário gerar e receber uma planilha .xlsx com os dados de rentabilidade de uma loja, dentro de um período definido.
- /notas: Permite consultar notas fiscais sem recebimento, com opção de modo automático (por usuário) ou manual (por loja e período).
- /ajuda: Lista os comandos disponíveis.


## Como executar

### 1. Clonar o repositório:

    git clone https://github.com/seu-usuario/seu-repositorio.git
    cd seu-repositorio

### 2. Criar e configurar o arquivo token.json:

Você deve criar um arquivo token.json na raiz do projeto com as seguintes chaves:
```
    {
      "bot_telegram": "SEU_TOKEN_DO_BOT_DO_TELEGRAM",
      "DRIVER": "SQL Server",
      "SERVER": "NOME_DO_SERVIDOR",
      "DATABASE": "NOME_DO_BANCO",
      "UID": "USUARIO_SQL",
      "PWD": "SENHA_SQL",
      "TrustServerCertificate": "yes"
    }
```
### 3. Instalar dependências:
   
   ```pip install -r requirements.txt```
   
- telebot
- pyodbc
- openpyxl

### 5. Banco SQLite:

O arquivo lojas.db precisa estar na raiz do projeto. Ele deve conter:

- Tabela usuarios: para autenticar usuários da empresa.
- Tabela lojas: contendo os números de lojas vinculadas aos usuários.
  
> [!TIP]
> Está disponivel como exemplo um arquivo .bd com valores ficticios.

## Execução

Com tudo configurado, inicie o bot com:

    python main.py
    
O bot iniciará o polling e ficará escutando os comandos enviados pelo Telegram.

## Estrutura do projeto

- main.py: entrada principal do bot Telegram e tratamento das mensagens.
- func.py: funções auxiliares para geração de relatórios, conexão com bancos de dados e manipulação de arquivos.
- lojas.db: banco SQLite local com os dados de usuários e lojas.
- token.json: arquivo de configuração com credenciais.
