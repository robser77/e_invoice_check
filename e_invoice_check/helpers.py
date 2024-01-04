from saxonche import PySaxonProcessor
from lxml import etree
from pathlib import Path


class Xslt_proc:
    proc = PySaxonProcessor(license=False)
    my_proc = proc.new_xslt30_processor()

    def __init__(self, stylesheet_text):
        self.stylesheet_text = stylesheet_text
        self.xform = self.my_proc.compile_stylesheet(stylesheet_text=stylesheet_text)


def validate_file_content(stream, file_ext):
    if file_ext == ".xml":
        try:
            tree = etree.parse(stream)
        except etree.XMLSyntaxError as error:
            return (False, 2, error, type(error))
        except Exception as error:
            return (False, 1, error, type(error))
    else:
        pass
    return (True, 0, None, None)


def transform_xml(xslt_proc, input_xml_text):
    doc = xslt_proc.proc.parse_xml(xml_text=input_xml_text)
    out = xslt_proc.xform.transform_to_string(xdm_node=doc)
    return out
