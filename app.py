from flask import Flask
app = Flask(__name__)

@app.get("/")
def hello():
    return "Hello from Flask on EC2!"


@app.get("/explorer")
def explorer():
    return (
        """
        <!doctype html>
        <html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n<title>NBA Player Stats Explorer</title>\n<style>\n  html, body { margin: 0; padding: 0; height: 100%; }\n  .frame-wrap { height: 100vh; width: 100%; display: flex; flex-direction: column; }\n  header { padding: 12px 16px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; border-bottom: 1px solid #eee; }\n  header h1 { font-size: 18px; margin: 0; }\n  .frame { flex: 1; border: 0; width: 100%; }\n</style>\n</head>\n<body>\n  <div class=\"frame-wrap\">\n    <header>\n      <h1>NBA Player Stats Explorer</h1>\n    </header>\n    <iframe class=\"frame\" src=\"/nba/\" allow=\"fullscreen\" loading=\"lazy\"></iframe>\n  </div>\n</body>\n</html>
        """
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
