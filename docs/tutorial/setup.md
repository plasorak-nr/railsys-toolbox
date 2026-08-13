# Setup

Open a PowerShell terminal and type:

```PowerShell
mkdir GitRepos  # Or wherever you want to put your codes
cd GitRepos
git clone https://github.com/plasorak-nr/railsys-toolbox.git
uv init rsys-toolbox-tutorial  # Or whatever else you want to call it
cd rsys-toolbox-tutorial
code .
```

Now open `pyproject.toml` and add the following section:

```toml
[project]
# ...
# let whatever you have here
# ...
dependencies = [
    "rsys-toolbox",
]

[tool.uv.sources]
rsys-toolbox = { path = "../rsys-toolbox", editable = true }
```

Then, back in your terminal:

```PowerShell
uv venv
uv sync
```

## Create a notebook

Create a new Python notebook in the root of your directory and name it `tutorial.ipynb`.