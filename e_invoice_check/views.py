import os
import uuid
from flask import (
    Blueprint,
    flash,
    render_template,
    request,
    abort,
    current_app,
    url_for,
)
from werkzeug.utils import secure_filename
from lxml import etree
from e_invoice_check.helpers import validate_file_content, transform_xml, Xslt_proc


bp = Blueprint("views", __name__)


@bp.route("/")
def home():
    return render_template("views/home.html")


@bp.route("/document/<document_html_name>")
def document(document_html_name):
    with open(
        f"e_invoice_check/templates/views/{document_html_name}", "r"
    ) as doc_template:
        data = doc_template.read()
    return data


@bp.route("/about", methods=["GET", "POST"])
def about():
    # get object from uploaded file
    if request.files.getlist("file"):
        for uploaded_file in request.files.getlist("file"):
            filename = uploaded_file.filename
            if filename != "":
                file_ext = os.path.splitext(filename)[1]
                # Check file extension
                if file_ext not in current_app.config["UPLOAD_EXTENSIONS"]:
                    flash(
                        f"File extension not allowed. Allowed values: xml \n Filename: {filename}"
                    )
                    # TODO add custom 400
                    abort(400)

                # validate file content
                result = validate_file_content(uploaded_file.stream, file_ext)
                if not result[0]:
                    flash(f"File content error: {result[2]}, ({result[3]})")
                    # TODO add custom 400
                    abort(400)

                # reset file stream
                uploaded_file.stream.seek(0)
                # parse xml and transform to str
                tree = etree.parse(uploaded_file.stream)
                xml = etree.tostring(tree, pretty_print="True", encoding="unicode")

                # parse xslt and transform to str
                stylesheet = etree.parse(
                    "e_invoice_check/static/xslt/stylesheet-ubl.xslt"
                )
                xslt = etree.tostring(
                    stylesheet, pretty_print="True", encoding="unicode"
                )

                # create html view of the document with xslt and save to template dir
                xslt_proc = Xslt_proc(stylesheet_text=xslt)
                document_html = transform_xml(xslt_proc, xml)

                document_html_name = str(uuid.uuid4()) + ".html"
                with open(
                    f"e_invoice_check/templates/views/{document_html_name}", "w"
                ) as document_html_file:
                    document_html_file.write(document_html)

                document_html_url = url_for(
                    "views.document", document_html_name=document_html_name
                )
                return render_template(
                    "views/doc-view.html",
                    filename=filename,
                    document_html_url=document_html_url,
                )

    else:
        return render_template("views/about.html")
