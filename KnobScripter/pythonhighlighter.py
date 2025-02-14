# -*- coding: utf-8 -*-
""" Python Higlighter: KnobScripter's QSyntaxHighlighter adapted for python code.

Adapted from an original version by Wouter Gilsing. His comments:
Modified, simplified version of some code found I found when researching:
wiki.python.org/moin/PyQt/Python%20syntax%20highlighting
They did an awesome job, so credits to them. I only needed to make some modifications to make it fit my needs.

adrianpueyo.com

"""
import re

import nuke

if nuke.NUKE_VERSION_MAJOR >= 16:
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtCore import Qt
elif nuke.NUKE_VERSION_MAJOR < 11:
    from PySide import QtCore, QtGui, QtGui as QtWidgets
    from PySide.QtCore import Qt
else:
    from PySide2 import QtWidgets, QtGui, QtCore
    from PySide2.QtCore import Qt


class KSPythonHighlighter(QtGui.QSyntaxHighlighter):
    """
    Adapted from an original version by Wouter Gilsing. His comments:
    Modified, simplified version of some code found I found when researching:
    wiki.python.org/moin/PyQt/Python%20syntax%20highlighting
    They did an awesome job, so credits to them. I only needed to make some
    modifications to make it fit my needs for KS.
    """

    def __init__(self, document, style="monokai"):

        self.selected_text = ""
        self.selected_text_prev = ""

        self.blocked = False

        self.styles = self.loadStyles()  # Holds a dict for each style
        self._style = style  # Can be set via setStyle
        self.setStyle(self._style)  # Set default style
        # self.updateStyle()  # Load ks color scheme

        super(KSPythonHighlighter, self).__init__(document)

    def loadStyles(self):
        """ Loads the different sets of rules """
        styles = dict()

        # LOAD ANY STYLE
        default_styles_list = [
            {
                "title": "nuke",
                "styles": {
                    'base': self.format([255, 255, 255]),
                    'keyword': self.format([238, 117, 181], 'bold'),
                    'operator': self.format([238, 117, 181], 'bold'),
                    'number': self.format([174, 129, 255]),
                    'singleton': self.format([174, 129, 255]),
                    'string': self.format([242, 136, 135]),
                    'comment': self.format([143, 221, 144]),
                },
                "keywords": {},
            },
            {
                "title": "monokai",
                "styles": {
                    'base': self.format([255, 255, 255]),
                    'keyword': self.format([237, 36, 110]),
                    'operator': self.format([237, 36, 110]),
                    'string': self.format([237, 229, 122]),
                    'comment': self.format([125, 125, 125]),
                    'number': self.format([165, 120, 255]),
                    'singleton': self.format([165, 120, 255]),
                    'function': self.format([184, 237, 54]),
                    'argument': self.format([255, 170, 10], 'italic'),
                    'class': self.format([184, 237, 54]),
                    'callable': self.format([130, 226, 255]),
                    'error': self.format([130, 226, 255], 'italic'),
                    'underline': self.format([240, 240, 240], 'underline'),
                    'selected': self.format([255, 255, 255], 'bold underline'),
                    'custom': self.format([200, 200, 200], 'italic'),
                    'blue': self.format([130, 226, 255], 'italic'),
                    'self': self.format([255, 170, 10], 'italic'),
                },
                "keywords": {
                    'custom': ['nuke'],
                    'blue': ['def', 'class', 'int', 'str', 'float',
                             'bool', 'list', 'dict', 'set', ],
                    'base': [],
                    'self': ['self'],
                },
            }
        ]
        # TODO separate the format before the loadstyle thing. should be done here before looping.
        for style_dict in default_styles_list:
            if all(k in style_dict.keys() for k in ["title", "styles"]):
                styles[style_dict["title"]] = self.loadStyle(style_dict)

        return styles

    def loadStyle(self, style_dict):
        """
        Given a dictionary of styles and keywords, returns the style as a dict
        """

        styles = style_dict["styles"].copy()

        # 1. Base settings
        if "base" in styles:
            base_format = styles["base"]
        else:
            base_format = self.format([255, 255, 255])

        main_keywords = [
            'and', 'assert', 'break', 'continue',
            'del', 'elif', 'else', 'except', 'exec', 'finally',
            'for', 'from', 'global', 'if', 'import', 'in',
            'is', 'lambda', 'not', 'or', 'pass', 'print',
            'raise', 'return', 'try', 'while', 'yield', 'with', 'as'
        ]

        error_keywords = ['AssertionError', 'AttributeError', 'EOFError', 'FloatingPointError',
                          'FloatingPointError', 'GeneratorExit', 'ImportError', 'IndexError',
                          'KeyError', 'KeyboardInterrupt', 'MemoryError', 'NameError',
                          'NotImplementedError', 'OSError', 'OverflowError', 'ReferenceError',
                          'RuntimeError', 'StopIteration', 'SyntaxError', 'IndentationError',
                          'TabError', 'SystemError', 'SystemExit', 'TypeError', 'UnboundLocalError',
                          'UnicodeError', 'UnicodeEncodeError', 'UnicodeDecodeError', 'UnicodeTranslateError',
                          'ValueError', 'ZeroDivisionError',
                          ]

        base_keywords = [',']

        operator_keywords = [
            '=', '==', '!=', '<', '<=', '>', '>=',
            '\+', '-', '\*', '/', '//', '\%', '\*\*',
            '\+=', '-=', '\*=', '/=', '\%=',
            '\^', '\|', '\&', '\~', '>>', '<<'
        ]

        singletons = ['True', 'False', 'None']

        if 'comment' in styles:
            tri_single = (re.compile("'''"), 1, styles['comment'])
            tri_double = (re.compile('"""'), 2, styles['comment'])
        else:
            tri_single = (re.compile("'''"), 1, base_format)
            tri_double = (re.compile('"""'), 2, base_format)

        # 2. Rules
        rules = []

        if "argument" in styles:
            # Everything inside parentheses
            rules += [(r"def [\w]+[\s]*\((.*)\)", 1, styles['argument'])]
            # Now restore unwanted stuff...
            rules += [(i, 0, base_format) for i in base_keywords]
            rules += [(r"[^\(\w),.][\s]*[\w]+", 0, base_format)]

        if "callable" in styles:
            rules += [(r"\b([\w]+)[\s]*[(]", 1, styles['callable'])]

        if "keyword" in styles:
            rules += [(r'\b%s\b' % i, 0, styles['keyword']) for i in main_keywords]

        if "error" in styles:
            rules += [(r'\b%s\b' % i, 0, styles['error']) for i in error_keywords]

        if "operator" in styles:
            rules += [(i, 0, styles['operator']) for i in operator_keywords]

        if "singleton" in styles:
            rules += [(r'\b%s\b' % i, 0, styles['singleton']) for i in singletons]

        if "number" in styles:
            rules += [(r'\b[0-9]+\b', 0, styles['number'])]

        # Function definitions
        if "function" in styles:
            rules += [(r"def[\s]+([\w\.]+)", 1, styles['function'])]

        # Class definitions
        if "class" in styles:
            rules += [(r"class[\s]+([\w\.]+)", 1, styles['class'])]
            # Class argument (which is also a class so must be same color)
            rules += [(r"class[\s]+[\w\.]+[\s]*\((.*)\)", 1, styles['class'])]

        # Function arguments
        if "argument" in styles:
            rules += [(r"def[\s]+[\w]+[\s]*\(([\w]+)", 1, styles['argument'])]

        # Custom keywords
        if "keywords" in style_dict.keys():
            keywords = style_dict["keywords"]
            for k in keywords.keys():
                if k in styles:
                    rules += [(r'\b%s\b' % i, 0, styles[k]) for i in keywords[k]]

        if "string" in styles:
            # Double-quoted string, possibly containing escape sequences
            rules += [(r'"[^"\\]*(\\.[^"\\]*)*"', 0, styles['string'])]
            # Single-quoted string, possibly containing escape sequences
            rules += [(r"'[^'\\]*(\\.[^'\\]*)*'", 0, styles['string'])]

        # Comments from '#' until a newline
        if "comment" in styles:
            rules += [(r'#[^\n]*', 0, styles['comment'])]

        # 3. Resulting dictionary
        result = {
            "rules": [(re.compile(pat), index, fmt) for (pat, index, fmt) in rules],
            # Build a re.compile for each pattern
            "tri_single": tri_single,
            "tri_double": tri_double,
        }

        return result

    @staticmethod
    def format(rgb, style=''):
        """
        Return a QtWidgets.QTextCharFormat with the given attributes.
        """

        color = QtGui.QColor(*rgb)
        text_format = QtGui.QTextCharFormat()
        text_format.setForeground(color)

        if 'bold' in style:
            text_format.setFontWeight(QtGui.QFont.Bold)
        if 'italic' in style:
            text_format.setFontItalic(True)
        if 'underline' in style:
            text_format.setUnderlineStyle(QtGui.QTextCharFormat.SingleUnderline)

        return text_format

    def highlightBlock(self, text):
        """
        Apply syntax highlighting to the given block of text.
        """

        for expression, nth, text_format in self.styles[self._style]["rules"]:
            match = expression.search(text, 0)

            while match:
                # We actually want the index of the nth match
                index = match.start(nth)
                length = match.end(nth) - match.start(nth)
                try:
                    self.setFormat(index, length, text_format)
                except:
                    return False
                match = expression.search(text, match.end(nth))

        self.setCurrentBlockState(0)

        # Multi-line strings etc. based on selected scheme
        in_multiline = self.match_multiline(text, *self.styles[self._style]["tri_single"])
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.styles[self._style]["tri_double"])

        # TODO if there's a selection, highlight same occurrences in the full document.
        #   If no selection but something highlighted, unhighlight full document. (do it thru regex or sth)

    def setStyle(self, style_name="nuke"):
        if style_name in self.styles.keys():
            self._style = style_name
        else:
            raise Exception("Style {} not found.".format(str(style_name)))

    def match_multiline(self, text, delimiter, in_state, style):
        """
        Check whether highlighting requires multiple lines.
        """
        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            match = delimiter.search(text)
            start = match.start() if match else -1
            # Move past this match
            add = len(match.group()) if match else 0

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter
            match = delimiter.search(text, start + add)
            end = match.start() if match else -1
            # Ending delimiter on this line?
            if end >= add:
                length = end - start + add + len(match.group())
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
            # Apply formatting
            self.setFormat(start, length, style)
            # Look for the next match
            match = delimiter.search(text, start + length)
            start = match.start() if match else -1

        # Return True if still inside a multi-line string, False otherwise
        if self.currentBlockState() == in_state:
            return True
        else:
            return False

    @property
    def style(self):
        return self._style

    @style.setter
    def style(self, style_name="nuke"):
        self.setStyle(style_name)
