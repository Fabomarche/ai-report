import nlpcloud
from llamaapi import LlamaAPI
import ollama
import os
from dotenv import load_dotenv
import json
from progressbar import ProgressBar
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

client = nlpcloud.Client("xlm-roberta-large-xnli",  os.getenv("NPL_API_KEY"))

llama = LlamaAPI(os.getenv("LLAMA_API_KEY")) #not necesary if use ollama

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
MONTH = "JULIO24"

def read_json_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
            return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON in file: {file_path}")
        return None

def build_monthly_data(base_folder):
    tawkData = []
    for subfolder in os.listdir(base_folder):
        subfolder_path = os.path.join(base_folder, subfolder)
        if os.path.isdir(subfolder_path):
            files_in_subfolder = os.listdir(subfolder_path)
            for filename in files_in_subfolder:
                file_path = os.path.join(subfolder_path, filename)
                if filename.endswith(".json"):
                    json_content = read_json_file(file_path)
                    if json_content:
                        tawkData.append(json_content)

    return tawkData

folder_path = "./chats/07" #edit with month folder
tawkData = build_monthly_data(folder_path)

def llamaExternalChat(functionallity, prompt):
    api_request_json = {
        "model": "llama3-70b",
        "messages": [
            {"role": "user", "content": functionallity},
                {"role": "user", "content": prompt},
        ]
        }
    response = llama.run(api_request_json)
    return response["message"]["content"]


def llamaLocalChat(functionallity, prompt):
    try:
        response = ollama.chat(
            model="llama3.1",
            messages=[
                 {"role": "system", 
                  "content": functionallity
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )
        return response["message"]["content"]
    except ollama.ResponseError as e:
        print("Error:", e)


def get_most_likely_label(classification_result):
    scores = classification_result['scores']
    labels = classification_result['labels']
    max_score_index = scores.index(max(scores))
    most_likely_label = labels[max_score_index]
    return most_likely_label

def clasificate_chats_by_type(conversation):
    clasificatedChat = client.classification(conversation,
    labels=["Reporte de un mal funcionamiento", "Necesidad de capacitacion", "Solicitud de informe o reporte"],
    multi_class=True
    )

    most_likely = get_most_likely_label(clasificatedChat) 
    return most_likely



def chat_title(chat):
    return llamaLocalChat(
        "Eres un experto identificando el concepto principal de un chat de soporte de software de una plataforma de seguridad ciudadana para resumirlo en una frase. Sólo devuelve la frase que resume el chat.",
        chat
        )
     

def build_monthly_conversations(tawkData):
    monthly_conversations = []
    total_entries = len(tawkData)
    bar = ProgressBar(maxval=len(tawkData))

    for idx, entry in enumerate(tawkData, start=1):
        print(f"Processing input {idx}/{total_entries}")
        bar.update(idx)
        if "visitor" in entry and "location" in entry and "chatDuration" in entry and "messages" in entry:
            visitor_email = entry["visitor"].get("email", "")
            location_city = entry["location"].get("city", "")
            chat_duration = entry["chatDuration"]
            created_on = entry.get("createdOn", "")

            messages = entry["messages"]
            conversation = ""
            for i, msg in enumerate(messages):
                if i != 1:  # Exclude the second message
                    msg_content = msg.get("msg", "")
                    if msg_content.strip() and "Tu opinión nos ayuda a mejorar." not in msg_content:
                        conversation += msg_content + "\n"  # Add a newline

            conversation_obj = {
                "email": visitor_email,
                "location": location_city,
                "chatDuration": chat_duration,
                "createdOn": created_on, 
                "conversation": conversation.strip(),
                "type": clasificate_chats_by_type(conversation.strip()),
                "summarization": chat_title(conversation.strip())
            }
            monthly_conversations.append(conversation_obj)
            bar.finish()
    
    print("Monthly Conversations Built Right!")
    return monthly_conversations

monthly_conversations_result = build_monthly_conversations(tawkData)
print(monthly_conversations_result)



def duplicate_and_rename_sheet(service, spreadsheet_id, source_sheet_name, target_sheet_name):
    try:
        # Duplicate the sheet
        request = {
            "duplicateSheet": {
                "sourceSheetId": get_sheet_id(service, spreadsheet_id, source_sheet_name),
                "newSheetName": target_sheet_name,
            }
        }
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": [request]}).execute()
        print(f"Sheet '{source_sheet_name}' duplicated as '{target_sheet_name}'.")

    except HttpError as error:
        print(f"Error duplicating sheet: {error}")

def get_sheet_id(service, spreadsheet_id, sheet_name):
    result = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = result.get("sheets", [])
    for sheet in sheets:
        if sheet["properties"]["title"] == sheet_name:
            return sheet["properties"]["sheetId"]
    return None

def sheet_exists(service, spreadsheet_id, sheet_name):
    try:
        result = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = result.get("sheets", [])
        for sheet in sheets:
            if sheet["properties"]["title"] == sheet_name:
                return True
        return False
    except HttpError as error:
        print(f"Error checking sheet existence: {error}")
        return False

def write_values_to_sheet(service, spreadsheet_id, sheet_name, data, target_cell, column):
    range_name = f"{sheet_name}!{target_cell}"
    values = [[entry.get(column, "")] for entry in data]

    body = {"values": values}
    service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=range_name, valueInputOption="RAW", body=body).execute()




def main():
    credentials = None
    if os.path.exists("token.json"):
        credentials = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            credentials = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(credentials.to_json())

    try:
        service = build("sheets", "v4", credentials=credentials)

        if not sheet_exists(service, SPREADSHEET_ID, MONTH):
            duplicate_and_rename_sheet(service, SPREADSHEET_ID, "BASE", MONTH)
        else:
            print(f"Sheet '{MONTH}' already exists. Skipping duplication.")

        write_values_to_sheet(service, SPREADSHEET_ID, MONTH, monthly_conversations_result, "A5", "createdOn")
        write_values_to_sheet(service, SPREADSHEET_ID, MONTH, monthly_conversations_result, "B5", "email")
        write_values_to_sheet(service, SPREADSHEET_ID, MONTH, monthly_conversations_result, "C5", "location")
        write_values_to_sheet(service, SPREADSHEET_ID, MONTH, monthly_conversations_result, "E5", "type")
        write_values_to_sheet(service, SPREADSHEET_ID, MONTH, monthly_conversations_result, "D5", "summarization")

    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    main()