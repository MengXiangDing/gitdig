from setuptools import setup, find_packages

setup(
    name="gitdig",
    version="0.1.0",
    description="从 git 历史挖出工作日报",
    python_requires=">=3.9",
    package_dir={"": "src"},
    py_modules=["gitdig"],
    entry_points={
        "console_scripts": [
            "gitdig=gitdig:main",
        ],
    },
)
