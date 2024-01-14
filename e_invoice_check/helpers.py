from saxonche import PySaxonProcessor
from lxml import etree
from pathlib import Path

# instantiate a parser which removes white space while parsing
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
