FROM python:3.8.5
RUN mkdir /code
COPY requirements.txt /code
RUN pip install -r /code/requirements.txt
COPY *.py /code/
COPY db /code/db
WORKDIR /code
CMD python main.py
