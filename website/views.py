import datetime
import math
from flask import Blueprint, Response, current_app, make_response, render_template, request, redirect, url_for,jsonify , json, flash
from flask_login import login_required, current_user
from sqlalchemy import and_ #to restrict access only to loged user
from .models import Question , Answer,Etiquette,Sequence, StudentAnswer,User, question_etiquette
from . import db
from .helperFunctions import barcode_image, md2html , codeGen, randomNumbers
from .auth import teacherRequired
import csv
from werkzeug.security import generate_password_hash
import random
viewsBluprint = Blueprint('viewsBluprint',__name__)


#all routes are defined here (only login is in auth)
#after defining your routes you need to register them in 
#__init__.py
#route/endpoint for home page
@viewsBluprint.route('/',methods=['GET', 'POST']) 
@login_required
def home():
    return render_template("home.html",user = current_user)

# live question
show = {
    "Sequence":"",
    "actual":"",
    "action":""
}

@viewsBluprint.route('/question',methods=['GET', 'POST']) 
@login_required
def addQuestion():
    code = request.args.get("code")
    if not code:
        code = codeGen()
        tmp = Question.query.filter_by(code = code).first()
        while tmp:
            code = codeGen()
            tmp = Question.query.filter_by(code = code).first()
        return redirect(url_for('viewsBluprint.addQuestion',code=code))
    if request.method == 'POST':
        answers = []
        title = request.form.get('title')
        content = request.form.get('content')
        answer_names = request.form.get('answer-names').split(',')
        tags = request.form.get('tag').split(',')
        html = md2html(content,code)
        question = Question(code=code,title=title, rawContent=content,HTMLcontent=html, author_id=current_user.id)
        for tag in tags:
            tagDb = Etiquette.query.filter_by(title = tag).first()
            if not tagDb:
                tagDb = Etiquette(title = tag)
                db.session.add(tagDb)
                db.session.commit()
            question.etiquettes.append(tagDb)
        db.session.add(question)
        db.session.commit()
        if answer_names[0] !="": 
            for name in answer_names:
                answer = request.form.get(name+"Input")  
                correct = True if request.form.get(name) == "on" else False
                answerDb = Answer(content=answer,is_correct=correct,question_id=question.id)
                answerDb.add()
                answers.append(answerDb)
            question.updateAnswers(answers)
        return redirect(url_for('viewsBluprint.home'))
    tags = Etiquette.query.all()
    return render_template("addQuestion.html",tags = tags,code=code,user = current_user)

@viewsBluprint.route('/show_question') 
@login_required
def showQuestion():
    questionCode = request.args.get('code')
    sequenceCode = request.args.get('sequence')
    user = User.query.filter_by(id=current_user.id).first()
    if user.is_teacher:
        flash('you may see inactive questions Logged in as admin',category='success')
    if sequenceCode:
        sequence = Sequence.query.filter_by(code = sequenceCode).first()
        if not sequence:
            flash("Wrong Sequence Identifiant",category="error")
            return redirect(url_for("viewsBluprint.home"))
        if not sequence.is_active and not user.is_teacher:
            flash('Sequence is not active', category='error')
            return redirect(url_for("viewsBluprint.home"))
        if not questionCode:
            questionCode = sequence.questions[0].code
            return redirect(url_for('viewsBluprint.showQuestion',sequence=sequenceCode,code=questionCode))
        if questionCode=='Submit':
            return redirect(url_for('viewsBluprint.home'))
        question = Question.query.filter_by(code = questionCode).first() 
        index = sequence.questions.index(question)
        nextQuestion = sequence.questions[index+1].code if index+1 < len(sequence.questions) else 'Submit'

        return render_template("questions.html",sequence=sequenceCode,data=question,next=nextQuestion,user=current_user,type="not_open")
    if questionCode:
        question = Question.query.filter_by(code = questionCode).first()
        if not question:
            flash("Wrong Question Identifiant",category="error")
            return redirect(url_for("viewsBluprint.home"))
        if not question.is_active and not user.is_teacher:
            flash('Question is not active', category='error')
            return redirect(url_for("viewsBluprint.home"))
        if len(question.answers) == 0:
            return render_template("questions.html",data=question,user=current_user,type="open")
        return render_template("questions.html",data=question,user=current_user,type="not_open")

@viewsBluprint.route('/create_sequence',methods=['GET', 'POST']) 
@teacherRequired
def createSequence():
    if request.method == 'POST':
        data = request.get_json()
        sequence = Sequence(code=data['code'],title=data['title'])
        db.session.add(sequence)
        db.session.commit()
        sequence.add_questions(data['questions'])
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 
    code = request.args.get('code')
    if not code:
        code = codeGen()
        tmp = Sequence.query.filter_by(code = code).first()
        while tmp:
            code = codeGen()
            tmp = Sequence.query.filter_by(code = code).first()
        return redirect(url_for('viewsBluprint.createSequence',code=code))
    questions = Question.query.all()
    return render_template("createSequence.html",questions=questions,user=current_user)

@viewsBluprint.route('/questionspanel')
@teacherRequired
def configQuestions():
    return render_template("questionsPanel.html",user=current_user)
@viewsBluprint.route('/suequencespanel')
@teacherRequired
def configSequences():
    return render_template("sequencesPanel.html",user=current_user)


@viewsBluprint.route("/user_panel",methods=['GET','POST'])
@teacherRequired
def studentsPanel():
    usersExist=[]
    if request.method == "POST":
        if 'file' not in request.files:
            flash("No file found",category="error")
        file = request.files['file']
        csv_data = file.read().decode('utf-8')
        csv_reader = csv.reader(csv_data.splitlines(), delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            userCheck = User.query.filter_by(email=row[0]).first()
            if userCheck:
                usersExist.append(f"<p>{row[2]+row[3]} Already exists</p>")
                continue
            user = User(email=row[0], password=generate_password_hash(row[0], method='sha256'), first_name=row[1], last_name=row[2])
            db.session.add(user)
        db.session.commit()
        if len(usersExist) > 0:
            flash("".join(usersExist),category="error")
        else:
            flash("All users added succesfull",category="success")
    users = User.query.filter_by(is_teacher=False).all()
    return render_template("usersPanel.html",user=current_user,usersExist=usersExist,users=users)

@viewsBluprint.route('/sequences',methods = ['GET','POST'])
@login_required 
def sequences():
    action = request.args.get('action')
    id = request.args.get('id')
    code = request.args.get('code')
    red = request.args.get('redirect')
    global show
    if request.method == "POST":
        sequence = Sequence.query.filter_by(id=id).first()
        if not sequence:
            sequence = Sequence.query.filter_by(code=code).first()
        if action == "activate":
            sequence.activate()
            show = {}
        if action == "deactivate":
            sequence.deactivate()
        if action == "delete":
            sequence.delete()
        if action == "clear":
            rowsDelete = StudentAnswer.query.filter_by(sequence_id=id).all()
            for row in rowsDelete:
                db.session.delete(row)
            db.session.commit()
        if red:
            show['Sequence']=red
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
    sequences = Sequence.query.filter_by(is_control=False).order_by(Sequence.id.desc()).all()
    sequence_list = []
    for sequence in sequences:
        sequence_list.append({
            'id': sequence.id,
            'code':sequence.code,
            'title': sequence.title,
            'is_active':sequence.is_active,
            'questions' : len(sequence.questions)
        })
    return jsonify(sequence_list)
# used as API Fetch , Update , Delete
@viewsBluprint.route('/questions', methods = ['GET','POST'])
@login_required 
def questions():
    tag = request.args.get('tag')
    action = request.args.get('action')
    id = request.args.get('id')
    if request.method == "POST":
        question = Question.query.filter_by(id=id).first()
        if action == "activate":
            question.activate()
        if action == "deactivate":
            question.deactivate()
        if action == "delete":
            question.delete()
        if action == "clear":
            rowsDelete = StudentAnswer.query.filter_by(question_id=id).all()
            for row in rowsDelete:
                db.session.delete(row)
            db.session.commit()
        
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
    if tag:
        questions = Question.query.join(Question.etiquettes).filter(Etiquette.title.like(f'%{tag}%')).all()
    else:
        questions = Question.query.order_by(Question.id.desc()).all()
    question_list = []
    for question in questions:
        question_list.append({
            'id': question.id,
            'title': question.title,
            'date':question.date,
            'code':question.code,
            'is_active':question.is_active,
            'tags' : [tag.title for tag in question.etiquettes]
        })
    return jsonify(question_list)


# used as API
@viewsBluprint.route("/order_sequence",methods=["GET","POST"])
@teacherRequired
def orderSequence():
    code = request.args.get('code')
    if not code:
        return redirect(url_for('viewsBluprint.home'))
    sequence = Sequence.query.filter_by(code=code).first()
    if request.method == "POST":
        ids_list = request.get_json()
        sequence.setOrder(ids_list)
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
    return render_template("orderSequence.html",sequence=sequence,user=current_user)

@viewsBluprint.route("/answers",methods=["GET","POST"])
def answers():
    global show
    code = request.args.get('code')
    question = Question.query.filter_by(code=code).first()
    seq = request.args.get('sequence')
    sequence = Sequence.query.filter_by(code=seq).first()
    if sequence:
        studentAnswer = StudentAnswer.query.filter_by(student_id=current_user.id,sequence_id=sequence.id,question_id=question.id).first()
    else:
        studentAnswer = StudentAnswer.query.filter_by(student_id=current_user.id,question_id=question.id).first()
    answersList = question.answers
    if request.method == "POST":
        postData = request.get_json()
        if len(answersList) == 0:
            import difflib
            words = ['Python', 'Java', 'C++', 'JavaScript', 'PHP', 'Ruby', 'Swift', 'Kotlin', 'TypeScript', 'Rust', 'Go', 'C#', 'Perl', 'Lua', 'Scala', 'Haskell', 'R', 'MATLAB', 'SQL', 'Bash', 'Assembleur']
            word = postData['content']
            closest_match = difflib.get_close_matches(word, words, n=1)
            if closest_match:
                word =  closest_match[0]
            else:
                word =  word
            new_studentAnswer = StudentAnswer(student_id=current_user.id,question_id=question.id,answer=word,is_correct=True)
            db.session.add(new_studentAnswer)
        elif studentAnswer:
            studentAnswer.is_correct = True if postData['is_correct']=="true" else False
            studentAnswer.answer = postData['content']
        else:
            new_studentAnswer = StudentAnswer(student_id=current_user.id,sequence_id=sequence.id,question_id=question.id,answer=postData['content'],is_correct=True if postData['is_correct']=="true" else False)
            db.session.add(new_studentAnswer)
        db.session.commit()
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
    data = []
    global show
    for answer in answersList:
        if studentAnswer:
            checked = True if str(answer.content) == str(studentAnswer.answer) else False
            answerStd = str(studentAnswer.answer)
        else:
            checked = False
            answerStd = ""
        
        data.append({
                    'answerContent':answer.content,
                    'checked':checked,
                    'is_correct':answer.is_correct,
                    'answer':answerStd
                    })
    data.insert(0,{'action':show['action']})
    return jsonify(data)


@viewsBluprint.route("/liveQuestionsTracking",methods=['GET','POST'])
@login_required
def liveQuestionsTracking():
    global show
    if request.method == "POST":
        x = request.get_json()
        if 'actionType' in x:
            show['action'] = x["actionType"]
        if 'actualSeq' in x:
            show["Sequence"] = x['actualSeq']
            show["actual"] = x['actualQust']
            show['action'] = "stop"
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
    return show


@viewsBluprint.route('/correction',methods = ['GET','POST'])
@login_required 
def correction():
    code = request.args.get('code')
    sequence = request.args.get('sequence')
    return render_template("showcorrections.html",code=code,sequence=sequence,user=current_user)

@viewsBluprint.route('/show_correction',methods = ['GET','POST'])
@login_required 
def corrections():
    seq = request.args.get('sequence')
    sequence = Sequence.query.filter_by(code=seq).first()
    code = request.args.get('code')
    student = request.args.get('student')
    if student:
        user_id = User.query.filter_by(email=student).first().id
    else:
        user_id = current_user.id
    data = []
    if seq:
        if sequence:
            for question in sequence.questions:
                for answer in question.answers:
                    if answer.is_correct:
                        userAnswer = StudentAnswer.query.filter_by(sequence_id=sequence.id,student_id=user_id,question_id=question.id).first()
                        if userAnswer:
                            userAnswer = userAnswer.answer
                        else:
                            userAnswer = ""
                        data.append({
                            "id":question.id,
                            "title":question.title,
                            "correct":answer.content,
                            "userAnswer":userAnswer
                        })
    if code:
        question = Question.query.filter_by(code=code).first()
        userAnswer = StudentAnswer.query.filter_by(student_id=user_id,question_id=question.id).first()
        for answer in question.answers:
            if answer.is_correct:
                data.append({
                    "id":question.id,
                    "title":question.title,
                    "correct":answer.content,
                    "userAnswer":userAnswer
                })
    return jsonify(data)

@viewsBluprint.route('/logged_in_users',methods=['GET','POST'])
def logged_in_users():
    now = datetime.datetime.now()
    if request.method == 'POST':
        current_user.last_active = now
        db.session.commit()
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 
    code = request.args.get('code')
    seq = request.args.get('sequence')
    sequence_id = Sequence.query.filter_by(code=seq).first().id
    question = Question.query.filter_by(code=code).first()
    question_id = question.id
    ten_seconds_ago = now - datetime.timedelta(seconds=12)
    active_users = User.query.filter(User.last_active > ten_seconds_ago).count()
    student_answers = StudentAnswer.query.filter_by(sequence_id=sequence_id,question_id=question_id).all()
    answersContent = [x.answer for x in student_answers]
    answersCount = {}
    total = 0
    for answer in answersContent:
        if answer in answersCount:
            answersCount[answer] += 1
        else:
            answersCount[answer] = 1
        total += 1
    answersStd = [{'answer': answer, 'count': count} for answer, count in answersCount.items()]
    typeQuestion = "open" if len(question.answers) == 0 else "" 
    return jsonify({"active_users":active_users,"totalResponse":total,"answers":answersStd,"type":typeQuestion})

@viewsBluprint.route("/visualisation",methods=["GET","POST"])
@login_required
def visual():
    if request.method == "POST":
        x = request.get_json()
        answers = []
        # title = x['title']
        code = x['code']
        content = x['content']
        answer_names = x['answer-names'].split(',')
        html = md2html(content,code)
        if len(answer_names[0])>0:
            for name in answer_names:
                if len(answer_names)>1:
                    answer = md2html(x[name+"Input"]) 
                else:
                    answer = x[name+"Input"]
                answers.append(answer)
        
        data = {
            'content':html,
            'answers':answers
        }
        return jsonify(data)


@viewsBluprint.route('/statistics')
def statistics():
    # Get all the student answers
    all_answers = StudentAnswer.query
    sequenceCode = request.args.get("sequence")
    questionCode = request.args.get("question")
    studentCode = request.args.get("student")
    if sequenceCode:
        sequence = Sequence.query.filter_by(code=sequenceCode).first()
        all_answers = all_answers.filter_by(sequence_id=sequence.id)
    if questionCode:
        question = Question.query.filter_by(code=questionCode).first()
        all_answers = all_answers.filter_by(question_id=question.id)
    if studentCode:
        student = User.query.filter_by(email=studentCode).first()
        all_answers = all_answers.filter_by(student_id=student.id)

    # Create a dictionary to store the number of participants and correct answers for each student
    num_participants = {}
    num_correct_answers = {}
    all_answers = all_answers.all()
    # Loop through all the student answers and count the number of participants and correct answers for each student
    for answer in all_answers:
        date = answer.date.date()  # Extract the date portion of the datetime object
        student_id = answer.student_id
        if student_id not in num_participants:
            num_participants[student_id] = {}
            num_correct_answers[student_id] = {}
        if date not in num_participants[student_id]:
            num_participants[student_id][date] = set()  # Use a set to store unique question IDs
            num_correct_answers[student_id][date] = 0
        num_participants[student_id][date].add(answer.question_id)
        if answer.is_correct:
            num_correct_answers[student_id][date] += 1

    # Create a list of dictionaries to store the data for each student
    data = []
    for student_id, dates in num_participants.items():
        student = User.query.get(student_id)
        for date, question_ids in dates.items():
            total_answers = len(question_ids)
            correct_answers = num_correct_answers[student_id][date]
            percentage_correct = round(correct_answers / total_answers * 100, 2) if total_answers > 0 else 0
            answer = {
                'student': student.email,
                'date': date.strftime('%Y-%m-%d'),
                'total_answers': total_answers,
                'correct_answers': correct_answers,
                'percentage_correct': percentage_correct
            }
            year = date.year
            month = date.month
            day = date.day

            # Construct the date range using the extracted year, month, and day
            start_date = datetime.datetime(year, month, day, 0, 0, 0)
            end_date = datetime.datetime(year, month, day, 23, 59, 59)

            # Query for the student answer within the date range
            student_answer = StudentAnswer.query.filter(
                and_(
                    StudentAnswer.student_id == student_id,
                    StudentAnswer.date >= start_date,
                    StudentAnswer.date <= end_date,
                )
            ).first()
            if student_answer:
                if student_answer.sequence_id:
                    sequence_code = Sequence.query.filter_by(id=student_answer.sequence_id).first().code
                    answer['sequence_code'] = sequence_code
                    answer['question_code'] = ""
                elif not sequenceCode:
                    question_code = Question.query.filter_by(id=student_answer.question_id).first().code
                    answer['question_code'] = question_code
                    answer['sequence_code'] = ""
            data.append(answer)

    return jsonify(data)

@viewsBluprint.route("/stats")
@teacherRequired
def stats():
    return render_template("statistics.html",user=current_user)

@viewsBluprint.route("/controles",methods=["GET","POST"])
@teacherRequired
def generateControles():
    if request.method == "POST":
        idTagList = request.form.getlist('tagId')
        # 0 => ordered ; 1 => shuffle
        orderType = request.form.get("orderType")
        controleType = request.form.get("typeControle")
        # Basic == 0
        controlesCount = Sequence.query.filter_by(is_control=True).count()
        controleCode = f"N{controlesCount+1}"
        if str(controleType) == "0":
            nbrQuestion = request.form.getlist('questionNumber')
            nbrQuestion = [int(x) for x in nbrQuestion]

        # Advance == 1
        if str(controleType) == "1":
            minNumbers = request.form.getlist('questionNumberMin')
            maxNumbers = request.form.getlist('questionNumberMax')
            total = int(request.form.get('total'))
            # generate random numbers that add into given number
            ranges = list(zip(minNumbers,maxNumbers))
            nbrQuestion = randomNumbers(total=total,ranges=ranges)
        
        data = list(zip(idTagList,nbrQuestion))
        # checking if number of questions is enough to generate disctinct controles
        totalQuestions = sum(nbrQuestion)
        count = Question.query.filter(Question.etiquettes.any(Etiquette.id.in_(idTagList))).distinct(Question.code).count()
        numberSujets = int(request.form.get('numberSujets'))
        if math.comb(count,totalQuestions) < numberSujets:
            flash("number of question is not enough to generate distinct questions!",category="error")
            return redirect(url_for('viewsBluprint.generateControles'))
        tmp = []
        for _ in range(numberSujets):
            while True:
                controleQuestions = []
                # regenrate random number if controle is advanced
                if str(controleType) == "1":
                    nbrQuestion = randomNumbers(total=total,ranges=ranges)
                    data = list(zip(idTagList,nbrQuestion))
                for etiquette_id,questionsNumber in data:
                    count = 0
                    if len(controleQuestions) == totalQuestions:
                        break
                    while True:
                        questions = Question.query.join(question_etiquette).filter(question_etiquette.c.etiquette_id == etiquette_id).all()
                        questions = [question for question in questions if question not in controleQuestions]
                        if len(questions)<int(questionsNumber):
                            flash("Combinition couldn't be made",category="error")
                            return redirect(url_for('viewsBluprint.generateControles'))
                        questionsRand = random.sample(questions, int(questionsNumber))
                        if len(questionsRand) == int(questionsNumber):
                            controleQuestions.extend(questionsRand)
                            break
                if controleQuestions not in tmp:
                    break
            tmp.append(controleQuestions)
            if int(orderType) == 1:
                random.shuffle(controleQuestions)
            controle = Sequence(code=controleCode,title=f"Controle N{Sequence.query.filter_by(is_control=True).filter_by(code=controleCode).count()+1}",is_control=True)
            db.session.add(controle)
            db.session.commit()
            controle.controleQuestions(controleQuestions)
        else:
            flash("All controles added seccussfuly",category="success")
            return redirect(url_for('viewsBluprint.generateControles')) 
    tags = Etiquette.query.all()
    ettiquetes = []
    for tag in tags:
        maxQuestions = Question.query.filter(Question.etiquettes.contains(tag)).count()
        ettiquetes.append({'id':tag.id,'name':tag.title,'max':maxQuestions})
    return render_template("controles.html",user=current_user,tags=ettiquetes)

@viewsBluprint.route("/controles_panel",methods=["GET","POST"])
@teacherRequired
def controlesPanel():
    return render_template("controlesPanel.html",user=current_user)


@viewsBluprint.route("/controles_API",methods=["GET","POST"])
@teacherRequired
def controlesAPI():
    if request.method == "POST":
        controle_id = request.args.get("id")
        action = request.args.get("action")
        controle = Sequence.query.filter_by(id=controle_id).first()
        if action == "Delete":
            controle.delete()
    controles = Sequence.query.filter_by(is_control=True).all()
    controles_dict = {}
    for controle in controles:
        if controle.code in controles_dict:
            continue
        controles_dict[controle.code] = {
            "id":controle.id,
            "code":controle.code,
            "count":Sequence.query.filter_by(code = controle.code).count()
            }
    return jsonify(controles_dict)

@viewsBluprint.route("/show_controle")
@teacherRequired
def showControle():
    code = request.args.get('code')
    controleType = request.args.get('type')
    controles = Sequence.query.filter_by(code=code).all()
    html = ""
    for controle in controles:
        if controleType == "Anonyme":
            html += barcode_image(str(controle.id).zfill(12))
        else:
            html +="""
            <div class="container">
            <div class="form-row">
                <div class="col">
                    <label >Nom</label>
                    <input type="text" class="form-control">
                </div>
                <div class="col">
                    <label >Prenom</label>
                    <input type="text" class="form-control">
                </div>
                <div class="col">
                    <label >N° Etudiant</label>
                    <input type="text" class="form-control">
                </div>
            </div>
            </div>
            """
        html += f"<h1 align='center'>{controle.title}</h1>"
        for question in controle.questions:
            html += render_template("controleQuestions.html",question=question,user=current_user)
        
        html+= "<span class='pagebreak'></span>"
    return html

@viewsBluprint.route("/word_cloud")
@teacherRequired
def wordcloud():
    code = request.args.get('code')
    question_id = Question.query.filter_by(code=code).first().id
    students_answers = StudentAnswer.query.filter_by(question_id = question_id).all()
    data = []
    for answer in students_answers:
        lst = [answer.answer,StudentAnswer.query.filter_by(answer = answer.answer).filter_by(question_id = question_id).count()]
        if lst not in data:
            data.append(lst)
    
    min_num = min(data, key=lambda x: x[1])[1]
    max_num = max(data, key=lambda x: x[1])[1]

    for row in data:
        num = row[1]
        row[1] = math.floor(((num - min_num) / (max_num - min_num)) * 70 + 9)

    return data
