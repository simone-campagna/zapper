UXS_HOME_DIR="@UXS_HOME_DIR@"
UXS_RC_DIR="$HOME/@UXS_RC_DIR_NAME@"
PYTHON_EXECUTABLE="@PYTHON_EXECUTABLE@"
UXS_REQUIRED_COMPLETION_VERSION="@UXS_COMPLETION_VERSION@"

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
bash_completion_file="${UXS_RC_DIR}/completion.bash"
bash_completion_version_file="${bash_completion_file}.version"
if [[ ! -f ${bash_completion_version_file} ]] ; then
    rm -f "$bash_completion_file"
else
    . "$bash_completion_version_file"
    if [[ $UXS_CURRENT_COMPLETION_VERSION != $UXS_REQUIRED_COMPLETION_VERSION ]] ; then
        rm -f "$bash_completion_version_file"
        rm -f "$bash_completion_file"
    fi
fi
unset UXS_CURRENT_COMPLETION_VERSION
if [[ ! -f ${bash_completion_file} ]] ; then
    shelf completion "$bash_completion_file"
fi
if [[ -f ${bash_completion_file} ]] ; then
    . ${bash_completion_file}
fi
unset bash_completion_file

env UXS_QUIET_MODE=True shelf session update --quiet
