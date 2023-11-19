#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Console script for qtc-project."""

import click
import os.path
import glob
import pathlib
import fnmatch
import re
from typing import List


def fnmatch_filter_patterns(names: List[str], patterns: List[str]):
    for name in names:
        for pattern in patterns:
            if fnmatch.fnmatch(name, pattern):
                yield name
                break


@click.group()
def main():
    pass


@main.command()
def create():
    pass


@main.command()
def update():
    project_fpathes = glob.glob(os.path.join(os.curdir, "*.files"))
    if len(project_fpathes) <= 0:
        print("No QtCreator generic project found!")
        return -1

    if len(project_fpathes) >= 2:
        print(
            "Found more than one  QtCreator generic project: %s"
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
    dir_denylist = [
        ".git",
        "CVS",
        ".svn",
        ".hg",
        "CMakeFiles",
        ".vscode",
        ".idea",
    ]
    file_allowlist = [
        "*.h",
        "*.hpp",
        "*.hxx",
        "*.c",
        "*.cpp",
        "*.cxx",
        "*.inl",
        "*.in",
        "*.cmake",
    ]

    with open(files_fpath, "w", encoding="utf-8") as files_file:
        hdr_paths = []
        for root, dirs, files in os.walk(project_dir):
            allow_files = list(fnmatch_filter_patterns(files, file_allowlist))
            for fname in allow_files:
                fpath = pathlib.Path(os.path.join(root, fname))
                fpath = fpath.relative_to(project_dir)

                files_file.write(str(fpath).replace("\\", "/"))
                files_file.write("\n")

            # Remove all directories which matched the pattern in dir_denylist
            deny_dirs = list(fnmatch_filter_patterns(dirs, dir_denylist))
            for adir in deny_dirs:
                dirs.remove(adir)

            hdr_paths.extend(
                map(
                    lambda it: str(
                        pathlib.Path(os.path.join(root, it)).relative_to(
                            project_dir
                        )
                    ).replace("\\", "/"),
                    dirs,
                )
            )

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
