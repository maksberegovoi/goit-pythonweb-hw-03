from http.server import HTTPServer, BaseHTTPRequestHandler
import pathlib
import urllib.parse
import mimetypes
import json
from datetime import datetime
from jinja2 import Environment, FileSystemLoader


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)

        if parsed_path.path == "/":
            self.send_html("index.html")
        elif parsed_path.path == "/message":
            self.send_html("message.html")
        elif parsed_path.path == "/read":
            storage_file = pathlib.Path("storage") / "data.json"
            pathlib.Path("storage").mkdir(exist_ok=True)
            with open(storage_file, "r", encoding="utf-8") as f:
                messages = json.load(f)
            self.run_template("read.html", messages.values())
        else:
            if pathlib.Path().joinpath(parsed_path.path[1:]).exists():
                self.send_static()
            else:
                self.send_html("error.html", status=404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        data_parse = urllib.parse.unquote_plus(data.decode("utf-8"))
        print(f"Received POST data: {data_parse}")
        data_dict = {
            key: value
            for key, value in [item.split("=") for item in data_parse.split("&")]
        }
        print(f"Parsed data dictionary: {data_dict}")

        message_id = datetime.now().isoformat()
        storage_file = pathlib.Path("storage") / "data.json"
        pathlib.Path("storage").mkdir(exist_ok=True)

        try:
            with open(storage_file, "r", encoding="utf-8") as f:
                messages = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            messages = {}

        messages[message_id] = data_dict
        with open(storage_file, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)

        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def send_html(self, file, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        with open(file, "rb") as f:
            self.wfile.write(f.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(f".{self.path}", "rb") as file:
            self.wfile.write(file.read())

    def run_template(self, template_name, context):
        env = Environment(loader=FileSystemLoader(searchpath="./"))
        template = env.get_template(template_name)
        html_page = template.render(messages=context).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_page)


def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, port=3000):
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    try:
        print(f"Starting httpd server on port {port}...")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping httpd server...")
        httpd.server_close()


if __name__ == "__main__":
    run()