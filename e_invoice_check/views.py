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
path_to_document_html_files = "e_invoice_check/templates/views/tmp"
path_to_stylesheets = "e_invoice_check/static/xslt"
path_to_schemas = "e_invoice_check/static/xsd"

allowed_formats = {
    "peppol_bis_billing_3.0_invoice":"Peppol BIS Billing 3.0 -- Invoice",
    "peppol_bis_billing_3.0_credit_note":"Peppol BIS Billing 3.0 -- CreditNote"
}

format_to_schema_file = {
    "peppol_bis_billing_3.0_invoice":"oasis_ubl/maindoc/UBL-Invoice-2.1.xsd",
    "peppol_bis_billing_3.0_credit_note":"oasis_ubl/maindoc/UBL-CreditNote-2.1.xsd"
}

# TODO: 
# add schema validation


@bp.app_errorhandler(404)
def page_not_found(e):
    return render_template("error.html", error=e), 404


@bp.app_errorhandler(415)
def wrong_file_extension(e):
    return render_template("error.html", error=e), 415


@bp.app_errorhandler(418)
def wrong_file_extension(e):
    return render_template("error.html", error=e), 418


@bp.app_errorhandler(500)
def wrong_file_extension(e):
    return render_template("error.html", error=e), 500


@bp.route("/about")
def about():
    return render_template("views/about.html")


@bp.route("/document/<document_html_name>")
def document(document_html_name):
    with open(
        f"{path_to_document_html_files}/{document_html_name}", "r"
    ) as doc_template:
        data = doc_template.read()
    return data


@bp.route("/", methods=["GET", "POST"])
def home(filename="", document_html_url=""):
    # get object from uploaded file
    if request.files.getlist("file"):
        for uploaded_file in request.files.getlist("file"):
            filename = uploaded_file.filename
            # Check if file was provided
            if filename == "":
                return render_template("views/home.html")

            # Check file extension
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in current_app.config["UPLOAD_EXTENSIONS"]:
                flash(
                    f"File extension not allowed. Allowed values: 'xml', Filename: {filename}"
                )
                return render_template("views/home.html")

            # Validate file content
            result = validate_file_content(uploaded_file.stream, file_ext)
            if not result[0]:
                flash(f"File content error: {result[2]}")
                return render_template("views/home.html")

            # Reset file stream, since it was consumed by validation
            uploaded_file.stream.seek(0)
            # Parse xml and transform to str
            tree = etree.parse(uploaded_file.stream)
            xml = etree.tostring(tree, pretty_print="True", encoding="unicode")

            # Validate input file with corresponding xml schema
            current_format = request.form.get('format-dropdown')
            current_xsd_file_path = path_to_schemas + "/" + format_to_schema_file[current_format] 
            print(current_xsd_file_path)
            # Parse xslt and transform to str
            stylesheet = etree.parse(f"{path_to_stylesheets}/stylesheet-ubl.xslt")
            xslt = etree.tostring(stylesheet, pretty_print="True", encoding="unicode")

            # Create html view of the document with xslt and save to template dir
            xslt_proc = Xslt_proc(stylesheet_text=xslt)
            document_html = transform_xml(xslt_proc, xml)

            document_html_name = str(uuid.uuid4()) + ".html"
            with open(
                f"{path_to_document_html_files}/{document_html_name}", "w"
            ) as document_html_file:
                document_html_file.write(document_html)

            document_html_url = url_for(
                "views.document", document_html_name=document_html_name
            )

            return render_template(
                "views/home.html",
                filename=filename,
                document_html_url=document_html_url,
                allowed_formats=allowed_formats
            )

    return render_template("views/home.html", allowed_formats=allowed_formats)
