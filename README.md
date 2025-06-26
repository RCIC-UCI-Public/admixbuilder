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

## dependency graphs

Need ``dot`` command provided by graphviz RPM.

```bash
yum install graphviz
```

## Makefile targets

A list of targets that are used for making graphs, info files
for the ansible repo and for the website.

depinfo.yaml:
  In each <admix>/yamlspecs/ scan packages yaml files and
  create packages dependency info **depinfo.yaml** file.

dot: depinfo.yaml
   Using  obtained dependency info create dependency dot files for  making graphs.

dotpdf:
   From raw dot file create PDF format.

dotpng:
   From raw dot file create PNG format .

histogram:
  Uses admix build log files and extracts lines for begining and end of each package build
  into a file. Use ``plotHist`` on the file to create a **histogram.png** of build times.

ansible:
  For each admix  create a yaml file to add to the ansible repo  in applications role.

swtable:
  For each admix create information about packages and collate all into **sw.csv** file.
  The file is used for the website (loaded as a table)
