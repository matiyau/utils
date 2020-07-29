#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 28 01:31:03 2020

@author: matiyau
"""

import argparse
import os

def get_find_args(rel_path):
    """
    get_find_args(rel_path)

    Get the argument to be inserted to the find command so as to exclude
    the given path from search

    Parameters
    ----------
    rel_path : str
        Path of directory/file

    Returns
    -------
    str
        Argument for find command

    """
    return " ! \\( -path " + str(os.path.join(".", rel_path)) + " -prune \\)"


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
                    rm_child_list = [os.path.join(comp, child)
                                     for child in rm_child_list]
                    rm_list.extend(rm_child_list)
    return rm_list


def filt(src_paths, dst_repo=None, dst_branch=None, bkp_repo=True):
    """
    filt(src_paths, dst_repo, dst_branch, bkp_repo=True)

    Filter out specified files from the commit history and export the filtered
    history to a new repo, if specified

    Parameters
    ----------
    src_paths : list of str
        Paths of source files/directories

    dst_repo : str or None, optional
        Destination remote repo URL. If not specified, migration
        branch will not be pushed

    dst_branch : str or None, optional
        Destination branch on the remote repo. If not specified, master
        branch will not be considered

    bkp_repo : bool, optional
        If True, entire repo will be backed up to a different folder before
        proceeding

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

    if (dst_branch is None):
        dst_branch="master"
    src_branch = os.popen("git branch --show-current").read().strip("\n")

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

    find_cmd_pre = "find analytics . "
    # rem_empty_cmd = "git filter-branch -f --prune-empty -- --all"
    rm_list = get_rm_list(cwd, path_tree)

    return rm_list


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate Specified Files "
                                     "From The Specified Branch To The Given "
                                     "Remote Repository")
    parser.add_argument('-sb', required=True,
                        help="<Required> Source Branch")
    parser.add_argument("-sp", nargs="+", required=True,
                        help="<Required> Source Paths")
    parser.add_argument('-dr', default=None,
                        help="Destination Remote Repository")
    parser.add_argument("-db", default=None,
                        help="Destination Branch")
    parser.add_argument("-mb", default=None,
                        help="Migration branch")
    args = parser.parse_args()
    migrate(args.sb, args.sp, args.dr, args.db, args.mb)