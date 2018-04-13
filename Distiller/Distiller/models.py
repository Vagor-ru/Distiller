from datetime import datetime
from Distiller.database import db

class DS18B20(db.Model):
    u'''Таблица с текущими показаниями термометров'''
    __bind_key__ = 'Distiller'
    __tablename__ = 'DS18B20'
    id = db.Column(db.Integer, primary_key=True)
    IDthermometer = db.Column(db.String(16), nullable=False, unique=True)   #Заводской ID термометра
    Name = db.Column(db.String(64), nullable=False) #наименование (место установки)
    T = db.Column(db.Float)     #значение температуры
    Timestamp = db.Column(db.DateTime)  #момент фиксации температурного значения
    #log = db.relationship('log', backref='role')

    def __str__(self):
        return (self.Name+'=%.1f'%self.T)

class Parameters1(db.Model):
    u'''Параметры первого перегона (перегон бражки)'''
    __bind_key__ = 'Distiller'
    id = db.Column(db.Integer, primary_key=True)
    Symbol = db.Column(db.String(16), nullable=False, unique=True)  #обозначение
    Value = db.Column(db.Float)     #значение параметра
    Note = db.Column(db.Text, nullable=False, default='')   #описание параметра

    def __str__(self):
        return (self.Name+'=%.1f'%self.Value)

class Parameters2(db.Model):
    u'''Параметры второго перегона (перегон спирта-сырца)'''
    __bind_key__ = 'Distiller'
    id = db.Column(db.Integer, primary_key=True)
    Symbol = db.Column(db.String(16), nullable=False, unique=True)  #обозначение
    Value = db.Column(db.Float)     #значение параметра
    Note = db.Column(db.Text, nullable=False, default='')   #описание параметра

    def __str__(self):
        return (self.Name+'=%.1f'%self.Value)

class logT(db.Model):
    u'''Таблица для записи температурных данных в процессе перегона'''
    __bind_key__ = 'log'
    __tablename__ = 'logT'
    id = db.Column(db.Integer, primary_key=True)
    T = db.Column(db.Float)
    id_DS18B20 = db.Column(db.Integer, db.ForeignKey('DS18B20.id'))
    id_TimeStamp = db.Column(db.Integer, db.ForeignKey('log.id'))
    TimeStamp=db.relationship('log', backref='timestamp')
    Thermometer=db.relationship('DS18B20', backref='Thrmmtr')

class log(db.Model):
    u'''Таблица для записи моментов фиксации температурных данных'''
    __bind_key__ = 'log'
    __tablename__ = 'log'
    id = db.Column(db.Integer, primary_key=True)
    TimeStamp = db.Column(db.DateTime, default=datetime.now())  #Момент фиксации значений
    P = db.Column(db.Float)   #Значение мощности нагрева
    Deph=db.Column(db.Integer)  #Состояние клапана дефлегматора (1-вкл. 0-откл.)
    Cond=db.Column(db.Integer)  #Состояние клапана конденсатора (1-вкл. 0-откл.)
    Tenv=db.Column(db.Float)  #Температура окружающей среды
    Penv=db.Column(db.Float)  #Давление окружающей среды
    Tsample = db.relationship('logT', backref = 'Ts', lazy = 'dynamic')  #список значений от термометров колонны

    def __init__(self, TimeStamp=datetime.now(), P=0.0, Deph=0, Cond=0):
        self.TimeStamp=TimeStamp
        self.P=P
        self.Deph=Deph
        self.Cond=Cond
