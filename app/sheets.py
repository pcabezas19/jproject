import gspread, json
from oauth2client.service_account import ServiceAccountCredentials
from .config import GOOGLE_KEY_JSON, GOOGLE_SHEET_NAME, WORKSHEET_NAME

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials_info = json.loads(GOOGLE_KEY_JSON)
credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_info, scope)
client = gspread.authorize(credentials)
sheet = client.open(GOOGLE_SHEET_NAME).worksheet(WORKSHEET_NAME)
hoja_activa = WORKSHEET_NAME

LETRA_A_COLUMNA = {
    'V': 'B',
    'S': 'C',
    'C': 'D',
    'O': 'E',
}

def get_sheet():
    return sheet

def get_hoja_activa():
    return hoja_activa

def set_hoja(nueva_hoja):
    global sheet, hoja_activa
    sheet = client.open(GOOGLE_SHEET_NAME).worksheet(nueva_hoja)
    hoja_activa = nueva_hoja

def encontrar_fila_vacia(col_letra):
    valores = sheet.col_values(ord(col_letra.upper()) - 64)
    for i in range(3, len(valores)):
        if valores[i] == "":
            return i + 1
    return len(valores) + 1 if len(valores) >= 4 else 4

def encontrar_ultima_fila_con_valor(col_letra):
    valores = sheet.col_values(ord(col_letra.upper()) - 64)
    for i in range(len(valores) - 1, 3, -1):
        if valores[i].strip() != "":
            return i + 1
    return None
