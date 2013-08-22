UXS_HOME_DIR="@UXS_HOME_DIR@"
PYTHON_EXECUTABLE="@PYTHON_EXECUTABLE@"
function uxs {
    typeset _filename
    typeset _tmpdir=${TMPDIR:-/tmp}
    unset _filename
    while [[ -f ${_filename:="$_tmpdir/bash.$$.$RANDOM"} ]] ; do
        unset _filename
    done
    env UXS_TARGET_TRANSLATOR="bash:${_filename}" PYTHONPATH="${PYTHONPATH}:${UXS_HOME_DIR}/lib/python" ${UXS_HOME_DIR}/bin/session "$@"
    if [[ -f ${_filename} ]] ; then
        #echo "---> $_filename"
        #cat "$_filename"
        . "$_filename"
    fi
}
