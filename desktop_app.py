import threading
import webview
from app import app

def run_server():
    app.run(port=5000, debug=False)

if __name__ == '__main__':
    # Start Flask backend in a separate thread
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    # Create native OS desktop window
    webview.create_window('Debt Tracker', 'http://127.0.0.1:5000/', width=1200, height=800)
    webview.start()