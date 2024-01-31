import os
import re
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
    xslt_params,
)


bp = Blueprint("views", __name__)


# TODO:
# - clean up home view. The render_template should be called only once (continue?).
#
# - fix readable html view, height and width issue (100% doesn't work)
#
#
#
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
            validation_report["schema_validation_done"] = True

            # validation with schematron xslt
            if is_schema_validation_ok == True and \
               format_to_schematron_xslt_mapping[current_format] is not None:
                current_xslt_file = (
                    path_to_stylesheets + "/" + format_to_schematron_xslt_mapping[current_format]
                )
                stylesheet = etree.parse(current_xslt_file, parser=my_parser)
                xslt = etree.tostring(stylesheet, pretty_print="True", encoding="unicode")

                xslt_proc = Xslt_proc(stylesheet_text=xslt)
                schematron_result = transform_xml(xslt_proc, xml, xslt_params[current_format])

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
                        error_type = error.get("flag")         
                        error_id = error.get("id")         
                        error_text = error.find("./*[1]").text
                        error_location_raw = error.get("location")         

                        pattern_to_find = r"Q\{[^}]*\}"
                        error_location = re.sub(pattern_to_find, "", error_location_raw)
                        error_str = f"{error_type}, " + \
                                    f"{error_id} \n" + \
                                    f"{error_text} \n" + \
                                    f"{error_location}" 

                        schematron_validation_log.append(error_str)
                        is_schematron_validation_ok = False

                validation_report["schematron_validation_log"] = schematron_validation_log
                validation_report["is_schematron_validation_ok"] = is_schematron_validation_ok
                validation_report["schematron_validation_done"] = True
                    
            # Create html view of the document with xslt3 and save to template dir

            current_xslt_file = (
                path_to_stylesheets + "/" + format_to_xslt_mapping[current_format][0]
            )
            stylesheet = etree.parse(current_xslt_file, parser=my_parser)
            xslt = etree.tostring(stylesheet, pretty_print="True", encoding="unicode")

            xslt_proc = Xslt_proc(stylesheet_text=xslt)

            if len(format_to_xslt_mapping[current_format]) > 1:
                # for some formats a two step transformation is required
                pass
                # from intermediate transform to final html
                intermediate_format = transform_xml(xslt_proc, xml, xslt_params[current_format])


                current_xslt_file = (
                    path_to_stylesheets + "/" + format_to_xslt_mapping[current_format][1]
                )
                stylesheet = etree.parse(current_xslt_file, parser=my_parser)
                xslt = etree.tostring(stylesheet, pretty_print="True", encoding="unicode")

                xslt_proc2 = Xslt_proc(stylesheet_text=xslt)


                # document_html = transform_xml(xslt_proc2, intermediate_format, xslt_params[current_format])

            else:
                document_html = transform_xml(xslt_proc, xml, xslt_params[current_format])

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
