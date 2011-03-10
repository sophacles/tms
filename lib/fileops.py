from git import Repo
import git
from os.path import join as J
import os
from util import find_branch
import time

#def contextualize(f):
#    f.contextualize = True
#    return f

class BranchingError(Exception): pass


class contextualize(object):
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, klass=None):
        def newf(*args, **kw):

            # general stuff here: Im setting a new context for this, because
            # it allows a bunch of parameters taht always do the same thing
            # to extist consistently, and regular decorating doesn't quite cut
            # it, so...

            #########WARNING#############
            # Warning: this function does a lot, and im not currently sure of
            # how to keep it small, not crufty, factored, etc. hopefully
            # something will become apparent in the near futuer
            #############################

            oldctx = dict()

            # Set up th context.

            # always allow per-user branch parameters

            newbranch = kw.pop('user', False)
            if newbranch:
                oldctx['branch'] = obj.branch
                obj.branch = newbranch


            obj.commit_message = kw.pop("message",
                    "No commit message provided by user")

            # do actual work (anything that can error or otherwise mess up state
            try:
                # note: the branch may be created by this
                x = find_branch(obj.repo, obj.branch, obj._create_branches)
                if not x:
                    raise BranchingError("Branch %s does not exist, it must be"
                            "explicitly created" % (obj.branch,))
                else:
                    x.checkout()

                # magic! we have f as a function via the construct/decorator
                # call, but we need to access it as a method. fortunately the
                # way __get__ works for functions allwoas us to do this...
                # put another way, we trampoline a bunch to have this work right,
                # but we get some real magic so it's worth it
                res = self.f.__get__(obj)(*args, **kw)

            finally: # always cleanup the context
                for varname in oldctx:
                    setattr(obj, varname, oldctx[varname])

                # From this point forward, all values are the original values
                # entering the context

                # Checkout the main branch
                find_branch(obj.repo, obj.branch).checkout()

            return res
        return newf

    def __set__(self, obj, value):
        raise AttributeError("Can't override contextual function on %s object" %
                (type(obj),))

class DocStore(object):
    def __init__(self, repo_path="/tmp/foo", file_prefix="files/", create_branches=True):
        self.repo_path = repo_path
        self.file_prefix = file_prefix
        self.branch = 'master'
        self.set_repo(repo_path)

        # internal variables
        self._create_branches = create_branches

    # def __getattribute__(self, attr):
    #     a = super(DocStore, self).__getattribute__(attr)
    #     if callable(a) and hasattr(a, 'contextualize'):
    #         return self.__context(a)
    #     else:
    #         return a

    def make_repo(self):
        try:
            os.makedirs(self.repo_path)
        except OSError, e:
            if e.errno == 17:
                pass
            else:
                raise
        self.repo = Repo.init(self.repo_path)
        for d in ['files/', 'scripts/']:
            os.makedirs(J(self.repo_path, d))
        fd = open(J(self.repo_path, 'created'), 'w')
        fd.write("Created on %s\n" %(time.ctime(),))
        fd.close()
        self.repo.index.add(['created'])
        self.repo.index.commit("initialized the repo")

    def set_repo(self, path):
        self.repo_path = path
        try:
            self.repo = Repo(self.repo_path)
        except (git.NoSuchPathError, git.InvalidGitRepositoryError), e:
            print "got error in set_repo: %s" %(e,)
            self.make_repo()
        files = J(self.repo.working_dir, self.file_prefix)
        if not os.path.exists(files) and not os.path.isdir(files):
            os.mkdir(files)


    @contextualize
    def get_file(self, name):
        real_path = J(self.repo.working_dir, self.file_prefix, name)
        if os.path.exists(real_path) and os.path.isfile(real_path):
            return open(real_path, 'r').read()
        else:
            return None

    @contextualize
    def write_file(self, fname, data):
        r = self.repo
        f = file(J(r.working_dir, self.file_prefix, fname), 'w')
        f.write(data + '\n' + self.branch + "\n")
        f.close()
        r.index.add([f.name])
        r.index.commit(self.commit_message)

    @contextualize
    def stage_to(self, target, fname):
        '''NOTE: despite being called "stage_to" this method is simply
        push, but a bit more workflow oriented'''


    @contextualize
    def delete_file(self, x):
        pass

    @contextualize
    def revert_file(self, x):
        pass

