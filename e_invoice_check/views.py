import shutil
import os
import uuid
from flask import (
    Blueprint,
    flash,
    render_template,
    request,
    current_app,
    url_for,
)
from werkzeug.utils import secure_filename
from saxonche import PySaxonProcessor
from lxml import etree
from e_invoice_check.helpers import (
    validate_file_content,
    my_parser,
    path_to_document_html_files,
    path_to_uploaded,
    allowed_formats,
    format_to_schematron_xslt_mapping,
    evaluate_svrl_result,
    create_html_of_uploaded_file,
    validate_with_schematron,
    validate_with_schema,
)


bp = Blueprint("views", __name__)


# TODO:
# - fix readable html view, height and width issue (100% doesn't work)
# - why when returning xdm node strange results (schematron and html)?
# - add html to pdf feature
# - make better code view in html (formatting, highlighting, focus)
# - move dicts to db
# - add login and user interface


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
            ###################################################################
            #                        check uploaded file                      #
            ###################################################################
            filename = uploaded_file.filename
            #### Check if file was provided
            if filename == "":
                break

            #### Check file extension
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in current_app.config["UPLOAD_EXTENSIONS"]:
                flash(
                    f"File extension not allowed. Allowed values: 'xml', Filename: {filename}"
                )
                break

            #### Validate file content
            result = validate_file_content(uploaded_file.stream, file_ext)
            if not result[0]:
                flash(f"File content error: {result[2]}")
                break

            #### Reset file stream, since it was consumed by file content validation
            uploaded_file.stream.seek(0)
            my_uuid = str(uuid.uuid4())
            proc = PySaxonProcessor(license=False)
            xsltproc = proc.new_xslt30_processor()
            xpathproc = proc.new_xpath_processor()

            uploaded_file_name = path_to_uploaded + "/" + my_uuid + ".xml"
            with open(uploaded_file_name, "wb") as file:
                shutil.copyfileobj(uploaded_file.stream, file)

            input_obj = proc.parse_xml(xml_file_name=uploaded_file_name)

            #### Parse xml and transform to str
            uploaded_file.stream.seek(0)
            tree = etree.parse(uploaded_file.stream, parser=my_parser)
            xml = etree.tostring(tree, pretty_print="True", encoding="unicode")
            xml_test = xml

            #### Get target format from dropdown
            current_format = request.form.get("format-dropdown")

            ###################################################################
            #                     validation starts here                      #
            ###################################################################
            validation_report = {}

            #### apply xml schema
            schema_result = validate_with_schema(
                proc, xsltproc, input_obj, current_format
            )

            validation_report["schema_validation_log"] = schema_result[0]
            validation_report["is_schema_validation_ok"] = schema_result[1]
            validation_report["schema_validation_done"] = True

            is_schema_validation_ok = validation_report["is_schema_validation_ok"]

            ###################################################################
            #                 apply schematron (if we should)                 #
            ###################################################################
            if (
                is_schema_validation_ok == True
                and format_to_schematron_xslt_mapping[current_format] is not None
            ):
                #### validate with schematron xslt
                schematron_result = validate_with_schematron(
                    proc, xsltproc, input_obj, current_format
                )
                #### evaluate the result
                schematron_val_result = evaluate_svrl_result(
                    proc, xpathproc, schematron_result, current_format
                )

                validation_report["schematron_validation_log"] = schematron_val_result[
                    0
                ]
                validation_report[
                    "is_schematron_validation_ok"
                ] = schematron_val_result[1]
                validation_report["schematron_validation_done"] = True

            ###################################################################
            #                Create html view of the document                 #
            ###################################################################

            document_html = create_html_of_uploaded_file(
                proc, xsltproc, input_obj, current_format
            )
            #### save html to file
            document_html_name = my_uuid + ".html"
            with open(
                f"{path_to_document_html_files}/{document_html_name}", "w"
            ) as document_html_file:
                document_html_file.write(str(document_html))

            document_html_url = url_for(
                "views.document", document_html_name=document_html_name
            )

            return render_template(
                "views/home.html",
                filename=filename,
                document_html_url=document_html_url,
                allowed_formats=allowed_formats,
                validation_report=validation_report,
                xml_test=xml_test,
            )

    return render_template("views/home.html", allowed_formats=allowed_formats)
