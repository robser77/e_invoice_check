import io
import sys
import argparse
from lxml import etree
from saxonpy import PySaxonProcessor

parser = etree.XMLParser(remove_blank_text=True)


def parse_args(args):
    h_xslt_stylesheet = "input data: xslt stylesheet to apply"
    h_input_xml = 'input data: xml to transform (full path or "-" for stdin)'
    h_output_xml = 'output file (full path, "-" for stdout)'
    h_verbose = "increase output verbosity"
    h_version = "which xslt version to use (1.0|2.0)"
    h_pretty = "pretty print the result"
    h_messages = "output xsl:message to screen"
    h_error_log = "output error log to screen"
    h_no_xml = "do not output any xml (neither stdout nor file). To use in combination with logs and messages"
    h_xslt_param = "provide a parameter to a stylesheet"

    parser = argparse.ArgumentParser()
    parser.add_argument("xslt", type=str, help=h_xslt_stylesheet)
    parser.add_argument("input", type=str, help=h_input_xml)
    parser.add_argument("output", type=str, help=h_output_xml)
    parser.add_argument("-xv", "--version", help=h_version, choices=["1.0", "2.0"], default="1.0")
    parser.add_argument("-v", "--verbose", help=h_verbose, action="store_true")
    parser.add_argument("-pp", "--pretty", help=h_pretty, default=True)
    parser.add_argument("-m", "--messages", help=h_messages, action="store_true")
    parser.add_argument("-e", "--error_log", help=h_error_log, action="store_true")
    parser.add_argument(
        "-no", "--no_xml_output", help=h_no_xml, action="store_true", default=False
    )
    parser.add_argument("-p", "--stringparam", help=h_xslt_param, default="")

    return parser.parse_args(args)

def use_xslt_proc_1(xslt_stylesheet_text, input_xml_text, args):
    # https://lxml.de/xpathxslt.html#xslt
    '''to transform an xml (as string) with an xslt stylsheet (as string)
        using xslt version 1.0 (lxml).
        returns a tuple (transform result: string), errorlog: list)'''
    # etree from xslt stylesheet string 
    xslt_root = etree.XML(xslt_stylesheet_text)
    transform = etree.XSLT(xslt_root)
    # etree from input xml string
    input_xml_root = etree.XML(input_xml_text)

    # transform xml with stylesheet
    try:
        function = etree.XSLT.strparam(args.stringparam)
        result = transform(input_xml_root, function=function)
    except etree.XSLTApplyError as exception:
        print("xslt error: " + str(exception))
        sys.exit(14)

    return (etree.tostring(result, encoding="unicode"),
            transform.error_log)


def use_xslt_proc_2(xslt_stylesheet_text, input_xml_text, args):
    # https://pypi.org/project/saxonpy/
    with PySaxonProcessor(license=False) as proc:
        xsltproc = proc.new_xslt_processor()
        document = proc.parse_xml(xml_text=input_xml_text)
        xsltproc.set_source(xdm_node=document)

        function = proc.make_string_value(args.stringparam)
        xsltproc.set_parameter("function", function)

        xsltproc.compile_stylesheet(stylesheet_text=xslt_stylesheet_text)
        result = xsltproc.transform_to_string()
        
        return (result, [])


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])

    if args.verbose == True:
        print("xslt-stylesheet: " + args.xslt)
        print("input: " + args.input)
        print("output: " + args.output)
        print("version: " + args.version)
        print("==================")

    # check if stylesheet file is valid xml
    try:
        xslt_stylesheet = etree.parse(args.xslt, parser=parser)
    except etree.XMLSyntaxError as exception:
        print("xslt file no valid xml: " + str(exception))
        sys.exit(13)
    except OSError as exception:
        print("xslt file: " + str(exception))
        sys.exit(13)

    # convert xslt sytlesheet etree object to string 
    xslt_stylesheet_text = etree.tostring(xslt_stylesheet, encoding="unicode")

    # check if input xml comes from stdin or file and if it is a valid xml
    if args.input == "-":
        input_data = sys.stdin.read()
        try:
            input_xml = etree.fromstring(input_data, parser=parser)
        except etree.XMLSyntaxError as exception:
            print("stdin no valid xml: " + str(exception))
            sys.exit(11)
    else:
        try:
            input_xml = etree.parse(args.input, parser=parser)
        except etree.XMLSyntaxError as exception:
            print("input file no valid xml: " + str(exception))
            sys.exit(12)
        except OSError as exception:
            print("input file: " + str(exception))
            sys.exit(13)

    # convert input xml etree nodeset to string 
    input_xml_text = etree.tostring(input_xml, encoding="unicode")
    
    # use xslt processor version 1.0 lxml 
    if args.version == "1.0":
        result = use_xslt_proc_1(xslt_stylesheet_text, input_xml_text, args)
        output_xml = etree.XML(result[0].encode())
        if args.output == "-":
            print(etree.tostring(output_xml,
                                 pretty_print=args.pretty,
                                 encoding="unicode"
                                 ))
        else:
            out_tree = etree.ElementTree(output_xml)
            out_tree.write(args.output, pretty_print=args.pretty)

    # use xslt processor version 2.0 saxonica
    elif args.version == "2.0":
        result = use_xslt_proc_2(xslt_stylesheet_text, input_xml_text, args)
        if args.output == "-":
            print(result[0])
        else:
            with open (args.output, "w") as out_file:
                out_file.write(result[0])
    