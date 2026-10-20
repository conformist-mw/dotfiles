-- WezTerm config. Reloads automatically on save.
-- Docs: https://wezfurlong.org/wezterm/config/files.html
local wezterm = require 'wezterm'
local act = wezterm.action
local config = wezterm.config_builder()

-- Same look as the old kitty setup: gruvbox dark, FiraCode Nerd Font Mono 12.
-- Other popular built-in schemes: 'Catppuccin Mocha', 'Tokyo Night'.
config.color_scheme = 'GruvboxDark'
-- The external monitor runs at 1x (no Retina), where wezterm's FreeType renders
-- Regular too thin. Fira Code's Retina weight (450) is made for exactly this,
-- and Light hinting keeps the glyph shapes closer to macOS-native rendering.
config.font = wezterm.font('FiraCode Nerd Font Mono', { weight = 450 })
config.font_size = 12
config.freetype_load_target = 'Light'

-- I-beam cursor, no blinking
config.default_cursor_style = 'SteadyBar'

config.window_padding = { left = 8, right = 8, top = 6, bottom = 6 }
config.initial_cols = 140
config.initial_rows = 40
-- Tabs live in the title bar next to the traffic lights
config.window_decorations = 'INTEGRATED_BUTTONS|RESIZE'
config.window_frame = { font_size = 12 }
-- Dim the panes that don't have focus
config.inactive_pane_hsb = { saturation = 0.9, brightness = 0.7 }

config.scrollback_lines = 25000
config.audible_bell = 'Disabled'

-- Match shortcuts by physical key, so cmd+c/v/t/w still work on the Russian layout
config.key_map_preference = 'Physical'

config.keys = {
  -- iTerm-style splits
  { key = 'd', mods = 'CMD', action = act.SplitHorizontal { domain = 'CurrentPaneDomain' } },
  { key = 'd', mods = 'CMD|SHIFT', action = act.SplitVertical { domain = 'CurrentPaneDomain' } },
  -- cmd+w closes the pane, not the whole tab
  { key = 'w', mods = 'CMD', action = act.CloseCurrentPane { confirm = true } },
  { key = 'LeftArrow', mods = 'CMD|OPT', action = act.ActivatePaneDirection 'Left' },
  { key = 'RightArrow', mods = 'CMD|OPT', action = act.ActivatePaneDirection 'Right' },
  { key = 'UpArrow', mods = 'CMD|OPT', action = act.ActivatePaneDirection 'Up' },
  { key = 'DownArrow', mods = 'CMD|OPT', action = act.ActivatePaneDirection 'Down' },
  -- Zoom the current pane to full tab and back
  { key = 'Enter', mods = 'CMD|SHIFT', action = act.TogglePaneZoomState },
}

return config
