# Notes

## Font

 * Vegur (`nixpkgs.vegur`)

## What to replace?

 * `%NAME0%` → full names
 * `%NICK0%` → nicknames
 * `%IMAGE0%` → avatars

The indices go from one (1) to ten (10); yes, I'm mad.


## Making sure the image is 1024x1024

```
convert in.png -thumbnail 1024x1024^ -gravity center -extent 1024x1024 out.1024.png
```

## Exporting

```
inkscape --export-pdf=out.pdf badge-herma-9011.svg
```

## Script
`generate_badges.py` is a script consuming a Eventbrite "Attendee Summary" (CSV
format) from `members.csv`.

It downloads attendees github avatar images, updates the SVG as described
above (also removing the avatar space if no avatar found), and finally
concatenates pages together into a `out.pdf` file for easy printing

It doesn't resize images with imagemagick as described above, seems this was
not necessary.
