from saxonche import PySaxonProcessor, PySaxonApiError
from lxml import etree
from pathlib import Path


path_to_document_html_files = "e_invoice_check/templates/views/tmp"
path_to_stylesheets = "e_invoice_check/static/xslt"
path_to_schemas = "e_invoice_check/static/xsd"
path_to_uploaded = "e_invoice_check/uploaded/xml"


allowed_formats = {
    "peppol_bis_billing_3.0_invoice": "Peppol BIS Billing 3.0 ----- Invoice",
    "peppol_bis_billing_3.0_credit_note": "Peppol BIS Billing 3.0 -- CreditNote",
    "xrechnung_cii_2.3": "XRechnung CII 2.3 ---------- Invoice",
    "fatturaPA_v1.2": "FatturaPA 1.2 (Italy) ------ Invoice",
    "nav_osa_3.0_invoice": "NAV OSA 3.0 (Hungary) ------ Invoice",
    "ksef_eFaktura_2.0": "KSeF eFaktur 2.0 (Poland) - Invoice",
}

format_to_schema_mapping = {
    "peppol_bis_billing_3.0_invoice": "oasis_ubl/maindoc/UBL-Invoice-2.1.xsd",
    "peppol_bis_billing_3.0_credit_note": "oasis_ubl/maindoc/UBL-CreditNote-2.1.xsd",
    "xrechnung_cii_2.3": "D16B_SCRDM_Subset_CII_uncoupled/uncoupled_clm/CII/uncefact/data/standard/CrossIndustryInvoice_100pD16B.xsd",
    "fatturaPA_v1.2": "Schema_del_file_xml_FatturaPA_v1.2.2.xsd",
    "nav_osa_3.0_invoice": "OSA_Schemas_v3/invoiceData.xsd",
    "ksef_eFaktura_2.0": "KSeF_schemat.xsd",
}

format_to_schematron_xslt_mapping = {
    "peppol_bis_billing_3.0_invoice": "PEPPOL-EN16931-UBL_schematron.xslt",
    "peppol_bis_billing_3.0_credit_note": "PEPPOL-EN16931-UBL_schematron.xslt",
    "xrechnung_cii_2.3": None,
    "fatturaPA_v1.2": None,
    "nav_osa_3.0_invoice": None,
    "ksef_eFaktura_2.0": None,
}

format_to_schematron_mapping = {
    "peppol_bis_billing_3.0_invoice": "PEPPOL-EN16931-UBL.sch",
    "peppol_bis_billing_3.0_credit_note": "PEPPOL-EN16931-UBL.sch",
    "xrechnung_cii_2.3": None,
    "fatturaPA_v1.2": None,
    "nav_osa_3.0_invoice": None,
    "ksef_eFaktura_2.0": None,
}

format_to_xslt_mapping = {
    "peppol_bis_billing_3.0_invoice": ["stylesheet-ubl.xslt"],
    "peppol_bis_billing_3.0_credit_note": ["stylesheet-ubl.xslt"],
    "xrechnung_cii_2.3": [
        "xrechnung-2.3.1-xrechnung-visualization-2023-05-12/xsl/cii-xr.xsl",
        "xrechnung-2.3.1-xrechnung-visualization-2023-05-12/xsl/xrechnung-html.xsl",
    ],
    "fatturaPA_v1.2": ["fatturapa_v1.2.1_de-it.xsl"],
    "nav_osa_3.0_invoice": ["NAV_InvoiceDataTemplate_XSLT_HTML.xslt"],
    "ksef_eFaktura_2.0": ["kseffaktura.xsl"],
}

xslt_params = {
    "peppol_bis_billing_3.0_invoice": {"my_param": ""},
    "peppol_bis_billing_3.0_credit_note": {"my_param": ""},
    "xrechnung_cii_2.3": {"my_param": ""},
    "fatturaPA_v1.2": {"my_param": ""},
    "nav_osa_3.0_invoice": {"lang": "EN"},
    "ksef_eFaktura_2.0": {"my_param": ""},
}

curr_exec_dir = {
    "peppol_bis_billing_3.0_invoice": ".",
    "peppol_bis_billing_3.0_credit_note": ".",
    "xrechnung_cii_2.3": "xrechnung-2.3.1-xrechnung-visualization-2023-05-12/xsl/",
    "fatturaPA_v1.2": ".",
    "nav_osa_3.0_invoice": ".",
    "ksef_eFaktura_2.0": ".",
}
# instantiate a parser which removes white space while parsing with lxml
my_parser = etree.XMLParser(remove_blank_text=True)


# class Xslt_proc:
#     """to instantiate a saxon xslt3.0 processor object."""

#     proc = PySaxonProcessor(license=False)
#     my_proc = proc.new_xslt30_processor()

#     def __init__(self, stylesheet_text):
#         self.stylesheet_text = stylesheet_text
#         self.xform = self.my_proc.compile_stylesheet(stylesheet_text=stylesheet_text)


def validate_file_content(stream, file_ext):
    """to check if the content of the uploaded file is a well-formed xml"""
    if file_ext == ".xml":
        try:
            tree = etree.parse(stream, parser=my_parser)

        except PySaxonApiError as error:
            return (False, 2, error, type(error))
        except Exception as error:
            return (False, 1, error, type(error))
    else:
        pass
    return (True, 0, None, None)


# def transform_xml(xslt_proc, input_xml_text, params):
#     """takes an xslt proc object (with loaded stylesheet) and returns a serialized xml"""
#     doc = xslt_proc.proc.parse_xml(xml_text=input_xml_text)
#     for key, value in params.items():
#         print(f"{key}, {value}")
#         xslt_proc.xform.set_parameter(key, xslt_proc.proc.make_string_value(value))
#     out = xslt_proc.xform.transform_to_string(xdm_node=doc)
#     return out


def evaluate_xpath(proc, xpathproc, xml_string, xpath_expression, namespaces={}):
    xml_obj = proc.parse_xml(xml_text=xml_string)
    xpathproc.set_context(xdm_item=xml_obj)
    xpathproc.set_backwards_compatible(True)
    for key, value in namespaces.items():
        xpathproc.declare_namespace(key, value)
    return xpathproc.evaluate(xpath_expression)


def transform_xdm_nodes_to_string(
    proc, xsltproc, stylesheet_objs, input_obj, cwd="", params={}
):
    xsltproc.clear_parameters()
    xsltproc.set_cwd(cwd)

    for i, stylesheet in enumerate(stylesheet_objs):
        executable = xsltproc.compile_stylesheet(stylesheet_node=stylesheet)
        if len(params) != 0:
            for key, value in params.items():
                executable.set_parameter(key, proc.make_string_value(value))
        result_string = executable.transform_to_string(xdm_node=input_obj)
        if len(stylesheet_objs) > 1 and i != len(stylesheet_objs) - 1:
            print(result_string)
            input_obj = proc.parse_xml(xml_text=result_string)
    return result_string


def validate_with_schematron(proc, xsltproc, input_obj, current_format):
    stylesheets = []
    current_xslt_file = (
        path_to_stylesheets + "/" + format_to_schematron_xslt_mapping[current_format]
    )

    stylesheet_obj = proc.parse_xml(xml_file_name=current_xslt_file)
    stylesheets.append(stylesheet_obj)

    return transform_xdm_nodes_to_string(proc, xsltproc, stylesheets, input_obj)


def evaluate_svrl_result(proc, xpathproc, schematron_result_string, current_format):
    namespaces = {"svrl": "http://purl.oclc.org/dsdl/svrl"}
    xpath_expression = "//svrl:failed-assert"
    result = evaluate_xpath(
        proc,
        xpathproc,
        schematron_result_string,
        xpath_expression,
        namespaces=namespaces,
    )

    schematron_validation_log = []
    if not result:
        schematron_validation_log = [
            f"Validation with schema: "
            + format_to_schematron_mapping[current_format]
            + " was successful.",
        ]
        is_schematron_validation_ok = True
    else:
        for error in result:
            xpath_expression = "concat(svrl:failed-assert/@flag, ', ', \
                                       svrl:failed-assert/@id, '\n', \
                                       svrl:failed-assert/svrl:text/text(), '\n', \
                                       'local-name-path: \n', \
                                       replace(//svrl:failed-assert/@location, 'Q\{[^}]*\}' ,''))"
            error_str = evaluate_xpath(
                proc,
                xpathproc,
                str(error),
                xpath_expression,
                namespaces=namespaces,
            )

            schematron_validation_log.append(error_str)
            is_schematron_validation_ok = False
    return [schematron_validation_log, is_schematron_validation_ok]


def validate_with_schema(proc, xsltproc, input_obj, current_format):
    current_xsd_file = path_to_schemas + "/" + format_to_schema_mapping[current_format]
    schema = etree.parse(current_xsd_file, parser=my_parser)
    tree = etree.fromstring(str(input_obj), parser=my_parser)

    #### Validate input file with corresponding xml schema
    result = get_errors_from_schema_validation(tree, schema)
    if result is None:
        schema_validation_log = [
            f"Validation with schema: "
            + format_to_schema_mapping[current_format]
            + " was successful.",
        ]
        is_schema_validation_ok = True
    else:
        schema_validation_log = result
        is_schema_validation_ok = False
    return [schema_validation_log, is_schema_validation_ok]


def get_errors_from_schema_validation(xml, schema):
    """validates against the schema"""
    schema_validator = etree.XMLSchema(schema)
    try:
        schema_validator.assert_(xml)
    except AssertionError as e:
        return schema_validator.error_log


def create_html_of_uploaded_file(proc, xsltproc, input_obj, current_format):
    stylesheets = []
    for stylesheet in format_to_xslt_mapping[current_format]:
        current_xslt_file = path_to_stylesheets + "/" + stylesheet

        stylesheet_obj = proc.parse_xml(xml_file_name=current_xslt_file)
        stylesheets.append(stylesheet_obj)

    params = xslt_params[current_format]
    cwd = curr_exec_dir[current_format]
    document_html = transform_xdm_nodes_to_string(
        proc, xsltproc, stylesheets, input_obj, cwd=cwd, params=params
    )
    return document_html
