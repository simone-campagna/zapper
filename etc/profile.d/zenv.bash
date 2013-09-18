ZENV_HOME_DIR="@ZENV_HOME_DIR@"
ZENV_RC_DIR="$HOME/@ZENV_RC_DIR_NAME@"
PYTHON_EXECUTABLE="@PYTHON_EXECUTABLE@"
ZENV_REQUIRED_COMPLETION_VERSION="@ZENV_COMPLETION_VERSION@"

function zenv {
    typeset _filename
    typeset _tmpdir=${TMPDIR:-/tmp}
    unset _filename
    while [[ -f ${_filename:="$_tmpdir/bash.$$.$RANDOM"} ]] ; do
        unset _filename
    done
    env ZENV_TARGET_TRANSLATOR="bash:${_filename}" PYTHONPATH="${PYTHONPATH}:${ZENV_HOME_DIR}/lib/python" ${ZENV_HOME_DIR}/bin/zenv "$@"
    if [[ -f ${_filename} ]] ; then
        #echo "---> $_filename"
        #cat "$_filename"
        . "$_filename"
    fi
}

# set bash completion file:
bash_completion_file="${ZENV_RC_DIR}/completion.bash"
bash_completion_version_file="${bash_completion_file}.version"
if [[ ! -f ${bash_completion_version_file} ]] ; then
    rm -f "$bash_completion_file"
else
    . "$bash_completion_version_file"
    if [[ $ZENV_CURRENT_COMPLETION_VERSION != $ZENV_REQUIRED_COMPLETION_VERSION ]] ; then
        rm -f "$bash_completion_version_file"
        rm -f "$bash_completion_file"
    fi
fi
unset ZENV_CURRENT_COMPLETION_VERSION
if [[ ! -f ${bash_completion_file} ]] ; then
    zenv completion "$bash_completion_file"
fi
if [[ -f ${bash_completion_file} ]] ; then
    . ${bash_completion_file}
fi
unset bash_completion_file

# zenv update
export ZENV_QUIET_MODE=True
zenv session update --quiet
unset ZENV_QUIET_MODE
