# One image for both Lambdas; each picks its handler (infra/api.tf).
# Build from the repo root: the API reads data/ at startup.
#   docker build --platform linux/amd64 --provenance=false -f api/Dockerfile -t saklolo-api .
FROM public.ecr.aws/lambda/python:3.12

COPY api/pyproject.toml api/uv.lock /tmp/build/
RUN pip install --no-cache-dir uv \
    && cd /tmp/build \
    && uv export --frozen --no-dev --no-emit-project --no-hashes -o requirements.txt \
    && pip install --no-cache-dir -r requirements.txt -t "${LAMBDA_TASK_ROOT}" \
    && pip uninstall -y uv \
    && rm -rf /tmp/build

# The repo's layout is kept: settings find data/ three levels above config.py.
COPY data/ ${LAMBDA_TASK_ROOT}/data/
COPY api/src/ ${LAMBDA_TASK_ROOT}/api/src/
ENV PYTHONPATH=${LAMBDA_TASK_ROOT}/api/src

CMD ["saklolo.handlers.lambda_api.handler"]
