"""
AI Generative Module for Neo-Sousse 2030
UPDATED: PostgreSQL + OpenRouter API (free tier available)
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import psycopg2
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ✅ CHANGE 1: PostgreSQL configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_NAME = os.getenv('DB_NAME', 'neo_sousse_2030')
DB_PORT = os.getenv('DB_PORT', '5432')

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )


class AIGenerator:
    """AI-powered content generator using OpenRouter API"""
    
    def __init__(self, api_key: Optional[str] = None, db_path: str = "neo_sousse.db", 
                 use_openrouter: bool = True):
        """
        Initialize AI Generator
        
        Args:
            api_key: API key (if None, reads from environment)
            db_path: Not used in PostgreSQL mode, kept for compatibility
            use_openrouter: If True, use OpenRouter API (default), else use OpenAI
        """
        self.use_openrouter = use_openrouter
        
        if use_openrouter:
            self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
            self.base_url = "https://openrouter.ai/api/v1"
            self.model = "openrouter/auto"
        else:
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            self.base_url = "https://api.openai.com/v1"
            self.model = "gpt-4o-mini"
        
        if not self.api_key:
            raise ValueError(
                "API key required. Set OPENROUTER_API_KEY environment variable "
                "or pass api_key parameter. Get free key at: https://openrouter.ai/keys"
            )
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        self.db_path = db_path
        
        print(f"✓ AI Generator initialized")
        print(f"  Provider: {'OpenRouter' if use_openrouter else 'OpenAI'}")
        print(f"  Model: {self.model}")
    
    def _query_database(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute database query using PostgreSQL and return results as list of dicts"""
        # ✅ CHANGE 2: Use PostgreSQL
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            cursor.close()
            return results
        finally:
            if conn:
                conn.close()
    
    def _call_ai(self, system_prompt: str, user_prompt: str, 
                 temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Make API call (works with both OpenRouter and OpenAI)"""
        try:
            extra_headers = {}
            if self.use_openrouter:
                extra_headers = {
                    "HTTP-Referer": "https://github.com/neo-sousse-2030",
                    "X-Title": "Neo-Sousse 2030 Smart City"
                }
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                extra_headers=extra_headers if extra_headers else None
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Erreur lors de la génération: {str(e)}"
    
    # ========================================================================
    # AIR QUALITY REPORTS
    # ========================================================================
    
    def generate_air_quality_report(self, zone_id: Optional[int] = None, 
                                    date_str: Optional[str] = None) -> str:
        """Generate natural language air quality report"""
        
        # ✅ CHANGE 3: Use %s instead of ? and CAST for PostgreSQL
        query = """
            SELECT 
                z.nom as zone_name,
                m.type_mesure,
                AVG(m.valeur) as avg_value,
                MAX(m.valeur) as max_value,
                MIN(m.valeur) as min_value,
                SUM(CASE WHEN m.est_anomalie = TRUE THEN 1 ELSE 0 END) as anomaly_count,
                COUNT(*) as total_measurements
            FROM mesures m
            JOIN capteurs c ON m.capteur_id = c.capteur_id
            JOIN zones z ON c.zone_id = z.zone_id
            WHERE c.type_capteur = 'air'
        """
        
        params = []
        if zone_id:
            query += " AND z.zone_id = %s"
            params.append(zone_id)
        
        if date_str:
            query += " AND DATE(m.timestamp) = %s"
            params.append(date_str)
        else:
            query += " AND DATE(m.timestamp) = CURRENT_DATE"
        
        query += " GROUP BY z.nom, m.type_mesure ORDER BY z.nom, m.type_mesure"
        
        data = self._query_database(query, tuple(params))
        
        if not data:
            return "Aucune donnée de qualité de l'air disponible pour la période demandée."
        
        data_summary = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        
        date_display = date_str or datetime.now().strftime("%d/%m/%Y")
        zone_display = f"zone {zone_id}" if zone_id else "toutes les zones"
        
        system_prompt = f"""Tu es un expert en qualité de l'air pour la ville de Sousse. 
Tu génères des rapports clairs et professionnels en français pour les autorités municipales.

Contexte: Système de surveillance Neo-Sousse 2030
Date du rapport: {date_display}
Zone(s): {zone_display}

Ton rapport doit:
1. Commencer par un titre clair
2. Résumer l'état général de la qualité de l'air
3. Identifier les zones/polluants problématiques (si applicable)
4. Mentionner les anomalies détectées
5. Conclure avec des recommandations si nécessaire

Utilise un ton professionnel mais accessible. Mets en avant les chiffres importants.
"""
        
        user_prompt = f"""Génère un rapport de qualité de l'air basé sur ces données:

{data_summary}

Note: 
- PM2.5 seuil recommandé: 25 µg/m³
- CO2 seuil: 1000 ppm
- NO2 seuil: 40 µg/m³
"""
        
        return self._call_ai(system_prompt, user_prompt, temperature=0.5, max_tokens=800)
    
    # ========================================================================
    # SENSOR MAINTENANCE RECOMMENDATIONS
    # ========================================================================
    
    def generate_maintenance_recommendation(self, capteur_id: str) -> str:
        """Generate maintenance recommendation for a specific sensor"""
        
        # ✅ CHANGE 3: Use %s instead of ? and INTERVAL for PostgreSQL
        query = """
            SELECT 
                c.capteur_id,
                c.type_capteur,
                c.statut,
                c.taux_erreur,
                c.nb_anomalies_totales,
                c.seuil_alerte,
                c.date_installation,
                z.nom as zone_name,
                COUNT(m.mesure_id) as total_measurements,
                SUM(CASE WHEN m.est_anomalie = TRUE THEN 1 ELSE 0 END) as recent_anomalies
            FROM capteurs c
            JOIN zones z ON c.zone_id = z.zone_id
            LEFT JOIN mesures m ON c.capteur_id = m.capteur_id 
                AND m.timestamp >= NOW() - INTERVAL '7 days'
            WHERE c.capteur_id = %s
            GROUP BY c.capteur_id, z.zone_id, z.nom
        """
        
        data = self._query_database(query, (capteur_id,))
        
        if not data:
            return f"Capteur {capteur_id} introuvable dans la base de données."
        
        sensor_info = data[0]
        
        # ✅ CHANGE 3: Use %s instead of ?
        intervention_query = """
            SELECT statut, date_demande
            FROM interventions
            WHERE capteur_id = %s
            ORDER BY date_demande DESC
            LIMIT 1
        """
        interventions = self._query_database(intervention_query, (capteur_id,))
        
        sensor_data = json.dumps(sensor_info, indent=2, ensure_ascii=False, default=str)
        intervention_data = json.dumps(interventions, indent=2, ensure_ascii=False, default=str) if interventions else "Aucune"
        
        system_prompt = """Tu es un expert en maintenance de capteurs IoT pour le système Neo-Sousse 2030.
Tu analyses l'état des capteurs et génères des recommandations techniques précises en français.

Ton analyse doit considérer:
1. Le taux d'erreur (seuil critique: 15%)
2. Le nombre d'anomalies récentes
3. L'état actuel du capteur
4. Les interventions en cours
5. L'ancienneté du capteur

Ta recommandation doit:
- Être concise et actionnable
- Indiquer le niveau d'urgence (urgent, moyen, faible)
- Proposer des actions concrètes
- Estimer si une intervention est nécessaire
"""
        
        user_prompt = f"""Analyse ce capteur et génère une recommandation de maintenance:

Données du capteur:
{sensor_data}

Interventions existantes:
{intervention_data}

Génère une recommandation structurée avec:
1. État général du capteur
2. Niveau d'urgence
3. Actions recommandées
4. Estimation du temps d'intervention
"""
        
        return self._call_ai(system_prompt, user_prompt, temperature=0.3, max_tokens=600)
    
    # ========================================================================
    # TRAFFIC ANALYSIS
    # ========================================================================
    
    def generate_traffic_analysis(self, zone_id: Optional[int] = None) -> str:
        """Generate traffic pattern analysis"""
        
        # ✅ CHANGE 3: Use %s and EXTRACT for PostgreSQL instead of strftime
        query = """
            SELECT 
                z.nom as zone_name,
                COUNT(DISTINCT t.trajet_id) as total_trips,
                SUM(t.distance_km) as total_distance,
                SUM(t.economie_co2) as total_co2_saved,
                AVG(t.distance_km) as avg_trip_distance,
                COUNT(DISTINCT t.vehicule_id) as unique_vehicles,
                CASE 
                    WHEN EXTRACT(HOUR FROM t.timestamp_depart) BETWEEN 7 AND 9 THEN 'Matin (7-9h)'
                    WHEN EXTRACT(HOUR FROM t.timestamp_depart) BETWEEN 12 AND 14 THEN 'Midi (12-14h)'
                    WHEN EXTRACT(HOUR FROM t.timestamp_depart) BETWEEN 17 AND 19 THEN 'Soir (17-19h)'
                    ELSE 'Heures creuses'
                END as time_period,
                COUNT(*) as trips_in_period
            FROM trajets t
            JOIN zones z ON t.zone_depart_id = z.zone_id
            WHERE t.timestamp_depart >= NOW() - INTERVAL '7 days'
        """
        
        params = []
        if zone_id:
            query += " AND z.zone_id = %s"
            params.append(zone_id)
        
        query += " GROUP BY z.nom, time_period ORDER BY z.nom, trips_in_period DESC"
        
        data = self._query_database(query, tuple(params))
        
        if not data:
            return "Aucune donnée de trafic disponible pour la période demandée."
        
        data_summary = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        
        system_prompt = """Tu es un analyste en mobilité urbaine pour Neo-Sousse 2030.
Tu génères des analyses de trafic claires et exploitables en français.

Ton analyse doit:
1. Identifier les patterns de trafic (heures de pointe, zones congestionnées)
2. Quantifier l'impact écologique (CO2 économisé)
3. Proposer des optimisations possibles
4. Comparer les différentes zones si applicable

Utilise un ton analytique mais compréhensible pour les décideurs urbains.
"""
        
        user_prompt = f"""Génère une analyse de trafic basée sur ces données (7 derniers jours):

{data_summary}

Inclus dans ton analyse:
1. Résumé des patterns de déplacement
2. Heures de pointe identifiées
3. Impact écologique (CO2)
4. Recommandations d'optimisation
"""
        
        return self._call_ai(system_prompt, user_prompt, temperature=0.5, max_tokens=800)
    
    # ========================================================================
    # FSM TRANSITION VALIDATION
    # ========================================================================
    
    def validate_fsm_transition(self, entity_type: str, current_state: str, 
                               proposed_event: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to validate if a state transition makes logical sense"""
        
        context_str = json.dumps(context, indent=2, ensure_ascii=False, default=str)
        
        system_prompt = f"""Tu es un validateur de transitions d'états pour le système Neo-Sousse 2030.
Tu analyses si une transition d'état proposée est logique et appropriée.

Type d'entité: {entity_type}

Règles FSM:
- Sensor: inactif → actif → signalé → en_maintenance → hors_service
- Intervention: demande → tech1_assigné → tech2_validé → ia_validé → terminé
- Vehicle: stationné → en_route → arrivé (ou en_panne)

Ta validation doit considérer:
1. La logique métier du domaine
2. Le contexte actuel de l'entité
3. Les contraintes temporelles/opérationnelles
4. Les dépendances entre états

Réponds UNIQUEMENT en JSON avec:
{{
  "is_valid": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "explication détaillée",
  "alternative": "suggestion si invalide (optionnel)"
}}
"""
        
        user_prompt = f"""Valide cette transition:

État actuel: {current_state}
Événement proposé: {proposed_event}

Contexte:
{context_str}

Est-ce que cette transition est logique et appropriée?
"""
        
        try:
            response = self._call_ai(system_prompt, user_prompt, temperature=0.2, max_tokens=400)
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            return {
                "is_valid": None,
                "confidence": 0.0,
                "reasoning": f"Réponse du modèle non parsable: {response}"
            }
    
    # ========================================================================
    # CITIZEN ECO-SCORE REPORT
    # ========================================================================
    
    def generate_eco_score_report(self, citoyen_id: int) -> str:
        """Generate personalized eco-score report for a citizen"""
        
        # ✅ CHANGE 3: Use %s and INTERVAL for PostgreSQL
        query = """
            SELECT 
                c.nom,
                c.email,
                c.score_ecologique,
                z.nom as zone_name,
                COUNT(DISTINCT v.vehicule_id) as vehicle_count,
                COUNT(DISTINCT t.trajet_id) as total_trips,
                SUM(t.distance_km) as total_distance,
                SUM(t.economie_co2) as total_co2_saved
            FROM citoyens c
            LEFT JOIN zones z ON c.zone_id = z.zone_id
            LEFT JOIN vehicules v ON c.citoyen_id = v.citoyen_id
            LEFT JOIN trajets t ON v.vehicule_id = t.vehicule_id
                AND t.timestamp_depart >= NOW() - INTERVAL '30 days'
            WHERE c.citoyen_id = %s
            GROUP BY c.citoyen_id, z.zone_id, z.nom
        """
        
        data = self._query_database(query, (citoyen_id,))
        
        if not data:
            return f"Citoyen {citoyen_id} introuvable."
        
        citizen_data = json.dumps(data[0], indent=2, ensure_ascii=False, default=str)
        
        system_prompt = """Tu es un conseiller en mobilité durable pour Neo-Sousse 2030.
Tu génères des rapports personnalisés sur l'empreinte écologique des citoyens.

Ton rapport doit:
1. Féliciter les bonnes pratiques
2. Quantifier l'impact positif (CO2 économisé)
3. Suggérer des améliorations concrètes
4. Comparer au score moyen de la ville (score moyen: 65/100)

Ton ton doit être encourageant, positif, et motivant.
"""
        
        user_prompt = f"""Génère un rapport éco-citoyen personnalisé:

{citizen_data}

Inclus:
1. Analyse du score écologique actuel
2. Bilan des déplacements du mois
3. Impact CO2 (positif ou négatif)
4. 3 recommandations concrètes pour améliorer le score
"""
        
        return self._call_ai(system_prompt, user_prompt, temperature=0.6, max_tokens=700)


# ============================================================================
# TEMPLATE-BASED FALLBACK (NO API KEY REQUIRED)
# ============================================================================

class TemplateAIGenerator:
    """Template-based generator as fallback when no API key"""
    
    def __init__(self, db_path: str = "neo_sousse.db"):
        self.db_path = db_path
    
    def _query_database(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute database query using PostgreSQL"""
        # ✅ CHANGE 2: Use PostgreSQL
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            cursor.close()
            return results
        finally:
            if conn:
                conn.close()
    
    def generate_air_quality_report(self, zone_id: Optional[int] = None, 
                                    date_str: Optional[str] = None) -> str:
        """Template-based air quality report"""
        
        # ✅ CHANGE 3: Use %s instead of ? and CAST for PostgreSQL
        query = """
            SELECT 
                z.nom as zone_name,
                m.type_mesure,
                AVG(m.valeur) as avg_value,
                MAX(m.valeur) as max_value,
                SUM(CASE WHEN m.est_anomalie = TRUE THEN 1 ELSE 0 END) as anomaly_count
            FROM mesures m
            JOIN capteurs c ON m.capteur_id = c.capteur_id
            JOIN zones z ON c.zone_id = z.zone_id
            WHERE c.type_capteur = 'air'
        """
        
        params = []
        if zone_id:
            query += " AND z.zone_id = %s"
            params.append(zone_id)
        
        if date_str:
            query += " AND DATE(m.timestamp) = %s"
            params.append(date_str)
        else:
            query += " AND DATE(m.timestamp) = CURRENT_DATE"
        
        query += " GROUP BY z.nom, m.type_mesure"
        
        data = self._query_database(query, tuple(params))
        
        if not data:
            return "Aucune donnée disponible."
        
        date_display = date_str or datetime.now().strftime("%d/%m/%Y")
        zone_display = f"zone {zone_id}" if zone_id else "toutes les zones"
        
        report = f"=== RAPPORT QUALITÉ DE L'AIR ===\n"
        report += f"Date: {date_display}\n"
        report += f"Zone(s): {zone_display}\n\n"
        
        problems = []
        for row in data:
            report += f"{row['zone_name']} - {row['type_mesure']}:\n"
            report += f"  Moyenne: {row['avg_value']:.1f} {self._get_unit(row['type_mesure'])}\n"
            report += f"  Maximum: {row['max_value']:.1f} {self._get_unit(row['type_mesure'])}\n"
            
            if row['anomaly_count'] and row['anomaly_count'] > 0:
                report += f"  ⚠️  {row['anomaly_count']} anomalie(s) détectée(s)\n"
                problems.append(f"{row['zone_name']} ({row['type_mesure']})")
            
            report += "\n"
        
        if problems:
            report += f"ZONES À SURVEILLER: {', '.join(problems)}\n"
        else:
            report += "✓ Aucune anomalie majeure détectée.\n"
        
        return report
    
    def _get_unit(self, type_mesure: str) -> str:
        """Get measurement unit"""
        units = {
            'PM2.5': 'µg/m³',
            'CO2': 'ppm',
            'NO2': 'µg/m³',
            'temperature': '°C',
            'humidite': '%'
        }
        return units.get(type_mesure, '')
    
    def generate_maintenance_recommendation(self, capteur_id: str) -> str:
        """Template-based maintenance recommendation"""
        
        # ✅ CHANGE 3: Use %s instead of ?
        query = """
            SELECT 
                c.capteur_id,
                c.type_capteur,
                c.statut,
                c.taux_erreur,
                c.nb_anomalies_totales,
                z.nom as zone_name
            FROM capteurs c
            JOIN zones z ON c.zone_id = z.zone_id
            WHERE c.capteur_id = %s
        """
        
        data = self._query_database(query, (capteur_id,))
        
        if not data:
            return f"Capteur {capteur_id} introuvable."
        
        sensor = data[0]
        
        report = f"=== RECOMMANDATION MAINTENANCE ===\n"
        report += f"Capteur: {sensor['capteur_id']} ({sensor['type_capteur']})\n"
        report += f"Zone: {sensor['zone_name']}\n"
        report += f"État: {sensor['statut']}\n"
        report += f"Taux d'erreur: {sensor['taux_erreur']:.1f}%\n\n"
        
        if sensor['taux_erreur'] > 15:
            report += "🔴 URGENCE ÉLEVÉE\n"
            report += "→ Intervention immédiate requise\n"
            report += "→ Taux d'erreur au-dessus du seuil critique (15%)\n"
        elif sensor['taux_erreur'] > 10:
            report += "🟡 SURVEILLANCE RECOMMANDÉE\n"
            report += "→ Planifier une inspection dans les 48h\n"
        else:
            report += "🟢 ÉTAT NORMAL\n"
            report += "→ Maintenance préventive selon calendrier\n"
        
        return report