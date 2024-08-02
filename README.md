# Automatic Report for Support Chats in Tawk

This project automates the generation of support chat reports using a specific pre created Google Sheets template.

## How to Run

1. **Setting Up the Virtual Environment:**
   - Create a virtual environment using Python's built-in `venv` module:
     ```
     python -m venv .venv
     ```
   - Activate the virtual environment:
     - On Windows:
       ```
       .venv\Scripts\activate
       ```
     - On macOS/Linux:
       ```
       source .venv/bin/activate
       ```
2. **Install Dependencies:**
   - Install the required packages listed in `requirements.txt`:
     ```
     pip install -r requirements.txt
     ```
3. **Environment Variables:**
   - Create a `.env` file with any necessary configuration variables. (.env.example)
   - If you're working locally, consider downloading and installing the LLama model from the Ollama website.
   - Get credentials.json from Google Sheets API.
4. **Configuration Constants:**
   - Define the following constants in your code:
     - `SPREADSHEET_ID`: The Google Sheets spreadsheet ID.
     - `folder_path`: The path to the folder where your reports will be saved.
     - `MONTH`: The name of the sheet corresponding to the month (e.g., "July").

5. **Run the Script:**
   - Execute the main script:
     ```
     python auto-report.py
     ```

## Downloading Chats from Tawk

### Accessing the Tawk.to Dashboard:
1. Make sure you're on the correct dashboard.
2. Hover over the hamburger icon at the top and navigate to the Messaging section by clicking on the inbox icon on the left side.

### Viewing Chats:
1. Below the green "+ New Ticket" button, you'll find two checkboxes. Make sure to check the box labeled "Chats."
2. Use the search function in the top right corner to find specific chats. You can filter by dates, duration, status, and tags.

### Exporting July Chats:
1. Ensure that the chat list displays all chats from July.
2. Select the chats you want to export by checking the checkbox next to each chat.
3. Look for the export option in the Tawk.to interface (usually at the top or bottom of the chat list).
