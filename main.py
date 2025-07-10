import sqlite3
import telebot
import json
import datetime

from func import gerarRentabilidade, getLojas, consultarNotas, desconto

conn = sqlite3.connect('lojas.db', check_same_thread=False)

with open('token.json') as token_file:
    token = json.load(token_file)

bot = telebot.TeleBot(token['bot_telegram'])
    
@bot.message_handler(commands=['ajuda'])
def ajuda(message):
    bot.reply_to(message, "Comandos disponíveis:\n\n"
                          "/rentabilidade - Consultar rentabilidade\n"
                          "/notas - Consultar notas sem recebimento\n")

@bot.message_handler(commands=['rentabilidade'])
def rentabilidade(message):
    bot.reply_to(message, "Digite a data inicial (DD/MM/AAAA):")
    bot.register_next_step_handler(message, lambda msg: fluxoRentabilidade(msg, etapa=1, dados={}))

def fluxoRentabilidade(msg, etapa, dados):
    texto = msg.text

    if verificarSaida(texto, msg):
        return

    if etapa in [1, 2]:  # Validação de datas
        try:
            datetime.datetime.strptime(texto, "%d/%m/%Y")
        except ValueError:
            bot.send_message(msg.chat.id, "Data inválida. Tente novamente (DD/MM/AAAA) ou digite 'sair' para cancelar.")
            bot.register_next_step_handler(msg, lambda m: fluxoRentabilidade(m, etapa, dados=dados))
            return

    if etapa == 1:
        dados["data_inicial"] = texto
        bot.send_message(msg.chat.id, "Digite a data final (DD/MM/AAAA):")
        bot.register_next_step_handler(msg, lambda m: fluxoRentabilidade(m, etapa=2, dados=dados))

    elif etapa == 2:
        dados["data_final"] = texto
        bot.send_message(msg.chat.id, "Digite o número da loja:")
        bot.register_next_step_handler(msg, lambda m: fluxoRentabilidade(m, etapa=3, dados=dados))

    elif etapa == 3:
        loja = texto
        if not loja.isdigit():
            bot.reply_to(msg, "Número da loja inválido. Tente novamente ou digite 'sair' para cancelar.")
            bot.register_next_step_handler(msg, lambda m: fluxoRentabilidade(m, etapa=3, dados=dados))
            return

        bot.send_document(msg.chat.id, open(gerarRentabilidade(tratar_data(dados["data_inicial"]), tratar_data(dados["data_final"]), loja), 'rb'))

#notas sem recebimento
@bot.message_handler(commands=['notas'])
def notasSemReceb(message):
    bot.reply_to(message, "Escolha o tipo da consulta :\n\n1. Automatico \n2. Manual")
    bot.register_next_step_handler(message, lambda msg: fluxoNotas(msg, etapa=1, dados={}))

def fluxoNotas(msg, etapa, dados):
    texto = msg.text

    cursor = conn.cursor()
    cursor.execute(f"SELECT id,nome FROM usuarios")
    result = cursor.fetchall()
    usuarios = [row for row in result]

    if verificarSaida(texto, msg):
        return
    
    if etapa == 1:
        #verificar tipo
        if texto not in ['1', '2']:
            bot.reply_to(msg, "Tipo inválido. Tente novamente ou digite 'sair' para cancelar.")
            bot.register_next_step_handler(msg, lambda m: fluxoNotas(m, etapa, dados=dados))
            return

    if etapa == 2:
        #verificar usuario
        if not texto.isdigit() or int(texto) < 1 or int(texto) > len(usuarios):
            bot.reply_to(msg, "Número de usuário inválido. Tente novamente ou digite 'sair' para cancelar.")
            bot.register_next_step_handler(msg, lambda m: fluxoNotas(m, etapa, dados=dados))
            return
        else:
            dados["usuario"] = int(texto)
            bot.send_message(msg.chat.id, "Segue as notas sem recebimento:")
            for loja in getLojas(dados["usuario"]):
                bot.send_message(msg.chat.id, loja)

    if etapa in [4, 5]:
        #verificar data
        try:
            datetime.datetime.strptime(texto, "%d/%m/%Y")
        except ValueError:
            bot.reply_to(msg, "Data inválida. Tente novamente (DD/MM/AAAA) ou digite 'sair' para cancelar.")
            bot.register_next_step_handler(msg, lambda m: fluxoNotas(m, etapa, dados=dados))
            return
        if etapa == 5:
            dados["data_final"] = texto
            bot.send_message(msg.chat.id, consultarNotas(dados["data_inicial"], dados["data_final"], dados['loja']))
            return

    if etapa == 1:
        dados["tipo"] = texto

        if dados["tipo"] == '1':
            printar = "Digite o número do usuário:"
            for usuario in usuarios:
                printar = printar +"\n " +( f"{usuario[0]}. {usuario[1]}")
            bot.send_message(msg.chat.id, printar)
            bot.register_next_step_handler(msg, lambda m: fluxoNotas(m, etapa=2, dados=dados))
        else:
            bot.send_message(msg.chat.id, "Digite o número da loja:")
            bot.register_next_step_handler(msg, lambda m: fluxoNotas(m, etapa=3, dados=dados))
    
    elif etapa == 3:
        dados["loja"] = texto
        if not texto.isdigit():
            bot.reply_to(msg, "Número da loja inválido. Tente novamente ou digite 'sair' para cancelar.")
            bot.register_next_step_handler(msg, lambda m: fluxoNotas(m, etapa=3, dados=dados))
            return
        
        bot.send_message(msg.chat.id, "Digite a data inicial (DD/MM/AAAA):")
        bot.register_next_step_handler(msg, lambda m: fluxoNotas(m, etapa=4, dados=dados))

    elif etapa == 4:

        dados["data_inicial"] = texto
        bot.send_message(msg.chat.id,"Digite a data final (DD/MM/AAAA):")
        bot.register_next_step_handler(msg, lambda m: fluxoNotas(m, etapa=5, dados=dados))

def verificarSaida(texto, message):
    if texto.strip().lower() == 'sair':
        bot.reply_to(message, "Operação cancelada.")
        return True
    return False

def tratar_data(data):
    dia, mes, ano = data.split('/')
    return(ano+mes+dia)

@bot.menssage_handler(commands=['desconto'])
def atualizarDesconto(message):
    bot.reply_to(message, "Envie o codigo interno do produto: ")
    bot.registre_next_step_handler(message, lambda msg: desconto(msg))

bot.polling(none_stop=True)