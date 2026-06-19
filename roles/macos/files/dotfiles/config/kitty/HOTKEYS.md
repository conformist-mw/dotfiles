# Kitty — шпаргалка по хоткеям

Иерархия: **OS window** → **tab** (вкладка) → **window** (split/панель внутри вкладки).

## Окно (OS window)
| Хоткей | Действие |
|---|---|
| `Cmd+Ctrl+F` | Toggle нативный macOS fullscreen (отдельный Space, без menu bar) |
| `Cmd+Shift+S` | Открыть новое OS-окно по example-session |
| `Cmd+=` / `Cmd+-` / `Cmd+0` | Размер шрифта +/-/сброс |
| `Ctrl+Shift+Backspace` | Сбросить размер шрифта |

При запуске kitty восстанавливает размер последнего окна (`remember_window_size yes`). Чтобы он всегда открывался во весь экран — один раз разверни окно вручную и закрой.

Альтернатива из CLI: `kitty --start-as=maximized` или `--start-as=fullscreen`.

## Вкладки (tabs)
| Хоткей | Действие |
|---|---|
| `Ctrl+Shift+T` | Новая вкладка |
| `Ctrl+Shift+Q` | Закрыть вкладку |
| `Ctrl+Shift+←` / `→` | Предыдущая / следующая вкладка |
| `Cmd+1` … `Cmd+9` | Перейти на вкладку 1–9 |
| `Cmd+0` | Перейти на последнюю вкладку |
| `Cmd+E` | Интерактивный селектор вкладок |
| `Cmd+Shift+R` | Переименовать вкладку |
| `Cmd+Shift+,` / `Cmd+Shift+.` | Переместить вкладку влево / вправо |

## Splits / windows (мультиплексирование внутри вкладки)
| Хоткей | Действие |
|---|---|
| `Cmd+D` | Вертикальный split (новая колонка справа) |
| `Cmd+Shift+D` | Горизонтальный split (новая строка снизу) |
| `Cmd+W` | Закрыть текущий split |
| `Ctrl+Shift+Enter` | Новый window (по правилам текущего layout) |
| `Cmd+←` / `↓` / `↑` / `→` | Перейти в соседний split |
| `Ctrl+Shift+[` / `Ctrl+Shift+]` | Предыдущий / следующий split |
| `Cmd+Shift+←/↓/↑/→` | Изменить размер split’а |

## Layouts (как располагаются splits)
Доступные: `splits`, `tall`, `fat`, `grid`, `stack`.

| Хоткей | Действие |
|---|---|
| `Cmd+Shift+Space` | Следующий layout |
| `Ctrl+Alt+R` | Layout **tall** (большой слева + стопка справа) |
| `Ctrl+Alt+S` | Layout **stack** (zoom: показан только активный split) |

> Лайфхак: `stack` — аналог `tmux zoom`. Остальные splits живые, просто скрыты.

## Поиск и скроллбэк
| Хоткей | Действие |
|---|---|
| `Cmd+F` | fzf по скроллбэку (быстрый поиск) |
| `Ctrl+F` | Просмотр скроллбэка через `bat` (с подсветкой) |
| `Cmd+Shift+F` | Стандартный `show_scrollback` |

## Полезные оверлеи / интеграции
| Хоткей | Действие |
|---|---|
| `Cmd+O` | Оверлей-окно (новый shell поверх, fullsize) |
| `Cmd+P` | lazygit оверлеем |
| `Cmd+I` | `git difftool` (unstaged) |
| `Cmd+Shift+I` | `git difftool --cached` (staged) |
| `Cmd+G` | SSH в `eugene@192.168.1.24:22122` (новая вкладка) |

## Базовые команды (с фиксом русской раскладки)
Все эти шорткаты работают и в EN, и в RU раскладке — позиции клавиш одинаковые.

| EN | RU | Действие |
|---|---|---|
| `Cmd+C` | `Cmd+С` | Копировать |
| `Cmd+V` | `Cmd+М` | Вставить |
| `Cmd+X` | `Cmd+Ч` | Вырезать |
| `Cmd+A` | `Cmd+Ф` | Выделить всё |
| `Cmd+Z` | `Cmd+Я` | Undo (для интерактивных инпутов) |
| `Cmd+F` | `Cmd+А` | Поиск (fzf) |
| `Cmd+D` | `Cmd+В` | Vsplit |
| `Cmd+W` | `Cmd+Ц` | Закрыть split |
| `Cmd+E` | `Cmd+У` | Селектор вкладок |
| `Cmd+O` | `Cmd+Щ` | Overlay |
| `Cmd+P` | `Cmd+З` | lazygit |
| `Cmd+I` | `Cmd+Ш` | git difftool |
| `Cmd+G` | `Cmd+П` | SSH |
| `Ctrl+Shift+T` | `Ctrl+Shift+Е` | Новая вкладка |
| `Ctrl+Shift+Q` | `Ctrl+Shift+Й` | Закрыть вкладку |
| `Cmd+Shift+R` | `Cmd+Shift+К` | Переименовать вкладку |
| `Cmd+Shift+S` | `Cmd+Shift+Ы` | Загрузить session в новом OS-окне |

> Цифры (`Cmd+1..9`, `Cmd+0`) и стрелки от раскладки не зависят, дублировать не нужно.

## Файлы конфигурации
- `~/.config/kitty/kitty.conf` — основной конфиг
- `~/.config/kitty/quick-access-terminal.conf` — конфиг выпадающего терминала
- `~/.config/kitty/theme.conf` → `kitty-themes/themes/gruvbox_dark.conf`

## Применить изменения
После правок конфига: `Ctrl+Shift+F5` — перезагрузить конфиг без рестарта.
