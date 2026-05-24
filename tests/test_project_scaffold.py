from importlib.metadata import PackageNotFoundError, version

import idea_forge


def test_package_imports_cleanly() -> None:
    assert idea_forge.__version__ == "0.1.0"


def test_project_metadata_is_available_when_installed() -> None:
    try:
        project_version = version("idea-forge")
    except PackageNotFoundError:
        project_version = idea_forge.__version__

    assert project_version == idea_forge.__version__
