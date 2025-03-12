# File Downloader Server by G-flame (https://github.com/g-lame
# Importing shit 
import os
import sys
import threading
import http.server
import socketserver
import urllib.parse
import socket
import webbrowser
import signal
import mimetypes
from http import HTTPStatus
from pathlib import Path
from datetime import datetime
# Configuration
PORT = 8080 # Port for the Server
HOST = "0.0.0.0" # IP address for the server
DOWNLOAD_DIR = os.path.abspath("/app/data") # The path to show to the user
 
## Don't edit anything below Here if you don't know what you are doing !! 
# ------------------------------------------------------------------------


SERVER_INSTANCE = None # for the 'done' and 'CTRL + C' stopping sequence.. 
class FileServer(http.server.SimpleHTTPRequestHandler):
    """Custom request handler with improved UI and functionality"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DOWNLOAD_DIR, **kwargs)
    
    def log_message(self, format, *args):
        """Override to provide cleaner logging"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")
    
    def send_headers(self, status_code=HTTPStatus.OK, content_type="text/html"):
        """Helper to send response headers"""
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
    
    def format_size(self, size_bytes):
        """Format file size in human-readable format"""
        if size_bytes == 0:
            return "0B"
        size_names = ("B", "KB", "MB", "GB", "TB")
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
        return f"{size_bytes:.2f} {size_names[i]}"
    
    def render_template(self, content, title="File Downloader"): # HTML CSS JS From here on out
        """Render HTML template with provided content"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        :root {{
            --primary: #0ea5e9;
            --secondary: #0284c7;
            --background: #0f172a;
            --surface: #1e293b;
            --text: #e2e8f0;
            --text-secondary: #94a3b8;
            --border: #334155;
            --hover: #334155;
            --success: #10b981;
            --danger: #ef4444;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--background);
            color: var(--text);
            line-height: 1.6;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .container {{
            background-color: var(--surface);
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        
        header {{
            background-color: var(--primary);
            color: white;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        h1 {{
            margin: 0;
            font-size: 24px;
        }}
        
        .breadcrumb {{
            background-color: var(--hover);
            padding: 10px 20px;
            border-bottom: 1px solid var(--border);
        }}
        
        .breadcrumb a {{
            color: var(--primary);
            text-decoration: none;
        }}
        
        .breadcrumb a:hover {{
            text-decoration: underline;
        }}
        
        .files {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .files th {{
            text-align: left;
            padding: 12px 20px;
            border-bottom: 2px solid var(--border);
            font-weight: 600;
            color: var(--text-secondary);
        }}
        
        .files td {{
            padding: 12px 20px;
            border-bottom: 1px solid var(--border);
        }}
        
        .files tr:hover {{
            background-color: var(--hover);
        }}
        
        .files .icon {{
            width: 20px;
            text-align: center;
            padding-right: 0;
        }}
        
        .files a {{
            color: var(--text);
            text-decoration: none;
            display: block;
        }}
        
        .files a:hover {{
            color: var(--primary);
        }}
        
        .folder {{
            color: var(--primary);
        }}
        
        .file {{
            color: var(--text);
        }}
        
        footer {{
            margin-top: 20px;
            text-align: center;
            color: var(--text-secondary);
            font-size: 14px;
        }}
        
        .license {{
            margin-top: 10px;
            font-size: 12px;
            color: var(--text-secondary);
        }}
        
        @media (max-width: 768px) {{
            .size, .modified {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>File Downloader</h1>
            <div>
                <span id="server-info">Server: {socket.gethostbyname(socket.gethostname())}:{PORT}</span>
            </div>
        </header>
        {content}
    </div>
    <footer>
        <p>Python File Downloader &copy; {datetime.now().year}</p>
        <div class="license">
            <p>MIT License</p>
            <p>Copyright (c) 2023 G-flame</p>
            <p>Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files, to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software.</p>
        </div>
    </footer>
</body>
</html>"""
    
    def create_breadcrumbs(self, path):
        """Create breadcrumb navigation"""
        if not path:
            return '<div class="breadcrumb">Home</div>'
        
        parts = path.strip('/').split('/')
        breadcrumbs = '<div class="breadcrumb">'
        breadcrumbs += '<a href="/">Home</a>'
        
        current_path = ""
        for i, part in enumerate(parts):
            current_path += f"/{part}"
            if i == len(parts) - 1:
                breadcrumbs += f' / {part}'
            else:
                breadcrumbs += f' / <a href="{current_path}">{part}</a>'
        
        breadcrumbs += '</div>'
        return breadcrumbs
    
    def create_file_listing(self, dir_path, rel_path):
        """Create HTML for file listing"""
        try:
            items = os.listdir(dir_path)
            
            # Separate directories and files, and sort each alphabetically
            directories = sorted([item for item in items if os.path.isdir(os.path.join(dir_path, item))])
            files = sorted([item for item in items if not os.path.isdir(os.path.join(dir_path, item))])
            
            html = f"""
            <table class="files">
                <thead>
                    <tr>
                        <th class="icon"></th>
                        <th>Name</th>
                        <th class="size">Size</th>
                        <th class="modified">Modified</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            # Add parent directory link if not at root
            if rel_path:
                parent_path = os.path.dirname(rel_path.rstrip('/'))
                html += f"""
                    <tr>
                        <td class="icon">📁</td>
                        <td><a href="/{parent_path}" class="folder">..</a></td>
                        <td class="size">-</td>
                        <td class="modified">-</td>
                    </tr>
                """
            
            # Add directories
            for item in directories:
                item_path = os.path.join(dir_path, item)
                item_time = datetime.fromtimestamp(os.path.getmtime(item_path)).strftime('%Y-%m-%d %H:%M')
                item_link = f"/{os.path.join(rel_path, item)}"
                
                html += f"""
                    <tr>
                        <td class="icon">📁</td>
                        <td><a href="{item_link}" class="folder">{item}</a></td>
                        <td class="size">-</td>
                        <td class="modified">{item_time}</td>
                    </tr>
                """
            
            # Add files
            for item in files:
                item_path = os.path.join(dir_path, item)
                item_size = self.format_size(os.path.getsize(item_path))
                item_time = datetime.fromtimestamp(os.path.getmtime(item_path)).strftime('%Y-%m-%d %H:%M')
                item_link = f"/{os.path.join(rel_path, item)}"
                
                html += f"""
                    <tr>
                        <td class="icon">📄</td>
                        <td><a href="{item_link}" class="file">{item}</a></td>
                        <td class="size">{item_size}</td>
                        <td class="modified">{item_time}</td>
                    </tr>
                """
            
            html += """
                </tbody>
            </table>
            """
            return html
        except Exception as e:
            return f"""
            <div style="padding: 20px; color: var(--danger); text-align: center;">
                Error listing directory: {str(e)}
            </div>
            """
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        request_path = urllib.parse.unquote(parsed_path.path)
        
        # Handle server stop - removed, now controlled via terminal
        
        # Normalize the path
        rel_path = request_path.strip('/')
        file_path = os.path.normpath(os.path.join(DOWNLOAD_DIR, rel_path))
        
        # Security check - prevent directory traversal
        if not os.path.abspath(file_path).startswith(os.path.abspath(DOWNLOAD_DIR)):
            self.send_headers(HTTPStatus.FORBIDDEN)
            self.wfile.write(self.render_template("""
            <div style="padding: 40px; text-align: center; color: var(--danger);">
                <h2>Access Forbidden</h2>
                <p>The requested path is outside the downloads directory.</p>
            </div>
            """, "Forbidden").encode())
            return
        
        # Handle directory listing
        if os.path.isdir(file_path):
            self.send_headers()
            breadcrumbs = self.create_breadcrumbs(rel_path)
            file_listing = self.create_file_listing(file_path, rel_path)
            
            content = f"""
            {breadcrumbs}
            {file_listing}
            """
            
            self.wfile.write(self.render_template(content).encode())
            return
        
        # Handle file download
        if os.path.exists(file_path):
            try:
                # Guess content type
                content_type, _ = mimetypes.guess_type(file_path)
                if not content_type:
                    content_type = 'application/octet-stream'
                
                # Determine if file should be displayed inline or downloaded
                disposition = 'attachment'
                if content_type.startswith(('image/', 'text/', 'video/', 'audio/')):
                    disposition = 'inline'
                
                with open(file_path, 'rb') as f:
                    fs = os.fstat(f.fileno())
                    
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Length", str(fs.st_size))
                    self.send_header("Content-Disposition", f'{disposition}; filename="{os.path.basename(file_path)}"')
                    self.end_headers()
                    
                    # Send file content
                    self.copyfile(f, self.wfile)
            except Exception as e:
                self.send_headers(HTTPStatus.INTERNAL_SERVER_ERROR)
                self.wfile.write(self.render_template(f"""
                <div style="padding: 40px; text-align: center; color: var(--danger);">
                    <h2>Error</h2>
                    <p>Could not serve file: {str(e)}</p>
                </div>
                """, "Error").encode())
            return
        
        # Handle file not found
        self.send_headers(HTTPStatus.NOT_FOUND)
        self.wfile.write(self.render_template("""
        <div style="padding: 40px; text-align: center; color: var(--danger);">
            <h2>File Not Found</h2>
            <p>The requested file does not exist.</p>
        </div>
        """, "Not Found").encode())

def get_local_ip():
    """Get the local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def signal_handler(sig, frame):
    """Handle Ctrl+C to gracefully shut down the server"""
    print("\nShutting down server...")
    if SERVER_INSTANCE:
        SERVER_INSTANCE.shutdown()
    sys.exit(0)

def terminal_monitor():
    """Monitor terminal for 'done' command to stop server"""
    print("Type 'done' to stop the server")
    while True:
        command = input().strip().lower()
        if command == 'done':
            print("\nShutting down server...")
            if SERVER_INSTANCE:
                SERVER_INSTANCE.shutdown()
            break

def run_server():
    """Run the file server"""
    global SERVER_INSTANCE
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create download directory if it doesn't exist
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    # Display info message
    local_ip = get_local_ip() # Display
    print(f"\n{'='*60}")
    print(f"  File Downloader Server by G-flame (https://github.com/g-lame)")
    print(f"{'='*60}")
    print(f"  Directory: {DOWNLOAD_DIR}")
    print(f"  Local:     http://localhost:{PORT}")
    print(f"  Network:   http://{local_ip}:{PORT}")
    print(f"{'='*60}")
    print(f"  Type 'done' to stop the server")
    print(f"{'='*60}\n")
    
    # Start the server
    socketserver.TCPServer.allow_reuse_address = True
    SERVER_INSTANCE = socketserver.ThreadingTCPServer((HOST, PORT), FileServer)
    
    # Open web browser
    try:
        webbrowser.open(f"http://localhost:{PORT}")
    except:
        pass
    
    # Start terminal monitor in a separate thread
    terminal_thread = threading.Thread(target=terminal_monitor, daemon=True)
    terminal_thread.start()
    
    # Run the server
    try:
        SERVER_INSTANCE.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if SERVER_INSTANCE:
            SERVER_INSTANCE.server_close()
            print("Server stopped")

if __name__ == "__main__":
    run_server()
