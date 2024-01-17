from saxonche import PySaxonProcessor
from lxml import etree
from pathlib import Path


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

format_to_schematron_xslt_mapping = {
    "peppol_bis_billing_3.0_invoice": "PEPPOL-EN16931-UBL_schematron.xslt",
    "peppol_bis_billing_3.0_credit_note": "PEPPOL-EN16931-UBL_schematron.xslt",
}

format_to_schematron_mapping = {
    "peppol_bis_billing_3.0_invoice": "PEPPOL-EN16931-UBL.sch",
    "peppol_bis_billing_3.0_credit_note": "PEPPOL-EN16931-UBL.sch",
}

format_to_xslt_mapping = {
    "peppol_bis_billing_3.0_invoice": "stylesheet-ubl.xslt",
    "peppol_bis_billing_3.0_credit_note": "stylesheet-ubl.xslt",
}

# instantiate a parser which removes white space while parsing with lxml
my_parser = etree.XMLParser(remove_blank_text=True)


class Xslt_proc:
    """to instantiate a saxon xslt3.0 processor object."""

    proc = PySaxonProcessor(license=False)
    my_proc = proc.new_xslt30_processor()

    def __init__(self, stylesheet_text):
        self.stylesheet_text = stylesheet_text
        self.xform = self.my_proc.compile_stylesheet(stylesheet_text=stylesheet_text)


def validate_file_content(stream, file_ext):
    """to check if the content of the uploaded file is a well-formed xml"""
    if file_ext == ".xml":
        try:
            tree = etree.parse(stream, parser=my_parser)
        except etree.XMLSyntaxError as error:
            return (False, 2, error, type(error))
        except Exception as error:
            return (False, 1, error, type(error))
    else:
        pass
    return (True, 0, None, None)


def transform_xml(xslt_proc, input_xml_text):
    """takes an xslt proc object (with loaded stylesheet) and returns a serialized xml"""
    doc = xslt_proc.proc.parse_xml(xml_text=input_xml_text)
    out = xslt_proc.xform.transform_to_string(xdm_node=doc)
    return out


def get_errors_from_schema_validation(xml, schema):
    """validates against the schema"""
    schema_validator = etree.XMLSchema(schema)
    try:
        schema_validator.assert_(xml)
    except AssertionError as e:
        return schema_validator.error_log
