#!/usr/bin/python2
# vim: sw=4:ts=4:sts=4
# Python-bases PmWiki Editor (Pywe)
# =================================
# Copyright (c) 2006 Benjamin C. Wilson. All Rights Reserved.
# See LICENSE for licensing information.
# Software version: v1.0 - Public Release May 20, 2006
# Software version: v1.1 - Public Release May 30, 2006
# Software version: v1.2 - Public Release June 2, 2006
# Software version: v1.3 - Public Release February 7, 2007
# Software version: v1.3.1 - Public Release February 9, 2007
__version__ = 'v1.3.1 - February 9, 2007'
from   ConfigParser import ConfigParser, DEFAULTSECT
from   getpass      import getpass
import logging      #      basicConfig, error, info
from   optparse     import OptionParser
import os           #      path, system
import re           #      compile, sub
import sys          #      argv, exit, path, stderr
from   tempfile     import NamedTemporaryFile, tempdir
from   time         import strftime
from   urllib       import urlencode, urlopen
from   urlparse     import urljoin, urlsplit

#===================================
# Various Custom Exception Classes.
class Unauthorized(Exception):
    def __init__(self, url=''):
        say_error('Wiki said authentication needed.' + url)

class NoEditor(Exception):
    def __init__(self, msg):
        say_error(msg)

class NoSource(Exception):
    def __init__(self):
        say_error('No local source file to read from.')

class TempWriteError(Exception):
    def __init__(self):
        say_error('Could not write to the temporary file')

class MultipleDomains(Exception):
    def __init__(self):
        say_error('No domain specified and multiple domains are configured, not guessing.')

class NoDomains(Exception):
    def __init__(self):
        say_error("You don't have any domains configured.")

#===================================
# PmWiki Configuration Class
#-----------------------------------
class PmwikiConfig:
    def __init__(self, dom, api):
        self.api = api
        c = self._config = ConfigParser()
        self.file = os.path.expanduser('~/.config/pywe.ini')

        c.read(self.file)
        self.doms = c.sections()
        layout = {
            'api': str,
            'author': str,
            'browser': str,
            'deleteword':  str,
            'editor': str,
            'enablepathinfo': bool,
            'keep': bool,
            'page': str,
            'password': str,
            'url': str,
        }
        if not dom:
            if len(self.doms) == 1:
                self.dom = dom = self.doms[0]
                say_info('No domain specified, using "' + self.dom + '"')
            elif len(self.doms) > 1: raise MultipleDomains
            else: raise NoDomains

        for option in layout.keys():
            if c.has_section(dom) and c.has_option(dom, option):
                if layout[option] is str: val = c.get(dom, option)
                elif layout[option] is bool: val = c.getboolean(dom, option)
            else: val = ''
            setattr(self, option, val)
        if not self.url: self.url = self.api
        if not self.deleteword: self.deleteword = 'delete'

#===================================
# PmWiki Page Class
#-----------------------------------
class PmwikiPage :
    def __init__(self, api, page, epi):
        self.api = api
        self.page = page
        self.enablepathinfo = epi
        self.passwd = None
        self.text = None

    def _fmtPage(self, action):
        page = self.page
        api = self.api
        if self.enablepathinfo:
            if api[-1] != '/': api += '/'
            return urljoin(api, page) + '?action=' + action
        else:
            api = re.sub('/$','',api)
            page = re.sub('/','.', page)
            return '%s?n=%s&action=%s' % (api, page, action)

    def pull(self, author='', passwd=None):
        '''Retrieves the PmWiki source from the website'''
        source = self._fmtPage('source')
        payload = urlencode({'authid' : author, 'authpw' : passwd})
        try:
            fh  = urlopen(source, payload)
            content = fh.read()
            if content[4:11] == 'DOCTYPE': raise Unauthorized(self.api)
            else: return content
        except IOError: say_error('Could not access: ' + self.api)

    def push(self, text, src, author='', passwd=None):
        '''Writes the page back to the website'''
        if  src == text:
            say_info("Aborting write: you didn't make any changes!")
        else:
            if text != 'delete': text = self.editMark(text)
            api = self._fmtPage('edit')
            payload = {
                'action': 'edit',
                'authid': author,
                'author': author,
                'authpw': passwd,
                'n': self.page,
                'post': 1,
                'text': text
            }
            if passwd is None:
                del(payload['authid'])
                del(payload['authpw'])

            payload = urlencode(payload)
            try: post  = urlopen(api, payload)
            except IOError, e:
                fn = self.savepage(text)
                msg = 'Failed to write to website: %s\nChanges saved to "%s"' % (e, fn)
                say_error(msg)

    def savepage(self, t):
        fn = '%s.pmwiki' % self.page
        fn = fn.replace('/','.')
        f = open(fn, 'w')
        f.write(t)
        f.close()
        return fn

    def open(self, editor, text):
        '''Open the page in your favorite editor'''
        if len(text) == 0:
            say_info('New page: %s' % self.page)
            text = '(:comment %s is a new page, save as empty to abort:)' % self.page

        f = NamedTemporaryFile('r+w', -1, '.pmwiki', 'pywe-', tempdir)
        say_info('Using tempfile: ' + f.name, 1)
        try:
            f.write(text)
            f.flush()
            f.seek(0)
        except IOError: raise TempWriteError

        cmd = editor + ' ' + f.name
        os.system(cmd)

        output = f.read()
        f.close()
        return output

    def editMark(self, t) :
       # TODO: make optional... for now, disabled
       #m = "\n(:comment This page has been edited using Pywe:)"
       #m_RE = re.compile("\n+\(:comment This page has been edited using Pywe:\)")
       #t = m_RE.sub('', t)
       #t += m
        return t

def findApp(f,m='Could not find application: '):
    '''If we don't have the application at first, we go looking.'''
    if os.path.isfile(f): return f
    dirs = sys.path
    dirs.insert(0,os.environ['HOME'])
    for d in dirs:
      c = os.path.join(d, f)
      if os.path.isfile(c): return c
    raise NoEditor(m+f)

def say_info(msg, squash=0):
    # TODO: global debug var
    if squash: return
    sys.stderr.write(msg+'\n')
    logging.info(msg)

def say_error(msg):
    '''Prints errors to stderr, logs the error and quits.'''
    sys.stderr.write(msg + '\n')
    logging.error(msg)
    sys.exit(0)

def checkApp(o, a, m):
    if not o: return 0
    msg = {
      'noeditor': 'You must configure an editor to edit a page.',
      'nobrowser': 'You must configure a browser to us this option.'
    }
    check = a.split(' ',1)[0]

    a = findApp(check)
    if not os.path.isfile(check): say_error(msg[m])
    return True

#===================================
# Main:
#-----------------------------------
def main(argv=None):
    page = None
    api = None

    p = OptionParser(
            conflict_handler='resolve',version='%prog '+__version__)
    p.add_option(
            '-a','--author',dest='author',
            help="sets author's name from the command line")
    p.add_option(
            '-b',action='store_true',dest='browse',
            help='after edit, load the page in the configured browser.')
    p.add_option(
            '-c','--calendar',action='store_true',
            help="append today's date to page")
    p.add_option(
            '-d','--domain',dest='domain',
            help='Specify domain to use.')
    p.add_option(
            '-e','--editor',dest='editor',
            help='sets editor (full path) from the command line.')
    p.add_option(
            '-j','--journal',action='store_true',
            help="append today's date to page")
    p.add_option(
            '-k','--keep',action='store_true',dest='keep',
            help='retain local copy of page source after edit.')
    p.add_option(
            '-n','--nopass',action='store_true',dest='nopass',
            help='site does not require a password.')
    p.add_option(
            '-v','--debug',action='store_true',dest='debug')
    option, args = p.parse_args()

    if not len(args) or args[0] not in ('push', 'pull', 'edit', 'delete', 'list'):
        say_error('Must command a push, pull, edit, delete, or list. Use --help for options.')
    option.command = args[0]
    dom = option.domain
    c = PmwikiConfig(dom, api)

    if option.command == 'list':
        print 'Configured domains:'
        print
        for dom in c.doms: print dom
        sys.exit(0)

    if len(args) < 2:
        say_error('Must provide a page to use.')

    try: page = args[1]
    except IndexError: page = c.page
    page_group = page.split('.')[0]
    page_name = page.split('.')[1]
    c.url = c.url.replace('$Group', page_group).replace('$Name', page_name)

    pm = PmwikiPage(c.api, page, c.enablepathinfo)

    #-----------------------------------
    # Editor checksum
    if (option.editor): c.editor = option.editor
    checkApp(True, c.editor, 'noeditor')

    if (option.keep): c.keep = option.keep

    #-----------------------------------
    # Password management
    if option.nopass: password = None
    elif c.password and not option.nopass: password = c.password
    else: password = getpass()

    #-----------------------------------
    # Command management
    if option.command == 'push':
        if os.path.isfile(page):
            say_info('Pushing: '+page+' ('+c.url+')')
            f = open(page, 'r')
            new = f.read()
            f.close()
            src = ''
            if page.endswith('.pmwiki'): pm.page = page.replace('.pmwiki', '')
        else:
            raise NoSource

    elif option.command == 'delete':
        delete = raw_input('Deleting: '+page+'. Are you sure? (Type delete)\n')
        if delete == 'delete':
            src = ''
            new = c.deleteword
        else:
            print 'Deletion aborted.'
            sys.exit(0)
    else:
        if option.journal: pm.page += strftime('-%Y-%m-%d')
        if option.calendar: pm.page += strftime('%Y%m%d')

        say_info('Editing: '+page+' ('+c.url+')')
        src = pm.pull(c.author, password)
        if option.command == 'pull':
            say_info('Pulling: '+page+' ('+c.url+')')
            print pm.savepage(src)
            sys.exit(0)
        else:
            new = pm.open(c.editor, src)

    if (option.keep or c.keep):
        pm.savepage(new)

    pm.push(new, src, c.author, password)

    if checkApp(option.browse, c.browser, 'nobrowser'):
        cmd = '%s %s' % (c.browser, c.url)
        os.system(cmd)

if __name__ == '__main__':
    '''When we're running from the command line. Perhaps in the future a GUI
    will come?'''

    try:
        logging.basicConfig(
            level=logging.ERROR,
            format='%(asctime)s %(levelname)-8s %(message)s',
            datefmt='%a, %d %b %Y %H:%M:%S',
            filename = '/tmp/pywe.log',
            filemode='a+')
    except TypeError:
        logging.basicConfig()

    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        say_error('User terminated program via keyboard')
