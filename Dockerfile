FROM python:2
ARG cert_path=./x509/cert

ENV PYTHONUNBUFFERED 1

RUN mkdir /code
RUN mkdir /cert

VOLUME /cert

WORKDIR /code

COPY requirements.txt /code/
RUN pip install -r requirements.txt

COPY . /code/

EXPOSE 443
CMD [ "python", "manage.py", "runsslserver", "--certificate /cert/fullchain1.pem", "--key /cert/privkey1.pem", "0.0.0.0:443" ]

