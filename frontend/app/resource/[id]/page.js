'use client';
import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiClient } from '../../../lib/api';
import Button from '../../../components/ui/Button';
import Card, { CardContent, CardHeader } from '../../../components/ui/Card';
import LoadingSpinner from '../../../components/ui/LoadingSpinner';
import { getLearningStyleName } from '../../../lib/utils';
import toast from 'react-hot-toast';

export default function ResourcePage({ params }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { id: resourceId } = params;
  const learnerId = searchParams.get('learner');
  
  const [isLoading, setIsLoading] = useState(true);
  const [resource, setResource] = useState(null);

  useEffect(() => {
    if (resourceId) {
      loadResource();
    }
  }, [resourceId]);

  const loadResource = async () => {
    try {
      setIsLoading(true);
      console.log('Loading resource:', resourceId);
      
      const response = await apiClient.getResource(resourceId);
      console.log('Resource response:', response);
      
      if (response.success && response.data) {
        setResource(response.data);
      } else {
        throw new Error(response.error || 'Failed to load resource');
      }
    } catch (error) {
      console.error('Error loading resource:', error);
      toast.error('Failed to load learning resource');
      router.back();
    } finally {
      setIsLoading(false);
    }
  };

  const handleTakeQuiz = () => {
    if (learnerId) {
      router.push(`/quiz/${resourceId}?learner=${learnerId}`);
    } else {
      toast.error('Learner ID not found');
    }
  };

  const handleBackToPath = () => {
    if (learnerId) {
      router.push(`/learning-path/${learnerId}`);
    } else {
      router.back();
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-indigo-50 flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="xl" />
          <p className="mt-4 text-gray-600">Loading learning content...</p>
        </div>
      </div>
    );
  }

  if (!resource) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-indigo-50 flex items-center justify-center">
        <Card className="max-w-md w-full mx-4 shadow-xl border-0 bg-white/80 backdrop-blur-sm">
          <CardContent className="text-center py-16">
            <div className="text-6xl mb-4">📚</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Resource Not Found</h2>
            <p className="text-gray-600 mb-6">
              The learning resource you're looking for doesn't exist.
            </p>
            <Button onClick={() => router.back()} className="w-full">
              <span className="mr-2">←</span>
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-indigo-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <Button
              variant="outline"
              onClick={handleBackToPath}
              className="border-purple-600 text-purple-600 hover:bg-purple-600 hover:text-white"
            >
              <span className="mr-2">←</span>
              Back to Path
            </Button>
          </div>
          <Button
            onClick={handleTakeQuiz}
            className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800"
          >
            <span className="mr-2">📝</span>
            Take Quiz
          </Button>
        </div>

        {/* Resource Header */}
        <Card className="mb-8 shadow-xl border-0 bg-white/80 backdrop-blur-sm">
          <CardContent className="p-8">
            <div className="flex items-start space-x-6 mb-6">
              <div className="flex-shrink-0">
                <div className="w-24 h-24 bg-gradient-to-br from-purple-100 to-purple-200 rounded-2xl flex items-center justify-center shadow-lg">
                  <span className="text-5xl">
                    {resource.type === 'lesson' ? '📖' : 
                     resource.type === 'interactive' ? '🎮' : 
                     resource.type === 'video_script' ? '🎥' : '📝'}
                  </span>
                </div>
              </div>
              <div className="flex-1">
                <h1 className="text-4xl font-bold text-gray-900 mb-4">
                  {resource.title}
                </h1>
                
                {resource.summary && (
                  <p className="text-xl text-gray-600 mb-6 leading-relaxed">
                    {resource.summary}
                  </p>
                )}

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <div className="flex items-center space-x-2 text-gray-600">
                    <span className="text-lg">📖</span>
                    <div>
                      <div className="text-xs text-gray-500">Type</div>
                      <div className="font-medium capitalize">{resource.type.replace('_', ' ')}</div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 text-gray-600">
                    <span className="text-lg">🎯</span>
                    <div>
                      <div className="text-xs text-gray-500">Topic</div>
                      <div className="font-medium capitalize">{resource.topic}</div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 text-gray-600">
                    <span className="text-lg">🏆</span>
                    <div>
                      <div className="text-xs text-gray-500">Difficulty</div>
                      <div className="font-medium">Level {resource.difficulty_level}/5</div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 text-gray-600">
                    <span className="text-lg">⏱️</span>
                    <div>
                      <div className="text-xs text-gray-500">Duration</div>
                      <div className="font-medium">{resource.estimated_duration || 15} min</div>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <span className="inline-flex items-center px-4 py-2 rounded-full text-sm font-medium bg-purple-100 text-purple-800 border border-purple-200">
                    <span className="mr-2">🧠</span>
                    {getLearningStyleName(resource.learning_style)} Optimized
                  </span>
                  <span className="inline-flex items-center px-4 py-2 rounded-full text-sm font-medium bg-blue-100 text-blue-800 border border-blue-200">
                    <span className="mr-2">🤖</span>
                    AI Generated
                  </span>
                </div>
              </div>
            </div>

            {/* Learning Objectives */}
            {resource.learning_objectives && resource.learning_objectives.length > 0 && (
              <div className="mb-8 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl">
                <h3 className="text-lg font-semibold text-blue-900 mb-4 flex items-center">
                  <span className="mr-2">🎯</span>
                  Learning Objectives
                </h3>
                <ul className="space-y-2">
                  {resource.learning_objectives.map((objective, index) => (
                    <li key={index} className="flex items-start space-x-3 text-blue-800">
                      <span className="text-blue-600 font-bold">•</span>
                      <span>{objective}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Main Content */}
        <Card className="mb-8 shadow-xl border-0 bg-white/80 backdrop-blur-sm">
          <CardHeader>
            <h2 className="text-2xl font-bold text-gray-900 flex items-center">
              <span className="text-2xl mr-3">📚</span>
              Learning Content
            </h2>
          </CardHeader>
          <CardContent>
            <div className="prose prose-lg max-w-none">
              <div 
                className="text-gray-700 leading-relaxed whitespace-pre-line"
                style={{ lineHeight: '1.8' }}
              >
                {resource.content}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Next Steps */}
        <Card className="shadow-xl border-0 bg-white/80 backdrop-blur-sm">
          <CardContent className="p-8 text-center">
            <div className="text-6xl mb-4">🎯</div>
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              Ready to Test Your Knowledge?
            </h3>
            <p className="text-gray-600 mb-8 max-w-2xl mx-auto">
              Great job completing this learning resource! Now it's time to put your new knowledge to the test 
              with a personalized quiz designed specifically for this content.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                onClick={handleTakeQuiz}
                className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 shadow-lg"
                size="lg"
              >
                <span className="mr-2">📝</span>
                Take Quiz Now
              </Button>
              <Button
                onClick={handleBackToPath}
                variant="outline"
                className="border-purple-600 text-purple-600 hover:bg-purple-600 hover:text-white"
                size="lg"
              >
                <span className="mr-2">🛤️</span>
                Back to Learning Path
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}