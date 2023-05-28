import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
import json

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    CORS(app)
    
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response
    
    @app.route("/categories")
    def retrieve_categories():
        categories = Category.query.order_by(Category.id).all()
        current_categories = [category.format() for category in categories]
        current_categories_dic = {sub['id']: sub['type'] for sub in current_categories}
        return jsonify(
            {
                "success": True,
                "categories": current_categories_dic,
                "total_categories": len(Category.query.all()),
            }
        )

    
    @app.route("/questions")
    def retrieve_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)
        categories = Category.query.order_by(Category.id).all()
        current_categories = [category.format() for category in categories]
        current_categories_dic = {sub['id']: sub['type'] for sub in current_categories}
 
        if len(current_questions) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "total_questions": len(selection),
                "categories":  current_categories_dic,
                "current_category": current_categories_dic[1]
            }
        )

    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def delete_question(question_id):
        try:
            quetion = Question.query.filter(Question.id == question_id).one_or_none()

            if quetion is None:
                abort(404)

            quetion.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify(
                {
                    "success": True,
                    "deleted": question_id,
                    "questions": current_questions,
                    "total_questions": len(Question.query.all()),
                }
            )

        except:
            abort(422)


    @app.route("/questions", methods=["POST"])
    def create_question():
        body = request.get_json()

        new_question = body.get("question", None)
        new_answer = body.get("answer", None)
        new_category = body.get("category", None)
        new_difficulty = body.get("difficulty", None)

        try:
            question = Question(question=new_question, answer=new_answer, category=new_category, difficulty=new_difficulty)
            question.insert()

            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify(
                {
                    "questions": current_questions,
                    "answer": question.answer,
                    "difficulty": question.difficulty,
                    "category": question.category,
                    "id": question.id
                }
            )

        except:
            abort(422)
    
    @app.route("/questions/search", methods=["POST"])
    def search():
        body = request.get_json()
        search_term = body.get("searchTerm", None)
        selection = Question.query.order_by(Question.id).filter(
                    Question.question.ilike("%{}%".format(search_term))
                )
        if len(selection.all()) == 0:
            abort(404)

        current_questions = paginate_questions(request, selection)

        return jsonify(
            {
                "questions": current_questions,
                "totalQuestions": len(selection.all())
            }
        )


    @app.route("/categories/<int:category_id>/questions")
    def retrieve_questions_by_category(category_id):
        category = Category.query.filter(Category.id == category_id).one_or_none()
        if category is None:
            abort(404)

        questions = Question.query.filter(Question.category == category_id).order_by(Question.id).all()
        current_questions = [question.format() for question in questions]

        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "total_questions": len(questions),
                "current_category": category.type
            }
        )

    
    @app.route("/quizzes", methods=["POST"])
    def get_random_question():
        body = request.get_json()

        previous_question = body.get("previous_questions", None)
        quiz_category = body.get("quiz_category", None)

        category = Category.query.join(Question, Category.id == Question.category).filter(Category.type == quiz_category).one_or_none()
        if category is None:
            abort(404)

        found_question = None
        for question in category.questions:
            if not question.id in previous_question:
                found_question = question.format()
                break
        
        if found_question is None:
            abort(404)

        #print(found_question)

        return jsonify(
            {
                "success": True,
                "question": found_question
            }
        )

    
    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404, "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422, "message": "unprocessable"}),
            422,
        )
    
    return app

