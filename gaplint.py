#!/usr/bin/env python2
"""
This module provides functions for automatically checking the format of a GAP
file according to some conventions.
"""
#pylint: disable=invalid-name, dangerous-default-value, too-few-public-methods,
#pylint: disable=fixme

import re
import sys
import argparse
import os

################################################################################
# Globals
################################################################################

_VERBOSE = False
_SILENT = True

################################################################################
# Colourize strings
################################################################################

def _red_string(string):
    assert isinstance(string, str)
    return '\033[31m' + string + '\033[0m'

def _yellow_string(string):
    assert isinstance(string, str)
    return '\033[33m' + string + '\033[0m'

def _neon_green_string(string):
    assert isinstance(string, str)
    return '\033[40;38;5;82m' + string + '\033[0m'

def _orange_string(string):
    assert isinstance(string, str)
    return '\033[40;38;5;208m' + string + '\033[0m'

################################################################################
# Exit messages
################################################################################

def _exit_abort(message=None):
    if message:
        assert isinstance(message, str)
        sys.exit(_red_string('gaplint: ' + message + '! Aborting!'))
    else:
        sys.exit(_red_string('gaplint: Aborting!'))

################################################################################
# Info messages
################################################################################

def _info_statement(message):
    assert isinstance(message, str)
    sys.stdout.write(_neon_green_string(message + '\n'))

def _info_action(message):
    assert isinstance(message, str)
    sys.stdout.write(_yellow_string(message + '\n'))

def _info_verbose(message):
    assert isinstance(message, str)
    if not _SILENT and _VERBOSE:
        sys.stdout.write(_orange_string(message + '\n'))

def _info_warn(fname, line_nr, message, nr_lines):
    assert isinstance(fname, str) and isinstance(message, str)
    assert isinstance(line_nr, int) and isinstance(nr_lines, int)

    if not _SILENT:
        pad = ((len(str(nr_lines)) + 1) - len(str(line_nr + 1)))
        sys.stderr.write(_red_string('WARNING in ' + fname + ':'
                                     + str(line_nr + 1) + ' ' * pad
                                     + message + '\n'))

################################################################################
# Rule output
################################################################################

class RuleOutput(object):
    '''
    The output of a rule.

    Attributes:
        line  (str) : possibly modified version of the argument line
        msg   (str) : a warning message (defaults to None)
        abort (bool): indicating if we should abort the script
                      (defaults to False)
    '''

    def __init__(self, line, msg=None, abort=False):
        '''
        This is used for the output of a rule as applied to line.

        Args:
            line  (str) : a line of GAP code
            msg   (str) : a warning message (defaults to None)
            abort (bool): indicating if we should abort the script
                          (defaults to False)
        '''
        self.line = line
        self.msg = msg
        self.abort = abort

################################################################################
# Rules: a rule is just a function or callable class returning a RuleOutput
################################################################################

def _skip_tst_or_xml_file(ext):
    return ext == 'tst' or ext == 'xml'

class Rule(object):
    '''
    Base class for rules.

    A rule is a subclass of this class which has a __call__ method that returns
    a RuleOutput object.
    '''

    def reset(self):
        '''
        Reset the rule.

        This is only used by rules like those for checking the indentation of
        lines. This method is called once per file on which gaplint it run, so
        that issues with indentation, for example, in one file do not spill
        over into the next file.
        '''
        pass

    def skip(self, ext):
        '''
        Skip the rule.

        In some circumstances we might want to skip a rule, the rule is skipped
        if this method returns True. The default return value is falsy.
        '''
        pass

class ReplaceMultilineStrings(Rule):
    '''
    Replace multiline strings.

    When called this rule modifies the line given as a parameter to remove any
    multiline strings, and replace them with __REMOVED_MULTILINE_STRING__. This
    is to avoid matching linting issues within strings, where the issues do not
    apply.

    This rule does not return any warnings.
    '''
    def __init__(self):
        self._consuming = False

    def __call__(self, line):
        ro = RuleOutput(line)
        if self._consuming:
            end = line.find('"""')
            ro.line = '__REMOVED_MULTILINE_STRING__'
            if end != -1:
                ro.line += line[end + 3:]
                self._consuming = False
        else:
            start = line.find('"""')
            if start != -1:
                self._consuming = True
                end = line.find('"""', start + 3)
                ro.line = line[:start] + '__REMOVED_MULTILINE_STRING__'
                if end != -1:
                    self._consuming = False
                    ro.line += line[end + 3:]
        return ro

    def reset(self):
        self._consuming = False

class ReplaceQuotes(Rule):
    '''
    Remove everything between non-escaped <quote>s in a line.

    Strings and chars are replaced with <replacement>, and hence alter the
    length of the line, and its contents. If either of these is important for
    another rule, then that rule should be run before this one.

    This rule returns warnings if a line has an escaped quote outside a string
    or character, or if a line contains an unmatched unescaped quote.
    '''
    def __init__(self, quote, replacement):
        self._quote = quote
        self._replacement = replacement
        self._escape_pattern = re.compile(r'(^\\(\\\\)*[^\\]+.*$|^\\(\\\\)*$)')

    def _is_escaped(self, line, pos):
        if line[pos - 1] != '\\':
            return False
        # search for an odd number of backslashes immediately before line[pos]
        return self._escape_pattern.search(line[:pos][::-1])

    def _next_nonescaped_quote(self, line, pos):
        assert isinstance(line, str) and isinstance(pos, int)
        assert pos >= 0 and pos < len(line)
        pos = line.find(self._quote, pos)
        while pos > 0 and self._is_escaped(line, pos):
            pos = line.find(self._quote, pos + 1)
        return pos

    def __call__(self, line):
        assert isinstance(line, str)
        ro = RuleOutput(line)
        quote = self._quote
        replacement = self._replacement
        # TODO if we want to allow the script to modify the input, then we
        # better keep the removed strings/chars, and index the replacements so
        # that we can put them back at some point later on.
        beg = line.find(quote)
        if beg == -1:
            return ro
        elif self._is_escaped(line, beg):
            ro.msg = 'escaped quote outside string!'
            ro.abort = True
            return ro
        end = self._next_nonescaped_quote(line, beg + 1)

        while beg != -1:
            if end == -1:
                ro.msg = 'unmatched quote!'
                ro.abort = True
                break
            line = line[:beg] + replacement + line[end + 1:]
            beg = line.find(quote, beg + len(replacement) + 1)

            if beg > 0 and self._is_escaped(line, beg):
                ro.msg = 'escaped quote outside string!'
                ro.abort = True
                break
            end = self._next_nonescaped_quote(line, beg + 1)
        ro.line = line
        return ro

class RemoveComments(Rule):
    '''
    Remove the GAP comments in a line.

    When called this rule truncates the line given as a parameter to remove any
    comments. This is to avoid matching linting issues within comments, where
    the issues do not apply.

    This rule does not return any warnings.
    '''
    def __call__(self, line):
        assert isinstance(line, str)
        return RuleOutput(line[:line.find('#')])

class RemovePrefix(object):
    '''
    This is not a rule. This is just a callable class to remove the prefix
    'gap>' or '>' if called with a line from a file with extension 'tst' or
    'xml', if the line does not start with a 'gap>' or '>', then the entire
    line is replaced with __REMOVED_LINE_FROM_TST_OR_XML_FILE__.
    '''
    def __init__(self):
        self._gap_gt_prefix = re.compile(r'^gap>')
        self._gt_prefix = re.compile(r'^>')

    def __call__(self, line, ext):
        if ext != 'tst' and ext != 'xml':
            return line
        m = self._gap_gt_prefix.search(line) or self._gt_prefix.search(line)
        if m:
            line = line[m.end():]
        else:
            line = '__REMOVED_LINE_FROM_TST_OR_XML_FILE__'
        return line

class LineTooLong(Rule):
    '''
    Warn if the length of a line exceeds 80 characters.

    This rule does not modify the line.
    '''
    def __call__(self, line):
        assert isinstance(line, str)
        ro = RuleOutput(line)
        if len(line) > 81:
            ro.msg = 'too long line (' + str(len(line) - 1) + ' / 80)'
        return ro

class WarnRegex(Rule):
    '''
    Instances of this class produce a warning whenever a line matches the
    pattern used to construct the instance except if one of a list of
    exceptions is also matched.
    '''

    def __init__(self,
                 pattern,
                 warning_msg,
                 exceptions=[],
                 skip=lambda ext: None):
        #pylint: disable=bad-builtin, unnecessary-lambda, deprecated-lambda
        assert isinstance(pattern, str)
        assert isinstance(warning_msg, str)
        assert isinstance(exceptions, list)
        assert reduce(lambda x, y: x and isinstance(y, str), exceptions, True)

        self._pattern = re.compile(pattern)
        self._warning_msg = warning_msg
        self._exception_patterns = exceptions
        self._exception_group = None
        self._exceptions = map(lambda e: re.compile(e), exceptions)
        self._skip = skip

    def __call__(self, line):
        nr_matches = 0
        msg = None
        exception_group = self._exception_group
        it = self._pattern.finditer(line)
        for x in it:
            if len(self._exceptions) > 0:
                exception = False
                x_group = x.groups().index(exception_group) + 1
                for e in self._exceptions:
                    ite = e.finditer(line)
                    for m in ite:
                        m_group = m.groups().index(exception_group) + 1
                        if m.start(m_group) == x.start(x_group):
                            exception = True
                            break
                    if exception:
                        break
                else:
                    nr_matches += 1
            else:
                nr_matches += 1
        if nr_matches > 0:
            msg = self._warning_msg
        return RuleOutput(line, msg, False)

    def skip(self, ext):
        return self._skip(ext)

class WhitespaceOperator(WarnRegex):
    '''
    Instances of this class produce a warning whenever the whitespace around an
    operator is incorrect.
    '''
    def __init__(self, op, exceptions=[]):
        #pylint: disable=bad-builtin, deprecated-lambda, unnecessary-lambda
        WarnRegex.__init__(self, '', '')
        assert isinstance(op, str)
        assert op[0] != '(' and op[-1] != ')'
        assert exceptions is None or isinstance(exceptions, list)
        assert reduce(lambda x, y: x and isinstance(y, str), exceptions, True)
        gop = '(' + op + ')'
        pattern = (r'(\S' + gop + '|' + gop + r'\S|\s{2,}' + gop +
                   '|' + gop + r'\s{2,})')
        self._pattern = re.compile(pattern)
        self._warning_msg = ('wrong whitespace around operator '
                             + op.replace('\\', ''))
        exceptions = map(lambda e: e.replace(op, '(' + op + ')'), exceptions)
        self._exceptions = map(lambda e: re.compile(e), exceptions)

        self._exception_group = op.replace('\\', '')

class Indentation(Rule):
    '''
    This class checks that the indentation level is correct in a given line.

    Certain keywords increase the indentation level, while others decrease it,
    this rule checks that a given line has the minimum indentation level
    required.
    '''
    def __init__(self):
        self._expected = 0
        self._before = [(re.compile('( |^)(elif|else)( |$)'), -2),
                        (re.compile(r'( |^)end(;|\)|,)'), -2),
                        (re.compile('( |^)(until|od|fi);'), -2),
                        (re.compile('( |^)until '), -2)]
        self._after = [(re.compile(r'\s(then|do)(\s|$)'), -2),
                       (re.compile(r'( |^)(repeat|else)(\s|$)'), 2),
                       (re.compile(r'( |^)function(\s|\()'), 2),
                       (re.compile('( |^)(if|for|while|elif) '), 4)]
        self._indent = re.compile(r'^( *)\S')
        self._blank = re.compile(r'^\s*$')

    def __call__(self, line):
        assert self._expected >= 0
        ro = RuleOutput(line)
        if self._blank.search(line):
            return ro
        for pair in self._before:
            if pair[0].search(line):
                self._expected += pair[1]

        _info_verbose(line + ' [expected indentation level ' +
                      str(self._expected) + ']')

        if self._get_indent_level(line) < self._expected:
            ro.msg = ('bad indentation: found ' +
                      str(self._get_indent_level(line)) +
                      ' expected at least ' + str(self._expected))
        for pair in self._after:
            if pair[0].search(line):
                self._expected += pair[1]
        return ro

    def _get_indent_level(self, line):
        indent = self._indent.search(line)
        assert indent
        return len(indent.group(1))

    def reset(self):
        self._expected = 0

    def skip(self, ext):
        return _skip_tst_or_xml_file(ext)

class ConsecutiveEmptyLines(WarnRegex):
    '''
    This rule checks if there are consecutive empty lines in a file.
    '''
    def __init__(self):
        WarnRegex.__init__(self, r'^\s*$', 'consecutive empty lines!')
        self._prev_line_empty = False

    def __call__(self, line):
        ro = WarnRegex.__call__(self, line)
        if ro.msg:
            if not self._prev_line_empty:
                self._prev_line_empty = True
                ro.msg = None
        else:
            self._prev_line_empty = False
        return ro

    def reset(self):
        self._prev_line_empty = False

################################################################################
# Functions for running this as a script instead of a module
################################################################################

def _parse_args(kwargs):
    global _SILENT, _VERBOSE #pylint: disable=global-statement
    parser = argparse.ArgumentParser(prog='gaplint',
                                     usage='%(prog)s [options]')
    if __name__ == '__main__':
        parser.add_argument('files', nargs='+', help='the files to lint')

    parser.add_argument('--max-warnings', nargs='?', type=int,
                        help='max number of warnings reported (default: 1000)')
    parser.set_defaults(max_warnings=1000)

    parser.add_argument('--silent', dest='silent', action='store_true',
                        help='silence all warnings (default: False)')
    parser.set_defaults(silent=False)

    parser.add_argument('--verbose', dest='verbose', action='store_true',
                        help=' (default: False)')
    parser.set_defaults(verbose=False)

    args = parser.parse_args()

    if 'silent' in kwargs:
        _SILENT = kwargs['silent']
    else:
        _SILENT = args.silent

    if 'verbose' in kwargs:
        _VERBOSE = kwargs['verbose']
    else:
        _VERBOSE = args.verbose

    if 'max-warnings' in kwargs:
        args.max_warnings = kwargs['max-warnings']

    if __name__ != '__main__':
        if not ('files' in kwargs and isinstance(kwargs['files'], list)):
            _exit_abort('no files specified or not specified in a list')
        args.files = kwargs['files']

    for fname in args.files:
        if not (os.path.exists(fname) and os.path.isfile(fname)):
            _exit_abort(fname + ' no such file!')

    return args

################################################################################
# The list of rules (the order is important!)
################################################################################

# TODO process rules according to the content of a configuration file, i.e.
# include some rules and not others, allows options line the indentation level,
# the length of a line, etc...

# TODO allow skipping a file in that file
# gaplint: skip-file

_remove_prefix = RemovePrefix()

RULES = [LineTooLong(),
         WarnRegex(r'^.*\s+\n$',
                   'trailing whitespace!',
                   [],
                   _skip_tst_or_xml_file),
         ReplaceMultilineStrings(),
         ReplaceQuotes('"', '__REMOVED_STRING__'),
         WarnRegex(r'#{3,}.*\w', 'too many hashes!!'),
         ConsecutiveEmptyLines(),
         RemoveComments(),
         ReplaceQuotes('\'', '__REMOVED_CHAR__'),
         Indentation(),
         WarnRegex(r',(([^, ]+)|( {2,})\w)',
                   'exactly one space required after comma'),
         WarnRegex(r'\s,', 'no space before comma'),
         WarnRegex(r'(\(|\[|\{)\s',
                   'no space allowed after bracket'),
         WarnRegex(r'\s(\)|\]|\})',
                   'no space allowed before bracket'),
         WarnRegex(r';.*;',
                   'more than one semicolon!',
                   [],
                   _skip_tst_or_xml_file),
         WarnRegex(r'(\s|^)function[^\(]',
                   'keyword function not followed by ('),
         WarnRegex(r'(\S:=|:=(\S|\s{2,}))',
                   'wrong whitespace around operator :='),
         WarnRegex(r'\t',
                   'there are tabs in this line, replace with spaces!'),
         WhitespaceOperator(r'\+', [r'^\s*\+']),
         WhitespaceOperator(r'\*', [r'^\s*\*', r'\\\*']),
         WhitespaceOperator(r'-',
                            [r'-(>|\[)', r'(\^|\*|,|=|\.|>) -',
                             r'(\(|\[)-', r'return -infinity',
                             r'return -\d']),
         WhitespaceOperator(r'\<', [r'^\s*\<', r'\<(\>|=)',
                                    r'\\\<']),
         WhitespaceOperator(r'\<='),
         WhitespaceOperator(r'\>', [r'(-|\<)\>', r'\>=']),
         WhitespaceOperator(r'\>='),
         WhitespaceOperator(r'=', [r'(:|>|<)=', r'^\s*=', r'\\=']),
         WhitespaceOperator(r'->'),
         WhitespaceOperator(r'\/', [r'\\\/']),
         WhitespaceOperator(r'\^', [r'^\s*\^', r'\\\^']),
         WhitespaceOperator(r'<>', [r'^\s*<>']),
         WhitespaceOperator(r'\.\.', [r'\.\.(\.|\))'])]

################################################################################
# The main event
################################################################################

def run_gaplint(**kwargs): #pylint: disable=too-many-branches
    '''
    This function applies all rules in this module to the files specified by
    the keywords argument files.

    Keyword Args:
        files (list):      a list of the filenames (str) of the files to lint
        maxwarnings (int): the maximum number of warnings before giving up
                           (defaults to 1000)
        silent (bool):     no output
        verbose (bool):    so much output you will not know what to do
    '''
    args = _parse_args(kwargs)

    total_nr_warnings = 0

    for fname in args.files:
        try:
            ffile = open(fname, 'r')
            lines = ffile.readlines()
            ffile.close()
        except IOError:
            _exit_abort('cannot read ' + fname)

        ext = fname.split('.')[-1]
        nr_warnings = 0
        for i in xrange(len(lines)):
            lines[i] = _remove_prefix(lines[i], ext)
            for rule in RULES:
                if not rule.skip(ext):
                    ro = rule(lines[i])
                    assert isinstance(ro, RuleOutput)
                    if ro.msg:
                        nr_warnings += 1
                        _info_warn(fname, i, ro.msg, len(lines))
                    if ro.abort:
                        _exit_abort()
                    lines[i] = ro.line
                    if total_nr_warnings + nr_warnings >= args.max_warnings:
                        _exit_abort('Too many warnings')
        for rule in RULES:
            rule.reset()
        total_nr_warnings += nr_warnings
        if nr_warnings == 0:
            _info_statement('SUCCESS in ' + fname)
    if total_nr_warnings != 0:
        if not _SILENT:
            sys.stderr.write(_red_string('FAILED with '
                                         + str(total_nr_warnings)
                                         + ' warnings!\n'))
            if __name__ == '__main__':
                sys.exit(1)
    if __name__ == '__main__':
        sys.exit(0)

if __name__ == '__main__':
    run_gaplint()