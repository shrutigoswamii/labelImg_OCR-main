from PyQt5.QtWidgets import QDialog, QTextEdit, QVBoxLayout, QDialogButtonBox
from PyQt5.QtCore import Qt

class OCRTextDialog(QDialog):
    def __init__(self, parent=None, text=""):
        super(OCRTextDialog, self).__init__(parent)
        self.setWindowTitle("Enter OCR Ground Truth Text")
        self.text_edit = QTextEdit()
        self.text_edit.setText(text)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def pop_up(self):
        if self.exec_():
            return self.text_edit.toPlainText().strip()
        return None
