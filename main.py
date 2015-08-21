#!/usr/bin/python3
# Python-based PmWiki Editor (pywe)
# Copyright (c) 2006 Benjamin C. Wilson. All Rights Reserved.
# See LICENSE for licensing information.
from   configparser   import ConfigParser
from   getpass        import getpass
from   argparse       import ArgumentParser
import os             # path, system
import sys            # argv, exit, path, stderr
from   tempfile       import NamedTemporaryFile
from   urllib.parse   import urlencode
from   urllib.request import urlopen
# Software version: v1.0 - Public Release May 20, 2006
# Software version: v1.1 - Public Release May 30, 2006
# Software version: v1.2 - Public Release June 2, 2006
# Software version: v1.3 - Public Release February 7, 2007
# Software version: v1.3.1 - Public Release February 9, 2007
__version__ = 'v1.3.1 - February 9, 2007'
commands = ('push', 'pull', 'edit', 'delete', 'list')


class RequiredSetting:

    pass


class PmConfig:

    def __init__(self, server):
        '''Generates the PmConfig object from the INI file.'''
        c = self._config = ConfigParser()
        self.file = os.path.expanduser('~/.config/pywe.ini')

        c.read(self.file)
        self.servers = c.sections()
        if not server:
            if len(self.servers) == 1:
                self.server = server = self.servers[0]
                log('No server specified, using "'+self.server+'"')
            elif len(self.servers) > 1:
                fatal('No server specified and multiple servers are'
                      ' configured, not guessing')
            else:
                fatal("You don't have any servers configured")

        layout = {
            'api': RequiredSetting,
            'url': '',
            'defaultgroup': 'Main',
            'defaultpage': '',
            'deleteword':  'delete',
            'keep': False,
            'author': RequiredSetting,
            'password': '',
            'browser': '',
            'editor': '',
        }

        for setting in layout.keys():
            if c.has_section(server) and c.has_option(server, setting):
                if isinstance(layout[setting], str):
                    val = c.get(server, setting)
                elif isinstance(layout[setting], bool):
                    val = c.getboolean(server, setting)
                elif layout[setting] is RequiredSetting:
                    val = c.get(server, setting)
            else:
                if layout[setting] is RequiredSetting:
                    fatal('The setting "' + setting + '" is required')
                else:
                    val = layout[setting]

            setattr(self, setting, val)

        if not self.url:
            self.url = self.api

        self.resolve(self.browser)
        self.resolve(self.editor)

    def resolve(self, command):
        '''Checks the validity of the browser and editor settings.'''
        path = command.split(' ', 1)[0]
        if not os.path.isfile(path):
            if path.find('/') == -1:
                fatal('The program "' + path + '" must be specified as an'
                      ' absolute path')
            else:
                fatal("Couldn't find", path)


class PmPage:

    def __init__(self, config, name):
        '''Parses the given name into a fully-qualified PmWiki page name.'''
        self.c = config
        if name:
            self.name = name
        else:
            self.name = self.c.defaultpage

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

        self.url = self.c.url.replace('$Group', self.group)
        self.url = self.url.replace('$Name', self.shortname)

    def api(self, action=None):
        '''Returns a PmWiki action URL.'''
        if not action:
            return self.c.api
        else:
            page = self.name.replace('/', '.')
            api = self.c.api.rstrip('/')
            return '%s?n=%s&action=%s' % (api, page, action)

    def pull(self):
        '''Retrieves the page from the server.'''
        log('Pulling', self.name, '('+self.url+')')
        url = self.api('source')
        payload = urlencode({'authid': self.c.author,
                             'authpw': self.c.password}).encode()
        try:
            response = urlopen(url, payload)
            content = response.read().decode()
            if content.startswith('<!DOCTYPE'):
                fatal('Authentication required for', url)
            else:
                return content
        except IOError:
            fatal('Could not access', url)

    def push(self, old='', new='', fromfile=False):
        '''Writes the page back to the server.'''
        if fromfile:
            if os.path.isfile(self.file):
                log('Pushing', self.name, '('+self.url+')')
                with open(self.file, 'r') as f:
                    new = f.read()
                old = ''
            else:
                fatal("Couldn't find", self.file)

        if new == old:
            log("Aborting write: you didn't make any changes!")
        else:
            url = self.api('edit')
            payload = {
                'action': 'edit',
                'author': self.c.author,
                'n':      self.name,
                'post':   1,
                'text':   new
            }
            if self.c.password is not None:
                payload['authid'] = self.c.author
                payload['authpw'] = self.c.password

            payload = urlencode(payload).encode()
            try:
                urlopen(url, payload)
            except IOError as error:
                if new != self.c.deleteword or str(error) != 'HTTP Error' \
                                                             ' 404: Not Found':
                    filename = self.cache(new)
                    fatal('Failed to write to website: %s\nChanges saved'
                          ' to "%s"' % (error, filename))

    def cache(self, text):
        '''Saves a local copy of the page.'''
        name = '%s.pmwiki' % self.name.replace('/', '.')
        with open(name, 'w') as f:
            f.write(text)

        return name

    def edit(self, editor, old):
        '''Edits the page with the configured editor.'''
        log('Editing', self.name, '('+self.url+')')
        if not len(old):
            log('New page:', self.name)
            old = '(:comment %s is a new page, leave only this line to' \
                  ' abort:)' % self.name

        with NamedTemporaryFile('w+', suffix='.pmwiki',
                                prefix=self.name + '-') as f:
            log('Using tempfile', f.name)
            try:
                f.write(old)
                f.flush()
                f.seek(0)
            except IOError:
                fatal('Could not write to the temporary file')

            cmd = editor + ' ' + f.name
            os.system(cmd)

            new = f.read()
            if self.c.keep:
                self.cache(new)
            self.push(old, new)

    def delete(self):
        '''Deletes the page from the server.'''
        confirm = input('Deleting: ' + self.name + '.\nAre you sure? (Type'
                        ' delete to confirm)\n')
        if confirm == 'delete':
            self.push(new=self.c.deleteword)
        else:
            print('Deletion aborted')


def log(*args):
    '''Prints message to stderr.'''
    args = ' '.join(args) + '\n'
    sys.stderr.write(args)


def fatal(*args):
    '''Prints message to stderr and exits.'''
    log(*args)
    sys.exit(1)


def main():
    readline = ArgumentParser()
    readline.add_argument(
        '-a', '--author',
        help="sets author's name from the command line")
    readline.add_argument(
        '-s', '--server',
        help='specify server to use')
    readline.add_argument(
        '-b', '--browse', action='store_true',
        help='after edit, load the page in the configured browser')
    readline.add_argument(
        '-k', '--keep', action='store_true',
        help='retain local copy of page source after edit')
    readline.add_argument(
        '-n', '--nopass', action='store_true',
        help='explicitly use no password when authenticating')
    readline.add_argument(
        '-v', '--version', action='version', version='%prog ' + __version__)
    readline.add_argument(
        'command', metavar='<command>', choices=commands,
        help='Push sends the given page to the server. Pull will retrieve the'
        ' given page. Edit will pull the page, open it in the configured'
        ' editor, and push the changes. Delete will confirm before deleting'
        ' the page on the server. List will show all configured servers.')
    readline.add_argument(
        'page', metavar='<page>',
        help='The page with which to work. This is not required for the "list"'
        ' command.')
    option = readline.parse_args()
    c = PmConfig(option.server)
    if option.keep:
        c.keep = True
    if option.author:
        c.author = option.author

    if option.command == 'list':
        print('Configured servers:')
        print()
        for server in c.servers:
            print(server)
        sys.exit(0)

    page = PmPage(c, option.page)

    # Password management
    if option.nopass:
        c.password = None
    elif not c.password:
        c.password = getpass('Password for ' + c.author + ': ')

    # Command management
    if option.command == 'push':
        page.push(fromfile=True)

    elif option.command == 'delete':
        page.delete()

    else:
        old = page.pull()
        if option.command == 'pull':
            log('Saved to', page.cache(old))
        else:
            new = page.edit(c.editor, old)

    if option.browse:
        cmd = '%s %s' % (c.browser, page.url)
        os.system(cmd)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        fatal('User terminated program via keyboard')
