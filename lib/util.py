import git
import os

#add another comment

def find_branch(repo, branch, create=False):
    for x in repo.branches:
        if x.name == branch:
            return x
    if create:
        return repo.create_head(branch)
    else:
        return None

# Note this should be called from a contextualized place,
# and as a result, there is no need to put a bunch of target
# crap in here.
def pull_file(repo, source, target, fname):
    '''repo is a repository. that repositories currently checked out
    branch is the target. source is the name of a repo where the file
    designated by fname comes from'''

    source = find_branch(repo, source)
    target = find_branch(repo, target)
    if not (source or target):
        raise Exception("foo")

    #idx = git.index.IndexFile(repo, file_path='/tmp/gitn')
    idx = git.index.IndexFile.from_tree(repo, target.commit.tree)
    idx.add([source.commit.tree[fname]])
    t = idx.write_tree()
    c = git.Commit.create_from_tree(repo, t,
            "pulling file: %s to %s from %s" % (fname, target.name, source.name),
            parent_commits=(source.commit, target.commit)
            )
    target.set_commit(c)
    del idx
    #os.unlink('/tmp/gitn')
    return t

