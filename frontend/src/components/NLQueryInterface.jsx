import { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { executeNLQuery } from '../services/api';

const NLQueryInterface = () => {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const exampleQueries = [
    "Affiche les 5 zones les plus polluées",
    "Combien de capteurs sont hors service ?",
    "Quels citoyens ont un score écologique > 80 ?",
    "Donne-moi le trajet le plus économique en CO2",
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await executeNLQuery(query);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Query execution failed');
    } finally {
      setLoading(false);
    }
  };

  const handleExampleClick = (exampleQuery) => {
    setQuery(exampleQuery);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">
        Requête en Langage Naturel
      </h2>

      {/* Query Input */}
      <form onSubmit={handleSubmit} className="mb-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ex: Affiche les 5 zones les plus polluées"
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Traitement...
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                Exécuter
              </>
            )}
          </button>
        </div>
      </form>

      {/* Example Queries */}
      <div className="mb-6">
        <p className="text-sm text-gray-600 mb-2">Exemples de requêtes :</p>
        <div className="flex flex-wrap gap-2">
          {exampleQueries.map((example, index) => (
            <button
              key={index}
              onClick={() => handleExampleClick(example)}
              className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200 transition-colors"
            >
              {example}
            </button>
          ))}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
          <strong>Erreur:</strong> {error}
        </div>
      )}

      {/* Results Display */}
      {result && (
        <div className="space-y-4">
          {/* Generated SQL */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">SQL Généré:</h3>
            <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm">
              {result.sql}
            </pre>
          </div>

          {/* Results Table */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">
              Résultats ({result.count} ligne{result.count > 1 ? 's' : ''}):
            </h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {result.results.length > 0 &&
                      Object.keys(result.results[0]).map((key) => (
                        <th
                          key={key}
                          className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                          {key}
                        </th>
                      ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {result.results.map((row, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      {Object.values(row).map((value, i) => (
                        <td key={i} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {typeof value === 'number' ? value.toFixed(2) : value}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NLQueryInterface;