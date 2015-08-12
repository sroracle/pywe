#!/usr/bin/python3
# vim: sw=4:ts=4:sts=4
# Python-based PmWiki Editor (pywe)
# =================================
# Copyright (c) 2006 Benjamin C. Wilson. All Rights Reserved.
# See LICENSE for licensing information.
# Software version: v1.0 - Public Release May 20, 2006
# Software version: v1.1 - Public Release May 30, 2006
# Software version: v1.2 - Public Release June 2, 2006
# Software version: v1.3 - Public Release February 7, 2007
# Software version: v1.3.1 - Public Release February 9, 2007
__version__ = 'v1.3.1 - February 9, 2007'
from   configparser   import ConfigParser, DEFAULTSECT
from   getpass        import getpass
import logging        #      basicConfig, error, info
from   argparse       import ArgumentParser
import os             #      path, system
import re             #      compile, sub
import sys            #      argv, exit, path, stderr
from   tempfile       import NamedTemporaryFile
from   time           import strftime
from   urllib.parse   import urlencode, urljoin, urlsplit
from   urllib.request import urlopen

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
        fatal('No local source file to read from')

class TempWriteError(Exception):
    def __init__(self):
        fatal('Could not write to the temporary file')

class MultipleServers(Exception):
    def __init__(self):
        fatal('No server specified and multiple servers are configured, not guessing')

class NoServers(Exception):
    def __init__(self):
        fatal("You don't have any servers configured")

class RequiredSetting(Exception):
    def __init__(self, setting):
        fatal('The setting "' + setting + '" is required')

#===================================
# PmWiki Configuration Class
#-----------------------------------
class PmConfig:
    def __init__(self, server):
        c = self._config = ConfigParser()
        self.file = os.path.expanduser('~/.config/pywe.ini')

        c.read(self.file)
        self.servers = c.sections()
        layout = {
            'api': RequiredSetting,
            'url': '',
            'author': RequiredSetting,
            'password': '',
            'defaultgroup': 'Main',
            'deleteword':  'delete',
            'browser': '',
            'editor': '',
            'keep': False,
            'page': '',
        }
        if not server:
            if len(self.servers) == 1:
                self.server = server = self.servers[0]
                log('No server specified, using "'+self.server+'"')
            elif len(self.servers) > 1:
                raise MultipleServers
            else:
                raise NoServers

        for setting in layout.keys():
            if c.has_section(server) and c.has_option(server, setting):
                if type(layout[setting]) is str:
                    val = c.get(server, setting)
                elif type(layout[setting]) is bool:
                    val = c.getboolean(server, setting)
                elif layout[setting] is RequiredSetting:
                    val = c.get(server, setting)
            else:
                if layout[setting] is RequiredSetting: raise RequiredSetting(setting)
                else: val = layout[setting]

            setattr(self, setting, val)

        if not self.url: self.url = self.api

#===================================
# PmWiki Page Class
#-----------------------------------
class PmPage:
    def __init__(self, config, name):
        self.c = config
        if name:
            self.name = name
        else:
            self.name = self.c.page

        self.file = self.name
        if self.name.rfind('.pmwiki') != -1:
            self.name = self.name.replace('.pmwiki', '')

        self.group = self.name.split('.')[0]
        try:
            self.shortname = self.name.split('.')[1]
        except IndexError:
            log('No group specified, using "Main"')
            self.shortname = self.group
            self.group = self.c.defaultgroup
            self.name = self.group + '.' + self.shortname

        self.url = self.c.url.replace('$Group', self.group).replace('$Name', self.shortname)

    def api(self, action = ''):
        if not action:
            return self.c.api
        else:
            page = self.name.replace('/', '.')
            api = self.c.api.rstrip('/')
            return '%s?n=%s&action=%s' % (api, page, action)

    def pull(self, author = '', passwd = None):
        '''Retrieves the PmWiki source from the website'''
        url = self.api('source')
        payload = urlencode({'authid' : author, 'authpw' : passwd}).encode()
        try:
            fh  = urlopen(url, payload)
            content = fh.read().decode()
            if content.startswith('<!DOCTYPE'): raise Unauthorized(url)
            else: return content
        except IOError:
            fatal('Could not access', url)

    def push(self, old, new, author = '', passwd = None):
        '''Writes the page back to the website'''
        if new == old:
            log("Aborting write: you didn't make any changes!")
        else:
            url = self.api('edit')
            payload = {
                'action': 'edit',
                'author': author,
                'n':      self.name,
                'post':   1,
                'text':   new
            }
            if passwd is not None:
                payload['authid'] = author
                payload['authpw'] = passwd

            payload = urlencode(payload).encode()
            try:
                post  = urlopen(url, payload)
            except IOError as e:
                fn = self.cache(new)
                msg = 'Failed to write to website: %s\nChanges saved to "%s"' % (e, fn)
                fatal(msg)

    def cache(self, text):
        name = '%s.pmwiki' % self.name.replace('/', '.')
        f = open(name, 'w')
        f.write(text)
        f.close()
        return name

    def open(self, editor, text):
        '''Open the page in your favorite editor'''
        if len(text) == 0:
            log('New page:', self.name)
            text = '(:comment %s is a new page, save as empty to abort:)' % self.name

        f = NamedTemporaryFile('w+', suffix = '.pmwiki', prefix = self.name + '-')
        log('Using tempfile', f.name)
        try:
            f.write(text)
            f.flush()
            f.seek(0)
        except IOError:
            raise TempWriteError

        cmd = editor + ' ' + f.name
        os.system(cmd)

        output = f.read()
        f.close()
        return output

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

def checksetting(command):
    path = command.split(' ',1)[0]
    if not os.path.isfile(path):
        if path.find('/') == -1:
            fatal('The program "' + path + '" must be specified as an absolute path')
        else:
            fatal("Couldn't find", path)

#===================================
# Main:
#-----------------------------------
def main(argv=[]):
    p = ArgumentParser()
    p.add_argument(
        '-a', '--author',
        help = "sets author's name from the command line")
    p.add_argument(
        '-s', '--server',
        help = 'Specify server to use.')
    p.add_argument(
        '-b', '--browse', action = 'store_true',
        help = 'after edit, load the page in the configured browser.')
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
    c = PmConfig(option.server)

    if option.command == 'list':
        print('Configured servers:')
        print()
        for server in c.servers:
            print(server)
        sys.exit(0)

    page = PmPage(c, option.page)

    #-----------------------------------
    # Password management
    if option.nopass:
        password = None
    elif c.password and not option.nopass:
        password = c.password
    else:
        password = getpass()

    #-----------------------------------
    # Command management
    if option.command == 'push':
        if os.path.isfile(option.page):
            log('Pushing', page.name, '('+page.url+')')
            f = open(page.file, 'r')
            new = f.read()
            f.close()
            old = ''
        else:
            raise NoSource

    elif option.command == 'delete':
        delete = input('Deleting: ' + page.name + '. Are you sure? (Type delete)\n')
        if delete == 'delete':
            old = ''
            new = c.deleteword
        else:
            print('Deletion aborted.')
            sys.exit(0)

    else:
        old = page.pull(c.author, password)
        if option.command == 'pull':
            log('Pulling', page.name, '('+page.url+')')
            log('Saved to', page.cache(old))
            sys.exit(0)
        else:
            log('Editing', page.name, '('+page.url+')')
            checksetting(c.editor)
            new = page.open(c.editor, old)

    if c.keep or option.keep:
        page.cache(new)

    page.push(old, new, c.author, password)

    if option.browse:
        checksetting(c.browser)
        cmd = '%s %s' % (c.browser, page.url)
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
