UXS_HOME_DIR="@UXS_HOME_DIR@"
UXS_RC_DIR="$HOME/@UXS_RC_DIR_NAME@"
PYTHON_EXECUTABLE="@PYTHON_EXECUTABLE@"
function shelf {
    typeset _filename
    typeset _tmpdir=${TMPDIR:-/tmp}
    unset _filename
    while [[ -f ${_filename:="$_tmpdir/bash.$$.$RANDOM"} ]] ; do
        unset _filename
    done
    env UXS_TARGET_TRANSLATOR="bash:${_filename}" PYTHONPATH="${PYTHONPATH}:${UXS_HOME_DIR}/lib/python" ${UXS_HOME_DIR}/bin/shelf "$@"
    if [[ -f ${_filename} ]] ; then
        #echo "---> $_filename"
        #cat "$_filename"
        . "$_filename"
    fi
}

# set bash completion file:
bash_completion_file=${UXS_RC_DIR}/bash_completion.shelf
if [[ ! -f ${UXS_RC_DIR}/bash_completion.shelf ]] ; then
    export UXS_ENABLE_BASH_COMPLETION_OPTION=True
    shelf bash_completion "$bash_completion_file"
    unset UXS_ENABLE_BASH_COMPLETION_OPTION
fi
if [[ -f ${bash_completion_file} ]] ; then
    . ${bash_completion_file}
fi
unset bash_completion_file
