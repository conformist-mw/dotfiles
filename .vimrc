set number
set nocompatible              " be iMproved, required
filetype off                  " required

set rtp+=~/.vim/bundle/Vundle.vim
call vundle#begin()

Plugin 'VundleVim/Vundle.vim'
Plugin 'tpope/vim-fugitive'
Plugin 'git://git.wincent.com/command-t.git'
Plugin 'rstacruz/sparkup', {'rtp': 'vim/'}
Plugin 'wakatime/vim-wakatime'
Plugin 'vim-airline/vim-airline'
Plugin 'rakr/vim-one'
Plugin 'preservim/nerdtree'
call vundle#end()            " required

filetype plugin indent on    " required
set laststatus=2
set tabstop=2 shiftwidth=2 expandtab
let g:airline_theme='one'
let g:airline_powerline_fonts = 1
colorscheme one
set background=light

autocmd VimEnter * NERDTree | wincmd p
autocmd BufEnter * if tabpagenr('$') == 1 && winnr('$') == 1 && exists('b:NERDTree') && b:NERDTree.isTabTree() |
    \ quit | endif
nnoremap <leader>n :NERDTreeFocus<CR>
nnoremap <C-n> :NERDTree<CR>
nnoremap <C-t> :NERDTreeToggle<CR>
nnoremap <C-f> :NERDTreeFind<CR>
