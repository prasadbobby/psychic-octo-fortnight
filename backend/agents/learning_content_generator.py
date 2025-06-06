# agents/learning_content_generator.py
import json
import uuid
import re
from typing import List, Dict, Any
from .content_generator import GeminiClient
from .models import LearningContent

class LearningContentGenerator:
    """AI Agent for generating actual learning content using Gemini AI"""
    
    def __init__(self, gemini_api_key: str):
        self.gemini = GeminiClient(gemini_api_key)
        self.agent_name = "LearningContentGenerator"
        self.system_context = """You are an expert educational content creator and curriculum designer. 
        Your role is to create engaging, comprehensive learning materials tailored to specific learning styles and difficulty levels."""
    
    def generate_learning_sequence(self, learner_profile, topic: str, num_resources: int = 5) -> List[LearningContent]:
        """Generate a complete learning sequence for a topic"""
        
        print(f"📚 Generating learning sequence for {topic} - {learner_profile.learning_style} learner")
        
        # Define resource types based on learning style
        resource_types = self._get_resource_types_for_style(learner_profile.learning_style)
        
        learning_contents = []
        
        for i in range(num_resources):
            difficulty = min(5, learner_profile.knowledge_level + (i // 2))  # Gradual progression
            resource_type = resource_types[i % len(resource_types)]
            
            content = self._generate_single_content(
                topic=topic,
                resource_type=resource_type,
                difficulty=difficulty,
                learning_style=learner_profile.learning_style,
                sequence_position=i + 1,
                total_sequence=num_resources
            )
            
            if content:
                learning_contents.append(content)
        
        return learning_contents
    
    def _get_resource_types_for_style(self, learning_style: str) -> List[str]:
        """Get preferred resource types for learning style"""
        
        style_preferences = {
            'visual': ['infographic_lesson', 'diagram_tutorial', 'visual_guide', 'chart_explanation'],
            'auditory': ['audio_lesson', 'discussion_guide', 'verbal_explanation', 'story_based_lesson'],
            'reading': ['text_lesson', 'article', 'step_by_step_guide', 'detailed_explanation'],
            'kinesthetic': ['interactive_exercise', 'hands_on_activity', 'practice_problems', 'simulation']
        }
        
        return style_preferences.get(learning_style, ['lesson', 'tutorial', 'guide', 'practice'])
    
    def _generate_single_content(self, topic: str, resource_type: str, difficulty: int, learning_style: str, sequence_position: int, total_sequence: int) -> LearningContent:
        """Generate a single piece of learning content"""
        
        try:
            prompt = f"""{self.system_context}

TASK: Create educational content for a {learning_style} learner.

CONTENT SPECIFICATIONS:
- Topic: {topic}
- Resource Type: {resource_type}
- Difficulty Level: {difficulty}/5
- Learning Style: {learning_style}
- Position in Sequence: {sequence_position} of {total_sequence}
- Target Audience: {"Beginner" if difficulty <= 2 else "Intermediate" if difficulty <= 4 else "Advanced"}

REQUIREMENTS:
1. Create engaging, comprehensive content appropriate for the difficulty level
2. Tailor the presentation style to {learning_style} learners
3. Include clear learning objectives
4. Provide practical examples and applications
5. Make it progressive (building on previous knowledge)

Please generate content in the following JSON format:
{{
    "title": "Engaging title for the content",
    "content": "Full educational content (800-1200 words for lessons, shorter for exercises)",
    "summary": "Brief summary (2-3 sentences)",
    "learning_objectives": ["Objective 1", "Objective 2", "Objective 3"],
    "estimated_duration": 15,
    "key_concepts": ["Concept 1", "Concept 2", "Concept 3"]
}}

CONTENT STYLE GUIDELINES:
- Visual learners: Include descriptions of diagrams, charts, visual examples
- Auditory learners: Use conversational tone, include discussion questions
- Reading/Writing learners: Structured text, clear headings, note-taking prompts
- Kinesthetic learners: Include hands-on activities, practice exercises, real-world applications

Generate the content now:"""

            response = self.gemini.generate(prompt, max_tokens=3000)
            
            # Clean and parse JSON response
            json_content = self._extract_json_from_response(response)
            
            if json_content:
                content_data = json.loads(json_content)
                
                return LearningContent(
                    id=str(uuid.uuid4()),
                    title=content_data.get('title', f'{topic} - Part {sequence_position}'),
                    type=resource_type,
                    content=content_data.get('content', ''),
                    summary=content_data.get('summary', ''),
                    difficulty_level=difficulty,
                    learning_style=learning_style,
                    topic=topic,
                    estimated_duration=content_data.get('estimated_duration', 15),
                    prerequisites=[],
                    learning_objectives=content_data.get('learning_objectives', [])
                )
            else:
                return self._generate_fallback_content(topic, resource_type, difficulty, learning_style, sequence_position)
                
        except Exception as e:
            print(f"❌ Error generating content: {e}")
            return self._generate_fallback_content(topic, resource_type, difficulty, learning_style, sequence_position)
    
    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON from Gemini response"""
        
        # Remove markdown code blocks
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        
        # Find JSON object boundaries
        start_idx = response.find('{')
        end_idx = response.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            return response[start_idx:end_idx + 1]
        
        return None
    
    def _generate_fallback_content(self, topic: str, resource_type: str, difficulty: int, learning_style: str, sequence_position: int) -> LearningContent:
        """Generate basic fallback content when AI fails"""
        
        content_templates = {
            'algebra': {
                1: {
                    'title': 'Introduction to Algebraic Variables',
                    'content': f"""Welcome to the world of algebra! This {learning_style}-focused lesson will introduce you to one of the most fundamental concepts in mathematics: variables.

What is a Variable?
A variable is a letter or symbol that represents an unknown number. Think of it as a placeholder or a mystery box that contains a value we don't know yet. The most commonly used variables are x, y, and z, but any letter can be a variable.

Why Do We Use Variables?
Variables are incredibly useful because they allow us to:
1. Write general rules and formulas
2. Solve problems where we don't know all the values
3. Express relationships between quantities
4. Make mathematics more flexible and powerful

Examples in Real Life:
Let's say you're planning a pizza party. You know each pizza costs $12, but you don't know how many pizzas you'll need. We can write this as:
Total cost = 12 × p (where p is the number of pizzas)

If you end up buying 3 pizzas, then p = 3, and the total cost = 12 × 3 = $36.

Basic Operations with Variables:
When working with variables, we can perform the same operations as with regular numbers:
- Addition: x + 5 (add 5 to whatever x represents)
- Subtraction: y - 3 (subtract 3 from whatever y represents)
- Multiplication: 4z (multiply whatever z represents by 4)
- Division: x/2 (divide whatever x represents by 2)

Key Points to Remember:
- A variable can represent any number
- The same variable in an expression represents the same value
- Variables help us write general mathematical statements
- We can substitute actual numbers for variables when we know their values

Practice Thinking:
Look around your daily life and try to identify situations where you might use variables. How much will groceries cost if you buy x items? How long will it take to drive somewhere at y miles per hour?

This foundation will be crucial as we move forward to more complex algebraic concepts!""",
                    'summary': 'An introduction to algebraic variables, explaining what they are, why we use them, and how they work in basic mathematical operations.',
                    'objectives': ['Understand what a variable represents', 'Identify variables in mathematical expressions', 'Apply variables to real-world situations']
                },
                2: {
                    'title': 'Working with Linear Equations',
                    'content': f"""Now that you understand variables, let's explore linear equations - one of the most important topics in algebra!

What is a Linear Equation?
A linear equation is an equation where the highest power of the variable is 1. It creates a straight line when graphed. The general form is: ax + b = c, where a, b, and c are numbers, and x is our variable.

Examples of Linear Equations:
- x + 3 = 7
- 2y - 5 = 11
- 3z + 8 = 20

The Goal: Solving for the Variable
When we solve a linear equation, we're finding the value of the variable that makes the equation true. Think of it as solving a puzzle!

The Golden Rule: Balance
Whatever you do to one side of the equation, you must do to the other side. This keeps the equation balanced, like a scale.

Step-by-Step Solution Process:
Let's solve: 2x + 3 = 11

Step 1: Isolate the term with the variable
Subtract 3 from both sides: 2x + 3 - 3 = 11 - 3
This gives us: 2x = 8

Step 2: Get the variable by itself
Divide both sides by 2: 2x ÷ 2 = 8 ÷ 2
This gives us: x = 4

Step 3: Check your answer
Substitute x = 4 back into the original equation:
2(4) + 3 = 8 + 3 = 11 ✓

Real-World Applications:
Linear equations appear everywhere:
- If you earn $15 per hour, how many hours (h) do you need to work to earn $120?
  Equation: 15h = 120, Solution: h = 8 hours

- A phone plan costs $30 plus $0.10 per text. If your bill is $45, how many texts (t) did you send?
  Equation: 30 + 0.10t = 45, Solution: t = 150 texts

Common Mistakes to Avoid:
1. Forgetting to do the same operation to both sides
2. Making arithmetic errors
3. Not checking your answer
4. Mixing up positive and negative signs

Practice Strategy:
Start with simple equations and gradually work up to more complex ones. Always check your answers by substituting back into the original equation!""",
                    'summary': 'Learn to solve linear equations using balance principles, step-by-step methods, and real-world applications.',
                    'objectives': ['Solve linear equations systematically', 'Apply linear equations to real problems', 'Check solutions for accuracy']
                },
                3: {
                    'title': 'Mastering Systems of Equations',
                    'content': f"""Welcome to systems of equations - where we solve multiple equations with multiple variables simultaneously!

What is a System of Equations?
A system of equations is a set of two or more equations with the same variables. Our goal is to find values for the variables that satisfy ALL equations at the same time.

Example System:
x + y = 10
2x - y = 2

This system asks: "What values of x and y make both equations true?"

Method 1: Substitution
This method involves solving one equation for one variable, then substituting that expression into the other equation.

Solving our example:
From equation 1: y = 10 - x
Substitute into equation 2: 2x - (10 - x) = 2
Simplify: 2x - 10 + x = 2
Combine: 3x - 10 = 2
Solve: 3x = 12, so x = 4

Find y: y = 10 - 4 = 6
Solution: x = 4, y = 6

Method 2: Elimination
This method involves adding or subtracting equations to eliminate one variable.

Using our example:
x + y = 10
2x - y = 2

Add the equations: (x + y) + (2x - y) = 10 + 2
Simplify: 3x = 12
Solve: x = 4

Substitute back: 4 + y = 10, so y = 6

Method 3: Graphing
Each equation represents a line. The solution is where the lines intersect.

Real-World Applications:
1. Business Problems:
   A store sells t-shirts for $15 and hats for $10. If they sold 100 items for $1300 total:
   t + h = 100 (total items)
   15t + 10h = 1300 (total revenue)

2. Motion Problems:
   Two cars travel toward each other. Car A travels at 60 mph, Car B at 40 mph. They start 200 miles apart:
   Distance₁ + Distance₂ = 200
   60t + 40t = 200 (where t is time in hours)

Choosing the Best Method:
- Substitution: When one equation is easily solved for a variable
- Elimination: When coefficients can be easily made opposite
- Graphing: For visual learners or to estimate solutions

Special Cases:
- No Solution: Lines are parallel (inconsistent system)
- Infinite Solutions: Lines are the same (dependent system)
- One Solution: Lines intersect at one point (independent system)

Practice Tips:
1. Always check your solution in BOTH original equations
2. Keep your work organized and neat
3. Choose the method that seems easiest for each problem
4. Draw graphs when helpful for visualization""",
                    'summary': 'Master three methods for solving systems of equations: substitution, elimination, and graphing, with real-world applications.',
                    'objectives': ['Apply substitution method effectively', 'Use elimination to solve systems', 'Recognize and interpret different types of solutions']
                },
                4: {
                    'title': 'Understanding Quadratic Functions',
                    'content': f"""Welcome to quadratic functions - the curved world of algebra that opens doors to advanced mathematics!

What is a Quadratic Function?
A quadratic function is a function where the highest power of the variable is 2. The standard form is:
f(x) = ax² + bx + c, where a ≠ 0

The graph of a quadratic function is a parabola - a U-shaped or upside-down U-shaped curve.

Key Features of Parabolas:
1. Vertex: The highest or lowest point
2. Axis of Symmetry: A vertical line through the vertex
3. Y-intercept: Where the parabola crosses the y-axis
4. X-intercepts (zeros): Where the parabola crosses the x-axis

Direction of Opening:
- If a > 0: parabola opens upward (has a minimum)
- If a < 0: parabola opens downward (has a maximum)

Finding the Vertex:
For f(x) = ax² + bx + c, the vertex is at x = -b/(2a)

Example: f(x) = x² - 4x + 3
Vertex x-coordinate: x = -(-4)/(2×1) = 4/2 = 2
Vertex y-coordinate: f(2) = 2² - 4(2) + 3 = 4 - 8 + 3 = -1
Vertex: (2, -1)

Solving Quadratic Equations:
Method 1: Factoring
x² - 5x + 6 = 0
Factor: (x - 2)(x - 3) = 0
Solutions: x = 2 or x = 3

Method 2: Quadratic Formula
For ax² + bx + c = 0:
x = [-b ± √(b² - 4ac)] / (2a)

Method 3: Completing the Square
Transform the equation into perfect square form.

Real-World Applications:
1. Projectile Motion:
   A ball thrown upward: h(t) = -16t² + 64t + 5
   (height in feet after t seconds)

2. Profit Maximization:
   A company's profit: P(x) = -2x² + 200x - 3000
   (profit for selling x items)

3. Area Problems:
   A rectangular garden with fixed perimeter: A(w) = w(20 - w)
   (area as function of width)

The Discriminant:
The expression b² - 4ac tells us about solutions:
- If b² - 4ac > 0: Two real solutions
- If b² - 4ac = 0: One real solution (vertex touches x-axis)
- If b² - 4ac < 0: No real solutions (parabola doesn't cross x-axis)

Transformations:
Starting with f(x) = x²:
- f(x) = x² + k: shifts up k units
- f(x) = (x - h)²: shifts right h units
- f(x) = a(x - h)² + k: combines shifts and stretches

Vertex Form:
f(x) = a(x - h)² + k
Where (h, k) is the vertex

This form makes it easy to identify transformations and sketch graphs quickly.

Advanced Concepts:
- Axis of symmetry: x = h
- Maximum/minimum value: k
- Domain: all real numbers
- Range: depends on whether parabola opens up or down

Practice Strategy:
1. Start by identifying a, b, and c
2. Determine if parabola opens up or down
3. Find the vertex
4. Find intercepts
5. Sketch the graph
6. Solve related equations""",
                    'summary': 'Explore quadratic functions, their graphs (parabolas), key features, and multiple solution methods with real-world applications.',
                    'objectives': ['Identify key features of parabolas', 'Solve quadratic equations using multiple methods', 'Apply quadratic functions to real-world problems']
                },
                5: {
                    'title': 'Advanced Polynomial Operations',
                    'content': f"""Master the advanced techniques for working with polynomials - the building blocks of higher mathematics!

What are Polynomials?
Polynomials are expressions with variables raised to whole number powers, combined with addition, subtraction, and multiplication. Examples:
- 3x² + 2x - 5 (quadratic)
- x³ - 4x² + x + 6 (cubic)
- 5x⁴ - 2x² + 1 (quartic)

Key Terminology:
- Degree: highest power of the variable
- Leading coefficient: coefficient of the highest degree term
- Constant term: term without a variable
- Standard form: terms arranged from highest to lowest degree

Polynomial Addition and Subtraction:
Combine like terms (terms with the same variable and power).

Example:
(3x³ + 2x² - x + 4) + (x³ - 5x² + 3x - 2)
= (3x³ + x³) + (2x² - 5x²) + (-x + 3x) + (4 - 2)
= 4x³ - 3x² + 2x + 2

Polynomial Multiplication:
Use the distributive property repeatedly.

Multiplying by a Monomial:
3x(2x² - 4x + 1) = 6x³ - 12x² + 3x

Multiplying Binomials (FOIL):
(x + 3)(2x - 5)
= x(2x) + x(-5) + 3(2x) + 3(-5)
= 2x² - 5x + 6x - 15
= 2x² + x - 15

Special Products:
1. Square of a Binomial:
   (a + b)² = a² + 2ab + b²
   (a - b)² = a² - 2ab + b²

2. Difference of Squares:
   (a + b)(a - b) = a² - b²

3. Sum and Difference of Cubes:
   a³ + b³ = (a + b)(a² - ab + b²)
   a³ - b³ = (a - b)(a² + ab + b²)

Polynomial Division:
Long Division Method:
Divide x³ + 2x² - 5x + 2 by x + 3

Step 1: Divide leading terms: x³ ÷ x = x²
Step 2: Multiply: x²(x + 3) = x³ + 3x²
Step 3: Subtract: (x³ + 2x² - 5x + 2) - (x³ + 3x²) = -x² - 5x + 2
Step 4: Repeat until degree of remainder < divisor

Synthetic Division:
A shortcut for dividing by (x - c).

Factoring Polynomials:
1. Greatest Common Factor (GCF):
   6x³ + 9x² = 3x²(2x + 3)

2. Factoring by Grouping:
   x³ + 2x² + 3x + 6 = x²(x + 2) + 3(x + 2) = (x² + 3)(x + 2)

3. Factoring Quadratics:
   x² + 5x + 6 = (x + 2)(x + 3)

4. Special Cases:
   x² - 9 = (x + 3)(x - 3) [difference of squares]
   x³ + 8 = (x + 2)(x² - 2x + 4) [sum of cubes]

The Remainder Theorem:
If a polynomial P(x) is divided by (x - c), the remainder equals P(c).

The Factor Theorem:
(x - c) is a factor of P(x) if and only if P(c) = 0.

Rational Root Theorem:
For polynomial P(x) = aₙxⁿ + ... + a₁x + a₀, any rational root p/q must have:
- p divides a₀ (constant term)
- q divides aₙ (leading coefficient)

Finding Zeros of Polynomials:
1. Try rational roots using Rational Root Theorem
2. Use synthetic division to factor
3. Apply quadratic formula to remaining quadratic factors
4. Consider complex roots for higher-degree polynomials

Graphing Polynomial Functions:
Key features to identify:
- End behavior (determined by leading term)
- x-intercepts (zeros of the function)
- y-intercept (constant term)
- Turning points (at most n-1 for degree n)
- Multiplicity of roots affects graph behavior

Real-World Applications:
1. Volume Problems:
   Box volume: V(x) = x(20-2x)(15-2x) where x is cut size

2. Economics:
   Revenue functions: R(x) = -0.01x³ + 50x² - 1000x

3. Physics:
   Position functions: s(t) = -16t² + v₀t + s₀

Advanced Techniques:
- Polynomial long division
- Synthetic division
- Descartes' Rule of Signs
- Complex roots and conjugate pairs
- Fundamental Theorem of Algebra

Mastery Tips:
1. Practice factoring patterns daily
2. Memorize special products
3. Check work by expanding factored forms
4. Use graphing to verify algebraic solutions
5. Connect polynomial operations to geometric interpretations""",
                    'summary': 'Master advanced polynomial operations including multiplication, division, factoring, and finding zeros with real-world applications.',
                    'objectives': ['Perform complex polynomial operations', 'Factor polynomials using multiple techniques', 'Find and interpret zeros of polynomial functions']
                }
            },
            'geometry': {
                1: {
                    'title': 'Fundamentals of Geometric Shapes',
                    'content': f"""Welcome to geometry - the study of shapes, sizes, and spatial relationships!

What is Geometry?
Geometry is the branch of mathematics that deals with points, lines, angles, surfaces, and solids. It helps us understand the world around us through shapes and spatial reasoning.

Basic Building Blocks:

1. Points:
A point is a location in space with no size or dimension. We name points with capital letters (A, B, C).

2. Lines:
A line extends infinitely in both directions. It has no thickness and is perfectly straight. We name lines with two points on them (line AB) or with lowercase letters.

3. Line Segments:
A part of a line with two endpoints. Segment AB has definite length.

4. Rays:
A part of a line that starts at one point and extends infinitely in one direction.

5. Angles:
Formed when two rays share a common endpoint (vertex).

Types of Angles:
- Acute: less than 90°
- Right: exactly 90°
- Obtuse: between 90° and 180°
- Straight: exactly 180°
- Reflex: between 180° and 360°

Basic Shapes:

Triangles:
- 3 sides, 3 angles
- Sum of angles = 180°
- Types: equilateral, isosceles, scalene
- By angles: acute, right, obtuse

Quadrilaterals:
- 4 sides, 4 angles
- Sum of angles = 360°
- Types: square, rectangle, parallelogram, rhombus, trapezoid

Circles:
- All points equidistant from center
- Radius: distance from center to edge
- Diameter: distance across through center
- Circumference: distance around the circle

Polygons:
- Closed figures with straight sides
- Regular: all sides and angles equal
- Examples: pentagon (5 sides), hexagon (6 sides), octagon (8 sides)

Measuring and Relationships:
When working with shapes, we often need to find:
- Perimeter: distance around the outside
- Area: space inside the shape
- Volume: space inside 3D shapes

Geometric Relationships:
- Parallel lines: never intersect
- Perpendicular lines: intersect at 90°
- Congruent: same size and shape
- Similar: same shape, different size

Real-World Applications:
Geometry is everywhere:
- Architecture: designing buildings
- Art: creating balanced compositions
- Sports: calculating playing field dimensions
- Navigation: using coordinates and distances
- Technology: computer graphics and design

Visual Learning Tips:
Since this is tailored for visual learners:
- Draw diagrams for every problem
- Use different colors for different parts
- Create charts showing angle relationships
- Build or visualize 3D models for spatial problems
- Use geometric software or apps when available

Key Formulas to Remember:
- Triangle area: A = ½ × base × height
- Rectangle area: A = length × width
- Circle area: A = πr²
- Circle circumference: C = 2πr

Practice Strategies:
1. Start with simple shapes and build complexity
2. Always label your diagrams clearly
3. Look for patterns in geometric relationships
4. Connect abstract concepts to real objects
5. Practice estimation skills alongside exact calculations

Geometry Tools:
- Ruler: measuring lengths
- Protractor: measuring angles
- Compass: drawing circles and arcs
- Straightedge: drawing straight lines

This foundation will prepare you for more advanced geometric concepts like proofs, coordinate geometry, and trigonometry!""",
                    'summary': 'Introduction to basic geometric concepts including points, lines, angles, and fundamental shapes with their properties.',
                    'objectives': ['Identify and classify basic geometric shapes', 'Understand angle relationships and measurements', 'Apply geometric concepts to real-world situations']
                },
                2: {
                    'title': 'Exploring Angles, Lines, and Triangles',
                    'content': f"""Dive deeper into the fascinating relationships between angles, lines, and triangles!

Angle Relationships:

Adjacent Angles:
Two angles that share a common vertex and side but don't overlap.

Vertical Angles:
Opposite angles formed when two lines intersect. They are always equal.
Example: If two lines intersect forming angles of 60°, the opposite angle is also 60°.

Complementary Angles:
Two angles whose measures add up to 90°.
Example: 30° and 60° are complementary.

Supplementary Angles:
Two angles whose measures add up to 180°.
Example: 120° and 60° are supplementary.

Parallel Lines and Transversals:
When a line (transversal) crosses two parallel lines, it creates special angle relationships:

- Corresponding Angles: Same position at each intersection (equal)
- Alternate Interior Angles: Inside the parallel lines, opposite sides (equal)
- Alternate Exterior Angles: Outside the parallel lines, opposite sides (equal)
- Co-interior Angles: Inside the parallel lines, same side (supplementary)

Triangle Fundamentals:

The Triangle Angle Sum:
The sum of all angles in ANY triangle is always 180°.
If you know two angles, you can find the third: Third angle = 180° - (angle1 + angle2)

Triangle Classification by Sides:
1. Equilateral: All three sides equal, all angles 60°
2. Isosceles: Two sides equal, two angles equal
3. Scalene: All sides different, all angles different

Triangle Classification by Angles:
1. Acute: All angles less than 90°
2. Right: One angle exactly 90°
3. Obtuse: One angle greater than 90°

Special Right Triangles:

45-45-90 Triangle:
- Angles: 45°, 45°, 90°
- Side ratio: 1 : 1 : √2
- If legs = x, then hypotenuse = x√2

30-60-90 Triangle:
- Angles: 30°, 60°, 90°
- Side ratio: 1 : √3 : 2
- If short leg = x, then long leg = x√3, hypotenuse = 2x

Triangle Congruence:
Two triangles are congruent if they have the same size and shape.

Congruence Rules:
- SSS: Three sides equal
- SAS: Two sides and included angle equal
- ASA: Two angles and included side equal
- AAS: Two angles and non-included side equal
- HL: Hypotenuse-leg (right triangles only)

Triangle Inequality Theorem:
The sum of any two sides of a triangle must be greater than the third side.
For triangle with sides a, b, c:
- a + b > c
- a + c > b
- b + c > a

Exterior Angles:
An exterior angle of a triangle equals the sum of the two non-adjacent interior angles.

Practical Applications:

Construction and Architecture:
- Roof trusses use triangle stability
- Bridge designs rely on triangular support
- Angle measurements ensure proper building alignment

Navigation:
- Triangulation helps determine location
- Pilots use angle relationships for flight paths
- GPS systems use geometric principles

Art and Design:
- Perspective drawing uses angle relationships
- Geometric patterns in art follow triangle rules
- Photography composition uses triangle principles

Problem-Solving Strategies:

1. Draw and Label:
Always sketch the problem with all given information clearly marked.

2. Identify Relationships:
Look for parallel lines, angle pairs, and triangle types.

3. Use Known Theorems:
Apply angle sum, congruence rules, and special relationships.

4. Work Step by Step:
Don't try to solve everything at once. Find what you can, then use that to find more.

5. Check Your Work:
Verify that angle sums are correct and relationships make sense.

Real-World Problem Example:
A ladder leans against a wall at a 70° angle. If the wall is perpendicular to the ground, what's the angle between the ladder and the ground?

Solution: The ladder, wall, and ground form a right triangle.
Angles in triangle: 90° (wall-ground) + 70° (ladder-wall) + ? = 180°
Ladder-ground angle = 180° - 90° - 70° = 20°

Advanced Concepts Preview:
- Similarity and proportional relationships
- Triangle centers (centroid, circumcenter, incenter)
- Law of Sines and Law of Cosines
- Trigonometric ratios

Study Tips:
1. Practice identifying angle relationships in real buildings and objects
2. Use a protractor to measure angles in your environment
3. Create flashcards for triangle properties and angle relationships
4. Draw large, clear diagrams with proper labels
5. Practice mental math for common angle calculations (30°, 45°, 60°, 90°)

Common Mistakes to Avoid:
- Forgetting that triangle angles sum to 180°
- Confusing angle relationships (complementary vs supplementary)
- Not recognizing special right triangles
- Mixing up interior and exterior angles
- Assuming triangles are congruent without proving it

This knowledge forms the foundation for advanced geometry, trigonometry, and real-world problem solving!""",
                   'summary': 'Explore angle relationships, parallel line properties, and triangle classifications with practical applications.',
                   'objectives': ['Apply angle relationships to solve problems', 'Classify triangles by sides and angles', 'Use triangle congruence rules effectively']
               },
               3: {
                   'title': 'Calculating Area and Perimeter',
                   'content': f"""Master the essential skills of measuring spaces and boundaries in geometry!

Understanding Perimeter:
Perimeter is the distance around the outside of a shape. Think of it as the length of fence needed to surround a yard.

Basic Perimeter Formulas:

Rectangle: P = 2l + 2w (or 2(l + w))
Square: P = 4s
Triangle: P = a + b + c (sum of all sides)
Regular Polygon: P = n × s (number of sides × side length)
Circle (Circumference): C = 2πr or C = πd

Understanding Area:
Area is the amount of space inside a shape. Think of it as the amount of paint needed to cover a surface.

Basic Area Formulas:

Rectangle: A = l × w
Square: A = s²
Triangle: A = ½ × base × height
Parallelogram: A = base × height
Trapezoid: A = ½ × (b₁ + b₂) × h
Circle: A = πr²

Special Triangle Areas:
- Right Triangle: A = ½ × leg₁ × leg₂
- Equilateral Triangle: A = (s²√3)/4
- Using Heron's Formula: A = √[s(s-a)(s-b)(s-c)]
 where s = (a+b+c)/2

Composite Figures:
For complex shapes, break them into familiar pieces:

Example: L-shaped figure
Method 1: Add areas of rectangles
Method 2: Subtract cut-out area from larger rectangle

Step-by-Step Process:
1. Identify the basic shapes
2. Find all necessary measurements
3. Apply appropriate formulas
4. Add or subtract as needed

Units and Conversions:
Perimeter: linear units (feet, meters, inches)
Area: square units (ft², m², in²)

Common conversions:
- 1 foot = 12 inches
- 1 yard = 3 feet
- 1 meter = 100 centimeters
- 1 square foot = 144 square inches

Real-World Applications:

Home Improvement:
- Flooring: Calculate area to determine how much tile or carpet needed
- Fencing: Calculate perimeter to determine fence length
- Painting: Calculate wall area minus doors and windows
- Gardening: Calculate garden bed area for soil and plants

Construction:
- Concrete pouring: Calculate area for slabs
- Roofing: Calculate surface area for materials
- Landscaping: Calculate lawn area for seeding

Cost Calculations:
If carpet costs $3 per square foot, and a room is 12 ft × 10 ft:
Area = 12 × 10 = 120 ft²
Cost = 120 × $3 = $360

Problem-Solving Strategies:

1. Draw and Label:
Sketch the figure with all given measurements clearly marked.

2. Identify What's Asked:
Determine whether you need perimeter, area, or both.

3. Choose the Right Formula:
Match the shape to the appropriate formula.

4. Substitute and Calculate:
Replace variables with given values and solve.

5. Check Units:
Ensure your answer has the correct units (linear for perimeter, square for area).

6. Verify Reasonableness:
Does your answer make sense in context?

Advanced Techniques:

Using Coordinate Geometry:
For shapes on a coordinate plane:
- Distance formula for side lengths
- Shoelace formula for polygon areas

Irregular Shapes:
- Break into triangles and use coordinates
- Use integration for curved boundaries
- Approximate with rectangles or trapezoids

Optimization Problems:
Finding maximum area with fixed perimeter or minimum perimeter with fixed area.

Example: What rectangle with perimeter 40 has maximum area?
Let width = w, then length = 20 - w
Area = w(20 - w) = 20w - w²
Maximum when w = 10, giving a 10×10 square

Circle Sectors and Segments:
Sector area: A = (θ/360°) × πr² (for angle θ in degrees)
Arc length: s = (θ/360°) × 2πr

Practice Problems Types:

1. Basic Calculations:
Find area and perimeter of standard shapes.

2. Composite Figures:
Combine multiple shapes.

3. Word Problems:
Apply to real-world situations.

4. Missing Dimensions:
Given area or perimeter, find unknown measurements.

5. Comparison Problems:
Which shape has greater area or perimeter?

Common Mistakes to Avoid:
- Confusing perimeter and area formulas
- Using wrong units or forgetting to convert
- Not breaking complex shapes into simpler parts
- Forgetting to include all sides in perimeter
- Using diameter instead of radius in circle formulas

Tips for Success:
- Keep a formula sheet handy while learning
- Practice with real measurements around your home
- Use grid paper to visualize areas
- Double-check calculations with estimation
- Learn to recognize when answers are unreasonable

Technology Tools:
- Calculators for π calculations
- Geometry software for complex shapes
- Measurement apps on phones
- Online area calculators for verification

This foundation prepares you for surface area, volume, and advanced applications in higher mathematics!""",
                   'summary': 'Learn to calculate area and perimeter for various shapes with real-world applications and problem-solving strategies.',
                   'objectives': ['Apply area and perimeter formulas correctly', 'Solve problems involving composite figures', 'Use measurements for practical applications']
               },
               4: {
                   'title': 'Circle Geometry and Properties',
                   'content': f"""Explore the fascinating world of circles - one of geometry's most perfect and useful shapes!

Circle Fundamentals:

Definition:
A circle is the set of all points that are the same distance from a central point.

Key Parts of a Circle:
- Center: The fixed point in the middle
- Radius (r): Distance from center to any point on the circle
- Diameter (d): Distance across the circle through the center (d = 2r)
- Chord: A line segment connecting two points on the circle
- Arc: A portion of the circle's circumference
- Sector: A "slice" of the circle (like a piece of pie)
- Segment: The region between a chord and the arc it cuts off

Essential Circle Measurements:

Circumference (Perimeter of Circle):
C = 2πr or C = πd
π ≈ 3.14159... (pi is the ratio of circumference to diameter)

Area of Circle:
A = πr²

Important Relationships:
- All radii of a circle are equal
- Diameter is twice the radius
- Circumference is π times the diameter

Angles in Circles:

Central Angles:
Angle with vertex at the center of the circle.
The arc it intercepts has the same measure as the angle.

Inscribed Angles:
Angle with vertex on the circle and sides that are chords.
An inscribed angle is half the central angle that intercepts the same arc.

Key Angle Theorems:
1. Inscribed Angle Theorem: Inscribed angle = ½ × Central angle
2. Angles in a semicircle are always 90°
3. Opposite angles in a cyclic quadrilateral sum to 180°

Tangent and Secant Relationships:

Tangent Lines:
A line that touches the circle at exactly one point.
- Tangent is perpendicular to radius at point of contact
- Two tangents from external point are equal in length

Secant Lines:
A line that intersects the circle at two points.

Power of a Point:
For intersecting chords, tangents, and secants:
If two chords intersect inside a circle: a × b = c × d
If two secants from external point: (whole₁)(part₁) = (whole₂)(part₂)

Arcs and Sectors:

Arc Length:
For central angle θ (in degrees): Arc length = (θ/360°) × 2πr
For central angle θ (in radians): Arc length = θr

Sector Area:
For central angle θ (in degrees): Sector area = (θ/360°) × πr²
For central angle θ (in radians): Sector area = ½θr²

Real-World Applications:

Architecture and Design:
- Circular windows and domes
- Arches and curved structures
- Rotundas and circular buildings

Transportation:
- Wheel design and tire calculations
- Circular traffic patterns (roundabouts)
- Satellite dish curvature

Sports and Recreation:
- Athletic tracks and fields
- Basketball court circles
- Dartboard design

Technology:
- Gear ratios and mechanical systems
- Satellite orbital calculations
- Antenna design

Manufacturing:
- Pipe and tube specifications
- Circular saw blade design
- Container and tank design

Problem-Solving Strategies:

1. Identify Circle Elements:
Clearly mark center, radius, diameter, chords, tangents.

2. Choose Appropriate Formulas:
Match the problem type to the right formula.

3. Convert Units if Needed:
Ensure all measurements use the same units.

4. Use Relationships:
Apply theorems about angles, chords, and tangents.

5. Check Reasonableness:
Verify that answers make sense in context.

Advanced Circle Concepts:

Equation of a Circle:
Standard form: (x - h)² + (y - k)² = r²
Where (h, k) is the center and r is the radius

Circle on Coordinate Plane:
Use distance formula and circle equation to solve problems.

Concentric Circles:
Circles with the same center but different radii.
Area between circles = π(R² - r²)

Practical Examples:

Example 1: Pizza Problem
A 16-inch pizza is cut into 8 equal slices. What's the area of each slice?
Total area = π(8)² = 64π square inches
Each slice = 64π ÷ 8 = 8π ≈ 25.1 square inches

Example 2: Garden Sprinkler
A sprinkler waters in a circle with radius 15 feet. What area does it cover?
Area = π(15)² = 225π ≈ 707 square feet

Example 3: Ferris Wheel
A Ferris wheel has a radius of 50 feet. How far does a passenger travel in one complete rotation?
Distance = circumference = 2π(50) = 100π ≈ 314 feet

Common Mistakes to Avoid:
- Confusing radius and diameter
- Forgetting to square the radius in area formula
- Using degrees instead of the decimal equivalent in calculations
- Not converting between different angle measures
- Mixing up circumference and area formulas

Memory Aids:
- "Area uses r-squared" (A = πr²)
- "Circumference is 2πr or πd"
- "Inscribed angles are half the central angle"
- "Tangents are perpendicular to radii"

Technology Integration:
- Use π button on calculator for accuracy
- Graphing software to visualize circle problems
- Online circle calculators for verification
- Compass and protractor for hands-on construction

This circle knowledge connects to trigonometry, calculus, and advanced applications in engineering and science!""",
                   'summary': 'Master circle properties, measurements, angles, and real-world applications with comprehensive problem-solving techniques.',
                   'objectives': ['Calculate circle measurements accurately', 'Apply circle theorems to solve problems', 'Use circle geometry in practical situations']
               },
               5: {
                   'title': 'Three-Dimensional Shapes and Volume',
                   'content': f"""Enter the exciting world of 3D geometry where shapes have length, width, AND height!

Understanding 3D Space:

Dimensions:
- 1D: Length only (line)
- 2D: Length and width (flat shapes)
- 3D: Length, width, and height (solid objects)

Key 3D Concepts:
- Face: A flat surface of a 3D shape
- Edge: Where two faces meet
- Vertex: Where three or more edges meet
- Volume: Amount of space inside a 3D shape
- Surface Area: Total area of all faces

Common 3D Shapes:

Rectangular Prism (Box):
- 6 rectangular faces
- 12 edges, 8 vertices
- Volume: V = length × width × height
- Surface Area: SA = 2(lw + lh + wh)

Cube:
- Special rectangular prism with all edges equal
- Volume: V = s³
- Surface Area: SA = 6s²

Cylinder:
- Two circular bases connected by curved surface
- Volume: V = πr²h
- Surface Area: SA = 2πr² + 2πrh

Cone:
- Circular base with curved surface meeting at apex
- Volume: V = ⅓πr²h
- Surface Area: SA = πr² + πrl (where l is slant height)

Sphere:
- All points equidistant from center
- Volume: V = ⁴⁄₃πr³
- Surface Area: SA = 4πr²

Pyramid:
- Polygon base with triangular faces meeting at apex
- Volume: V = ⅓ × base area × height
- Square pyramid: V = ⅓s²h

Prism:
- Two parallel, congruent bases connected by rectangles
- Volume: V = base area × height
- Triangular prism: V = ½bwh (where b is triangle base, w is triangle height)

Volume Relationships:

Key Pattern:
- Prisms and Cylinders: V = base area × height
- Pyramids and Cones: V = ⅓ × base area × height
- Sphere: V = ⁴⁄₃πr³

Surface Area Strategies:

Net Method:
"Unfold" the 3D shape to see all faces, then add their areas.

Formula Method:
Use established formulas for common shapes.

Component Method:
Break complex shapes into simpler parts.

Real-World Applications:

Architecture and Construction:
- Building volume for heating/cooling calculations
- Material estimates for concrete, paint, roofing
- Storage capacity planning

Manufacturing:
- Container design and capacity
- Material usage optimization
- Packaging efficiency

Science and Engineering:
- Fluid dynamics and flow rates
- Structural load calculations
- Heat transfer and insulation

Everyday Life:
- Cooking (recipe scaling based on container size)
- Shipping and storage
- Home improvement projects

Problem-Solving Examples:

Example 1: Swimming Pool
A rectangular pool is 20 ft long, 10 ft wide, and 5 ft deep.
Volume = 20 × 10 × 5 = 1,000 cubic feet
To convert to gallons: 1,000 × 7.48 ≈ 7,480 gallons

Example 2: Ice Cream Cone
A cone has radius 3 cm and height 12 cm.
Volume = ⅓π(3)²(12) = ⅓π(9)(12) = 36π ≈ 113 cubic cm

Example 3: Storage Tank
A cylindrical tank has radius 5 ft and height 20 ft.
Volume = π(5)²(20) = 500π ≈ 1,571 cubic feet

Composite Figures:

Many real objects combine basic shapes:
- House: rectangular prism + triangular prism (roof)
- Silo: cylinder + cone or hemisphere
- Trophy: various shapes stacked

Strategy:
1. Identify component shapes
2. Calculate each volume separately
3. Add or subtract as appropriate

Units and Conversions:

Volume Units:
- Cubic inches (in³), cubic feet (ft³), cubic meters (m³)
- Liters, gallons, milliliters

Common Conversions:
- 1 ft³ = 1,728 in³
- 1 m³ = 1,000 liters
- 1 ft³ ≈ 7.48 gallons

Surface Area Applications:
- Paint needed for walls
- Material for packaging
- Heat loss through surfaces

Advanced Concepts:

Similar Solids:
If linear scale factor is k:
- Surface area scale factor: k²
- Volume scale factor: k³

Cross-Sections:
When a plane cuts through a 3D shape, it creates a 2D cross-section.

Cavalieri's Principle:
If two solids have the same height and equal cross-sectional areas at every level, they have equal volumes.

Optimization Problems:
Finding maximum volume with constraints or minimum surface area for given volume.

Technology Integration:

3D Modeling Software:
- SketchUp, Tinkercad for visualization
- CAD programs for precise calculations
- 3D printing for physical models

Calculators:
- Volume and surface area calculators
- Unit conversion tools
- Graphing calculators with 3D capabilities

Problem-Solving Steps:

1. Identify the Shape:
Determine what 3D shape(s) you're working with.

2. Gather Measurements:
Find all necessary dimensions (radius, height, length, width).

3. Choose Formulas:
Select appropriate volume or surface area formulas.

4. Calculate Carefully:
Pay attention to units and order of operations.

5. Check Reasonableness:
Does your answer make sense in the real-world context?

Common Mistakes:
- Confusing radius and diameter
- Forgetting to convert units
- Using wrong formula for the shape
- Mixing up volume and surface area
- Not accounting for all parts of composite figures

Study Tips:
- Build physical models with clay or blocks
- Use everyday objects to practice measurements
- Create formula cards with visual diagrams
- Practice with real-world scenarios
- Use online 3D shape manipulatives

This 3D geometry foundation is essential for calculus, physics, engineering, and countless practical applications!""",
                   'summary': 'Explore three-dimensional shapes, volume calculations, surface area, and real-world applications with comprehensive problem-solving methods.',
                   'objectives': ['Calculate volumes of common 3D shapes', 'Find surface areas using multiple methods', 'Apply 3D geometry to practical problems']
               }
           },
           'trigonometry': {
               1: {
                   'title': 'Introduction to Trigonometry',
                   'content': f"""Welcome to trigonometry - the mathematics of triangles and circular motion!

What is Trigonometry?
Trigonometry comes from Greek words meaning "triangle measurement." It's the study of relationships between angles and sides in triangles, with applications extending far beyond geometry into physics, engineering, and astronomy.

The Right Triangle Foundation:
Trigonometry begins with right triangles - triangles with one 90° angle.

In a right triangle, we have:
- Hypotenuse: The longest side (opposite the right angle)
- Adjacent side: The side next to the angle we're considering
- Opposite side: The side across from the angle we're considering

The Big Three: Sine, Cosine, and Tangent

For any acute angle θ (theta) in a right triangle:

Sine (sin): sin θ = opposite/hypotenuse
Cosine (cos): cos θ = adjacent/hypotenuse  
Tangent (tan): tan θ = opposite/adjacent

Memory Device - SOH CAH TOA:
- SOH: Sine = Opposite/Hypotenuse
- CAH: Cosine = Adjacent/Hypotenuse
- TOA: Tangent = Opposite/Adjacent

Why These Ratios Matter:
These ratios are constant for any given angle, regardless of the triangle's size. This makes them incredibly powerful tools for solving problems.

Example Problem:
In a right triangle, if one angle is 30° and the hypotenuse is 10 units:
- sin 30° = 0.5, so opposite side = 10 × 0.5 = 5 units
- cos 30° ≈ 0.866, so adjacent side = 10 × 0.866 ≈ 8.66 units

Special Right Triangles:

30-60-90 Triangle:
- Angles: 30°, 60°, 90°
- Side ratios: 1 : √3 : 2
- sin 30° = 1/2, cos 30° = √3/2, tan 30° = 1/√3

45-45-90 Triangle:
- Angles: 45°, 45°, 90°
- Side ratios: 1 : 1 : √2
- sin 45° = √2/2, cos 45° = √2/2, tan 45° = 1

Key Angle Values to Memorize:
- sin 0° = 0, cos 0° = 1, tan 0° = 0
- sin 30° = 1/2, cos 30° = √3/2, tan 30° = √3/3
- sin 45° = √2/2, cos 45° = √2/2, tan 45° = 1
- sin 60° = √3/2, cos 60° = 1/2, tan 60° = √3
- sin 90° = 1, cos 90° = 0, tan 90° = undefined

Reciprocal Functions:
- Cosecant (csc): csc θ = 1/sin θ = hypotenuse/opposite
- Secant (sec): sec θ = 1/cos θ = hypotenuse/adjacent
- Cotangent (cot): cot θ = 1/tan θ = adjacent/opposite

Real-World Applications:

Navigation:
Pilots and sailors use trigonometry to calculate distances and directions.

Construction:
Architects use trig to calculate roof angles, ramp slopes, and structural supports.

Astronomy:
Astronomers measure distances to stars and planets using trigonometric principles.

Physics:
Trigonometry describes wave motion, oscillations, and circular motion.

Technology:
Computer graphics, GPS systems, and engineering all rely heavily on trigonometry.

Problem-Solving Strategy:

1. Draw and Label:
Sketch the triangle and clearly label the given information.

2. Identify the Angle:
Determine which angle you're working with.

3. Identify Sides:
Relative to your angle, identify opposite, adjacent, and hypotenuse.

4. Choose the Right Ratio:
Based on what you know and what you need to find.

5. Set Up the Equation:
Write the trigonometric equation.

6. Solve:
Use algebra to find the unknown value.

Types of Problems:

Finding Missing Sides:
Given an angle and one side, find another side.

Finding Missing Angles:
Given two sides, find an angle using inverse trig functions.

Angle of Elevation/Depression:
Real-world problems involving looking up or down at an angle.

Example Applications:

Height of Building:
From 100 feet away, the angle of elevation to the top of a building is 30°.
Height = 100 × tan 30° = 100 × (√3/3) ≈ 57.7 feet

Ladder Safety:
A 20-foot ladder leans against a wall at a 75° angle.
Distance from wall = 20 × cos 75° ≈ 5.2 feet

Calculator Usage:
Make sure your calculator is in the correct mode:
- Degree mode for angle measurements in degrees
- Radian mode for angle measurements in radians

Common Mistakes to Avoid:
- Confusing opposite and adjacent sides
- Using wrong trigonometric ratio
- Calculator in wrong mode (degrees vs radians)
- Not labeling triangles clearly
- Forgetting to identify the reference angle

Study Tips for Success:
- Practice identifying sides relative to different angles
- Memorize special angle values
- Work with real objects to visualize problems
- Use mnemonics like SOH CAH TOA
- Check answers for reasonableness

Building Intuition:
- sin θ increases as angle increases (0° to 90°)
- cos θ decreases as angle increases (0° to 90°)
- tan θ increases rapidly as angle approaches 90°
- For complementary angles: sin θ = cos(90° - θ)

This foundation prepares you for the unit circle, trigonometric identities, and applications in calculus and physics!""",
                   'summary': 'Introduction to trigonometric ratios, special triangles, and fundamental applications in right triangle geometry.',
                   'objectives': ['Master the three basic trigonometric ratios', 'Solve right triangle problems using SOH CAH TOA', 'Apply trigonometry to real-world situations']
               }
           },
           'calculus': {
               1: {
                   'title': 'Understanding Limits and Continuity',
                   'content': f"""Welcome to calculus - the mathematics of change and motion!

What is Calculus?
Calculus is the study of continuous change. It has two main branches:
- Differential Calculus: Rates of change (derivatives)
- Integral Calculus: Accumulation of quantities (integrals)

The Foundation: Limits

What is a Limit?
A limit describes the value that a function approaches as the input approaches a certain value.

Notation: lim[x→a] f(x) = L
This reads: "The limit of f(x) as x approaches a equals L"

Intuitive Understanding:
Imagine walking toward a wall. Even though you never actually touch the wall, you can get arbitrarily close. The limit is like that wall - the value you're approaching.

Types of Limits:

One-Sided Limits:
- Left-hand limit: lim[x→a⁻] f(x) (approaching from the left)
- Right-hand limit: lim[x→a⁺] f(x) (approaching from the right)

For a limit to exist: Left-hand limit = Right-hand limit

Infinite Limits:
When function values grow without bound:
lim[x→a] f(x) = ∞ or lim[x→a] f(x) = -∞

Limits at Infinity:
Behavior of functions as x gets very large:
lim[x→∞] f(x) or lim[x→-∞] f(x)

Finding Limits:

Direct Substitution:
If the function is continuous at the point, simply substitute:
lim[x→2] (x² + 3x - 1) = 2² + 3(2) - 1 = 9

Factoring Method:
For indeterminate forms like 0/0:
lim[x→2] (x² - 4)/(x - 2) = lim[x→2] (x + 2)(x - 2)/(x - 2) = lim[x→2] (x + 2) = 4

Rationalization:
For limits involving square roots:
Multiply by conjugate to eliminate radicals

L'Hôpital's Rule:
For 0/0 or ∞/∞ forms:
lim[x→a] f(x)/g(x) = lim[x→a] f'(x)/g'(x)

Squeeze Theorem:
If g(x) ≤ f(x) ≤ h(x) and lim[x→a] g(x) = lim[x→a] h(x) = L,
then lim[x→a] f(x) = L

Continuity:

Definition of Continuity:
A function f(x) is continuous at x = a if:
1. f(a) exists
2. lim[x→a] f(x) exists  
3. lim[x→a] f(x) = f(a)

Types of Discontinuities:

Removable Discontinuity:
A "hole" in the graph that can be "filled" by redefining the function at one point.

Jump Discontinuity:
Left and right limits exist but are different.

Infinite Discontinuity:
Function approaches ±∞ at the point.

Continuous Functions:
- Polynomial functions are continuous everywhere
- Rational functions are continuous except where denominator = 0
- Trigonometric functions are continuous on their domains
- Exponential and logarithmic functions are continuous on their domains

Intermediate Value Theorem:
If f is continuous on [a,b] and N is between f(a) and f(b), then there exists c in [a,b] such that f(c) = N.

Applications: This guarantees that continuous functions take on all intermediate values.

Real-World Applications:

Physics:
- Velocity as the limit of average velocity over shrinking time intervals
- Instantaneous rate of change

Economics:
- Marginal cost and revenue as limits of average rates

Engineering:
- Stress analysis and material properties
- Control systems and feedback loops

Biology:
- Population growth rates
- Enzyme kinetics

Practical Examples:

Speed Limit:
If you drive 60 miles in 1 hour, your average speed is 60 mph. But your instantaneous speed at any moment might be different. The speedometer reading is essentially a limit - speed over an infinitesimally small time interval.

Temperature Change:
The rate at which temperature changes throughout the day can be modeled using limits and derivatives.

Problem-Solving Strategy:

1. Identify the Type:
Determine what kind of limit problem you're solving.

2. Try Direct Substitution:
If it works, you're done. If you get 0/0 or ∞/∞, use other methods.

3. Simplify if Possible:
Factor, rationalize, or use algebraic manipulation.

4. Apply Appropriate Technique:
Use the method that best fits the problem structure.

5. Verify Your Answer:
Check that your result makes sense graphically and numerically.

Common Limit Patterns:

Standard Limits:
- lim[x→0] (sin x)/x = 1
- lim[x→∞] (1 + 1/x)ˣ = e
- lim[x→0] (eˣ - 1)/x = 1
- lim[x→0] (ln(1 + x))/x = 1

Polynomial Limits at Infinity:
Determined by the highest degree terms

Rational Function Limits:
Compare degrees of numerator and denominator

Technology and Graphing:
- Use graphing calculators to visualize limit behavior
- Tables of values can approximate limits numerically
- Computer algebra systems can evaluate complex limits

Common Mistakes:
- Assuming a limit exists when it doesn't
- Incorrect application of limit laws
- Confusing limit value with function value
- Not recognizing indeterminate forms

Study Strategies:
- Practice with various function types
- Sketch graphs to visualize limit behavior
- Work with both algebraic and numerical approaches
- Connect limits to real-world scenarios
- Master basic limit patterns

This foundation in limits and continuity is essential for understanding derivatives, integrals, and all advanced calculus concepts!""",
                   'summary': 'Master the fundamental concept of limits and continuity as the foundation for all calculus operations and applications.',
                   'objectives': ['Evaluate limits using multiple techniques', 'Understand and identify continuity', 'Apply limit concepts to real-world problems']
               }
           }
       }
       
        templates = content_templates.get(topic.lower().split()[0], content_templates['algebra'])
        template_data = templates.get(difficulty, templates[1])
        
        return LearningContent(
            id=str(uuid.uuid4()),
            title=template_data['title'],
            type=resource_type,
            content=template_data['content'],
            summary=template_data['summary'],
            difficulty_level=difficulty,
            learning_style=learning_style,
            topic=topic,
            estimated_duration=15,
            prerequisites=[],
            learning_objectives=template_data['objectives']
        )