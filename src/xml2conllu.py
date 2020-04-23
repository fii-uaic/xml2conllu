import lxml.etree as ET
import io
import itertools as IT

from argparse import ArgumentParser

_UNSPECIFIED_CHAR = '_'

_REQUIRED_ATTRIBUTES = ['id', 'form', 'postag', 'head', 'deprel']


def get_validation_errors(line, xml_word, postag_data):
    # Check required fields
    word_dict = xml_word.attrib
    line_no, column_no = xml_word.sourceline - 1, None
    msg = ""

    missing_attrs = list(
        filter(lambda x: x not in word_dict, _REQUIRED_ATTRIBUTES))

    if missing_attrs:
        msg = "missing '%s' attribute/attributes" % ",".join(missing_attrs)
    else:
        postag = word_dict['postag']
        if postag not in postag_data:
            column_no = line.find('postag="') + 8
            msg = "invalid postag '%s'" % postag

    if msg != "":
        return [ConvertError("ConvertError", msg, line_no, column_no, line)]


def build_pretty_error_msg(error, column_no, line):
    caret = "" if column_no is None else '{:=>{}}'.format('^', column_no)
    return '{}\n{}\n{}'.format(error, line.expandtabs(1), caret)


class ConvertError(Exception):
    def __init__(self, err_name, err_type, line_no, column_no, line):
        column_msg = ""
        if column_no is not None:
            column_msg = ", column %s" % column_no

        error_msg = "%s: %s: line %s%s" % (err_name, err_type, line_no,
                                           column_msg)
        self.msg = build_pretty_error_msg(error_msg, column_no, line)

    def __str__(self):
        return self.msg


def convert2conllu(xml_content, postag_data=None, sent_id_from_input=False):
    """
    Converts the XML content to CoNLL-U using specified POS tags.

    Parameters
    ----------
    xml_content: string, required
        The contents of the XML file given as input to the applicaiton.
    postag_data: dict, optional
        The dictionary containing features of POS tags.
        Default is None.
    sent_id_from_input: boolean, optional
        Specifies whether sent_id attribute should be taken from
        id attribute of sentence element or it should start at 1.
        Default is False which means start at 1.

    Returns
    -------
    (conllu_output, validation_errors)
        Tuple containing the output and the validation errors.
    """
    if postag_data is None:
        postag_data = {}
    xml_lines = xml_content.splitlines()
    xml_content_encoded = xml_content.encode('utf-8')

    try:
        xml_root = ET.fromstring(xml_content_encoded)
    except ET.ParseError as err:
        line_no, column_no = err.position
        line = next(IT.islice(io.StringIO(xml_content), line_no))
        err.msg = build_pretty_error_msg(err, column_no, line)
        return "", [err]

    conllu_output = ""
    sentence_id = 1
    validation_errors = []
    for xml_sentence in xml_root.findall('sentence'):
        citation_part = xml_sentence.attrib.get('citation-part')

        word_conllu_lines = []
        sentence = ""

        for xml_word in xml_sentence.findall('word'):
            word_dict = xml_word.attrib
            line_no = xml_word.sourceline - 1

            convert_errors = get_validation_errors(xml_lines[line_no],
                                                   xml_word, postag_data)

            if convert_errors:
                validation_errors.extend(convert_errors)
                continue

            word = word_dict['form']
            ref = citation_part.replace(' ', '') if citation_part else ""
            misc = 'ref=' + ref

            postag = word_dict['postag']
            upostag, xpostag, features = postag_data[postag]
            deprel = word_dict['deprel']
            head = word_dict['head']

            if head == '0':
                deprel = 'root'

            if deprel == 'punct':
                # Special case.
                # Add SpaceAfter=No to previous element.
                if word_conllu_lines:
                    word_conllu_lines[-1] += '|SpaceAfter=No'
            if word[0] == '-' and len(word_conllu_lines) > 0:
                word_conllu_lines[-1] += '|SpaceAfter=No'
            if word[-1] == '-':
                misc += '|SpaceAfter=No'

            # This is the first word
            if sentence == "":
                sentence = word
            else:
                if (deprel != 'punct') and (sentence[-1] != '-'):
                    sentence += ' '
                if (sentence[-1] == ' ') and (word[0] == '-'):
                    sentence = sentence.rstrip()
                sentence += word

            word_conllu_line = "\t".join([
                word_dict['id'], word,
                word_dict.get('lemma', _UNSPECIFIED_CHAR), upostag, xpostag,
                features,
                word_dict.get('head', _UNSPECIFIED_CHAR), deprel,
                word_dict.get('deps', _UNSPECIFIED_CHAR), misc
            ])

            word_conllu_lines.append(word_conllu_line)

        # Print the sentence
        sent_id = xml_sentence.attrib.get('id') if sent_id_from_input else str(
            sentence_id)
        conllu_output += '# sent_id = test-%s\n' % sent_id
        conllu_output += '# text = %s\n' % sentence
        if citation_part:
            conllu_output += '# citation-part=%s\n' % citation_part
        conllu_output += "\n".join(word_conllu_lines)
        conllu_output += '\n\n'

        sentence_id += 1
    return conllu_output, validation_errors


def split_with_positions(string):
    results = []
    for k, g in IT.groupby(enumerate(string), lambda x: not x[1].isspace()):
        if k:
            pos, first_item = next(g)
            results.append((pos, first_item + ''.join([x for _, x in g])))
    return results


def convert(xml_file, conllu_file, postag_file, sent_id_from_input=False):
    """
    Reads the content of input files and prerforms conversion.

    Parameters
    ----------
    xml_file: string, required
        Path of the input XML file.
    conllu_file: string, required
        Path of the output CoNLL-U file.
    postag_file: string, required
        Path of input the POSTag file.
    sent_id_from_input: boolean, optional
        Specifies whether to populate attribute sent_id
        with values from the id attribute of the sentence tag
        from input XML file.
        Default is False.
    """
    postag_data = {}
    with open(postag_file, 'r') as fposttag:
        data_lines = fposttag.read().splitlines()
        for idx, line in enumerate(data_lines):
            splits = split_with_positions(line)
            if len(splits) == 5:
                postag, _, upostag, xpostag, features = map(
                    lambda x: x[1], splits)
                postag_data[postag] = (upostag, xpostag, features)
            else:
                raise ConvertError("PostagFileError", "too many values", idx,
                                   splits[5][0], line)

    with open(xml_file, 'r', encoding='utf-8') as fxml:
        xml_content = fxml.read()

        conllu_data, errors = convert2conllu(
            xml_content,
            postag_data=postag_data,
            sent_id_from_input=sent_id_from_input)

        with open(conllu_file, 'w', encoding='utf-8') as fconllu:
            fconllu.write(conllu_data)

    return errors


def parse_arguments():
    parser = ArgumentParser()
    parser.add_argument(
        '--no-window',
        help='Run in command line mode, i.e. without displaying GUI.',
        action='store_true')
    parser.add_argument('--xml-file',
                        help="Path of the input XML file.",
                        required=False)
    parser.add_argument('--conllu-file',
                        help="Path of the output CoNLL-U file.",
                        required=False)
    parser.add_argument('--postag-file',
                        help="Path of the input POSTag file.",
                        required=False)
    parser.add_argument(
        '--use-input-sentence-id',
        help="Use sentence id from input XML or to start at 1.",
        action='store_true',
        required=False)

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    if args.no_window:
        convert(args.xml_file,
                args.conllu_file,
                args.postag_file,
                sent_id_from_input=args.use_input_sentence_id)
    else:
        from application import Application
        from tkinter import Tk
        root = Tk()
        app = Application(convert, master=root)
        app.mainloop()
