import React from 'react';
import { AnalysisResult as AnalysisType } from '../types/fantasy';
import { TrendingUp, Clock, CheckCircle, AlertTriangle } from 'lucide-react';

interface AnalysisResultProps {
  result: AnalysisType;
}

const AnalysisResult: React.FC<AnalysisResultProps> = ({ result }) => {
  const getGradeColor = (grade: string) => {
    const gradeUpper = grade.toUpperCase();
    if (gradeUpper.startsWith('A')) return 'text-green-600';
    if (gradeUpper.startsWith('B')) return 'text-blue-600';
    if (gradeUpper.startsWith('C')) return 'text-yellow-600';
    if (gradeUpper.startsWith('D')) return 'text-red-600';
    return 'text-red-800';
  };

  const getBrutalityColor = (score: number) => {
    if (score <= 3) return 'text-green-600 bg-green-50';
    if (score <= 6) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b pb-4">
        <h3 className="text-lg font-semibold text-gray-800">Team Analysis</h3>
        <div className="flex items-center space-x-4">
          <div className="text-center">
            <div className={`text-2xl font-bold ${getGradeColor(result.team_grade)}`}>
              {result.team_grade}
            </div>
            <div className="text-xs text-gray-500">Grade</div>
          </div>
          <div className="text-center">
            <div className={`text-2xl font-bold px-3 py-1 rounded-lg ${getBrutalityColor(result.brutality_score)}`}>
              {result.brutality_score}/10
            </div>
            <div className="text-xs text-gray-500">Brutality</div>
          </div>
        </div>
      </div>

      {/* Analysis Text */}
      <div className="prose prose-sm max-w-none">
        <div className="bg-gray-50 rounded-lg p-4 whitespace-pre-wrap font-mono text-sm">
          {result.analysis}
        </div>
      </div>

      {/* Recommendations */}
      {result.recommendations && result.recommendations.length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-800 mb-3 flex items-center">
            <TrendingUp size={16} className="mr-2 text-fantasy-600" />
            Key Recommendations
          </h4>
          <ul className="space-y-2">
            {result.recommendations.map((rec, index) => (
              <li key={index} className="flex items-start space-x-2">
                <CheckCircle size={16} className="text-green-500 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-700">{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Metadata */}
      <div className="border-t pt-4 space-y-3">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center space-x-2">
            <Clock size={14} className="text-gray-400" />
            <span className="text-gray-500">
              Analyzed at {new Date(result.timestamp).toLocaleString()}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-gray-500">Confidence:</span>
            <span className="font-semibold text-fantasy-600">
              {Math.round(result.confidence_score * 100)}%
            </span>
          </div>
        </div>

        {/* Data Sources */}
        <div>
          <span className="text-sm text-gray-500 mb-2 block">Data Sources:</span>
          <div className="flex flex-wrap gap-2">
            {Object.entries(result.data_sources).map(([source, available]) => (
              <span
                key={source}
                className={`px-2 py-1 rounded-full text-xs ${
                  available 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-gray-100 text-gray-600'
                }`}
              >
                {source.replace('_', ' ').toUpperCase()}
                {available ? ' ✓' : ' ✗'}
              </span>
            ))}
          </div>
        </div>

        {/* Execution Summary */}
        {result.execution_summary && (
          <details className="text-sm">
            <summary className="cursor-pointer text-gray-500 hover:text-gray-700">
              Execution Details ({result.execution_summary.steps_completed.length} steps completed)
            </summary>
            <div className="mt-2 p-3 bg-gray-50 rounded text-xs">
              <div className="space-y-1">
                {result.execution_summary.steps_completed.map((step, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <CheckCircle size={12} className="text-green-500" />
                    <span>{step}</span>
                  </div>
                ))}
              </div>
              {result.execution_summary.errors.length > 0 && (
                <div className="mt-3 pt-3 border-t">
                  <div className="text-red-600 font-medium mb-1">Errors:</div>
                  {result.execution_summary.errors.map((error, index) => (
                    <div key={index} className="flex items-center space-x-2">
                      <AlertTriangle size={12} className="text-red-500" />
                      <span>{error}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </details>
        )}
      </div>
    </div>
  );
};

export default AnalysisResult;