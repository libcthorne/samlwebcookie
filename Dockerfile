FROM debian:bullseye-slim

RUN apt-get update && apt-get install -y \
    python3-pip

RUN mkdir /samlwebcookie
ADD requirements.txt /samlwebcookie/requirements.txt
ADD webcookie.py /samlwebcookie/webcookie.py

RUN pip3 install -r /samlwebcookie/requirements.txt

CMD python3 /samlwebcookie/webcookie.py
