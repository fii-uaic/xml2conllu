import lxml.etree as ET
import io
import itertools as IT
from tkinter import filedialog, Tk, Frame, Button, Entry, Label, END
from tkinter import Toplevel
from tkinter import Text

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


def convert2conllu(xml_content, postag_data=None):
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
            if word[0] == '-':
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
        conllu_output += '# sent_id = test-%s\n' % sentence_id
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


def convert(xml_file, conllu_file, postag_file):
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

        conllu_data, errors = convert2conllu(xml_content,
                                             postag_data=postag_data)

        with open(conllu_file, 'w', encoding='utf-8') as fconllu:
            fconllu.write(conllu_data)

    return errors


class Application(Frame):
    def ask_open_postag_file(self):
        filename = filedialog.askopenfilename(initialdir="./",
                                              title="Select file",
                                              filetypes=(("txt files",
                                                          "*.txt"),
                                                         ("all files", "*.*")))
        self.postag_input.delete(0, END)
        self.postag_input.insert(0, filename)

    def ask_open_xml_file(self):
        filename = filedialog.askopenfilename(initialdir="./",
                                              title="Select file",
                                              filetypes=(("xml files",
                                                          "*.xml"),
                                                         ("all files", "*.*")))
        self.xml_input.delete(0, END)
        self.xml_input.insert(0, filename)

    def ask_save_conllu_file(self):
        filename = filedialog.asksaveasfilename(
            initialdir="./",
            title="Select file",
            filetypes=(("conllu files", "*.conllu"), ("all files", "*.*")))
        self.conllu_output.delete(0, END)
        self.conllu_output.insert(0, filename)

    def __init__(self, master=None):
        Frame.__init__(self, master)

        # ## XML Input ## #
        Label(master, text="Xml file").grid(row=0)
        self.xml_input = Entry(master)
        self.xml_input.grid(row=0, column=1)
        Button(master,
               text='Browse',
               command=self.ask_open_xml_file) \
            .grid(row=0, column=2)
        # ## END ## #

        # ## Postag Input ## #
        Label(master, text="Postag file").grid(row=1)
        self.postag_input = Entry(master)
        self.postag_input.grid(row=1, column=1)
        Button(master,
               text='Browse',
               command=self.ask_open_postag_file) \
            .grid(row=1, column=2)
        # ## END ## #

        # ## Conllu output ## #
        Label(master, text="Output conllu file").grid(row=2)
        self.conllu_output = Entry(master)
        self.conllu_output.grid(row=2, column=1)
        Button(master,
               text='Browse',
               command=self.ask_save_conllu_file) \
            .grid(row=2, column=2)
        # ## END ## #

        self.convert_button = Button(master,
                                     text='Convert!',
                                     command=self.convert)
        self.convert_button.grid(row=3, column=1)

    def convert(self):
        xml_filename = self.xml_input.get()
        postag_filename = self.postag_input.get()
        conllu_filename = self.conllu_output.get()

        full_text = "Success!"
        try:
            errors = convert(xml_filename, conllu_filename, postag_filename)
            if errors:
                full_text = "\n".join(map(lambda x: x.msg, errors))
        except Exception as err:
            full_text = "\n".join(["Fatal error!", str(err)])

        status_window = Toplevel(self)
        status_window.wm_title("Convert output!")

        text = Text(status_window, width=100, height=20)
        text.insert(END, full_text)
        text.pack()

        quit = Button(status_window,
                      text="Close",
                      command=status_window.destroy)
        quit.pack()


if __name__ == '__main__':
    root = Tk()
    app = Application(master=root)
    app.mainloop()
    root.destroy()
