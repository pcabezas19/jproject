import logging
import gspread
import re
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import os
from dotenv import load_dotenv

# --- CONFIGURACIÓN ---
load_dotenv()
BOT_TOKEN = os.getenv('TOKEN_TELEGRAM')
GOOGLE_SHEET_NAME = 'CopiaPedro'
WORKSHEET_NAME = 'Nuevo'  # Usar el nombre real de la hoja (tab)
GOOGLE_CREDENTIALS_FILE = 'key.json'

# Mapeo de letras a columnas de hoja de cálculo
LETRA_A_COLUMNA = {
    'V': 'B',  # Verdulería
    'S': 'C',  # Super & Farma
    'C': 'D',  # Comida calle
    'O': 'E',  # Otros
}

# --- CONEXIÓN A GOOGLE SHEETS ---
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS_FILE, scope)
client = gspread.authorize(credentials)
sheet = client.open(GOOGLE_SHEET_NAME).worksheet(WORKSHEET_NAME)
hoja_activa = WORKSHEET_NAME

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)

# --- FUNCIONES AUXILIARES ---
def encontrar_fila_vacia(col_letra):
    """Busca la próxima fila vacía a partir de la fila 4 en la columna especificada (ej: 'B')."""
    valores = sheet.col_values(ord(col_letra.upper()) - 64)  # Convertir letra a índice (A=1, B=2, ...)
    for i in range(3, len(valores)):  # fila 4 = índice 3
        if valores[i] == "":
            return i + 1
    return len(valores) + 1 if len(valores) >= 4 else 4

def encontrar_ultima_fila_con_valor(col_letra):
    """Devuelve la última fila con datos en la columna especificada (desde la fila 4)."""
    valores = sheet.col_values(ord(col_letra.upper()) - 64)
    for i in range(len(valores) - 1, 3, -1):  # desde abajo hacia fila 4
        if valores[i].strip() != "":
            return i + 1
    return None


# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola 👋🏼. Envía Letra e Importe para guardar un gasto.", parse_mode="Markdown")

# --- COMANDO /hoja ---
async def set_hoja(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global sheet, hoja_activa
    if not context.args:
        await update.message.reply_text("❌ Escribe correctamente el nombre de la hoja")
        return
    nuevo_nombre = " ".join(context.args).strip()
    try:
        nueva_hoja = client.open(GOOGLE_SHEET_NAME).worksheet(nuevo_nombre)
        sheet = nueva_hoja
        hoja_activa = nuevo_nombre
        await update.message.reply_text(f"✅ Ahora estás sobre la hoja *{hoja_activa}*", parse_mode="Markdown")
    except Exception as e:
        logging.error("Error al cambiar de hoja:", exc_info=True)
        await update.message.reply_text("❌ No se pudo cambiar la hoja. ¿Está bien escrito el nombre?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()

    # Borrar último registro: "D V", "D C", etc.
    borrar_match = re.match(r'^D\s+([VSCO])$', texto.upper())
    if borrar_match:
        letra_borrar = borrar_match.group(1)
        col_letra_borrar = LETRA_A_COLUMNA[letra_borrar]

        try:
            fila = encontrar_ultima_fila_con_valor(col_letra_borrar)
            if fila:
                celda_valor = f"{col_letra_borrar}{fila}"
                valor_borrado = sheet.acell(celda_valor).value
                sheet.update(celda_valor, [[""]])  # Borra monto

                mensaje_confirmacion = f"🗑️ Se eliminó el valor ${valor_borrado} de la columna '{letra_borrar}'."

                # Si es la columna 'O', también borramos el comentario en columna 'F'
                if letra_borrar == 'O':
                    celda_comentario = f"F{fila}"
                    sheet.update(celda_comentario, [[""]])

                await update.message.reply_text(mensaje_confirmacion)
            else:
                await update.message.reply_text(f"⚠️ No hay valores para borrar en esa columna.")
        except Exception as e:
            logging.error("❌ Error al borrar en Google Sheets:", exc_info=True)
        return


    # Caso especial: O con monto y texto
    match_o_extendido = re.match(r'^O\s+([\d.]+)\s+(.+)$', texto, re.IGNORECASE)
    if match_o_extendido:
        monto_str, comentario = match_o_extendido.groups()
        monto = float(monto_str)
        col_monto = LETRA_A_COLUMNA['O']  # Columna 'E'
        col_texto = 'F'  # Cambiá esto si querés otra columna para los comentarios

        try:
            fila = encontrar_fila_vacia(col_monto)
            sheet.update(f"{col_monto}{fila}", [[monto]])
            sheet.update(f"{col_texto}{fila}", [[comentario]])
            monto_formateado = f"${monto:,.0f}".replace(",", ".")
            await update.message.reply_text(f"✅ {monto_formateado} guardado en '{letra}' y tambiém el comentario")
        except Exception as e:
            logging.error("❌ Error al guardar monto y comentario en Google Sheets:", exc_info=True)
        return

    # Caso general: Letra + monto
    match = re.match(r'^([VSCO])\s+([\d.]+)$', texto.upper())
    if not match:
        await update.message.reply_text("❌ Opción inválida. Usa el formato letra, espacio, importe.")
        return

    letra, monto_str = match.groups()
    monto = float(monto_str)
    col_letra = LETRA_A_COLUMNA[letra]

    try:
        fila = encontrar_fila_vacia(col_letra)
        celda = f"{col_letra}{fila}"
        sheet.update(celda, [[monto]])
        monto_formateado = f"${monto:,.0f}".replace(",", ".")
        await update.message.reply_text(f"✅ {monto_formateado} guardado en columna '{letra}'.")
    except Exception as e:
        logging.error("❌ Error al guardar en Google Sheets:", exc_info=True)


# --- BOT ---
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("hoja", set_hoja))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🤖 Bot corriendo...")
app.run_polling()