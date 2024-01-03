from saxonche import PySaxonProcessor
from lxml import etree
from pathlib import Path

class Xslt_proc:
    proc = PySaxonProcessor(license=False)
    my_proc = proc.new_xslt30_processor()
    def __init__(self, stylesheet_text):
        self.stylesheet_text = stylesheet_text    
        self.xform = self.my_proc.compile_stylesheet(stylesheet_text=stylesheet_text) 


def transform(processor, in_xml_text):
    doc = processor.proc.parse_xml(xml_text=in_xml_text) 
    out = processor.xform.transform_to_string(xdm_node=doc)
    return out

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


def use_xslt_proc_2(xslt_stylesheet_text, input_xml_text, stringparam):
    # https://pypi.org/project/saxonpy/
    # https://stackoverflow.com/questions/29443364/use-saxon-with-python
    with PySaxonProcessor(license=False) as proc:
        xsltproc = proc.new_xslt_processor()
        document = proc.parse_xml(xml_text=input_xml_text)
        xsltproc.set_source(xdm_node=document)

        function = proc.make_string_value(stringparam)
        xsltproc.set_parameter("function", function)

        xsltproc.compile_stylesheet(stylesheet_text=xslt_stylesheet_text)
        result = xsltproc.transform_to_string()
        
    return (result, [])


def use_xslt_proc_3(xslt_proc, xslt_stylesheet_text, input_xml_text, stringparam):
    # https://pypi.org/project/saxonpy/
    # https://stackoverflow.com/questions/29443364/use-saxon-with-python

    return transform(xslt_proc, input_xml_text)