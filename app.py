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

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola 👋🏼. Mandame un mensaje como `V 4350` para guardar un gasto.", parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip().upper()
    match = re.match(r'^([VSCO])\s+([\d.]+)$', texto)

    if not match:
        return  # Ignoramos mensajes mal formateados o con letras inválidas

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