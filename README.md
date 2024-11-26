# fargate-ecr-pretrained

> Experimental template for projects (Docker + Pretrained model)  deployed to AWS Fargate
>
> Supplemental UI project repository: [htmx-]

### Development

`uvicorn src.app:app --reload`

### Running tests

Run only unit tests
`tox -e py312 -- pytest -m unit`

Run only integration tests
`tox -e py312 -- pytest -m integration`

Run only e2e tests
`tox -e py312 -- pytest -m e2e`

Build the sh file `chmod +x workflow.sh`.

```bash
inv build

# alternatively, you can do
#  ./workflow.sh <aws_account_id> <region> [--complete | <function_name>]
# eg: ./push-to-ecr.sh 123456789012 ap-southeast-1 build
```

curl -X POST -F "file=@/path/to/your/test_video.webm" <http://127.0.0.1:8000/analyze-video/>
curl -X POST -F "file=@/home/devvien/plum/fargate-ecr-pretrained/output.mp4" <http://127.0.0.1:8000/analyze-video/>

To run the complete build-createrepo-push workflow

```bash
inv complete_workflow

# alternatively, you can do
#  ./workflow.sh <aws_account_id> <region> --complete
```

## Simulating the lambda locally via AWS RIE

1. Build Dockerfile

```docker build -t yolo_serverless -f Dockerfile.rie.local .```

2. Hot-reload

    ```bash
    watchmedo auto-restart --patterns="*.py" --recursive -- docker run -p 9000:8080 -v "$(pwd)":/var/task yolo_serverless
    ```

3. Test if the lambda runs locally

    - Inline json string:

        ```
        curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
        -H "Authorization: Bearer YOUR_TOKEN_HERE" \
        -d '{"key": "value", "httpMethod": "POST"}'
        ```

    - Using JSON file:

        ```
        curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
        -H "Authorization: Bearer YOUR_TOKEN_HERE" \
        -d @core_lambda/events/post.json
        ```
