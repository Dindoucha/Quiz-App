from flask_login import UserMixin
from . import db
from sqlalchemy.sql import func

question_sequence = db.Table('question_sequence',
    db.Column('question_id', db.Integer, db.ForeignKey('question.id')),
    db.Column('sequence_id', db.Integer, db.ForeignKey('sequence.id')),
    db.Column('qs_index', db.Integer)
)
question_etiquette = db.Table('question_etiquette',
    db.Column('question_id', db.Integer, db.ForeignKey('question.id')),
    db.Column('etiquette_id', db.Integer, db.ForeignKey('etiquette.id'))
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    last_name = db.Column(db.String(150))
    department = db.Column(db.String(150))
    questions = db.relationship('Question')
    answers = db.relationship('StudentAnswer', backref='user')
    is_teacher = db.Column(db.Boolean, default=False)
    last_active = db.Column(db.DateTime)
    
class Etiquette(db.Model, UserMixin) : 
    id = db.Column(db.Integer, primary_key=True) 
    title = db.Column(db.String(30), unique=True) 
    questions = db.relationship('Question', secondary=question_etiquette, backref='etiquettes')

class Question(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8))
    title = db.Column(db.String(150))
    HTMLcontent = db.Column(db.Text)
    rawContent = db.Column(db.Text)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    answers = db.relationship('Answer', backref='question')
    is_active = db.Column(db.Boolean, default=True)
    is_sequence = db.Column(db.Boolean, default=False)
    def activate(self):
        self.is_active = True
        db.session.commit()
    def deactivate(self):
        self.is_active = False
        db.session.commit()
    def updateAnswers(self, answerList:list):
        self.answers = answerList
        db.session.commit()
    def delete(self):
        db.session.delete(self)
        db.session.commit()

class Sequence(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32))
    title = db.Column(db.String(150))
    is_active = db.Column(db.Boolean, default=False)
    is_control = db.Column(db.Boolean,default=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    student_answers = db.relationship('StudentAnswer', backref='sequence')
    questions = db.relationship('Question', secondary=question_sequence, backref=db.backref('sequences', lazy='dynamic'), order_by=question_sequence.c.qs_index)
    def activate(self):
        self.is_active = True
        db.session.commit()
    def deactivate(self):
        self.is_active = False
        db.session.commit()
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    def add_questions(self, question_id_list):
        for index, question_id in enumerate(question_id_list):
            question = Question.query.filter_by(id=int(question_id)).first()
            if question:
                questions_sequence = question_sequence.insert().values(question_id=question.id, sequence_id=self.id,qs_index=index)
                db.session.execute(questions_sequence)
        db.session.commit()
    def controleQuestions(self, questionsList):
        for index, question in enumerate(questionsList):
            questions_sequence = question_sequence.insert().values(question_id=question.id, sequence_id=self.id,qs_index=index)
            db.session.execute(questions_sequence)
        db.session.commit()
    def setOrder(self, questions_idList:list):
        for index, question_id in enumerate(questions_idList):
            db.session.query(question_sequence).\
            filter_by(question_id=question_id, sequence_id=self.id).\
            update({'qs_index': index})
        db.session.commit()
        
class Answer(db.Model, UserMixin): 
    id = db.Column(db.Integer, primary_key=True) 
    content = db.Column(db.Text)
    is_correct = db.Column(db.Boolean)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    def add(self):
        db.session.add(self)
        db.session.commit()


class StudentAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    sequence_id = db.Column(db.Integer, db.ForeignKey('sequence.id'))
    answer = db.Column(db.Text)
    is_correct = db.Column(db.Boolean, default=False)
    date = db.Column(db.DateTime(timezone=True), default=func.now())