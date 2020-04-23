from tkinter import filedialog, Frame, Button, Entry, Label, END
from tkinter import Toplevel
from tkinter import Text
from tkinter import Radiobutton
from tkinter import StringVar


class Application(Frame):
    def __init__(self, convert_callback, master=None):
        Frame.__init__(self, master)
        self.convert_callback = convert_callback
        self.create_widgets(master)
        self.set_default_values()

    def create_widgets(self, master):
        # ## XML Input ## #
        Label(master, text="Xml file").grid(row=0)
        self.xml_input = Entry(master)
        self.xml_input.grid(row=0, column=1, sticky='EW')
        Button(master,
               text='Browse',
               command=self.ask_open_xml_file) \
            .grid(row=0, column=2)
        # ## END ## #

        # ## Postag Input ## #
        Label(master, text="Postag file").grid(row=1)
        self.postag_input = Entry(master)
        self.postag_input.grid(row=1, column=1, sticky='EW')
        Button(master,
               text='Browse',
               command=self.ask_open_postag_file) \
            .grid(row=1, column=2)
        # ## END ## #

        # ## Conllu output ## #
        Label(master, text="Output conllu file").grid(row=2)
        self.conllu_output = Entry(master)
        self.conllu_output.grid(row=2, column=1, sticky='EW')
        Button(master,
               text='Browse',
               command=self.ask_save_conllu_file) \
            .grid(row=2, column=2)
        # ## END ## #

        # ## Start sent_id widgets ## #
        Label(master, text="Start sent_id at:").grid(row=3, column=0)
        self.start_id_input = Entry(master)
        self.start_id_input.grid(row=3, column=1)
        # ## END ## #

        # ## Sentence type widgets ## #
        Label(master, text="Sentence type:").grid(row=4, column=0)
        self.sentence_type = StringVar()
        self.train_rb = Radiobutton(master,
                                    text="Train",
                                    variable=self.sentence_type,
                                    value='train')
        self.train_rb.grid(row=4, column=1, sticky='W')
        self.test_rb = Radiobutton(master,
                                   text="Test",
                                   variable=self.sentence_type,
                                   value='test')
        self.test_rb.grid(row=5, column=1, sticky='W')

        # ## END ## #

        # ## Convert button ## #
        self.convert_button = Button(master,
                                     text='Convert!',
                                     command=self.convert)
        self.convert_button.grid(row=6, column=1)
        # ## END ## #

    def set_default_values(self):
        """
        Sets default values for input widgets.
        """
        self.start_id_input.insert(0, '1')
        self.train_rb.select()

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

    def convert(self):
        xml_filename = self.xml_input.get()
        postag_filename = self.postag_input.get()
        conllu_filename = self.conllu_output.get()
        is_valid, sent_id_start = self.get_sent_id_input()
        if not is_valid:
            return
        full_text = "Success!"
        try:
            errors = self.convert_callback(
                xml_filename,
                conllu_filename,
                postag_filename,
                sent_id_start=sent_id_start,
                sentence_type=self.sentence_type.get())
            if errors:
                full_text = "\n".join(map(lambda x: x.msg, errors))
        except Exception as err:
            full_text = "\n".join(["Fatal error!", str(err)])

        self.display_message(full_text)

    def display_message(self, message, title="Conversion output"):
        status_window = Toplevel(self)
        status_window.wm_title(title)

        text = Text(status_window, width=100, height=20)
        text.insert(END, message)
        text.pack()

        quit = Button(status_window,
                      text="Close",
                      command=status_window.destroy)
        quit.pack()

    def get_sent_id_input(self):
        """
        Validates the input of start_id and returns it.

        Returns
        -------
        (is_valid, sent_id_start)
            A tuple specifying whether input is valid and its value.
            If input is invalid the return wil bee (False, None);
            otherwise (True, sent_id_start) will be returned.
        """
        try:
            sent_id_start = int(self.start_id_input.get())
            return True, sent_id_start
        except Exception:
            self.display_message('Please specify a valid integer value.',
                                 title="Validation error.")
            return False, None
