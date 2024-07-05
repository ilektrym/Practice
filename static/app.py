import requests
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_restful import Api, Resource
import sys


app = Flask(__name__)
api = Api()
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://postgres:1234@db:5432/practice"

db = SQLAlchemy(app)
migrate = Migrate(app, db)
ma = Marshmallow(app)


# Класс бд
class VacancyModel(db.Model):
    __tablename__ = 'Vacancy'

    id = db.Column(db.Integer(), primary_key=True)
    vacancy = db.Column(db.String(200), nullable=False)
    employer = db.Column(db.String(300), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    salaryFrom = db.Column(db.Integer(), nullable=False)
    salaryTo = db.Column(db.Integer(), nullable=False)
    requirement = db.Column(db.String(350), nullable=False)
    responsibility = db.Column(db.String(350), nullable=False)
    alternate_url = db.Column(db.String(120), default=False)
    time = db.Column(db.String(70), default=False)
    timeDay = db.Column(db.String(70), default=False)

    def __init__(self, id, vacancy, employer, address, salaryFrom, salaryTo, requirement, responsibility, alternate_url, time, timeDay):
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
        return [self.vacancy, self.employer, self.address, self.salaryFrom, self.salaryTo, self.requirement, self.responsibility, self.alternate_url, self.time, self.timeDay]


# Серриализатор
class VacancyModelShema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = VacancyModel


# Класс get запроса вакансий
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

# Класс get запроса региона
class region(Resource):
    @staticmethod
    def get(area):
        url = 'https://api.hh.ru/areas'
        response = requests.get(url)
        if response.status_code == 200:
            regs = response.json()
        reg_id = serch(regs, area)
        if reg_id != 0:
            return {"id": reg_id}
        else:
            return {"mesenge": "region not found"}


api.add_resource(Vacancy, '/vacancy')
api.add_resource(region, '/region/<string:area>')

api.init_app(app)


# Потключение к api hh.ru
def get_data_from_hh(url):
    user = get_headers()
    data = requests.get(url, headers=user['headers'], timeout=5).json()
    return data


# Heder для пропуска потключение
def get_headers():
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0 (Edition GX-CN)'}
    persona = {
        'headers': headers
    }
    return persona


# Функция парсера
def parser(data, text):
    # Полное количество страниц полученых по запросу
    quantity_pagination = round(data['found'] / 100, 0) + 1
    page = 0
    id = 1
    # Идём по страницам, максимум до 19. Так как максимальная глубина выдаваемых вакансий 2000
    while page < quantity_pagination and page < 20:
        # Получение даннчх со страници
        url = f'https://api.hh.ru/vacancies?text={text}&search_field=name&per_page=100&page={page}&area=1'
        data = get_data_from_hh(url)
        # Идём по каждому объявлению и обрабатываем его
        for vacancy in data['items']:
            # Проверка на наличее указаного адресса
            if vacancy['address'] is None:
                adress = 'Адресс не указан'
            else:
                adress = str(vacancy['address']['raw'])
            # Проверка на наличее верхний или нижний границы зарплаты
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
            # Убераем лишниие заголовки
            if vacancy['snippet']['requirement'] is not None:
                requirement = vacancy['snippet']['requirement'].replace('<highlighttext>', '')
            else:
                requirement = ''
            # Убераем лишниие заголовки
            if vacancy['snippet']['responsibility'] is not None:
                responsibility = vacancy['snippet']['responsibility'].replace('<highlighttext>', '')
            else:
                responsibility = ''

            resume = VacancyModel(id=id, vacancy=vacancy['name'], employer=vacancy['employer']['name'], address=adress,
                                  salaryFrom=salaryFrom, salaryTo=salaryTo,
                                  requirement=requirement, responsibility=responsibility,
                                  alternate_url=vacancy['alternate_url'], time=vacancy['published_at'][:10],
                                  timeDay=vacancy['employment']['name'])

            # Запись обработанных данных в таблицу
            db.session.add(resume)
            db.session.commit()
            id += 1
        page += 1


# Функция парсинга для запроса
def add_name(text):
    reset_table()
    url = f'https://api.hh.ru/vacancies?text={text}&search_field=name&per_page=100&area=1'
    data = get_data_from_hh(url)
    parser(data, text)


# Функция рессета таблицы
def reset_table():
    # Получаем таблицу
    al = VacancyModel.query.all()
    # Проходимся по таблицы и удаляме каждый элемент
    for a in range(len(al)):
        x = VacancyModel.query.get(al[a].id)
        db.session.delete(x)
        db.session.commit()

# Функция получения id региона по названию
def serch(regs, area):
    for reg in regs:
        if reg['name'].lower() == area.lower():
            reg_id = reg['id']
            return reg_id
        else:
            if reg['areas'] is not None:
                reg_id = serch(reg['areas'], area)
                if reg_id != 0:
                    return reg_id
    return 0


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
