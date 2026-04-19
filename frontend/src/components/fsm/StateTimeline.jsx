import { Clock } from 'lucide-react';

const StateTimeline = ({ history }) => {
  if (!history || history.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">State History</h2>
        <p className="text-gray-500 text-center py-8">No history available yet</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-6">State History</h2>

      <div className="space-y-4">
        {history.map((entry, index) => (
          <div key={index} className="flex gap-4">
            {/* Timeline dot */}
            <div className="flex flex-col items-center">
              <div className="w-4 h-4 rounded-full bg-blue-500 mt-1"></div>
              {index < history.length - 1 && (
                <div className="w-1 h-12 bg-blue-200"></div>
              )}
            </div>

            {/* Entry content */}
            <div className="flex-1 pb-4">
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="font-semibold text-gray-900">
                      {entry.from_state} → {entry.to_state}
                    </p>
                    <p className="text-sm text-blue-600 font-medium">
                      Event: {entry.event.replace(/_/g, ' ').toUpperCase()}
                    </p>
                  </div>
                  <div className="flex items-center gap-1 text-gray-500 text-xs">
                    <Clock className="w-3 h-3" />
                    {new Date(entry.timestamp).toLocaleTimeString()}
                  </div>
                </div>

                {entry.context && Object.keys(entry.context).length > 0 && (
                  <div className="text-xs text-gray-600 mt-2 p-2 bg-white rounded border border-gray-200">
                    <p className="font-medium mb-1">Context:</p>
                    <pre className="text-xs overflow-auto">
                      {JSON.stringify(entry.context, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-700">
        📊 Total transitions: <span className="font-bold">{history.length}</span>
      </div>
    </div>
  );
};

export default StateTimeline;