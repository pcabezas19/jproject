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
GOOGLE_SHEET_NAME = 'Jproject'
WORKSHEET_NAME = 'Hoja 1'  # Usar el nombre real de la hoja (tab)
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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip().upper()

    # Borrar último registro: "D V", "D C", etc.
    borrar_match = re.match(r'^D\s+([VSCO])$', texto)
    if borrar_match:
        letra_borrar = borrar_match.group(1)
        col_letra_borrar = LETRA_A_COLUMNA[letra_borrar]

        try:
            fila = encontrar_ultima_fila_con_valor(col_letra_borrar)
            if fila:
                celda = f"{col_letra_borrar}{fila}"
                sheet.update(celda, [[""]])  # Borrar el valor
                await update.message.reply_text(f"🗑️ Último valor eliminado de la celda {celda}.")
            else:
                await update.message.reply_text(f"⚠️ No hay valores para borrar en esa columna.")
        except Exception as e:
            logging.error("❌ Error al borrar en Google Sheets:", exc_info=True)
        return
    
    
    match = re.match(r'^([VSCO])\s+([\d.]+)$', texto)

    if not match:
        # Si el mensaje no coincide con el formato esperado, respondemos que la opción es inválida.
        await update.message.reply_text("❌ Opción inválida. Usa el formato letra, espacio, importe")
        return

    letra, monto_str = match.groups()

    monto = float(monto_str)
    col_letra = LETRA_A_COLUMNA[letra]

    try:
        fila = encontrar_fila_vacia(col_letra)
        celda = f"{col_letra}{fila}"
        sheet.update(celda, [[monto]])  # 👈 Esta línea es la clave
        await update.message.reply_text(f"✅ ${monto} guardado en celda {celda}.")
    except Exception as e:
        logging.error("❌ Error al guardar en Google Sheets:", exc_info=True)

# --- BOT ---
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🤖 Bot corriendo...")
app.run_polling()