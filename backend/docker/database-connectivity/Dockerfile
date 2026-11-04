FROM python:3.12-alpine
WORKDIR /lab
COPY sample.py /lab/sample.py
USER 65534:65534
ENTRYPOINT ["python", "-I", "-u", "/lab/sample.py"]
