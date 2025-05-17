import toml
from poetry.core.masonry.api import build_requires
from poetry.core.packages.locker import Locker
from poetry.core.pyproject.toml import PyProjectTOML
from pathlib import Path

def export_requirements(output_file="requirements.txt"):
    try:
        # Load pyproject.toml
        pyproject_path = Path("pyproject.toml")
        if not pyproject_path.exists():
            raise FileNotFoundError("pyproject.toml not found.")

        pyproject_toml = PyProjectTOML(pyproject_path)
        poetry_config = pyproject_toml.poetry_config

        # Resolve dependencies using Poetry's API
        dependencies = poetry_config.get("dependencies", {})
        dev_dependencies = poetry_config.get("dev-dependencies", {})
        all_dependencies = {**dependencies, **dev_dependencies}

        # Write dependencies to requirements.txt
        with open(output_file, "w") as f:
            for package_name, version_constraint in all_dependencies.items():
                if package_name != "python":
                    f.write(f"{package_name}{version_constraint}\n")

        print(f"Successfully exported requirements to {output_file}")

    except Exception as e:
        print(f"Failed to export requirements: {e}")
        exit(1)

if __name__ == "__main__":
    export_requirements()
