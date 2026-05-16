FROM fnproject/python:3.12-dev AS build
WORKDIR /function
COPY infra/functions/knowledge-refresh/requirements.txt /function/requirements.txt
COPY app/backend/requirements.txt /function/backend-requirements.txt
RUN pip install --target /python -r /function/requirements.txt -r /function/backend-requirements.txt

FROM fnproject/python:3.12
WORKDIR /function
COPY --from=build /python /python
COPY . /function
ENV PYTHONPATH=/python:/function/app/backend/src
ENTRYPOINT ["/python/bin/fdk", "/function/infra/functions/knowledge-refresh/func.py", "handler"]
