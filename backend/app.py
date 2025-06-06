# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from pymongo import MongoClient
from datetime import datetime
import uuid
from dataclasses import asdict
from dotenv import load_dotenv

# Import agents
from agents import (
    AgentOrchestrator, 
    ContentGeneratorAgent, 
    EvaluatorAgent,
    LearnerProfile, 
    LearningResource,
    QuizQuestion
)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:3000"])
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Gemini AI configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY not found in environment variables!")
    print("Please set your Gemini API key in .env file")
else:
    print(f"🤖 Using Gemini AI with API key: {GEMINI_API_KEY[:10]}...")

# Database configuration
client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
db = client.personalized_tutor

def clean_mongo_doc(doc):
    if doc and '_id' in doc:
        del doc['_id']
    return doc

# Initialize orchestrator
orchestrator = AgentOrchestrator(GEMINI_API_KEY)

# Routes without authentication
@app.route('/api/learner/create', methods=['POST'])
def create_learner():
    try:
        data = request.get_json()
        print(f"🏗️ Creating learner profile")
        
        result = orchestrator.process_new_learner(data, db)
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        print(f"❌ Error creating learner: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/learner/<learner_id>/pretest', methods=['POST'])
def conduct_pretest(learner_id):
    try:
        data = request.get_json()
        subject = data.get('subject', 'algebra')
        
        print(f"🧪 Conducting pretest for learner: {learner_id}, subject: {subject}")
        
        # Generate questions using content generator
        questions = orchestrator.content_agent.generate_quiz_questions(
            topic=subject,
            difficulty=2,  # Medium difficulty for pretest
            count=5
        )
        
        # Create pretest record
        pretest_id = str(uuid.uuid4())
        pretest_doc = {
            'id': pretest_id,
            'learner_id': learner_id,
            'subject': subject,
            'questions': [asdict(q) for q in questions],
            'created_at': datetime.utcnow(),
            'status': 'active'
        }
        
        db.pretests.insert_one(pretest_doc)
        
        return jsonify({
            'success': True,
            'pretest_id': pretest_id,
            'questions': [asdict(q) for q in questions]
        })
        
    except Exception as e:
        print(f"❌ Error conducting pretest: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/pretest/<pretest_id>/submit', methods=['POST'])
def submit_pretest(pretest_id):
    try:
        data = request.get_json()
        answers = data.get('answers', {})
        
        print(f"📝 Submitting pretest: {pretest_id}")
        
        # Get pretest
        pretest = db.pretests.find_one({'id': pretest_id})
        if not pretest:
            return jsonify({'success': False, 'error': 'Pretest not found'}), 404
        
        # Evaluate answers
        results = []
        for question in pretest['questions']:
            user_answer = answers.get(question['id'], '')
            is_correct = user_answer.strip().lower() == question['correct_answer'].strip().lower()
            
            result = orchestrator.evaluator_agent.evaluate_quiz_response(
                QuizQuestion(**question),
                user_answer
            )
            results.append(result)
        
        # Generate overall feedback
        overall_feedback = orchestrator.evaluator_agent.generate_overall_feedback(results)
        
        # Update pretest with results
        db.pretests.update_one(
            {'id': pretest_id},
            {'$set': {
                'answers': answers,
                'results': results,
                'overall_feedback': overall_feedback,
                'completed_at': datetime.utcnow(),
                'status': 'completed'
            }}
        )
        
        return jsonify({
            'success': True,
            'results': results,
            'overall_feedback': overall_feedback
        })
        
    except Exception as e:
        print(f"❌ Error submitting pretest: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/learner/<learner_id>/path', methods=['GET'])
def get_learning_path(learner_id):
    try:
        print(f"🛤️ Getting learning path for learner: {learner_id}")
        
        # Get learner profile
        learner_profile = db.learner_profiles.find_one({'id': learner_id})
        if not learner_profile:
            return jsonify({'success': False, 'error': 'Learner profile not found'}), 404
        
        # Get learning path
        learning_path = db.learning_paths.find_one({'learner_id': learner_id})
        if not learning_path:
            return jsonify({'success': False, 'error': 'Learning path not found'}), 404
        
        # Get current resource
        current_resource = None
        if learning_path['current_position'] < len(learning_path['resources']):
            current_resource_id = learning_path['resources'][learning_path['current_position']]
            current_resource = db.learning_resources.find_one({'id': current_resource_id}, {'_id': 0})
        
        # Calculate progress
        total_resources = len(learning_path['resources'])
        completed_resources = learning_path['current_position']
        completion_percentage = (completed_resources / total_resources * 100) if total_resources > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'learner_id': learner_id,
                'current_position': learning_path['current_position'],
                'total_resources': total_resources,
                'completed_resources': completed_resources,
                'completion_percentage': completion_percentage,
                'current_resource': current_resource,
                'all_resources': learning_path['resources'],
                'progress': learning_path.get('progress', {})
            }
        })
        
    except Exception as e:
        print(f"❌ Error getting learning path: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/resource/<resource_id>', methods=['GET'])
def get_resource(resource_id):
    try:
        print(f"📚 Getting resource: {resource_id}")
        
        resource = db.learning_resources.find_one({'id': resource_id}, {'_id': 0})
        if not resource:
            return jsonify({'success': False, 'error': 'Resource not found'}), 404
        
        return jsonify({
            'success': True,
            'data': resource
        })
        
    except Exception as e:
        print(f"❌ Error getting resource: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/resource/<resource_id>/quiz', methods=['GET'])
def get_resource_quiz(resource_id):
    try:
        print(f"📝 Getting quiz for resource: {resource_id}")
        
        # Get resource
        resource = db.learning_resources.find_one({'id': resource_id})
        if not resource:
            return jsonify({'success': False, 'error': 'Resource not found'}), 404
        
        # Generate quiz questions
        questions = orchestrator.content_agent.generate_quiz_questions(
            topic=resource['topic'],
            difficulty=resource['difficulty_level'],
            count=3
        )
        
        # Create quiz record
        quiz_id = str(uuid.uuid4())
        quiz_doc = {
            'id': quiz_id,
            'resource_id': resource_id,
            'questions': [asdict(q) for q in questions],
            'created_at': datetime.utcnow(),
            'status': 'active'
        }
        
        db.quizzes.insert_one(quiz_doc)
        
        return jsonify({
            'success': True,
            'data': {
                'quiz_id': quiz_id,
                'questions': [asdict(q) for q in questions]
            }
        })
        
    except Exception as e:
        print(f"❌ Error getting resource quiz: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/quiz/<quiz_id>/submit', methods=['POST'])
def submit_quiz(quiz_id):
    try:
        data = request.get_json()
        learner_id = data.get('learner_id')
        answers = data.get('answers', {})
        
        print(f"📝 Submitting quiz: {quiz_id} for learner: {learner_id}")
        
        # Get quiz
        quiz = db.quizzes.find_one({'id': quiz_id})
        if not quiz:
            return jsonify({'success': False, 'error': 'Quiz not found'}), 404
        
        # Evaluate answers
        results = []
        for question in quiz['questions']:
            user_answer = answers.get(question['id'], '')
            is_correct = user_answer.strip().lower() == question['correct_answer'].strip().lower()
            
            result = orchestrator.evaluator_agent.evaluate_quiz_response(
                QuizQuestion(**question),
                user_answer
            )
            results.append(result)
        
        # Generate overall feedback
        overall_feedback = orchestrator.evaluator_agent.generate_overall_feedback(results)
        
        # Save quiz submission
        submission_doc = {
            'id': str(uuid.uuid4()),
            'quiz_id': quiz_id,
            'learner_id': learner_id,
            'answers': answers,
            'results': results,
            'overall_feedback': overall_feedback,
            'submitted_at': datetime.utcnow()
        }
        
        db.quiz_submissions.insert_one(submission_doc)
        
        # Update learning path progress if score is good
        if overall_feedback.get('average_score', 0) >= 60:
            learning_path = db.learning_paths.find_one({'learner_id': learner_id})
            if learning_path:
                new_position = min(learning_path['current_position'] + 1, len(learning_path['resources']))
                db.learning_paths.update_one(
                    {'learner_id': learner_id},
                    {'$set': {
                        'current_position': new_position,
                        f'progress.{quiz["resource_id"]}': overall_feedback,
                        'updated_at': datetime.utcnow()
                    }}
                )
        
        return jsonify({
            'success': True,
            'data': {
                'results': results,
                'overall_feedback': overall_feedback
            }
        })
        
    except Exception as e:
        print(f"❌ Error submitting quiz: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/learner/<learner_id>/progress', methods=['GET'])
def get_learner_progress(learner_id):
    try:
        print(f"📊 Getting progress for learner: {learner_id}")
        
        # Get learner profile
        learner_profile = db.learner_profiles.find_one({'id': learner_id}, {'_id': 0})
        if not learner_profile:
            return jsonify({'success': False, 'error': 'Learner profile not found'}), 404
        
        # Get learning path
        learning_path = db.learning_paths.find_one({'learner_id': learner_id}, {'_id': 0})
        if not learning_path:
            return jsonify({'success': False, 'error': 'Learning path not found'}), 404
        
        # Calculate progress metrics
        total_resources = len(learning_path['resources'])
        completed_resources = learning_path['current_position']
        completion_percentage = (completed_resources / total_resources * 100) if total_resources > 0 else 0
        
        progress_data = {
            'learner_profile': learner_profile,
            'learning_path': {
                'total_resources': total_resources,
                'completed_resources': completed_resources,
                'completion_percentage': completion_percentage,
                'current_position': learning_path['current_position']
            },
            'progress_details': learning_path.get('progress', {})
        }
        
        return jsonify({
            'success': True,
            'data': progress_data
        })
        
    except Exception as e:
        print(f"❌ Error getting learner progress: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analytics/dashboard', methods=['GET'])
def get_analytics_dashboard():
    try:
        print(f"📈 Getting analytics dashboard")
        
        # Get total learners
        total_learners = db.learner_profiles.count_documents({})
        
        # Get total learning paths
        total_paths = db.learning_paths.count_documents({})
        
        # Get total quizzes
        total_quizzes = db.quiz_submissions.count_documents({})
        
        # Calculate average completion rate
        paths = list(db.learning_paths.find({}, {'current_position': 1, 'resources': 1}))
        completion_rates = []
        for path in paths:
            if len(path['resources']) > 0:
                rate = (path['current_position'] / len(path['resources'])) * 100
                completion_rates.append(rate)
        
        avg_completion = sum(completion_rates) / len(completion_rates) if completion_rates else 0
        
        # Get learning styles distribution
        learning_styles = list(db.learner_profiles.aggregate([
            {'$group': {'_id': '$learning_style', 'count': {'$sum': 1}}}
        ]))
        
        analytics = {
            'total_learners': total_learners,
            'total_paths': total_paths,
            'total_quizzes': total_quizzes,
            'average_completion_rate': avg_completion,
            'learning_styles_distribution': learning_styles
        }
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        print(f"❌ Error getting analytics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Health check
@app.route('/api/health', methods=['GET'])
def health_check():
    gemini_status = test_gemini_connection()
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.utcnow().isoformat(),
        'gemini_connected': gemini_status,
        'ai_model': 'gemini-2.0-flash-exp',
        'auth_enabled': False,
        'public_access': True
    })

def test_gemini_connection():
    try:
        if not GEMINI_API_KEY:
            print("❌ Gemini API key not configured")
            return False
            
        from agents.content_generator import GeminiClient
        gemini = GeminiClient(GEMINI_API_KEY)
        response = gemini.generate("Test prompt: Say hello", max_tokens=10)
        print(f"✅ Gemini AI connection successful")
        return True
    except Exception as e:
        print(f"❌ Gemini AI connection failed: {e}")
        print("Make sure your GEMINI_API_KEY is correctly set in .env file")
        return False

if __name__ == '__main__':
    print("🤖 Starting Personalized Tutor API (No Authentication)")
    
    # Test Gemini connection
    if test_gemini_connection():
        print("✅ Ready to serve requests!")
    else:
        print("⚠️ Gemini AI connection issues detected, but server will start anyway")
        print("Make sure to set GEMINI_API_KEY in your .env file")
    
    app.run(debug=True, host='0.0.0.0', port=5000)