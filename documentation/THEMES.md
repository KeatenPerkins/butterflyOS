# ButterflyOS themes

From v1.0.4, ButterflyOS includes a selectable **ButterflyOS White** theme alongside
the original `es-theme-butterflyos` theme.

Open **User Interface Settings → Theme Set** and choose **ButterflyOS White**.
The frontend reloads the theme after applying the selection. Select
the original theme to return to its appearance. Packaged defaults may appear
as `system-theme` in the selector (the link to `es-theme-butterflyos`).

White keeps the original layout, scaling, colors and artwork, removes the large
butterfly branding image above the home carousel, and uses white outlines for
Games, Tools, Media, Favorites, Settings and the game-art frame. Butterfly
details drawn inside individual artwork, such as the Tools toolbox, remain.
Custom tools have their own presentation and are not changed by this theme.

Both packaged themes appear automatically on fresh installations and normal updates.

## Make your own theme

The easiest starting point is a **complete copy of an installed theme**. It
already contains the correct layout and all the console artwork. You do not
need to build the OS to edit or install a theme.

Custom themes go in:

```text
/storage/.config/emulationstation/themes/My Theme/
```

Use a unique folder name. Its name becomes the entry in **Theme Set**. Keep
`theme.xml` directly inside that folder; an extra folder level will prevent
discovery. The packaged themes in `/usr/share/themes` are read-only defaults.
Custom copies in `/storage` are retained by normal OS updates; reflashing a
card can erase them, so keep a PC backup.

For users comfortable with SSH, these commands create a working starting copy:

```sh
mkdir -p "/storage/.config/emulationstation/themes/My Theme"
cp -a /usr/share/themes/es-theme-butterflyos/. "/storage/.config/emulationstation/themes/My Theme/"
```

To start from White instead, use `/usr/share/themes/ButterflyOS White/.` as the
source after installing a build that includes it. Both are complete installed
themes. The repository's `white-files` directory contains only overrides and
cannot be installed by itself.

Use an SFTP client to download your custom folder to your PC, edit it, and
upload the changed files back. See [file-transfer instructions](TRANSFERRING_GAMES.md).
Enable showing hidden folders if `.config` does not appear. Leave the original
default theme available as a recovery option.

The folder should look like this:

```text
My Theme/
  theme.xml
  assets/
    background.svg
    card.png
    butterflyos-logo.png
    menu/
      games.png
      tools.png
      media.png
      auto-favorites.png
      settings-card.png
    systems/
      gba.png
      snes.png
      ...
```

After uploading, reopen **User Interface Settings → Theme Set**. Restart
EmulationStation, or reboot normally, if the new folder is not listed. Select
your theme and apply the settings. When editing an already-selected theme,
switch to the default and back, or restart the frontend, to reload cached images.

## Replace images without changing the layout

Use **PNG with transparency** for replacement artwork. Preserve the existing
canvas size and filename for the simplest drop-in replacement. Transparent
padding affects how large the subject looks: center the artwork on the canvas
and avoid large empty margins unless you want it to look smaller.

| What you want to replace | File inside your theme | Current canvas / recommendation |
| --- | --- | --- |
| Games home card | `assets/menu/games.png` | 320 × 480 PNG |
| Tools home card | `assets/menu/tools.png` | 320 × 480 PNG |
| Media home card | `assets/menu/media.png` | 320 × 480 PNG |
| Favorites home card | `assets/menu/auto-favorites.png` | 320 × 480 PNG |
| Settings home card | `assets/menu/settings-card.png` | 320 × 480 PNG |
| Console/system art | `assets/systems/<system>.png`, for example `gba.png` | GBA uses 384 × 256; preserve the particular file's dimensions and aspect ratio |
| Fallback system art | `assets/systems/_default.png` | Preserve its existing dimensions |
| Frame behind game cover art | `assets/card.png` | 640 × 640 PNG; artwork is drawn over this frame |
| Butterfly branding above the home carousel | `assets/butterflyos-logo.png` | Current source is 1448 × 1086; transparent PNG with the same aspect ratio |
| Background | `assets/background.svg` | SVG with a 640 × 480 viewBox; or change its XML path to a 640 × 480 PNG |
| Settings dialog panel | `assets/menu-panel.svg` | Preserve its geometry; panel tint comes from XML |

The five home-card PNGs include their frame, illustration and label. Replacing
one replaces the whole card. They are distinct from illustration inputs such
as `tools-main.png` and `settings.png`. Editing an illustration input alone does
not regenerate its visible card PNG.

The system identifier comes from EmulationStation's system theme name, not the
display label. Keep the existing filename; inspect `assets/systems` to find the
one to replace. Some aliases, such as Mega Drive, may be symlinks to another
system's image. Editing their shared target changes both; replace an alias
with a separate image if you want different artwork.

The logo paths in `theme.xml` are tried in order. A system image can be
overridden by a matching menu SVG, then menu PNG, then `-card.png`. This is why
Settings uses `settings-card.png` rather than its large illustration input.

Individual game cover art is loaded from each game's metadata through
`{game:image}`. Changing the theme's `card.png` changes its surrounding frame,
not the user's scraped cover art.

## Change colors in theme.xml

Edit XML in a plain-text editor. Theme XML colors use **eight hexadecimal
digits: RRGGBBAA**. For example, `ffffffff` is opaque white, `000000ff` is opaque
black, and `00000000` is transparent. SVG colors use their own syntax, usually
`#RRGGBB`, with separate opacity attributes.

Find these elements by their names rather than relying on line numbers:

| Area | XML element | Properties to edit |
| --- | --- | --- |
| Settings background | `menuBackground name="menubg"` | `color` and `centerColor`; keep equal for a uniform panel |
| Settings title | `menuText name="menutitle"` | `color` |
| Settings rows | `menuText name="menutext"` | `color`, `selectedColor`, `selectorColor`, `selectorColorEnd` |
| Small settings descriptions | `menuTextSmall name="menutextsmall"` | `color` |
| Settings group headings | `menuGroup name="menugroup"` | `color`, `backgroundColor`, `separatorColor` |
| Game list | `textlist name="gamelist"` | `primaryColor`, `secondaryColor`, `selectedColor`, `selectorColor` |
| Scrollbars | Relevant list or background element | `scrollbarColor` |
| Console title | `text name="logoText"` | `color` |
| Clock and battery | `clock` and `batteryIndicator` in the `screen` view | `color` |
| Bottom button labels | `start-menu-hint-label`, `select-menu-hint-label`, `search-button-hint-label`, `favorite-button-hint-label` | `color` |

For example, replace both selection colors in `menutext` to make its selection
bar solid gray:

```xml
<selectorColor>404040ff</selectorColor>
<selectorColorEnd>404040ff</selectorColorEnd>
```

The home-card outlines are drawn into image assets. Changing XML text colors
will not recolor them. Edit the corresponding SVG source and export it to the
PNG the theme displays, or use the White variant's existing cards.

## Fonts, position and scaling

The `variables` section defines `fontRegular` and `fontBold`. To bundle your
own font, place an appropriately licensed `.ttf` file in `assets/fonts` and
change the variable, for example:

```xml
<fontRegular>./assets/fonts/MyFont-Regular.ttf</fontRegular>
```

The current UI uses proportional coordinates: `pos` controls position, `size`
controls bounds, and `origin` controls the anchor. A value of `0.5` represents
half the available dimension. `maxSize` fits an image within bounds while
preserving its aspect ratio. `fontSize` is proportional to screen height;
`zIndex` controls drawing order. Keep the existing values if you want the same
layout and scaling. Some properties have component-specific meanings; for
example, the current menu panel's `cornerSize` is measured in texture pixels.

To remove the large butterfly branding, remove the complete
`<image name="butterfly-brand" extra="true"> ... </image>` element from the
`system` view, as White does. This does not remove butterflies drawn into other
artwork.

## Check your theme

1. Check every home destination, particularly selected and unselected cards.
2. Check a console with short names and one with long names.
3. Check game lists with and without cover art and long game titles.
4. Open settings dialogs and the save-state manager; check text contrast,
   selection visibility and clipping.
5. Check clock, battery and bottom control hints. If available, also check HDMI
   at a wider resolution.
6. Reboot normally and confirm the theme remains selected.

If something breaks, select `es-theme-butterflyos`, fix your custom copy, and
try again. Do not delete the currently selected custom folder before switching
back to the default. Keep a working copy on your PC before large edits.

## Limits

This guide covers the EmulationStation theme: the home carousel, system/game
lists and theme-aware menus. The save-state manager uses some menu colors and
fonts, but its layout remains implemented in code. Blink and the other
custom tool applications have their own styling. SSH branding and the boot
splash are also separate from the selectable frontend theme.

Theme files do not change button mappings, emulator performance or supported
systems. Themes written for other EmulationStation variants may use unsupported
properties; start from ButterflyOS's installed theme for predictable results.

## Source assets

The base lives in `projects/ROCKNIX/packages/ui/themes/es-theme-butterflyos/files`.
The variant's overrides live in that package's `white-files` directory. Its
installer copies the base and overlays only the variant files, keeping the
default theme intact. Both are installed below `/usr/share/themes`.

`python3 tools/theme/build-white-variant.py` regenerates the variant from the
original XML and SVG sources. It requires `rsvg-convert` on the development PC;
the device and OS build use the already-generated assets. It preserves PNG
dimensions and original artwork while changing vector outlines to white.

When changing base layout or artwork, regenerate the variant before building.
