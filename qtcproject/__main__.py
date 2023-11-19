#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Console script for qtc-project."""

import click
import os.path
import glob
import pathlib
import fnmatch
import re
import pathspec
from typing import List


@click.group()
def main():
    pass


@main.command()
def create():
    """Create a general QtCreator project"""
    proj_dir = os.path.normpath(os.path.realpath(os.curdir))
    proj_name = os.path.basename(proj_dir)
    proj_file = os.path.join(proj_dir, f"{proj_name}.creator")
    if os.path.exists(proj_file):
        raise click.UsageError(f"Project '{proj_name}' already exists!")

    files = [
        ("cflags", "-std=c17\n"),
        ("cxxflags", "-std=c++17\n"),
        (
            "config",
            "// Add predefined macros for your project here. For example:\n"
            "// #define THE_ANSWER 42\n",
        ),
        ("includes", ""),
        ("files", ""),
        ("creator", "[General]\n"),
    ]

    for fext, content in files:
        fname = f"{proj_name}.{fext}"
        fpath = os.path.join(proj_dir, fname)
        click.echo(f"Creating: {fname}")
        with open(fpath, "w") as f:
            f.write(content)


@main.command()
def update():
    """Update project includes & files"""

    project_fpathes = glob.glob(os.path.join(os.curdir, "*.files"))
    if len(project_fpathes) <= 0:
        print("No QtCreator generic project found!")
        return -1

    if len(project_fpathes) >= 2:
        print(
            "Found more than one QtCreator generic project: %s"
            % project_fpathes
        )
        return -2

    files_fpath = project_fpathes[0]
    project_name = os.path.splitext(os.path.basename(files_fpath))[0]
    project_dir = os.path.realpath(
        os.path.normpath(os.path.dirname(files_fpath))
    )
    project_prefix_fpath = os.path.join(project_dir, project_name)

    print("Updating project: %s" % project_name)

    # Search project files
    lines = []
    gitignores_fpath = os.path.join(project_dir, ".gitignore")
    if os.path.exists(gitignores_fpath):
        with open(gitignores_fpath, "r") as f:
            lines.extend(f.readlines())

    qtcignores_fpath = os.path.join(project_dir, f"{project_name}.gitignore")
    if os.path.exists(qtcignores_fpath):
        with open(qtcignores_fpath, "r") as f:
            lines.extend(f.readlines())

    lines.extend(
        [
            ".git",
            ".svn",
            "CVS",
            ".hg",
            ".qtc_clangd",
            "CMakeFiles",
            ".vscode",
            ".idea",
            "__pycache__",
            "*.egg-info",
            ".eggs",
        ]
    )
    spec = pathspec.PathSpec.from_lines("gitwildmatch", lines)

    with open(files_fpath, "w", encoding="utf-8") as files_file:
        hdr_paths = []
        for root, dirs, files in os.walk(project_dir):
            for fname in files:
                fpath = pathlib.Path(os.path.join(root, fname))
                fpath_rel = fpath.relative_to(project_dir)
                if not spec.match_file(fpath_rel):
                    files_file.write(str(fpath_rel).replace("\\", "/"))
                    files_file.write("\n")

            dir_removes = []
            for adir in dirs:
                fpath = pathlib.Path(os.path.join(root, adir))
                fpath_rel = fpath.relative_to(project_dir)
                if spec.match_file(fpath_rel):
                    dir_removes.append(adir)
                else:
                    hdr_paths.append(str(fpath_rel).replace("\\", "/"))

            for adir in dir_removes:
                dirs.remove(adir)

        includes_fpath = "%s.includes" % project_prefix_fpath
        content = ""
        if os.path.exists(includes_fpath):
            with open(includes_fpath, "r", encoding="utf-8") as f:
                content = f.read().strip()

        with open(includes_fpath, "w", encoding="utf-8") as hdr_file:
            tag_begin = "# QTC_PROJECT_BEGIN"
            tag_end = "# QTC_PROJECT_END"

            new_content = "%s\n%s\n%s\n" % (
                tag_begin,
                "\n".join(hdr_paths),
                tag_end,
            )
            new_content = new_content.strip()

            if content.find(tag_begin) >= 0:
                modified_content = re.sub(
                    r"%s.*%s" % (tag_begin, tag_end),
                    new_content,
                    content,
                    flags=re.DOTALL | re.MULTILINE,
                )
                hdr_file.write(modified_content)
                hdr_file.write("\n")
            else:
                hdr_file.write(new_content)


if __name__ == "__main__":
    # execute only if run as a script
    main()
