from flask import Flask
from e_invoice_check import views


def create_app():
    app = Flask(__name__)

    app.secret_key = b'_5#y2L"F4Q8z_super_secret_wonder_key]/'
    app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
    app.config["UPLOAD_EXTENSIONS"] = [".xml"]
    app.config["UPLOAD_PATH"] = "uploads"

    app.register_blueprint(views.bp)

    with open(f"e_invoice_check/templates/views/document.html", "w") as html_file:
        html_file.write(
            """
        <!doctype html>
        <html>
            <head>
            <title>Document</title>
                <meta name="description" content="Nothing yet">
            </head>
            <body>
                Nothing to see here.
            </body>
        </html>
        """
        )

    return app
