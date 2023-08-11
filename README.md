# admixbuilder
High-level builder for UCI Admix collection


## how to generate changelog

Use the following command

```bash
auto-changelog
```
By default, a CHANGELOG.md file is generated.
Defaults are specified in the *.auto-changelog* at the git repo top level directory.

Verify created file and remove non-essential commits, specificaly for files
that are no longer part of the repo. commit the resulting CHANGELOG.md.

For the followup execution of the command can generate
starting from a specific tag and forward output in a separate file:

```bash
auto-changelog --starting-version 2.0 -o ADD.md
```

In addition, the following line in CHANGELOG.md will instruct
auto-changelog to add new data above this line without overwriting
the previous contents:

```html
<!-- auto-changelog-above -->
```
