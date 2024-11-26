import os

from dotenv import load_dotenv
from invoke import task


load_dotenv(dotenv_path=".env")


account_no = os.environ.get("AWS_ACCOUNT_NO")
region = os.environ.get("AWS_REGION")


@task
def build(c):
    c.run(f"./workflow.sh {account_no} {region} build", hide=False, warn=True)


@task
def complete_workflow(c):
    c.run(f"./workflow.sh {account_no} {region} --complete", hide=False, warn=True)

