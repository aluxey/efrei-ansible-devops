#!/bin/bash

PYTHON_REQUIREMENTS_FILE=requirements.txt

download_galaxy () {
  mkdir -p "${CUR_MOL_VENV_DIR}/.ansible/roles" "${CUR_MOL_VENV_DIR}/.ansible/collections"
  ansible-galaxy role install -r "${CUR_MOL_VENV_DIR}/roles/requirements.yml" -p "${CUR_MOL_VENV_DIR}/.ansible/roles" --force
  ansible-galaxy collection install -r "${CUR_MOL_VENV_DIR}/collections/requirements.yml" -p "${CUR_MOL_VENV_DIR}/.ansible/collections" --force
}

setup_env () {
  dir=$(basename "${CUR_MOL_VENV_DIR}")
  venv_path="${CUR_MOL_VENV_DIR}/.virtualenv/${dir}"
  if [[ -f "${venv_path}/bin/activate" ]]
  then
    source "${venv_path}/bin/activate"
  else
    if command -v virtualenv >/dev/null 2>&1
    then
      virtualenv -p "$(command -v python3)" "${venv_path}"
    else
      python3 -m venv "${venv_path}"
    fi
    source "${venv_path}/bin/activate" || { echo "[ERROR] venv activation failed"; return 1; }
    python -m pip install --upgrade pip || { echo "[ERROR] pip upgrade failed"; return 1; }
    python -m pip install -r "${CUR_MOL_VENV_DIR}/${PYTHON_REQUIREMENTS_FILE}" || { echo "[ERROR] pip install failed"; return 1; }
  fi

  _molecule_vagrant_module_path=$(python - <<'PY'
from pathlib import Path

try:
    import molecule_vagrant
except ImportError:
    raise SystemExit(1)

print(Path(molecule_vagrant.__file__).resolve().parent / "modules")
PY
)
  if [[ -n "${_molecule_vagrant_module_path}" ]]
  then
    export MOLECULE_VAGRANT_MODULE_PATH="${_molecule_vagrant_module_path}"
  fi

  # Force zsh/bash to rehash the command cache after activation
  hash -r 2>/dev/null || rehash 2>/dev/null || true
  echo "Python: $(python --version) | $(which python)"
}

update_requirements () {
  _python_requirements_file=$PYTHON_REQUIREMENTS_FILE
  PYTHON_REQUIREMENTS_FILE=requirements.update.txt
  rebuild_env
  PYTHON_REQUIREMENTS_FILE=$_python_requirements_file
  python -m pip freeze > ${CUR_MOL_VENV_DIR}/$PYTHON_REQUIREMENTS_FILE
}

rebuild_env () {
  command -v deactivate >/dev/null 2>&1 && deactivate
  rm -rf "${CUR_MOL_VENV_DIR}/.virtualenv"
  setup_env
}

if [[ ! -f "venv.sh" ]]; then
  echo "Sourcing must be done in the base directory"
  return 1
fi

CUR_MOL_VENV_DIR="$(pwd)"
setup_env

echo "############################################################"
echo "Type 'deactivate' to quit venv"
echo "Type 'download_galaxy' to download ansible roles"
echo "Type 'rebuild_env' to update your virtualenv"
echo "############################################################"
