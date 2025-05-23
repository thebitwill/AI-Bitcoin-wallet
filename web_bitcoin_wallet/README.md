# Web Bitcoin Wallet

## Description
A web-based Bitcoin wallet application allowing users to manage their Bitcoin assets through a browser interface. The backend is powered by Flask (Python), and the frontend is built with Vanilla JavaScript. The project plans to use `bitcoinjs-lib` for client-side Bitcoin operations.

## Technologies
*   **Backend:** Flask (Python)
*   **Frontend:** Vanilla JavaScript, HTML, CSS
*   **Planned Bitcoin Library (Frontend):** bitcoinjs-lib
*   **API Communication:** Fetch API, JSON

## Backend Setup

1.  **Navigate to the project root directory:**
    ```bash
    cd path/to/web_bitcoin_wallet
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Flask development server:**
    Navigate to the `backend` directory and run `app.py`:
    ```bash
    cd backend
    python app.py
    ```
    The backend API should now be running, typically on `http://127.0.0.1:5000`.
    The Flask application will also serve the frontend files.

## Accessing the Application
1.  Ensure the Flask backend server is running (see "Backend Setup" above).
2.  Open your web browser and navigate to `http://127.0.0.1:5000/`.
3.  The `index.html` page from the `frontend` directory should be displayed.
4.  The page will attempt to fetch the status from the backend API. Check the browser's console for messages or view the status on the page.

## Project Structure (Initial)
```
web_bitcoin_wallet/
├── backend/
│   └── app.py            # Flask application
├── frontend/
│   ├── css/
│   │   └── style.css     # Basic styles
│   ├── js/
│   │   └── main.js       # Frontend JavaScript logic
│   └── index.html        # Main HTML page
├── requirements.txt      # Python backend dependencies
└── README.md             # This file
```
