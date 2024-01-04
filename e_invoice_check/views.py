import os
import uuid
from flask import Blueprint, flash, render_template, request, abort, current_app
from werkzeug.utils import secure_filename
from lxml import etree
from e_invoice_check.helpers import validate_file_content, transform_xml, Xslt_proc


bp = Blueprint("views", __name__)


@bp.route("/")
def home():
    return render_template("views/home.html")


@bp.route("/document")
def document():
    doc_template_name = "document.html"
    with open(f"e_invoice_check/templates/views/{doc_template_name}", "r") as html_file:
        data = html_file.read()
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

                # create html view of the invoice with xslt and save to template dir
                # doc_template_name = "document.html"
                doc_template_name = str(uuid.uuid4()) + ".html"
                xslt_proc = Xslt_proc(stylesheet_text=xslt)
                doc_template_html = transform_xml(xslt_proc, xml)

                with open(
                    f"e_invoice_check/templates/views/{doc_template_name}", "w"
                ) as html_file:
                    html_file.write(doc_template_html)

                return render_template(
                    "views/doc-view.html",
                    filename=filename,
                    doc_template_name=doc_template_name,
                )

    else:
        return render_template("views/about.html")
