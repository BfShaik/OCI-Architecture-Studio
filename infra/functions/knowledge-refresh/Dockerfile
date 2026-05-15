FROM fnproject/python:3.12-dev AS build
WORKDIR /function
COPY infra/functions/knowledge-refresh/requirements.txt /function/requirements.txt
RUN pip install --target /python -r /function/requirements.txt

FROM fnproject/python:3.12
WORKDIR /function
COPY --from=build /python /python
COPY . /function
ENV PYTHONPATH=/function/app/backend/src
ENTRYPOINT ["/python/bin/fdk", "/function/infra/functions/knowledge-refresh/func.py", "handler"]
