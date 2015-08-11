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
from   argparse     import ArgumentParser
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
        fatal('Authentication required for', url)

class NoEditor(Exception):
    def __init__(self, msg):
        fatal(msg)

class NoSource(Exception):
    def __init__(self):
        fatal('No local source file to read from.')

class TempWriteError(Exception):
    def __init__(self):
        fatal('Could not write to the temporary file')

class MultipleDomains(Exception):
    def __init__(self):
        fatal('No server specified and multiple servers are configured, not guessing.')

class NoDomains(Exception):
    def __init__(self):
        fatal("You don't have any servers configured.")

#===================================
# PmWiki Configuration Class
#-----------------------------------
class PmwikiConfig:
    def __init__(self, server, api):
        self.api = api
        c = self._config = ConfigParser()
        self.file = os.path.expanduser('~/.config/pywe.ini')

        c.read(self.file)
        self.servers = c.sections()
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
        if not server:
            if len(self.servers) == 1:
                self.server = server = self.servers[0]
                log('No server specified, using "'+self.server+'"')
            elif len(self.servers) > 1: raise MultipleDomains
            else: raise NoDomains

        for option in layout.keys():
            if c.has_section(server) and c.has_option(server, option):
                if layout[option] is str: val = c.get(server, option)
                elif layout[option] is bool: val = c.getboolean(server, option)
            else: val = ''
            setattr(self, option, val)
        if not self.url: self.url = self.api
        if not self.deleteword: self.deleteword = 'delete'

#===================================
# PmWiki Page Class
#-----------------------------------
class PmwikiPage:
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
            # TODO: pass self.url (not defined in this class), not self.api
            if content.startswith('<!DOCTYPE'): raise Unauthorized(self.api)
            else: return content
        except IOError: fatal('Could not access', self.api)

    def push(self, old, new, author='', passwd=None):
        '''Writes the page back to the website'''
        if old == new: log("Aborting write: you didn't make any changes!")
        else:
            api = self._fmtPage('edit')
            payload = {
                'action': 'edit',
                'author': author,
                'n':      self.page,
                'post':   1,
                'text':   new
            }
            if passwd is not None:
                payload['authid'] = author
                payload['authpw'] = passwd

            payload = urlencode(payload)
            try: post  = urlopen(api, payload)
            except IOError, e:
                fn = self.savepage(new)
                msg = 'Failed to write to website: %s\nChanges saved to "%s"' % (e, fn)
                fatal(msg)

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
            log('New page:', self.page)
            text = '(:comment %s is a new page, save as empty to abort:)' % self.page

        f = NamedTemporaryFile('r+w', -1, '.pmwiki', 'pywe-', tempdir)
        log('Using tempfile:', f.name)
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

def findApp(f,m='Could not find application: '):
    '''If we don't have the application at first, we go looking.'''
    if os.path.isfile(f): return f
    dirs = sys.path
    dirs.insert(0,os.environ['HOME'])
    for d in dirs:
      c = os.path.join(d, f)
      if os.path.isfile(c): return c
    raise NoEditor(m+f)

def log(*args):
    # TODO: global debug var
    args = ' '.join(args) + '\n'
    sys.stderr.write(args)
    logging.info(args)

def fatal(*args):
    '''Prints errors to stderr, logs the error, and quits.'''
    args = ' '.join(args) + '\n'
    sys.stderr.write(args)
    logging.error(args)
    sys.exit(1)

def checkApp(o, a, m):
    # TODO: this is awful
    if not o: return 0
    msg = {
      'noeditor': 'You must configure an editor to edit a page.',
      'nobrowser': 'You must configure a browser to us this option.'
    }
    check = a.split(' ',1)[0]

    a = findApp(check)
    if not os.path.isfile(check): fatal(msg[m])
    return True

#===================================
# Main:
#-----------------------------------
def main(argv=[]):
    page = None
    api = None

    p = ArgumentParser()
    p.add_argument(
        '-a', '--author',
        help = "sets author's name from the command line")
    p.add_argument(
            '-s', '--server',
            help = 'Specify server to use.')
    p.add_argument(
        '-e', '--editor',
        help = 'sets the editor to use. This must be a full path.')
    p.add_argument(
        '-b', '--browse', action = 'store_true',
        help = 'after edit, load the page in the configured browser.')
#   p.add_argument(
#       '-c', '--calendar', action = 'store_true',
#       help = "append today's date to page")
#   p.add_argument(
#       '-j', '--journal', action = 'store_true',
#       help = "append today's date to page")
    p.add_argument(
        '-k', '--keep', action = 'store_true',
        help = 'retain local copy of page source after edit.')
    p.add_argument(
        '-n', '--nopass', action = 'store_true',
        help = 'Explicitly use no password when authenticating.')
#   p.add_argument(
#       '-d', '--debug', action = 'store_true', dest = 'debug')
    p.add_argument(
        '-v', '--version', action = 'version', version='%prog ' + __version__)
    p.add_argument(
        'command', metavar='<command>', choices = ('push', 'pull', 'edit', 'delete', 'list'),
        help = 'Push sends the given page to the server.'
        ' Pull will retrieve the given page.'
        ' Edit will pull the page, open it in the configured editor, and push the changes.'
        ' Delete will confirm before deleting the page on the server.'
        ' List will show all configured servers.')
    p.add_argument(
        'page', metavar='<page>',
        help = 'The page with which to work. This is not required for the "list" command.')
    option = p.parse_args()

    server = option.server
    c = PmwikiConfig(server, api)

    if option.command == 'list':
        print 'Configured servers:'
        print
        for server in c.servers: print server
        sys.exit(0)

    page = option.page or c.page
    page_group = page.split('.')[0]
    page_name = page.split('.')[1]
    c.url = c.url.replace('$Group', page_group).replace('$Name', page_name)

    pm = PmwikiPage(c.api, page, c.enablepathinfo)

    #-----------------------------------
    # Editor checksum
    if option.editor: c.editor = option.editor
    checkApp(True, c.editor, 'noeditor')

    if option.keep: c.keep = option.keep

    #-----------------------------------
    # Password management
    if option.nopass: password = None
    elif c.password and not option.nopass: password = c.password
    else: password = getpass()

    #-----------------------------------
    # Command management
    if option.command == 'push':
        if os.path.isfile(page):
            log('Pushing:', page, '('+c.url+')')
            f = open(page, 'r')
            new = f.read()
            f.close()
            old = ''
            if page.endswith('.pmwiki'): pm.page = page.replace('.pmwiki', '')
        else: raise NoSource

    elif option.command == 'delete':
        delete = raw_input('Deleting: '+page+'. Are you sure? (Type delete)\n')
        if delete == 'delete':
            old = ''
            new = c.deleteword
        else:
            print 'Deletion aborted.'
            sys.exit(0)
    else:
        #if option.journal: pm.page += strftime('-%Y-%m-%d')
        #if option.calendar: pm.page += strftime('%Y%m%d')

        log('Editing:', page, '('+c.url+')')
        old = pm.pull(c.author, password)
        if option.command == 'pull':
            log('Pulling:', page, '('+c.url+')')
            print pm.savepage(old)
            sys.exit(0)
        else:
            new = pm.open(c.editor, old)

    if c.keep: pm.savepage(new)

    pm.push(old, new, c.author, password)

    if checkApp(option.browse, c.browser, 'nobrowser'):
        cmd = '%s %s' % (c.browser, c.url)
        os.system(cmd)

if __name__ == '__main__':
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
        fatal('User terminated program via keyboard')
