from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QLabel, QPushButton, QCheckBox, \
                        QStatusBar, QMenuBar, \
                        QSizePolicy, QApplication, QLineEdit
from PyQt5.QtGui import  QDesktopServices
from PyQt5.QtCore import QUrl, pyqtSignal, Qt, QObject, QEvent
from .audio_selector import AudioSelector

from .multi_definition_widget import MultiDefinitionWidget
from .word_record_display import WordRecordDisplay

from ..global_names import app_title, settings, datapath, MOD

from ..record import Record
from ..local_dictionary import LocalDictionary
from .searchable_boldable_text_edit import SearchableBoldableTextEdit
from .freq_display_widget import FreqDisplayWidget
from .about import AboutDialog
from .logview import LogView
from ..models import AnkiSettings, WordActionWeights, KeyAction

import platform
import os
from sentence_splitter import SentenceSplitter
from pynput import keyboard


# If on macOS, display the modifier key as "Cmd", else display it as "Ctrl".
# For whatever reason, Qt automatically uses Cmd key when Ctrl is specified on Mac
# so there is no need to change the keybind, only the display text

class MainWindowBase(QMainWindow):
    audio_fetched = pyqtSignal(dict)
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(app_title(True))
        self.setFocusPolicy(Qt.StrongFocus)
        self.widget = QWidget()
        self.settings = settings
        self.rec = Record(self.settings, datapath)
        self.dictdb = LocalDictionary(datapath)
        self.splitter = SentenceSplitter(language=self.settings.value("target_language", "en"))
        self.setCentralWidget(self.widget)
        self.previousWord = ""
        self.audio_path = ""
        self.prev_clipboard = ""
        self.image_path = ""

        self.scaleFont()
        self.initWidgets()

        # TODO: find if that works in other displays and OSes
        # print(self.devicePixelRatioF())
        self.resize(int(550 / self.devicePixelRatioF()), int(900 / self.devicePixelRatioF()))
        # self.resize(500, 800)
        self.setupWidgetsV()

        # Setup Key monitoring to monitor the shit key
        self.monitor = KeyMonitor()
        self.monitor.keyEvent.connect(self.monitorEvent)
        self.monitor.start_monitoring()
        self.shift_pressed: bool = False

    def monitorEvent(self, action):
        match action:
            case KeyAction.pressed:
                self.shift_pressed = True
            case KeyAction.released:
                self.shift_pressed = False
            case _:
                self.shift_pressed = False


    def scaleFont(self) -> None:
        font = QApplication.font()
        font.setPointSize(
            int(font.pointSize() * self.settings.value("text_scale", type=int) / 100))
        QApplication.setFont(font)
        self.setFont(font)


    def initWidgets(self) -> None:
        self.namelabel = QLabel(
            "<h2 style=\"font-weight: normal;\">" + app_title(False) + "</h2>")
        self.menu = QMenuBar(self)
        self.sentence = SearchableBoldableTextEdit()
        self.sentence.setPlaceholderText(
            "Sentence copied to the clipboard will show up here.")
        self.sentence.setMinimumHeight(50)
        #self.sentence.setMaximumHeight(300)
        self.word = QLineEdit()
        self.word.setPlaceholderText("Word")
        self.definition = MultiDefinitionWidget(self.word)
        self.definition.setMinimumHeight(70)
        #self.definition.setMaximumHeight(1800)
        self.definition2 = MultiDefinitionWidget()
        self.definition2.setMinimumHeight(70)
        #self.definition2.setMaximumHeight(1800)
        self.tags = QLineEdit()
        self.tags.setPlaceholderText(
            "Tags to be used, separated by spaces")
        self.sentence.setToolTip(
            "Look up a word by double clicking it. Or, select it"
            ", then press \"Get definition\".")

        self.lookup_button = QPushButton(f"Define [{MOD}+D]") 
        self.lookup_exact_button = QPushButton(f"Define direct [Shift+{MOD}+D]")
        self.lookup_exact_button.setToolTip(
            "This will look up the word without lemmatization.")
        self.toanki_button = QPushButton(f"Add note [{MOD}+S]")
        self.view_last_note_button = QPushButton("View last note")
        self.view_last_note_button.setToolTip(f"View the last added note. [{MOD}+Shift+F]")

        self.read_button = QPushButton(f"Read clipboard")
        self.read_button.setToolTip(
            f"Read the clipboard contents to Sentence field [{MOD}+V]"
            )
        self.bar = QStatusBar()
        self.setStatusBar(self.bar)
        self.stats_label = QLabel()

        self.single_word = QCheckBox("Single word lookups")
        self.single_word.setToolTip(
            "If enabled, vocabsieve will act as a quick dictionary and look up any single words copied to the clipboard.\n"
            "This can potentially send your clipboard contents over the network if an online dictionary service is used.\n"
            "This is INSECURE if you use password managers that copy passwords to the clipboard.")
        self.lookup_definition_on_doubleclick = QCheckBox(
            "Lookup definition on double click")
        self.lookup_definition_on_doubleclick.setToolTip(
            f"Disable this if you want to use 3rd party dictionaries with copied text (e.g. with mpvacious).[{MOD}+2]")
        self.lookup_definition_on_doubleclick.clicked.connect(lambda v: self.settings.setValue("lookup_definition_on_doubleclick", v))
        self.lookup_definition_on_doubleclick.setChecked(self.settings.value("lookup_definition_on_doubleclick", True, type=bool))
        self.lookup_definition_when_hovering = QCheckBox("Lookup definition when hovering")
        self.lookup_definition_when_hovering.setToolTip("Hover over a word and press [Shift] to look its definition up")
        self.lookup_definition_when_hovering.clicked.connect(lambda v: self.settings.setValue("lookup_definition_when_hovering", v))
        self.lookup_definition_when_hovering.setChecked(self.settings.value("lookup_definition_when_hovering", True, type=bool))

        self.web_button = QPushButton(f"Open webpage")
        self.web_button.setToolTip(
            f"Open the webpage for the selected word. [{MOD}+1]")
        self.freq_widget = FreqDisplayWidget()
        self.freq_widget.setPlaceholderText("Word frequency")

        self.audio_selector = AudioSelector(self.settings)
        
        self.definition.setReadOnly(
            not (
                self.settings.value(
                    "allow_editing",
                    True,
                    type=bool)))
        self.definition2.setReadOnly(
            not (
                self.settings.value(
                    "allow_editing",
                    True,
                    type=bool)))
        self.definition.setPlaceholderText(
            f'Look up a word by double clicking it or by selecting it, then pressing {MOD}+D.\nUse Shift-{MOD}+D to look up the word without lemmatization.')
        self.definition2.setPlaceholderText(
            f'Look up a word by double clicking it or by selecting it, then pressing {MOD}+D.\nUse Shift-{MOD}+D to look up the word without lemmatization.')

        self.image_viewer = QLabel("<center><b>&lt;No image&gt;</center>")
        self.image_viewer.setScaledContents(True)
        self.image_viewer.setToolTip(f"{MOD}+W to clear the image.")
        self.image_viewer.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_viewer.setStyleSheet(
            '''
                border: 1px solid black;
            '''
        )
        self.word_record_display = WordRecordDisplay()


    def setupWidgetsV(self) -> None:
        """Prepares vertical layout"""

        layout = QGridLayout(self.widget)
        layout.addWidget(self.namelabel, 0, 0, 1, 2)

        layout.addWidget(self.single_word, 1, 0, 1, 2)
        layout.addWidget(self.lookup_definition_on_doubleclick, 2, 0, 1, 2)
        layout.addWidget(self.lookup_definition_when_hovering, 3, 0, 1, 2)

        layout.addWidget(self.read_button, 4, 0)
        layout.addWidget(self.web_button, 4, 1)
        layout.addWidget(self.image_viewer, 0, 2, 5, 1)
        layout.addWidget(self.sentence, 5, 0, 1, 3)
        layout.setRowStretch(5, 1)
        

        layout.addWidget(self.word, 6, 0)
        layout.addWidget(self.freq_widget, 6, 1)
        layout.addWidget(self.word_record_display, 6, 2)
        
        layout.setRowStretch(7, 2)
        layout.setRowStretch(9, 2)
        if self.settings.value("sg2_enabled", False, type=bool):
            layout.addWidget(self.definition, 7, 0, 2, 3)
            layout.addWidget(self.definition2, 9, 0, 2, 3)
        else:
            layout.addWidget(self.definition, 7, 0, 4, 3)

        layout.addWidget(self.audio_selector, 12, 0, 1, 3)
        layout.setRowStretch(12, 1)

        layout.addWidget(self.tags, 13, 0, 1, 3)

        layout.addWidget(self.toanki_button, 14, 1, 1, 2)
        layout.addWidget(self.view_last_note_button, 14, 0)

        layout.setColumnStretch(0, 2)
        layout.setColumnStretch(1, 2)
        layout.setColumnStretch(2, 5)
        self._layout = layout

    

    def onHelp(self) -> None:
        url = f"https://docs.freelanguagetools.org/"
        QDesktopServices.openUrl(QUrl(url))

    def onAbout(self) -> None:
        self.about_dialog = AboutDialog()
        self.about_dialog.exec_()

    def onOpenLogs(self):
        self.logview = LogView()
        self.logview.exec_()

    
    def getAnkiSettings(self) -> AnkiSettings:
        return AnkiSettings(
            deck=self.settings.value("deck_name", "Default"),
            model=self.settings.value("note_type", "vocabsieve-notes"),
            word_field=self.settings.value("word_field", "Word"),
            sentence_field=self.settings.value("sentence_field", "Sentence"),
            definition1_field=self.settings.value("definition1_field", "Definition"),
            definition2_field=self.settings.value("definition2_field"),
            audio_field=self.settings.value("pronunciation_field"),
            image_field=self.settings.value("image_field"),
        )

    def getWordActionWeights(self) -> WordActionWeights:
        return WordActionWeights(
            seen=self.settings.value("tracking/w_seen", 8, type=int),
            lookup=self.settings.value("tracking/w_lookup", 15, type=int),
            anki_mature_ctx=self.settings.value("tracking/w_anki_ctx", 30, type=int),
            anki_mature_tgt=self.settings.value("tracking/w_anki_word", 70, type=int),
            anki_young_ctx=self.settings.value("tracking/w_anki_ctx_y", 20, type=int),
            anki_young_tgt=self.settings.value("tracking/w_anki_word_y", 40, type=int),
            threshold=self.settings.value("tracking/known_threshold", 100, type=int),
            threshold_cognate=self.settings.value("tracking/known_threshold_cognate", 25, type=int)
        )


class KeyMonitor(QObject):
    """Monitors the activity of the shift key"""
    keyEvent = pyqtSignal(KeyAction)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.listener = keyboard.Listener(on_press=self.on_press,on_release=self.on_release)

    def on_press(self, key):
        if key == keyboard.Key.shift:
            self.keyEvent.emit(KeyAction.pressed)

    def on_release(self, key):
        if key == keyboard.Key.shift:
            self.keyEvent.emit(KeyAction.released)

    def stop_monitoring(self):
        self.listener.stop()

    def start_monitoring(self):
        self.listener.start()   