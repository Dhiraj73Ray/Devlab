import shutil
import subprocess
import yaml
from jinja2 import Template
from pathlib import Path
from typing import Callable
import re

BASE_DIR = Path(__file__).parent
RECIPES_DIR = BASE_DIR / "recipes"
WORKSPACES_DIR = BASE_DIR.parent / "workspaces"
WORKSPACES_DIR.mkdir(exist_ok=True)

def list_recipes():
    recipes = []
    if not RECIPES_DIR.exists():
        return recipes
    for folder in RECIPES_DIR.iterdir():
        manifest = folder / "recipe.yaml"
        if manifest.exists():
            data = yaml.safe_load(manifest.read_text())
            recipes.append({
                "name": folder.name,
                "description": data.get("description", ""),
                "variables": data.get("variables", {}),
            })
    return recipes

def validate_project_name(name: str):
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        raise ValueError(
            f"Invalid project name: '{name}'. "
            "Use only letters, numbers, hyphens, and underscores. "
            "No spaces, #, @, !, etc."
        )
    return name

def load_recipe(name: str):
    path = RECIPES_DIR / name / "recipe.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Recipe {name} not found")
    return yaml.safe_load(path.read_text())

def create_project(recipe_name: str, project_name: str, log: Callable[[str], None] = print):
    recipe = load_recipe(recipe_name)
    project_name = validate_project_name(project_name)
    variables = {k: v.get("default") for k, v in recipe.get("variables", {}).items()}
    variables["project_name"] = project_name

    target = WORKSPACES_DIR / project_name
    if target.exists():
        raise FileExistsError(f"{project_name} already exists")

    template_dir = RECIPES_DIR / recipe_name / "template"
    
    log(f"[devlab] Copying fat template from {template_dir}...")
    # 1. Copy everything (including node_modules)
    shutil.copytree(template_dir, target)
    log(f"[devlab] Copied instantly.")

    # 2. Only render files specified in files_to_template
    files_to_template = recipe.get("files_to_template", [])
    if files_to_template:
        log(f"[devlab] Applying variables to: {', '.join(files_to_template)}")
        for file_rel_path in files_to_template:
            file_path = target / file_rel_path
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                rendered = Template(content).render(variables)
                file_path.write_text(rendered, encoding="utf-8")
            else:
                log(f"[devlab] Warning: {file_rel_path} not found in template")

    # 3. Run hooks (e.g., git init)
    for command in recipe.get("hooks", {}).get("post_create", []):
        log(f"[devlab] $ {command}")
        proc = subprocess.Popen(
            command, shell=True, cwd=target,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
        for line in proc.stdout:
            log(line.rstrip())
        proc.wait()
        if proc.returncode != 0:
            log(f"[devlab] command failed: {command}")
            raise RuntimeError(f"Hook failed: {command}")

    log(f"[devlab] Done -> {target}")
    return str(target)

def list_workspaces():
    return [p.name for p in WORKSPACES_DIR.iterdir() if p.is_dir()]