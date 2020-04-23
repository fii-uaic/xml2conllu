from tkinter import filedialog, Frame, Button, Entry, Label, END
from tkinter import Toplevel
from tkinter import Text
from tkinter import Checkbutton
from tkinter import IntVar


class Application(Frame):
    def __init__(self, convert_callback, master=None):
        Frame.__init__(self, master)
        self.convert_callback = convert_callback
        self.create_widgets(master)

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

        # ## Input ids checkbox ## #
        self.use_input_ids = IntVar()
        self.use_input_ids_chk = Checkbutton(
            master,
            text="Use sentece ids from input file",
            onvalue=1,
            offvalue=0,
            variable=self.use_input_ids)
        self.use_input_ids_chk.grid(row=3, column=1)
        # ## END ## #

        # ## Convert button ## #
        self.convert_button = Button(master,
                                     text='Convert!',
                                     command=self.convert)
        self.convert_button.grid(row=4, column=1)
        # ## END ## #

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

        full_text = "Success!"
        try:
            errors = self.convert_callback(
                xml_filename,
                conllu_filename,
                postag_filename,
                sent_id_from_input=self.use_input_ids.get())
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
