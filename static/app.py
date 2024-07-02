import requests
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_restful import Api, Resource
import sys
app = Flask(__name__)
api = Api()
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://postgres:1234@localhost:5432/practica"

db = SQLAlchemy(app)
migrate = Migrate(app, db)
ma = Marshmallow(app)


class VacancyModel(db.Model):
    __tablename__ = 'Vacancy'

    id = db.Column(db.Integer(), primary_key=True)
    vacancy = db.Column(db.String(200), nullable=False)
    employer = db.Column(db.String(300), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    salaryFrom = db.Column(db.Integer())
    salaryTo = db.Column(db.Integer())
    requirement = db.Column(db.String(350), nullable=False)
    responsibility = db.Column(db.String(350), nullable=False)
    alternate_url = db.Column(db.String(120), default=False)
    time = db.Column(db.String(70), default=False)
    timeDay = db.Column(db.String(70), default=False)

    def __init__(self, id, vacancy, employer, address, salaryFrom, salaryTo, requirement, responsibility, alternate_url,
                 time, timeDay):
        self.id = id
        self.vacancy = vacancy
        self.employer = employer
        self.address = address
        self.salaryFrom = salaryFrom
        self.salaryTo = salaryTo
        self.requirement = requirement
        self.responsibility = responsibility
        self.alternate_url = alternate_url
        self.time = time
        self.timeDay = timeDay

    def __repr__(self):
        return [self.vacancy, self.employer, self.address, self.salaryFrom, self.salaryTo, self.requirement,
                self.responsibility, self.alternate_url, self.time, self.timeDay]


class VacancyModelShema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = VacancyModel


def get_data_from_hh(url):
    user = get_headers()
    data = requests.get(url, headers=user['headers'], timeout=5).json()
    return data


def get_headers():
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0 (Edition GX-CN)'}
    persona = {
        'headers': headers
    }
    return persona


def parser(data, text):
    quantity_pagination = round(data['found'] / 100, 0) + 1
    page = 0
    id = 1
    while page < quantity_pagination and page < 20:
        url = f'https://api.hh.ru/vacancies?text={text}&search_field=name&per_page=100&page={page}&area=1'
        data = get_data_from_hh(url)
        for vacancy in data['items']:
            if vacancy['address'] is None:
                adress = 'Нет адресса'
            else:
                adress = str(vacancy['address']['raw'])
            if vacancy.get('salary') is not None:
                if vacancy.get('salary').get('to') is not None:
                    salaryTo = vacancy['salary']['to']
                else:
                    salaryTo = 0
                if vacancy.get('salary').get('from') is not None:
                    salaryFrom = vacancy['salary']['from']
                else:
                    salaryFrom = 0
            else:
                salaryFrom = 0
                salaryTo = 0
            if vacancy['snippet']['requirement'] is not None:
                requirement = vacancy['snippet']['requirement'].replace('<highlighttext>', '')
            else:
                requirement = ''

            if vacancy['snippet']['responsibility'] is not None:
                responsibility = vacancy['snippet']['responsibility'].replace('<highlighttext>', '')
            else:
                responsibility = ''

            resume = VacancyModel(id=id, vacancy=vacancy['name'], employer=vacancy['employer']['name'], address=adress,
                                  salaryFrom=salaryFrom, salaryTo=salaryTo,
                                  requirement=requirement, responsibility=responsibility,
                                  alternate_url=vacancy['alternate_url'], time=vacancy['published_at'][:10],
                                  timeDay=vacancy['employment']['name'])
            db.session.add(resume)
            db.session.commit()
            id += 1
        page += 1


def add_name(text):
    reset_table()
    url = f'https://api.hh.ru/vacancies?text={text}&search_field=name&per_page=100&area=1'
    data = get_data_from_hh(url)
    parser(data, text)


def reset_table():
    al = VacancyModel.query.all()
    for a in range(len(al)):
        x = VacancyModel.query.get(al[a].id)
        db.session.delete(x)
        db.session.commit()


class Vacancy(Resource):
    @staticmethod
    def get():
        vacancy = request.args.get('vacancy', '')
        salary_from = request.args.get('salaryFrom', 0)
        salary_to = request.args.get('salaryTo', sys.maxsize)
        time_day = request.args.get('timeDay', '')
        add_name(vacancy)
        vacancy_shema = VacancyModelShema(many=True)
        if time_day in ["Полная занятость", "Частичная занятость"]:
            return vacancy_shema.dump(VacancyModel.query.filter(VacancyModel.salaryFrom >= salary_from)
                                      .filter(VacancyModel.salaryTo <= salary_to)
                                      .filter(VacancyModel.timeDay == time_day).all())
        else:
            return vacancy_shema.dump(VacancyModel.query.filter(VacancyModel.salaryFrom >= salary_from)
                                      .filter(VacancyModel.salaryTo <= salary_to).all())


api.add_resource(Vacancy, '/vacancy')

api.init_app(app)

if __name__ == '__main__':
    app.run(debug=True)
