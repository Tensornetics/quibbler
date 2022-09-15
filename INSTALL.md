## Install pyquibbler

### Install for users

You can simply install *pyquibbler* using pip: 

```pip install pyquibbler```


If you have *Jupyter lab*, you can also add the *pyquibbler Jupyter Lab extensions*:

```pip install pyquibbler_labextension```

### Install for development

To install pyquibbler for development, you can use the 'install.py' script. 
Follow these four steps: 

#### 1. Clone pyquibbler from GitHub.

```git clone https://github.com/Technion-Kishony-lab/quibbler```

#### 2. Create and activate a new virtual environment:

```conda create --name pyquibbler python=3.10``` 

```conda activate pyquibbler```

#### 3. Install Jupyter lab (optional):

```pip install jupyterlab``` 

#### 4. Run the 'install.py' script: 

```python install.py```

This will install *pyquibbler*, and if *Jupyter Lab* is installed it will also offer 
to install the *pyquibbler Jupyter Lab extension*.      

#### 5. Install chromedriver (for lab tests)

If you are developing the *pyquibbler jupyter-lab extension*, to be able to run 
the specific jupyterlab-extension tests, you will also need to install 
`chromedriver` (see [here](tests/lab_extension/README.md)).