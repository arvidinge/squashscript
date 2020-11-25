# squashscript
Squashes a range of commits on a Git branch (source) into a new, single commit. The new commit is placed on a complementary (target) review branch (source is unaffected by the operation). This script enables you to view all changes made on the source branch in several commits on a single GitHub commit page, which is handy for reviewing code.

# Usage
python squash.py [-p PATH_TO_REPO] [-b BRANCH_TO_SQUASH] [-c FIRST_COMMITISH_IN_CHANGESET]
