import { useState, useEffect } from 'react';
import { Download, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react';
import { 
  getAirQualityReport, 
  getTrafficAnalysis, 
  getAllSensors,
  getSensorRecommendation 
} from '../services/api';

const AIReports = () => {
  const [activeTab, setActiveTab] = useState('air-quality');
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);
  const [zoneId, setZoneId] = useState(null);
  const [selectedSensor, setSelectedSensor] = useState(null);
  const [sensors, setSensors] = useState([]);

  // Load sensors on mount
  useEffect(() => {
    const fetchSensors = async () => {
      try {
        const data = await getAllSensors();
        setSensors(data);
      } catch (err) {
        console.error('Failed to load sensors:', err);
      }
    };
    fetchSensors();
  }, []);

  const handleGenerateReport = async () => {
    setLoading(true);
    setError(null);
    setReport(null);

    try {
      let data;

      if (activeTab === 'air-quality') {
        data = await getAirQualityReport(zoneId, null);
      } else if (activeTab === 'traffic') {
        data = await getTrafficAnalysis(zoneId);
      } else if (activeTab === 'maintenance' && selectedSensor) {
        data = await getSensorRecommendation(selectedSensor);
      }

      setReport(data);
    } catch (err) {
      setError(err.message || 'Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = () => {
    if (!report) return;

    const text = `
${report.type.toUpperCase()} REPORT
Generated: ${new Date().toLocaleString('fr-FR')}

${report.content}

---
Neo-Sousse 2030 Smart City System
    `;

    const blob = new Blob([text], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `rapport-${report.type}-${new Date().getTime()}.txt`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const handlePrint = () => {
    if (!report) return;

    const printWindow = window.open('', '', 'height=600,width=800');
    printWindow.document.write(`
      <html>
        <head>
          <title>Rapport - ${report.type}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            h1 { color: #1f2937; border-bottom: 3px solid #3b82f6; }
            .content { white-space: pre-wrap; line-height: 1.6; }
            .footer { margin-top: 30px; font-size: 12px; color: #666; }
          </style>
        </head>
        <body>
          <h1>${report.type.toUpperCase()} REPORT</h1>
          <div class="content">${report.content}</div>
          <div class="footer">
            Generated: ${new Date().toLocaleString('fr-FR')}<br>
            Neo-Sousse 2030 Smart City System
          </div>
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.print();
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">🤖 Rapports IA Générative</h2>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('air-quality')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'air-quality'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          📊 Qualité de l'Air
        </button>
        <button
          onClick={() => setActiveTab('traffic')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'traffic'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          🚗 Analyse Trafic
        </button>
        <button
          onClick={() => setActiveTab('maintenance')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'maintenance'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          🔧 Maintenance
        </button>
      </div>

      {/* Tab Content */}
      <div className="mb-6">
        {activeTab === 'air-quality' && (
          <div className="space-y-4">
            <p className="text-gray-600">Générer un rapport sur la qualité de l'air</p>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Zone (optionnel)
              </label>
              <input
                type="number"
                value={zoneId || ''}
                onChange={(e) => setZoneId(e.target.value ? parseInt(e.target.value) : null)}
                placeholder="Laisser vide pour toutes les zones"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        )}

        {activeTab === 'traffic' && (
          <div className="space-y-4">
            <p className="text-gray-600">Analyser les patterns de trafic des 7 derniers jours</p>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Zone (optionnel)
              </label>
              <input
                type="number"
                value={zoneId || ''}
                onChange={(e) => setZoneId(e.target.value ? parseInt(e.target.value) : null)}
                placeholder="Laisser vide pour toutes les zones"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        )}

        {activeTab === 'maintenance' && (
          <div className="space-y-4">
            <p className="text-gray-600">Obtenir une recommandation de maintenance pour un capteur</p>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sélectionner un capteur
              </label>
              <select
                value={selectedSensor || ''}
                onChange={(e) => setSelectedSensor(e.target.value || null)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Choisir un capteur...</option>
                {sensors.map((sensor) => (
                  <option key={sensor.capteur_id} value={sensor.capteur_id}>
                    {sensor.capteur_id} - {sensor.type_capteur} ({sensor.statut})
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Generate Button */}
      <button
        onClick={handleGenerateReport}
        disabled={
          loading ||
          (activeTab === 'maintenance' && !selectedSensor)
        }
        className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
      >
        <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
        {loading ? 'Génération en cours...' : 'Générer Rapport'}
      </button>

      {/* Error Message */}
      {error && (
        <div className="mt-6 p-4 bg-red-100 border border-red-400 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-red-800">Erreur</h3>
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Report Display */}
      {report && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <h3 className="font-semibold text-gray-900">Rapport Généré</h3>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handlePrint}
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium rounded-lg transition-colors"
              >
                🖨️ Imprimer
              </button>
              <button
                onClick={handleExport}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg transition-colors flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Télécharger
              </button>
            </div>
          </div>

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
            <pre className="text-sm text-gray-800 whitespace-pre-wrap font-sans overflow-auto max-h-96">
              {report.content}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIReports;