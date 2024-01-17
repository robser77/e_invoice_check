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
    path_to_document_html_files,
    path_to_schemas,
    path_to_stylesheets,
    allowed_formats,
    format_to_schema_mapping,
    format_to_schematron_xslt_mapping,
    format_to_schematron_mapping,
    format_to_xslt_mapping,
)


bp = Blueprint("views", __name__)


# TODO:
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

            # validation phase starts here
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

            # validation with schematron xslt
            if is_schema_validation_ok == True:
                current_xslt_file = (
                    path_to_stylesheets + "/" + format_to_schematron_xslt_mapping[current_format]
                )
                stylesheet = etree.parse(current_xslt_file, parser=my_parser)
                xslt = etree.tostring(stylesheet, pretty_print="True", encoding="unicode")

                xslt_proc = Xslt_proc(stylesheet_text=xslt)
                schematron_result = transform_xml(xslt_proc, xml)

                # Encode the XML string to bytes
                schematron_result_bytes = schematron_result.encode('utf-8')
                # Parse the XML string
                schematron_result_tree = etree.fromstring(schematron_result_bytes)

                # Define the namespace map
                namespace_map = {'svrl': 'http://purl.oclc.org/dsdl/svrl'}

                # Use xpath with the namespace to select elements
                result = schematron_result_tree.xpath('//svrl:failed-assert', namespaces=namespace_map)                
                schematron_validation_log = []
                if not result:
                    schematron_validation_log =  [
                        f"Validation with schema: "
                        + format_to_schematron_mapping[current_format]
                        + " was successful.",]
                    is_schematron_validation_ok = True
                    flash(f" schematron result ok")
                else:
                    for error in result:
                        for attribute_name, attribute_value in error.attrib.items():
                            schematron_validation_log.append(attribute_name + "|" + attribute_value)
                    is_schematron_validation_ok = False
                    flash(f"File schematron result: {schematron_validation_log}")

                validation_report["schematron_validation_log"] = schematron_validation_log
                validation_report["is_schematron_validation_ok"] = is_schematron_validation_ok
                    
            # Create html view of the document with xslt3 and save to template dir
            current_xslt_file = (
                path_to_stylesheets + "/" + format_to_xslt_mapping[current_format]
            )
            stylesheet = etree.parse(current_xslt_file, parser=my_parser)
            xslt = etree.tostring(stylesheet, pretty_print="True", encoding="unicode")

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
