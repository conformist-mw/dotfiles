# dotfiles

### Used packages

[Starship](https://starship.rs)

[diff-so-fancy](https://github.com/so-fancy/diff-so-fancy)

- save `lib/`, `diff-so-fancy` to the `~/.local/bin`

##### Font

[FiraMono Nerd Font](https://www.nerdfonts.com/font-downloads)

1. download font
2. unzip
3. mv font_dir /usr/local/share/fonts
4. fc-cache -f -v

###### Installation:

```shell
git clone https://github.com/magicmonty/bash-git-prompt.git ~/.bash-git-prompt --depth=1
```

- [GNU's source-highlight](http://www.gnu.org/software/src-highlite/source-highlight.html#Using-source_002dhighlight-with-less)

###### Installation:

```shell
sudo apt install libsource-highlight-common source-highlight
dpkg -L libsource-highlight-common | grep lesspipe
# /usr/share/source-highlight/src-hilite-lesspipe.sh
```

#### Sublime-text

To easily create a project settings file, you need to create an venv first:

```shell
mkvirtualenv venv-name -a /abspath/to/project
cp /path/to/template.sublime-project /abspath/to/project
sed -i "s%PYTHON_INTERPRETER%`which python`%g" template.sublime-project
sed -i "s%PROJECT_PATH%`pwd`%g" template.sublime-project
mv template.sublime-project project-name.sublime-project
```

Also do not forget to add this directory to gitignore

##### tmux configuration

Check [.tmux](https://github.com/gpakosz/.tmux) project.

