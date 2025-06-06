# agents/content_generator.py
import json
import uuid
import time
import re
from typing import List, Dict
from dataclasses import dataclass
import requests
from .models import QuizQuestion

class GeminiClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent'
        
    def generate(self, prompt: str, max_tokens: int = 2048) -> str:
        """Generate text using Gemini AI API"""
        try:
            url = f"{self.base_url}?key={self.api_key}"
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": max_tokens,
                    "topP": 0.8,
                    "topK": 40
                }
            }
            
            print(f"🤖 Sending request to Gemini AI...")
            response = requests.post(
                url, 
                json=payload, 
                headers={'Content-Type': 'application/json'},
                verify=False
            )
            response.raise_for_status()
            
            result = response.json()
            
            if 'candidates' in result and len(result['candidates']) > 0:
                if 'content' in result['candidates'][0]:
                    if 'parts' in result['candidates'][0]['content']:
                        return result['candidates'][0]['content']['parts'][0]['text']
            
            print(f"❌ Unexpected Gemini response format: {result}")
            return ""
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Gemini request error: {e}")
            raise Exception(f"Failed to connect to Gemini AI: {e}")
        except Exception as e:
            print(f"❌ Gemini error: {e}")
            raise Exception(f"Gemini generation failed: {e}")

class ContentGeneratorAgent:
    """AI Agent for generating educational content using Gemini AI"""
    
    def __init__(self, gemini_api_key: str):
        self.gemini = GeminiClient(gemini_api_key)
        self.agent_name = "ContentGenerator"
        self.system_context = """You are an expert educational content generator. 
        Your role is to create high-quality learning materials, quizzes, and analyze learning patterns."""
        
    def generate_quiz_questions(self, topic: str, difficulty: int, count: int = 5) -> List[QuizQuestion]:
        """Generate quiz questions using Gemini AI"""
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                print(f"🤖 Generating {count} questions for topic: {topic}, difficulty: {difficulty}/5 (attempt {retry_count + 1})")
                
                prompt = f"""{self.system_context}

TASK: Create exactly {count} multiple choice questions about {topic} at difficulty level {difficulty} out of 5.

REQUIREMENTS:
- Each question must have exactly 4 options
- Difficulty level {difficulty}/5 where 1=beginner, 5=expert
- Focus specifically on {topic}
- Return ONLY valid JSON format
- Make questions educational and accurate
- Ensure one correct answer per question

FORMAT (return exactly this structure):
[
  {{
    "question": "What is the main concept of {topic}?",
    "options": ["Correct Answer", "Wrong Option 1", "Wrong Option 2", "Wrong Option 3"],
    "correct_answer": "Correct Answer",
    "topic": "{topic}"
  }}
]

Create {count} questions about {topic} now. Return only the JSON array without any additional text or formatting:"""
                
                response_text = self.gemini.generate(prompt, max_tokens=2048)
                
                if not response_text:
                    raise Exception("Empty response from Gemini AI")
                
                print(f"📥 Raw Gemini response: {response_text[:300]}...")
                
                # Clean the response
                response_text = self._clean_json_response(response_text)
                
                # Parse JSON
                questions_data = json.loads(response_text)
                
                if not isinstance(questions_data, list):
                    raise ValueError("Response is not a JSON array")
                
                # Take only the requested number of questions
                questions_data = questions_data[:count]
                
                questions = []
                for i, q_data in enumerate(questions_data):
                    # Validate question structure
                    required_fields = ['question', 'options', 'correct_answer']
                    if not all(field in q_data for field in required_fields):
                        print(f"⚠️ Question {i+1} missing fields, skipping")
                        continue
                    
                    if not isinstance(q_data['options'], list) or len(q_data['options']) < 4:
                        print(f"⚠️ Question {i+1} invalid options, skipping")
                        continue
                    
                    # Ensure we have exactly 4 options
                    options = q_data['options'][:4]
                    
                    # Make sure correct answer is in options
                    correct_answer = q_data['correct_answer']
                    if correct_answer not in options:
                        # Use the first option as correct answer
                        correct_answer = options[0]
                    
                    question = QuizQuestion(
                        id=str(uuid.uuid4()),
                        question=q_data['question'],
                        options=options,
                        correct_answer=correct_answer,
                        topic=q_data.get('topic', topic),
                        difficulty_level=difficulty,
                        resource_id=""
                    )
                    questions.append(question)
                
                if len(questions) >= count:
                    questions = questions[:count]
                    print(f"✅ Successfully generated {len(questions)} questions")
                    return questions
                else:
                    raise ValueError(f"Generated only {len(questions)} valid questions, need {count}")
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing error (attempt {retry_count + 1}): {e}")
                print(f"Response text: {response_text}")
                retry_count += 1
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error generating questions (attempt {retry_count + 1}): {e}")
                retry_count += 1
                time.sleep(2)
        
        # If all retries failed, generate simple questions
        print("⚠️ Gemini AI failed, generating basic questions")
        return self._generate_basic_questions(topic, difficulty, count)
    
    def _clean_json_response(self, response_text: str) -> str:
        """Clean the Gemini response to extract valid JSON"""
        
        # Remove markdown code blocks if present
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)
        
        # Find JSON array boundaries
        start_idx = response_text.find('[')
        end_idx = response_text.rfind(']')
        
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            json_content = response_text[start_idx:end_idx + 1]
        else:
            # Try to find individual objects and wrap in array
            objects = []
            lines = response_text.split('\n')
            current_object = ""
            brace_count = 0
            
            for line in lines:
                if '{' in line:
                    current_object = line
                    brace_count = line.count('{') - line.count('}')
                elif current_object and brace_count > 0:
                    current_object += " " + line
                    brace_count += line.count('{') - line.count('}')
                    
                    if brace_count == 0:
                        try:
                            obj = json.loads(current_object)
                            objects.append(obj)
                            current_object = ""
                        except:
                            current_object = ""
                            brace_count = 0
            
            if objects:
                json_content = json.dumps(objects)
            else:
                json_content = response_text
        
        return json_content
    
    def _generate_basic_questions(self, topic: str, difficulty: int, count: int) -> List[QuizQuestion]:
        """Generate basic questions when Gemini AI fails"""
        questions = []
        
        question_templates = {
            'algebra': [
                ("What is a variable in algebra?", ["A letter representing an unknown", "A constant number", "An operation", "A graph"]),
                ("How do you solve x + 5 = 10?", ["Subtract 5 from both sides", "Add 5 to both sides", "Multiply by 5", "Divide by 5"]),
                ("What is a linear equation?", ["An equation with degree 1", "An equation with degree 2", "A curved line", "A circle"]),
                ("What does 'like terms' mean?", ["Terms with same variables and powers", "Any two numbers", "Equal signs", "Multiplication terms"]),
                ("What is the order of operations?", ["PEMDAS/BODMAS", "Left to right always", "Addition first", "Random order"]),
            ],
            'calculus': [
                ("What is a limit?", ["Value a function approaches", "Maximum value", "Minimum value", "Average value"]),
                ("What is a derivative?", ["Rate of change", "Area under curve", "Maximum point", "Minimum point"]),
                ("What is integration?", ["Finding area under curve", "Finding slope", "Finding maximum", "Finding minimum"]),
                ("What does continuity mean?", ["No breaks in function", "Always increasing", "Always positive", "Has a maximum"]),
                ("What is the fundamental theorem?", ["Links derivatives and integrals", "States all functions continuous", "Proves limits exist", "Shows functions are smooth"]),
            ],
            'geometry': [
                ("Sum of angles in a triangle?", ["180 degrees", "360 degrees", "90 degrees", "270 degrees"]),
                ("Area of a rectangle?", ["length × width", "2(length + width)", "length + width", "length²"]),
                ("What is a right angle?", ["90 degrees", "180 degrees", "45 degrees", "60 degrees"]),
                ("What is the Pythagorean theorem?", ["a² + b² = c²", "a + b = c", "a × b = c", "a² = b² + c²"]),
                ("How many sides does a hexagon have?", ["6", "5", "7", "8"]),
            ],
            'trigonometry': [
                ("What is sine in a right triangle?", ["opposite/hypotenuse", "adjacent/hypotenuse", "opposite/adjacent", "hypotenuse/opposite"]),
                ("What is cosine in a right triangle?", ["adjacent/hypotenuse", "opposite/hypotenuse", "opposite/adjacent", "hypotenuse/adjacent"]),
                ("What is tangent in a right triangle?", ["opposite/adjacent", "adjacent/opposite", "opposite/hypotenuse", "adjacent/hypotenuse"]),
                ("What is the unit circle?", ["Circle with radius 1", "Circle with radius 2", "Any circle", "Circle with diameter 1"]),
                ("What is the period of sin(x)?", ["2π", "π", "π/2", "4π"]),
            ]
        }
        
        templates = question_templates.get(topic.lower(), question_templates['algebra'])
        
        for i in range(min(count, len(templates))):
            question_text, options = templates[i]
            question = QuizQuestion(
                id=str(uuid.uuid4()),
                question=question_text,
                options=options,
                correct_answer=options[0],  # First option is correct
                topic=topic,
                difficulty_level=difficulty,
                resource_id=""
            )
            questions.append(question)
        
        # If we need more questions, repeat with variations
        while len(questions) < count:
            template_idx = len(questions) % len(templates)
            question_text, options = templates[template_idx]
            question = QuizQuestion(
                id=str(uuid.uuid4()),
                question=f"Advanced: {question_text}",
                options=options,
                correct_answer=options[0],
                topic=topic,
                difficulty_level=difficulty,
                resource_id=""
            )
            questions.append(question)
        
        return questions[:count]
    
    def analyze_weak_areas(self, quiz_results: List[Dict]) -> List[str]:
        """Analyze quiz results to identify weak areas using Gemini AI"""
        try:
            if not quiz_results:
                return []
            
            prompt = f"""{self.system_context}

TASK: Analyze quiz results and identify weak learning areas.

Quiz Results:
{json.dumps(quiz_results, indent=2)}

Based on incorrect answers and topics, identify the main weak areas that need attention.
Return only a JSON array of weak area topics (maximum 5 topics).

Example format: ["algebra", "geometry", "calculus"]

Return only the JSON array without any additional text:"""
            
            response = self.gemini.generate(prompt, max_tokens=500)
            
            # Try to extract JSON array
            try:
                start = response.find('[')
                end = response.rfind(']')
                if start != -1 and end != -1:
                    weak_areas = json.loads(response[start:end+1])
                    return weak_areas if isinstance(weak_areas, list) else []
            except:
                pass
            
            # Fallback to simple analysis
            incorrect_topics = []
            for result in quiz_results:
                if not result.get('is_correct', False):
                    topic = result.get('topic', '').lower()
                    if topic:
                        incorrect_topics.append(topic)
            return list(set(incorrect_topics))
            
        except Exception as e:
            print(f"❌ Error analyzing weak areas: {e}")
            # Fallback analysis
            incorrect_topics = []
            for result in quiz_results:
                if not result.get('is_correct', False):
                    topic = result.get('topic', '').lower()
                    if topic:
                        incorrect_topics.append(topic)
            return list(set(incorrect_topics))