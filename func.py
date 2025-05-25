import json
import csv
import sqlite3
import pyodbc
import datetime
from openpyxl import Workbook

with open('token.json') as token_file:
    token = json.load(token_file)

# Configuração da conexão com o banco de dados
connectionString = f'''
    DRIVER={{{token["DRIVER"]}}};
    SERVER={token["SERVER"]};
    DATABASE={token["DATABASE"]};
    UID={token["UID"]};
    PWD={token["PWD"]};
    TrustServerCertificate={token["TrustServerCertificate"]};
'''

# Data atual
data_atual = datetime.datetime.now()

#connectar ao banco SQLite
conn = sqlite3.connect('lojas.db', check_same_thread=False)
cursor = conn.cursor()

#tabelas rentabilidade
colunas_desejadas = ["PRODUTO","DESCRICAO","QUANTIDADE","VENDA_BRUTA","DESCONTO_AUTOMATICO","DESCONTO_CONCEDIDO","IMPOSTOS","PLUCRO_BRUTO","PRECO_MEDIO","CUSTO_MEDIO"]

#Rentabilidade
def gerarRentabilidade(inic, fim, loja):  
    if(consultarRentabilidade(inic, fim, loja)):
        csv_para_xlsx(f"data/rentabilidade_{loja}_{inic}_{fim}.csv", f"data/rentabilidade_{loja}_{inic}_{fim}.xlsx", colunas_desejadas)
        return (f"data/rentabilidade_{loja}_{inic}_{fim}.xlsx")
    else:
        return (False)

def consultarRentabilidade(periodo_inicial, periodo_final, loja):
    
    # Conectar ao banco
    conn = pyodbc.connect(connectionString)

    sql_query = f"""
        DECLARE @MOVIMENTO_INICIAL DATE        = '{periodo_inicial}'
        DECLARE @MOVIMENTO_FINAL   DATE        = '{periodo_final}'
        DECLARE @PRODUTO           NUMERIC     = DBO.NUMERICO_NULL('')
        DECLARE @EMPRESA           NUMERIC(15) = '{loja}'

        SELECT 
            A.EMPRESA                     AS EMPRESA,
            A.PRODUTO                     AS PRODUTO,
            C.DESCRICAO                   AS DESCRICAO,
            D.DESCRICAO                   AS SECAO,
            E.DESCRICAO                   AS GRUPO,
            F.DESCRICAO                   AS SUBGRUPO,
            SUM(A.QUANTIDADE)             AS QUANTIDADE,
            SUM(A.VENDA_BRUTA)            AS VENDA_BRUTA,
            SUM(A.DESCONTO_AUTOMATICO)    AS DESCONTO_AUTOMATICO,
            SUM(A.DESCONTO_CONCEDIDO)     AS DESCONTO_CONCEDIDO,
            SUM(A.DESCONTO)               AS DESCONTO,
            SUM(A.VENDA_LIQUIDA)          AS VENDA_LIQUIDA,
            SUM(A.IMPOSTOS)               AS IMPOSTOS,
            SUM(A.CMV)                    AS CMV,
            SUM(A.COMISSAO)               AS COMISSAO,
            SUM(A.LUCRO_BRUTO)            AS LUCRO_BRUTO
        INTO #TEMP_01
        FROM VENDAS_AGRUPADAS A WITH (NOLOCK)
        LEFT JOIN PRODUTOS              C WITH (NOLOCK) ON C.PRODUTO            = A.PRODUTO
        LEFT JOIN SECOES_PRODUTOS       D WITH (NOLOCK) ON C.SECAO_PRODUTO      = D.SECAO_PRODUTO
        LEFT JOIN GRUPOS_PRODUTOS       E WITH (NOLOCK) ON C.GRUPO_PRODUTO      = E.GRUPO_PRODUTO
        LEFT JOIN SUBGRUPOS_PRODUTOS    F WITH (NOLOCK) ON C.SUBGRUPO_PRODUTO   = F.SUBGRUPO_PRODUTO
        WHERE 
            A.MOVIMENTO >= @MOVIMENTO_INICIAL AND
            A.MOVIMENTO <= @MOVIMENTO_FINAL AND
            (A.PRODUTO = @PRODUTO OR @PRODUTO IS NULL) AND
            A.EMPRESA = @EMPRESA
        --  AND A.QUANTIDADE > 0
        GROUP BY 
            A.EMPRESA, 
            A.PRODUTO, 
            C.DESCRICAO, 
            D.DESCRICAO, 
            E.DESCRICAO, 
            F.DESCRICAO
        ORDER BY A.PRODUTO

        SELECT 
            A.EMPRESA                    AS EMPRESA,
            A.PRODUTO                    AS PRODUTO,
            A.DESCRICAO                  AS DESCRICAO,
            A.SECAO                      AS SECAO,
            A.GRUPO                      AS GRUPO,
            A.SUBGRUPO                   AS SUBGRUPO,
            @MOVIMENTO_INICIAL           AS MOVIMENTO_INICIAL,
            @MOVIMENTO_FINAL             AS MOVIMENTO_FINAL,
            A.QUANTIDADE                 AS QUANTIDADE,
            A.VENDA_BRUTA                AS VENDA_BRUTA,
            A.DESCONTO                   AS DESCONTO,
            CASE 
                WHEN A.VENDA_BRUTA > 0 
                THEN (A.DESCONTO / A.VENDA_BRUTA) * 100
                ELSE 0 
            END                          AS PDESCONTO,
            A.DESCONTO_AUTOMATICO        AS DESCONTO_AUTOMATICO,
            CASE 
                WHEN A.VENDA_BRUTA > 0 
                THEN (A.DESCONTO_AUTOMATICO / A.VENDA_BRUTA) * 100
                ELSE 0 
            END                          AS PDESCONTO_AUTOMATICO,
            A.DESCONTO_CONCEDIDO         AS DESCONTO_CONCEDIDO,
            CASE 
                WHEN A.VENDA_BRUTA > 0 
                THEN (A.DESCONTO_CONCEDIDO / A.VENDA_BRUTA) * 100
                ELSE 0 
            END                          AS PDESCONTO_CONCEDIDO,
            A.VENDA_LIQUIDA              AS VENDA_LIQUIDA,
            A.IMPOSTOS                   AS IMPOSTOS,
            CASE 
                WHEN A.VENDA_LIQUIDA > 0 
                THEN (A.IMPOSTOS / A.VENDA_LIQUIDA) * 100
                ELSE 0 
            END                          AS PIMPOSTOS,
            A.CMV                        AS CMV,
            CASE 
                WHEN A.VENDA_LIQUIDA > 0 
                THEN (A.CMV / A.VENDA_LIQUIDA) * 100
                ELSE 0 
            END                          AS PCMV,
            A.COMISSAO                   AS COMISSAO,
            CASE 
                WHEN A.VENDA_LIQUIDA > 0 
                THEN (A.COMISSAO / A.VENDA_LIQUIDA) * 100
                ELSE 0 
            END                          AS PCOMISSAO,
            A.LUCRO_BRUTO                AS LUCRO_BRUTO,
            CASE 
                WHEN A.VENDA_LIQUIDA > 0 
                THEN (A.LUCRO_BRUTO / A.VENDA_LIQUIDA) * 100
                ELSE 0 
            END                          AS PLUCRO_BRUTO,
            CASE 
                WHEN A.QUANTIDADE > 0 
                THEN A.VENDA_LIQUIDA / A.QUANTIDADE
                ELSE 0 
            END                          AS PRECO_MEDIO,
            CASE 
                WHEN A.QUANTIDADE > 0 
                THEN A.CMV / A.QUANTIDADE
                ELSE 0 
            END                          AS CUSTO_MEDIO
        FROM #TEMP_01 A
        -- WHERE A.QUANTIDADE > 0
        ORDER BY A.EMPRESA

        DROP TABLE #TEMP_01
            """

    cursor = conn.cursor()
    cursor.execute(sql_query)

    while cursor.description is None:
        if not cursor.nextset():
            break

    if cursor.description:
        columns = [col[0] for col in cursor.description]
        records = cursor.fetchall()
        output_file = f"data/rentabilidade_{loja}_{periodo_inicial}_{periodo_final}.csv"
        with open(output_file, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(columns)  # cabeçalho
            for row in records:
                writer.writerow(row)  # dados

        print(f"{output_file}")
        return (True)
    else:
        print("Nenhum dado retornado pela consulta.")
    
    conn.close()

def csv_para_xlsx(caminho_csv, caminho_xlsx, colunas_desejadas):
    wb = Workbook()
    ws = wb.active
    ws.title = "Planilha1"

    with open(caminho_csv, "r", encoding="utf-8") as arquivo_csv:
        leitor = csv.reader(arquivo_csv)
        cabecalho = next(leitor)

        indices = [cabecalho.index(col) for col in colunas_desejadas if col in cabecalho]

        ws.append([cabecalho[i] for i in indices])

        for linha in leitor:
            ws.append([linha[i] for i in indices])

    wb.save(caminho_xlsx)
    print(f"Arquivo salvo como: {caminho_xlsx}")

#Notas sem recebimento

def verificarMes():
    dia, mes, ano = data_atual.day, data_atual.month, data_atual.year
    if(dia - 2 < 1):
        mes -= 1
        if(mes < 1):
            mes = 12
            ano -= 1
        ultimo_dia_mes_anterior = (datetime.datetime(ano, mes + 1, 1) - datetime.timedelta(days=1)).day
        dia = ultimo_dia_mes_anterior - 1 
    else:
        dia -= 2
        
    init = f"{ano}0{mes-1}0{1}"
    if(dia < 10):
        final = f"{ano}0{mes}0{dia}"
    else:
        final = f"{ano}0{mes}{dia}"
    
    return(init, final)

def getLojas(usuario):
    cursor = conn.cursor()
    cursor.execute(f"SELECT numero FROM lojas WHERE usuario = {usuario}")
    result = cursor.fetchall()

    lojas = [row[0] for row in result]

    inicial, final = verificarMes()

    msg = []
    for loja in lojas:
        msg.append(consultarNotas(inicial, final, loja))
    
    return(msg)

def consultarNotas(periodo_inicial, periodo_final, loja):
    
    print(f"{periodo_inicial} {periodo_final} {loja}")
    # Conectar ao banco
    conn = pyodbc.connect(connectionString)

    sql_query = f"""
    DECLARE @DATA_INI DATETIME = '{periodo_inicial}'
    DECLARE @DATA_FIM DATETIME = '{periodo_final}'
    DECLARE @EMPRESA  NUMERIC = {loja}

    IF OBJECT_ID('tempdb..#NOTAS') IS NOT NULL
        DROP TABLE #NOTAS;

    SELECT DISTINCT 
        A.NF_COMPRA
    INTO #NOTAS
    FROM NF_COMPRA A WITH(NOLOCK)
    WHERE A.MOVIMENTO >= @DATA_INI
    AND A.MOVIMENTO <= @DATA_FIM
    AND (@EMPRESA IS NULL OR A.EMPRESA = @EMPRESA);

    SELECT DISTINCT
        A.NF_COMPRA,
        A.DATA_HORA AS DATA_HORA_NOTA,
        A.EMPRESA,
        A.EMISSAO,
        A.NF_NUMERO,
        A.ENTIDADE,
        C.NOME,
        A.CHAVE_NFE,
        'NF S/ RECEBIMENTO' AS SITUACAO,
        1 AS ITEM

    FROM NF_COMPRA A WITH(NOLOCK)

    LEFT JOIN   RECEBIMENTOS_VOLUMES_NF             B WITH(NOLOCK) ON B.NF_COMPRA   = A.NF_COMPRA
    JOIN        ENTIDADES                           C WITH(NOLOCK) ON C.ENTIDADE    = A.ENTIDADE
    LEFT JOIN   RECEBIMENTOS_VOLUMES                D WITH(NOLOCK) ON D.RECEBIMENTO = A.RECEBIMENTO
    LEFT JOIN   APROVACOES_RECEB_VOLUMES_ITENS      E WITH(NOLOCK) ON E.RECEBIMENTO = A.RECEBIMENTO
    LEFT JOIN   NF_COMPRA_TOTAIS                    G WITH(NOLOCK) ON G.NF_COMPRA   = A.NF_COMPRA
    JOIN        #NOTAS                              H WITH(NOLOCK) ON H.NF_COMPRA   = A.NF_COMPRA

    JOIN (
        SELECT DISTINCT 
            A.NF_COMPRA, 
            MIN(ISNULL(B.OPERACAO_FISCAL, C.OPERACAO_FISCAL)) AS OPERACAO_FISCAL
        FROM NF_COMPRA A WITH(NOLOCK)
        LEFT JOIN NF_COMPRA_PRODUTOS             B WITH(NOLOCK) ON B.NF_COMPRA = A.NF_COMPRA
        LEFT JOIN NF_COMPRA_PRODUTOS_SEM_CADASTRO C WITH(NOLOCK) ON C.NF_COMPRA = A.NF_COMPRA
        JOIN #NOTAS                               D WITH(NOLOCK) ON D.NF_COMPRA = A.NF_COMPRA
        GROUP BY A.NF_COMPRA
    ) X ON X.NF_COMPRA = A.NF_COMPRA

    JOIN OPERACOES_FISCAIS        Y WITH(NOLOCK) ON Y.OPERACAO_FISCAL = X.OPERACAO_FISCAL
    JOIN TIPOS_OPERACOES          K WITH(NOLOCK) ON K.TIPO_OPERACAO   = Y.TIPO_OPERACAO

    WHERE A.PROCESSAR = 'N'
    AND Y.RECEBIMENTO = 'S'
    AND B.NF_COMPRA IS NULL

    ORDER BY A.EMPRESA, A.EMISSAO, C.NOME;
    """

    cursor = conn.cursor()
    cursor.execute(sql_query)

    while cursor.description is None:
        if not cursor.nextset():
            break

    if cursor.description:
        columns = [col[0] for col in cursor.description]
        records = cursor.fetchall()
        output_file = f"data/notas_sem_recebimento_{loja}.csv"
        with open(output_file, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(columns)  # cabeçalho
            for row in records:
                writer.writerow(row)  # dados
    else:
        print("Nenhum dado retornado pela consulta.")

    with open(output_file, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        row_count = sum(1 for row in reader)
    
    resposta = f"Loja {loja} tem {row_count - 1} notas sem recebimento.\n"
    
    conn.close()

    return(resposta)