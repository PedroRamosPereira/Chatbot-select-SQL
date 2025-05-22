import sqlite3
import telebot
import json
import datetime

from func import gerar_rentabilidade, get_lojas

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
    bot.register_next_step_handler(message, lambda msg: fluxo_rentabilidade(msg, etapa=1, dados={}))

def fluxo_rentabilidade(msg, etapa, dados):
    texto = msg.text

    if verificar_saida(texto, msg):
        return

    if etapa in [1, 2]:  # Validação de datas
        try:
            datetime.datetime.strptime(texto, "%d/%m/%Y")
        except ValueError:
            bot.send_message(msg.chat.id, "Data inválida. Tente novamente (DD/MM/AAAA) ou digite 'sair' para cancelar.")
            bot.register_next_step_handler(msg, lambda m: fluxo_rentabilidade(m, etapa, dados))
            return

    if etapa == 1:
        dados["data_inicial"] = texto
        bot.reply_to(msg, "Digite a data final (DD/MM/AAAA):")
        bot.register_next_step_handler(msg, lambda m: fluxo_rentabilidade(m, etapa=2, dados=dados))

    elif etapa == 2:
        dados["data_final"] = texto
        bot.reply_to(msg, "Digite o número da loja:")
        bot.register_next_step_handler(msg, lambda m: fluxo_rentabilidade(m, etapa=3, dados=dados))

    elif etapa == 3:
        loja = texto
        if not loja.isdigit():
            bot.reply_to(msg, "Número da loja inválido. Tente novamente ou digite 'sair' para cancelar.")
            bot.register_next_step_handler(msg, lambda m: fluxo_rentabilidade(m, etapa=3, dados=dados))
            return

        bot.send_document(msg.chat.id, open(gerar_rentabilidade(dados["data_inicial"], dados["data_final"], loja), 'rb'))

@bot.message_handler(commands=['notas'])
def notas_sem_receb(message):
    cursor = conn.cursor()
    cursor.execute(f"SELECT id,nome FROM usuarios")
    result = cursor.fetchall()
    usuarios = [row for row in result]
    printar = "Escolha o usuário:\n"
    for usuario in usuarios:
        printar = printar +"\n " +( f"{usuario[0]}. {usuario[1]}")
    
    bot.reply_to(message, printar)
    bot.register_next_step_handler(message, lambda msg: ask_tipo_consulta(msg, message))

def ask_tipo_consulta(user_message, original_message):
    usuario = user_message.text
    bot.reply_to(original_message, "Escolha o tipo da consulta :\n\n 1. Automatico \n 2. Manual")
    bot.register_next_step_handler(original_message, lambda msg: bot.reply_to(original_message, (get_lojas(usuario, msg.text))))


def verificar_saida(texto, message):
    if texto.strip().lower() == 'sair':
        bot.reply_to(message, "Operação cancelada.")
        return True
    return False

bot.polling(none_stop=True)