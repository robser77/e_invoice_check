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
from e_invoice_check.helpers import (
    get_errors_from_schema_validation,
    validate_file_content,
    transform_xml,
    Xslt_proc,
    my_parser,
)


bp = Blueprint("views", __name__)
path_to_document_html_files = "e_invoice_check/templates/views/tmp"
path_to_stylesheets = "e_invoice_check/static/xslt"
path_to_schemas = "e_invoice_check/static/xsd"

allowed_formats = {
    "peppol_bis_billing_3.0_invoice": "Peppol BIS Billing 3.0 -- Invoice",
    "peppol_bis_billing_3.0_credit_note": "Peppol BIS Billing 3.0 -- CreditNote",
}

format_to_schema_mapping = {
    "peppol_bis_billing_3.0_invoice": "oasis_ubl/maindoc/UBL-Invoice-2.1.xsd",
    "peppol_bis_billing_3.0_credit_note": "oasis_ubl/maindoc/UBL-CreditNote-2.1.xsd",
}

format_to_xslt_mapping = {
    "peppol_bis_billing_3.0_invoice": "stylesheet-ubl.xslt",
    "peppol_bis_billing_3.0_credit_note": "stylesheet-ubl.xslt",
}


# TODO:
# - move schema validation to helpers
# - make document_html_view generation with xslt dependent of format (dropdown)
# - clean up home view. The render_template should be called only once (continue?).
#
# what I dont like is that I use saxonche and lxml
# I would prefer to have only one (is this possible)
# - saxonche -> xslt3.0 (for xml to html, schematron)
# - lxml -> parsing and schema validation


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
                return render_template(
                    "views/home.html", allowed_formats=allowed_formats
                )

            # Check file extension
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in current_app.config["UPLOAD_EXTENSIONS"]:
                flash(
                    f"File extension not allowed. Allowed values: 'xml', Filename: {filename}"
                )
                return render_template(
                    "views/home.html", allowed_formats=allowed_formats
                )

            # Validate file content
            result = validate_file_content(uploaded_file.stream, file_ext)
            if not result[0]:
                flash(f"File content error: {result[2]}")
                return render_template(
                    "views/home.html", allowed_formats=allowed_formats
                )

            # Reset file stream, since it was consumed by file content validation
            uploaded_file.stream.seek(0)
            # Parse xml and transform to str
            tree = etree.parse(uploaded_file.stream, parser=my_parser)
            xml = etree.tostring(tree, pretty_print="True", encoding="unicode")
            xml_test = xml

            # Get target format from dropdown
            current_format = request.form.get("format-dropdown")
            # Get and load schema file based on format
            current_xsd_file = (
                path_to_schemas + "/" + format_to_schema_mapping[current_format]
            )
            schema = etree.parse(current_xsd_file, parser=my_parser)

            validation_report={}
            # Validate input file with corresponding xml schema
            result = get_errors_from_schema_validation(tree, schema)
            if result is None:
                schema_validation_log =  [
                    f"Validation with schema: "
                    + format_to_schema_mapping[current_format]
                    + " was successful.",]
                is_schema_validation_ok = True
            else:
                schema_validation_log = result
                is_schema_validation_ok = False

            validation_report["schema_validation_log"] = schema_validation_log
            validation_report["is_schema_validation_ok"] = is_schema_validation_ok
            current_xslt_file = (
                path_to_stylesheets + "/" + format_to_xslt_mapping[current_format]
            )
            stylesheet = etree.parse(current_xslt_file, parser=my_parser)
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
                allowed_formats=allowed_formats,
                validation_report=validation_report,
                xml_test=xml_test
            )

    return render_template("views/home.html", allowed_formats=allowed_formats)
