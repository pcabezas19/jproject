import re
import logging
from telegram import Update
from telegram.ext import ContextTypes
from .sheets import *

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola 👋🏼 Jessy. Envía letra e importe para guardar un gasto.")

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hoja = get_hoja_activa()
    mensaje = f"""📋 *Información para Pumbilita sobre Gastos*:

• Hoja activa: *{hoja}*
• Columnas disponibles:
  - V: Verdulería (columna B)
  - S: Super & Farma (columna C)
  - C: Comida calle (columna D)
  - O: Otros + Comentarios (columna E + F)

• Formatos válidos:
  - `V 5000` → Guarda $5000 en Verdulería
  - `O 3000 chocobanana` → Guarda $3000 en Otros + comentario
  - `D V` → Borra último registro en Verdulería

• Cambiar hoja: `/hoja NOMBRE_EN_MAYÚSCULAS`
"""
    await update.message.reply_text(mensaje, parse_mode="Markdown")

async def set_hoja_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Escribe correctamente el nombre de la hoja")
        return
    nuevo_nombre = " ".join(context.args).strip()
    try:
        set_hoja(nuevo_nombre)
        await update.message.reply_text(f"✅ Ahora estás sobre la hoja *{nuevo_nombre}*", parse_mode="Markdown")
    except Exception as e:
        logging.error("Error al cambiar de hoja:", exc_info=True)
        await update.message.reply_text("❌ No se pudo cambiar la hoja. ¿Está bien escrito el nombre?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()

    borrar_match = re.match(r'^D\s+([VSCO])$', texto.upper())
    if borrar_match:
        letra = borrar_match.group(1)
        col = LETRA_A_COLUMNA[letra]
        fila = encontrar_ultima_fila_con_valor(col)
        if fila:
            get_sheet().sheet.update(f"{col}{fila}", [[""]])
            if letra == 'O':
                get_sheet().sheet.update(f"F{fila}", [[""]])
            await update.message.reply_text(f"🗑️ Se eliminó el último valor de la columna '{letra}'.")
        else:
            await update.message.reply_text(f"⚠️ No hay valores para borrar en esa columna.")
        return

    match_o = re.match(r'^O\s+([\d.]+)\s+(.+)$', texto, re.IGNORECASE)
    if match_o:
        monto, comentario = match_o.groups()
        monto = int(float(monto))
        fila = encontrar_fila_vacia('E')
        get_sheet().sheet.update(f"E{fila}", [[monto]])
        get_sheet().sheet.update(f"F{fila}", [[comentario]])
        await update.message.reply_text(f"✅ ${float(monto):,.0f} guardado en 'O' con comentario")
        return

    match = re.match(r'^([VSCO])\s+([\d.]+)$', texto.upper())
    if match:
        letra, monto = match.groups()
        monto = int(float(monto))
        col = LETRA_A_COLUMNA[letra]
        fila = encontrar_fila_vacia(col)
        get_sheet().sheet.update(f"{col}{fila}", [[monto]])
        await update.message.reply_text(f"✅ ${float(monto):,.0f} guardado en columna '{letra}'")
        return

    await update.message.reply_text("❌ Opción inválida. Usa el formato letra + importe.")