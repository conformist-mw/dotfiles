# dotfiles

### Used packages

- [GIT prompt bash](https://github.com/magicmonty/bash-git-prompt)

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
