#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 28 01:31:03 2020

@author: matiyau
"""

import argparse
import os


def get_rm_list(dir_path, rel_path_tree):
    """
    get_rm_list(dir_path, rel_path_tree)

    Get the list of files and directories to be removed

    Parameters
    ----------
    dir_path : str
        Path of the parent directory

    rel_path_tree : dict like
        Nested dictionary specifying the path tree

    Returns
    -------
    rm_list : list of str
        List of files paths to be removed from commits

    """
    rm_list = []
    comps = os.listdir(dir_path)
    for comp in comps:
        if comp not in rel_path_tree:
            rm_list.append(comp)
        else:
            child_path = os.path.join(dir_path, comp)
            if os.path.isdir(child_path):
                child_tree = rel_path_tree[comp]
                if bool(child_tree):
                    rm_child_list = get_rm_list(child_path, child_tree)
                    rm_child_list = [str(os.path.join(comp, child))
                                     for child in rm_child_list]
                    rm_list.extend(rm_child_list)
    return rm_list


def filt(src_paths, dst_repo=None, dst_branch=None, bkp=True, force=False):
    """
    filt(src_paths, dst_repo, dst_branch, bkp_repo=True)

    Filter out specified files from the commit history and export the filtered
    history to a new repo, if specified

    Parameters
    ----------
    src_paths : list of str
        Paths of source files/directories

    dst_repo : str or None, optional
        Destination remote repo URL. If not specified, filtered
        branch will not be pushed

    dst_branch : str or None, optional
        Destination branch on the remote repo. If not specified, master
        branch will not be considered

    bkp : bool, optional
        If True, a backup will be created before
        proceeding

    force : bool, optional
        If True, the force option will be used in git commands

    Raises
    ------
    OSError
        If directory is not a git repository

    Returns
    -------
    None

    """
    cwd = os.getcwd()
    if not os.path.exists(os.path.join(cwd, ".git")):
        raise OSError(str(cwd) + " Is Not A Git Repository")

    src_branch = os.popen("git branch --show-current").read().strip("\n")
    print(src_branch)
    if (bkp):
        os.system("git branch -c " + src_branch + " " + src_branch + "_bkp")

    if (force):
        f_flag = " -f"
    else:
        f_flag = ""

    if (dst_branch is None):
        dst_branch="master"

    if (".git" not in src_paths):
        src_paths.append(".git")
    path_tree = {}
    for path in src_paths:
        path_split = path.split(os.sep)
        if ("." in path_split):
            path_split.remove(".")
        if ("" in path_split):
            path_split.remove("")
        sub_tree = path_tree
        for comp in path_split:
            if comp not in sub_tree:
                sub_tree[comp] = {}
            sub_tree = sub_tree[comp]

    rm_cmd_pre = "git rm --cached --ignore-unmatch -r "
    rm_list = get_rm_list(cwd, path_tree)
    rm_cmd = rm_cmd_pre + " ".join(rm_list)
    os.system("git filter-branch" + f_flag +
              " --index-filter '" + rm_cmd +
              "' --tag-name-filter cat -- --all")
    os.system("git filter-branch" + f_flag + " --prune-empty -- --all")

    if (dst_repo is not None):
        os.system("git push" + f_flag + " " + dst_repo + " " + src_branch +
                  ":" + dst_branch)
        tags = os.popen("git tag").read().split("\n")
        if ("" in tags):
            tags.remove("")
        for tag in tags:
            temp = os.popen("git branch --contains '" + tag + "'").read()
            tag_branches = temp.replace("* ", "").replace("  ", "").split("\n")
            if src_branch in tag_branches:
                os.system("git push" + f_flag + " " +
                          dst_repo + " '" + tag + "'")
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate Specified Files "
                                     "From The Current Branch To The Given "
                                     "Remote Repository")
    parser.add_argument("-sp", nargs="+", required=True,
                        help="<Required> Source Paths")
    parser.add_argument('-dr', default=None,
                        help="Destination Remote Repository")
    parser.add_argument("-db", default=None,
                        help="Destination Branch")
    parser.add_argument("-nb", default=True, action='store_false',
                        help="Don't create a backup before proceeding")
    parser.add_argument("-f", default=False, action='store_true',
                        help="Use the force option for git commands")
    args = parser.parse_args()
    filt(args.sp, args.dr, args.db, args.nb, args.f)