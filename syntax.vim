" Vim syntax file
" Language: PMWiki
" Maintainer: Ben Wilson <ameen@dausha.net>
" Last Change: 2017-06-30 by sroracle
" Remark: Second version

" Setup
if version >= 600
  if exists("b:current_syntax")
    finish
  endif
else
  syntax clear
endif

" Wiki variables and the like are case sensitive
syntax case match
syntax sync fromstart

" Links
syntax match pmwikiPageName  /\([A-Z][a-z]\+\.\)\?\([A-Z][A-Z0-9]*[a-z0-9]\+\)\{2,}/
syntax match pmwikiPageName  /Attach:[^\t "]\+/
syntax region pmwikiFixFormat start=/\(Attach:[^\t "]\+\)\@<="/ end=/"/ oneline
syntax region pmwikiPageName start=/\[\[/ end=/\]\]/ oneline
syntax region pmwikiCategory start=/\[\[!/ end=/\]\]/ oneline

" Organization
syntax region pmwikiTitle    start=/^!\+ / end=/$/  oneline " Headings
syntax match pmwikiListItem  /^\s*\*\+\s/           " Unordered list
syntax match pmwikiListItem  /^\s*\#\+\s/           " Ordered list
"syntax match pmwikiDefList   /^:/                   " Definition list
syntax match pmwikiSeparator /^----/                " Horizontal rule
syntax match pmwikiBackslash /\\*\s*$/              " Line continuation
syntax match pmwikiBackslash /\[\[<<\]\]/           " Line continuation
syntax match pmwikiIndent    /^-\+>/
syntax match pmwikiTable     /||/

" Text formatting
syntax match pmwikiStrike    /{-.\{-}-}/
syntax region pmwikiFixFormat start=/@@/ end=/@@/ oneline
syntax match pmwikiStrongEM  /'\{5}\('\{2,5}\)\@!.\{-}'\{5}/ " Bold and italic
syntax match pmwikiStrong    /'\{3}\('\{2,5}\)\@!.\{-}'\{3}/ " Bold
syntax match pmwikiEM        /'\{2}\('\{2,5}\)\@!.\{-}'\{2}/ " Italic
syntax region pmwikiDiffSize  start=/\[+/ end=/+\]/ oneline  " Increase Text Size
syntax region pmwikiDiffSize  start=/\[-/ end=/-\]/ oneline  " Decrease Text Size

" Directives
syntax region pmwikiCommand start=/(:/ end=/:)/ oneline
syntax match pmwikiStyle     /%[^%].\{-}\S%/
syntax match pmWikiStyleEnd  /%%/
syntax region pmwikiStyleBlock start=/>>/ end=/<</ oneline

" Nowiki and the like
syntax region pmwikiFixFormat start=/^\(\t\|\s\)\+\S/ end=/$/ oneline
syntax region pmwikiFixFormat start=/\[=/ end=/=\]/
syntax region pmwikiFixFormat start=/\[@/ end=/@\]/
syntax region pmwikiFixFormat start=/(:html:)/ end=/(:htmlend:)/

" Define the default highlighting
if version >= 508 || !exists("did_inittab_syntax_inits")
  if version < 508
    let did_inittab_syntax_inits = 1
    command -nargs=+ HiLink hi link <args>
  else
    command -nargs=+ HiLink hi def link <args>
  endif

  HiLink pmwikiPageNameOld  Identifier
  HiLink pmwikiPageLink     Identifier
  HiLink pmwikiPageName     Identifier
  HiLink pmwikiCategory     Special

  HiLink pmwikiTitle        Statement
  HiLink pmwikiListItem     Comment
  HiLink pmwikiDefList      Comment
  HiLink pmwikiSeparator    Comment
  HiLink pmwikiBackslash    Comment
  HiLink pmwikiIndent       Comment
  HiLink pmwikiTable        Comment

  HiLink pmwikiStrike       Ignore
  HiLink pmwikiStrongEM     Type
  HiLink pmwikiStrong       Type
  HiLink pmwikiEM           Type
  HiLink pmwikiDiffSize     Type

  HiLink pmwikiFixFormat    Constant

  HiLink pmwikiCommand      PreProc
  HiLink pmwikiStyle        PreProc
  HiLink pmwikiStyleEnd     PreProc
  HiLink pmwikiStyleBlock   PreProc


  delcommand HiLink
endif

let b:current_syntax = "pmwiki"
