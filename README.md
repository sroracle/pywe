## FAQ

**Q: I would like to edit PmWiki pages using my favorite text editor.**

A: The Python-based PmWiki Editor is a program intended to serve as an intermediary between your editor and the PmWiki page you want to edit. It was originally written to support vim. However, it should work with any text editor.
If you use Emacs, please consider the Emacs PmWiki Mode as it was designed with Emacs in mind. Not that this recipe slights Emacs, but that recipe may provide a better solution for your Emacs-need.
In case you're wondering, as of October 2010; this script is still in use and working fine.

## Background

Scott Duff wrote a program called pmwikiedit, a Perl-based application that retrieves source from a Pmwiki site, allows the individual to edit the source using his favorite text editor, then repost the amended content back to the web server. I used that program greatly in the beginning, but when PmWiki v.2.0 came along, I found increasing difficulty with its use.
Recently, I wanted to edit pages using vim like I used to when pmwikiedit worked. I also was working on my Python skills. As I am prone to doing, when trying to master a new language, I wrote this program from scratch in Python. I also sought to introduce various features that I found interesting to have. Pywe is a Python-based wiki-editor that allows the user to edit PmWiki pages using his preferred text editor.

## Files

* [main.py](main.py): the main application.
* [pywe.ini](pywe.ini): a sample configuration file for Pywe. You must modify this file and move it to `~/.config` to run the script.
* [syntax.vim](syntax.vim): a vim syntax file for PmWiki's syntax. Move it to `~/.vim/syntax/pmwiki.vim`.
* [ftdetect.vim](ftdetect.vim): a vim file that will activate the above file for all buffers ending in `.pmwiki`. Move it to `~/.vim/ftdetect/pmwiki.vim`.

## Usage

`pywe [options] <command> Group.Pagename[.pmwiki]`

## Commands
<dl>
<dt>push</dt>
<dd>Send the given page to the server.</dd>
<dt>pull</dt>
<dd>Retrieve the given page.</dd>
<dt>edit</dt>
<dd>Pull the page, open it in the configured editor, then push the changes.</dd>
<dt>delete</dt>
<dd>Confirm before deleting the given page remotely.</dd>
</dl>

## Options

<dl>
<dt>-a AUTHOR, --author AUTHOR</dt>
<dd>sets author's name from the command line</dd>
<dt>-b, --browse</dt>
<dd>after edit, load the page in the configured browser</dd>
<dt>-h, --help</dt>
<dd>show this help message and exit</dd>
<dt>-k, --keep</dt>
<dd>retain local copy of page source after edit</dd>
<dt>-n, --nopass</dt>
<dd>explicitly use no password when authenticating</dd>
<dt>-s, --server SERVER</dt>
<dd>Choose the configured server with which to work.</dd>
<dt>--version</dt>
<dd>show program's version number and exit.</dd>
</dl>

**Local File Interface.** Pywe has three primary ways of using local files. First, the push option submits a local text file to the PmWiki page. Second, the keep option keeps a local copy of the wiki page after it is edited by the author. That is, the remote copy is fed into the editor, and the copy submitted to the wiki site is kept as a local copy. Finally, the pull option simply pulls the remote copy and saves as a local copy. This can be used in conjunction with push to allow the author to pull down a copy, edit and repost (although interviening changes would be overwritten). Beyond these three methods, a failed upload should archive the edited copy (similar to keep) locally to allow the author to push the page when the network interference has passed.

**Deleting Pages.** Pywe will allow deleting of pages. When invoked, the delete option will ask the user to confirm deletion by typing the word 'delete,' which is meant to put a person in the process and avoid automated deletions.

## Configuration

The configuration file is an RFC 822 compliant INI file. This allows the user to configure options via a configuration file such that a different set of configurations exists per server. This is represented by the `pywe --server SERVER Group.Pagename` style of usage. The "server" is the section delimiter in the configuration file.

The following configuration options are supported for each server:
<dl>
<dt>api</dt>
<dd>The URL of the pmwiki.php endpoint.</dd>
<dt>url</dt>
<dd>The pretty form of the wiki's URL. $Group and $Name are replaced at runtime. This setting is only used for the --browse option and for messages.</dd>
<dt>defaultgroup</dt>
<dd>The default group to use if none is specified at runtime.</dd>
<dt>defaultpage</dt>
<dd>A default pagename.</dd>
<dt>deleteword</dt>
<dd>The word that deletes a page in PmWiki. This is "delete" by default.</dd>
<dt>keep</dt>
<dd>Whether the author would always like an edited page "kept."</dd>
<dt>author</dt>
<dd>The user name who is editing the page.</dd>
<dt>password</dt>
<dd>The password to use, if one is required.</dd>
<dt>browser</dt>
<dd>The full path to your preferred browser, with options.</dd>
<dt>editor</dt>
<dd>The full path to your preferred editor, with options.</dd>
</dl>

## Issue Tracking

Are you aware of a problem with Pmwe? Submit an issue or a pull request on the [GitHub repository](https://github.com/Merovex/pywe).

## License

This work is licensed under a [Creative Commons Attribution-NoDerivatives 4.0 International](http://creativecommons.org/licenses/by-nd/4.0/) License.

I would rather have one solid copy than various derivatives. If you'd like to contribute, submit a pull request and I'll strongly consider incorporating it.

## Release Notes

* v.1.3.1 August 20, 2015 BenWilson August 20, 2015, at 05:56 AM
** Updated License to CC BY-ND 4.0.
* v.1.3.1 February 9, 2007 BenWilson February 09, 2007, at 09:56 AM
   * Added some authentication testing.
   * Classed error handling.
* v.1.3.0 February 7, 2007 BenWilson February 08, 2007, at 09:50 AM
   * Fixed problem with being unable to delete pages via Pywe.
   * Fixed problem with accidently creating a new page when mistyping the pagename.
   * Added support for the common PmWiki calendar date format.
* v.1.2.0 June 2, 2006 Implemented Injection feature. BenWilson June 02, 2006, at 11:02 PM
* v.1.1.1 May 30, 2006 Fixed broken journal option. BenWilson May 30, 2006, at 05:40 PM
* v.1.1.0 May 29, 2006 Initial Public Release. BenWilson May 29, 2006, at 12:12 PM
