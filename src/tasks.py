from invoke import task


@task
def local_rie(c):
    c.run(
        'watchmedo auto-restart --patterns="*.py" --recursive -- docker run -p 9000:8080 -v "$(pwd)":/var/task yolo_serverless',
        hide=False,
        warn=True,
    )
