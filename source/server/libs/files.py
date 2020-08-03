"""Manager import/export file formats"""

import io
import os
import csv
import logging
from zipfile import ZipFile, ZIP_DEFLATED

import conllu
import chardet

from django.core.files.base import ContentFile
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from annotation.exceptions import FileParseException

ZIP_FILENAME_UTF8_FLAG = 0x800


class FilesBase:
    """Базовый класс для всех форматов"""

    format = ""  # unique name
    ds_type_import = []  # type dataset
    ds_type_export = []  # type dataset

    tp_format_name = ""  # name of format
    tp_description = ""  # Описание. Строка.
    tp_example = ""  # Пример формата. Многострочный

    # May defferent for modes
    # tp_description_export; tp_description_import
    # tp_example_export; tp_example_import

    mode_support = ["import", "export"]

    @staticmethod
    def factory(format: str, ds_type: str, mode: str, file_obj):
        """Create instance need format
        Args:
            mode - export/import
        """
        FilesBase.check_mode(mode)

        for cl in FilesBase.__subclasses__():
            support_ds_type = getattr(cl, "ds_type_" + mode)
            if cl.format == format and ds_type in support_ds_type:
                return cl(file_obj)
        return
    
    @staticmethod
    def get_docs(ds_type: str, mode: str):
        """
        Return:
            [(format, format_label, description, example)]
        """
        FilesBase.check_mode(mode)
        result = []
        for cl in FilesBase.__subclasses__():
            support_ds_type = getattr(cl, "ds_type_" + mode)
            if ds_type not in support_ds_type:
                continue
            result.append(
                (cl.format, cl.tp_format_name, cl.description(mode), cl.example(mode))
            )
        return result

    @staticmethod
    def check_mode(mode: str):
        if mode not in ["import", "export"]:
            raise ValueError("Unsupported mode")
    
    def __init__(self, file_obj, mode = ""):
        """
        Args:
            file_obj - file like object, binary format, encode UTF-8.
            mode - export/import
        """
        self.file_obj = file_obj
        self.mode = mode
    
    def import_ds(self):
        """
        Итерируемы объект
        Файл представляет массив строк с метками
        files:
            (data: list, meta: dict, filename: str, labels_for_docs)
        data:
        [
            (id: int, text_of_sequence: str, labels: list),
        ]
        labels ner: [
            (tag: str, char_fist: int, char_last: int),
        ]
        labels class in labels_for_docs: [
            (tag, 0),
            (tag, 1)
        ]
        """
        pass
    
    def export_ds(self, handler) -> bytes:
        """
        Args:
            handler - iteration handler for get data

        Return
            Full file with documents in zip
        """
        pass
    
    def _is_zip(self) -> bool:
        """Checks that the file is format zip"""
        name, ext = os.path.splitext(self.file_obj._name)
        if ext == ".zip":
            return True
        return False
    
    def _import_zip_file(self, cls):
        """Imports the file of zip"""
        with ZipFile(self.file_obj) as zip:
            for item in zip.infolist():
                if item.is_dir():
                    continue
                if item.filename.startswith("__MACOSX/"):
                    continue
                # Get filename and fix encoding
                # https://stackoverflow.com/questions/37723505/namelist-from-zipfile-returns-strings-with-an-invalid-encoding
                filename = os.path.split(item.filename)[1]
                if not item.flag_bits & ZIP_FILENAME_UTF8_FLAG:
                    fn_bytes = filename.encode('437')
                    guessed_encoding = chardet.detect(fn_bytes)
                    guessed_encoding = guessed_encoding.get("encoding", "utf-8")
                    filename = fn_bytes.decode(guessed_encoding, "replace")

                content = io.BytesIO(zip.read(item.filename))
                content._name = filename
                tmp_obj = cls(content)
                for item in tmp_obj.import_ds():
                    yield item
    
    def _file_obj_to_strio(self):
        buf = io.StringIO(self.file_obj.read().decode())
        buf.seek(0)
        buf._name = self.file_obj._name
        return buf
    
    @classmethod
    def description(cls, mode):
        prop = "tp_description_{}".format(mode)
        if hasattr(cls, prop):
            return getattr(cls, prop)
        return cls.tp_description
    
    @classmethod
    def example(cls, mode):
        prop = "tp_example_{}".format(mode)
        if hasattr(cls, prop):
            return getattr(cls, prop)
        return cls.tp_example


class ConllupNER(FilesBase):

    format = "conllup"
    ds_type_import = ["text_label"]
    ds_type_export = ["text_label"]

    tp_format_name = "CoNLL-U Plus"
    tp_description = format_lazy(
        "{first} <a href=\"https://universaldependencies.org/ext-format.html\">{two}</a> {three}",
    # "{first} <a href=\"https://universaldependencies.org/ext-format.html\">{two}</a> {three}".format(
        first=_("It's an extension of CoNLL-U. File can have any non-zero number of columns."),
        two=_("Format."),
        three=_("Must be in coding UTF-8")
    )
    tp_example_import = """
    # global.columns = FORM NE

    This  _
    is  VERB
    only  _
    example _
    """

    file_ext = "conllup"

    def import_ds(self):
        if self._is_zip():
            return self._import_zip_file(ConllupNER)
        else:
            return self._import_conllup()
    
    def export_ds(self, handler):
        zip_file = io.BytesIO()
        zip_obj = ZipFile(zip_file, mode="w", compression=ZIP_DEFLATED)

        for data, meta, file_name, lables_on_doc in handler():
            content = self._export_to_conllup(data)
            zip_obj.writestr("{}.{}".format(file_name, self.file_ext), content)
        zip_obj.close()
        return zip_file.getvalue()
    
    def _import_conllup(self):
        """Imports the file of format CoNLLU Plus"""
        field_parsers = {
            "ne": lambda line, i: conllu.parser.parse_nullable_value(line[i]),
        }
        filename = self.file_obj._name

        try:
            sentences = conllu.parse(
                self.file_obj.read().decode("UTF-8"),
                fields=("form", "ne"),
                field_parsers=field_parsers
            )
        except conllu.parser.ParseException as e:
            raise FileParseException(str(e))
        except UnicodeDecodeError:
            raise FileParseException(_("The file is not encoded in UTF-8"))

        result = []
        meta = {}

        for index, sentence in enumerate(sentences):
            if not sentence:
                continue
            words, labels = [], []
            for item in sentence:
                word = item.get("form")
                tag = item.get("ne", None)

                if tag is not None:
                    char_left = sum(map(len, words)) + len(words)
                    char_right = char_left + len(word)
                    span = (tag, char_left, char_right)
                    labels.append(span)

                words.append(word)
            
            # result
            result.append((index, " ".join(words), labels))
        
        yield result, meta, filename, None
    
    def _export_to_conllup(self, data) -> bytes:
        """Getting the file in need format"""
        buf = io.StringIO()

        # Header
        buf.write("# global.columns = FORM NE\n")

        for seq in self._export_one_doc(data):
            buf.write("\n")
            for word, label in seq:
                if label is None:
                    label = "_"
                buf.write("{}\t{}\n".format(word, label))
        buf.seek(0)
        return buf.read().encode()
    
    def _export_one_doc(self, data) -> list:
        """Get the end document as array of arrays tuples
        (word, labels)
        """
        result = []
        for idx, text, labels in data:
            seq_res = self._eod_process_seq(text, labels)
            result.append(seq_res)
        return result
    
    def _eod_process_seq(self, text, labels: list) -> list:
        """Last index not included

        Args:
            labels - [(tag, char_fist, char_last)]
        """
        result = []
        lb_last_index = None  # Last index processed labels
        offsetStart = 0       # Offset current word
        for word in text.split(" "):
            range_word = (offsetStart, offsetStart + len(word))
            lb_last_index = self._eod_set_lb_index(labels, range_word)
            if lb_last_index is not None:
                rbase = (
                    labels[lb_last_index][1],  # offset_start
                    labels[lb_last_index][2]   # offset_stop
                )
                if self._eod_ch_cross(range_word, rbase):
                    result.append((word, labels[lb_last_index][0]))  # name
                else:
                    result.append((word, None))
            else:
                result.append((word, None))

            offsetStart = range_word[1] + 1

        return result
    
    def _eod_set_lb_index(self, labels, range_word):
        for index, item in enumerate(labels):
            _, _, offset_stop = item
            if range_word[0] < offset_stop:
                return index
        return None
    
    def _eod_ch_cross(self, rword: tuple, rbase: tuple) -> bool:
        """Does the word cross the base range"""
        start = 0
        end = 1
        if rword[end] > rbase[start] and rword[end] < rbase[end]:
            return True
        if rword[start] >= rbase[start] and rword[end] < rbase[end]:
            return True
        if rword[start] >= rbase[start] and rword[start] < rbase[end]:
            return True
        return False


class PlainText(FilesBase):

    format = "plaintext"
    ds_type_import = ["text_label", "document_classificaton"]

    tp_format_name = "Plain text"
    tp_description = _("Plain text.")
    tp_example = """
    Any text. Multiline.
    """

    def import_ds(self):
        if self._is_zip():
            return self._import_zip_file(PlainText)
        else:
            return self._import()
    
    def _import(self):
        buf = self._file_obj_to_strio()
        text = buf.read()
        filename = buf._name
        result = []
        for idx, line in enumerate(text.split("\n")):
            line = line.strip()
            if not line:
                continue
            result.append((idx, line, []))
        yield result, {}, filename, []
    

class CSVLabel(FilesBase):

    format = "csvlabel"
    ds_type_import = ["document_classificaton"]
    ds_type_export = ["document_classificaton"]

    tp_format_name = "CSV Label"
    tp_description = _("Simple csv. Description format: delimiter=';'; quotechar='\"'. One row one file. Meta format: key = value is one string. Label value may be: 0/1")
    tp_example_import = """
    id;meta;text;label1;label2;...
    """

    file_ext = "csv"

    def import_ds(self):
        if self._is_zip():
            return self._import_zip_file(CSVLabel)
        else:
            return self._import()

    def export_ds(self, handler):
        zip_file = io.BytesIO()
        zip_obj = ZipFile(zip_file, mode="w", compression=ZIP_DEFLATED)

        buf = io.StringIO()
        writer = csv.writer(buf, delimiter=';', quotechar='"')
        header = ["id", "meta", "text"]
        
        for idx, item in enumerate(handler()):
            data, meta, file_name, lables_on_doc = item
            if idx == 0:
                header_lb = [x[0] for x in lables_on_doc]
                writer.writerow(header + header_lb)
                continue
            text = "\n".join([x[1] for x in data])
            writer.writerow(
                [file_name, self._dict_to_meta(meta), text] + 
                [x[1] for x in lables_on_doc]
            )
        
        buf.seek(0)
        content = buf.read().encode()
        zip_obj.writestr("{}.{}".format("export", self.file_ext), content)
        zip_obj.close()
        return zip_file.getvalue()
    
    def _import(self):
        buf = self._file_obj_to_strio()

        reader = csv.reader(buf, delimiter=';', quotechar='"')
        labels_name = []
        for idx, row in enumerate(reader):
            if idx == 0:
                if len(row) < 4:
                    raise FileParseException(_("Length of header is short"))
                labels_name = row[3:]
                continue
            row_id = row[0]
            row_meta = self._meta_to_dict(row[1])
            row_text = self._split_text_to_seq(row[2])
            row_label = self._label_get_dict(labels_name, row[3:])
            file_name = "{}_{}.csv".format(
                os.path.splitext(buf._name)[0] , row_id)

            yield row_text, row_meta, file_name, row_label
      
    def _meta_to_dict(self, meta: str) -> dict:
        """Convert meta key = value to dictionary"""
        result = {}
        for line in meta.split("\n"):
            r = line.split("=")
            if len(r) != 2:
                continue
            result[r[0].strip()] = r[1].strip()
        return result
    
    def _dict_to_meta(self, meta: dict) -> str:
        result = ""
        for k, v in meta.items():
            result += "{} = {}\n".format(k, v)
        return result
    
    def _split_text_to_seq(self, text: str) -> list:
        result = []
        for idx, line in enumerate(text.split("\n")):
            line = line.strip()
            result.append((idx, line, None))
        return result
    
    def _label_get_dict(self, labels_name, labels_value) -> list:
        result = []
        try:
            for i, key in enumerate(labels_name):
                value = int(labels_value[i])
                if value not in [0, 1]:
                    raise FileParseException(_("Label value not valid"))
                result.append((key, value))
        except (ValueError, TypeError):
            raise FileParseException(_("Label value not int"))
        return result
