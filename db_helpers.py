# db_helpers.py
# Common database operations

import pandas as pd
from sqlalchemy import text
import json
from db_config import get_db_engine

def execute_query(query, params=None):
    """Execute a query and return results as DataFrame"""
    engine = get_db_engine()
    with engine.connect() as conn:
        if params:
            result = conn.execute(text(query), params)
        else:
            result = conn.execute(text(query))
        conn.commit()
        return result

def fetch_dataframe(query, params=None):
    """Fetch query results as pandas DataFrame"""
    engine = get_db_engine()
    if params:
        return pd.read_sql(text(query), engine, params=params)
    else:
        return pd.read_sql(text(query), engine)

def insert_and_get_id(query, params):
    """Insert record and return the inserted ID"""
    engine = get_db_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        conn.commit()
        return result.lastrowid

# ============================================
# TEAM OPERATIONS
# ============================================

def get_teams():
    """Get all teams"""
    query = "SELECT * FROM teams ORDER BY created_at DESC"
    return fetch_dataframe(query)

def get_current_team_id():
    """Get the most recent team ID (for single-team tracking)"""
    df = get_teams()
    return df.iloc[0]['team_id'] if not df.empty else None

def create_team(team_name, season):
    """Create a new team"""
    query = """
        INSERT INTO teams (team_name, season) 
        VALUES (:team_name, :season)
    """
    return insert_and_get_id(query, {'team_name': team_name, 'season': season})

# ============================================
# PLAYER OPERATIONS
# ============================================

def get_players(team_id):
    """Get all players for a team"""
    query = """
        SELECT * FROM players 
        WHERE team_id = :team_id 
        ORDER BY jersey_number
    """
    return fetch_dataframe(query, {'team_id': team_id})

def add_player(team_id, name, number, position=None):
    """Add a new player"""
    query = """
        INSERT INTO players (team_id, player_name, jersey_number, position) 
        VALUES (:team_id, :name, :number, :position)
    """
    return insert_and_get_id(query, {
        'team_id': team_id,
        'name': name,
        'number': number,
        'position': position
    })

def update_player(player_id, name, number, position):
    """Update player information"""
    query = """
        UPDATE players 
        SET player_name = :name, jersey_number = :number, position = :position
        WHERE player_id = :player_id
    """
    execute_query(query, {
        'player_id': player_id,
        'name': name,
        'number': number,
        'position': position
    })

# ============================================
# GAME OPERATIONS
# ============================================

def create_game(team_id, game_date, opponent, location):
    """Create a new game"""
    query = """
        INSERT INTO games (team_id, game_date, opponent, location) 
        VALUES (:team_id, :game_date, :opponent, :location)
    """
    return insert_and_get_id(query, {
        'team_id': team_id,
        'game_date': game_date,
        'opponent': opponent,
        'location': location
    })

def get_game(game_id):
    """Get game details"""
    query = "SELECT * FROM games WHERE game_id = :game_id"
    df = fetch_dataframe(query, {'game_id': game_id})
    return df.iloc[0].to_dict() if not df.empty else None

def update_game_score(game_id, score_us, score_them):
    """Update game score"""
    query = """
        UPDATE games 
        SET final_score_us = :score_us, final_score_them = :score_them
        WHERE game_id = :game_id
    """
    execute_query(query, {
        'game_id': game_id,
        'score_us': score_us,
        'score_them': score_them
    })

def complete_game(game_id):
    """Mark game as completed"""
    query = "UPDATE games SET game_completed = TRUE WHERE game_id = :game_id"
    execute_query(query, {'game_id': game_id})

def get_games(team_id, completed_only=False):
    """Get all games for a team"""
    query = """
        SELECT * FROM games 
        WHERE team_id = :team_id
    """
    if completed_only:
        query += " AND game_completed = TRUE"
    query += " ORDER BY game_date DESC"
    return fetch_dataframe(query, {'team_id': team_id})

def get_active_game(team_id):
    """Get the current active (incomplete) game"""
    query = """
        SELECT * FROM games 
        WHERE team_id = :team_id AND game_completed = FALSE
        ORDER BY created_at DESC
        LIMIT 1
    """
    df = fetch_dataframe(query, {'team_id': team_id})
    return df.iloc[0].to_dict() if not df.empty else None

# ============================================
# POSSESSION OPERATIONS (Simple Model)
# ============================================

def add_possession(game_id, quarter, time_remaining, outcome, failure_type, players_on_court):
    """Add a possession"""
    query = """
        INSERT INTO possessions 
        (game_id, quarter, time_remaining, outcome, failure_type, players_on_court)
        VALUES (:game_id, :quarter, :time_remaining, :outcome, :failure_type, :players)
    """
    execute_query(query, {
        'game_id': game_id,
        'quarter': quarter,
        'time_remaining': time_remaining,
        'outcome': outcome,
        'failure_type': failure_type,
        'players': json.dumps(players_on_court)
    })

def get_possessions(game_id):
    """Get all possessions for a game"""
    query = "SELECT * FROM possessions WHERE game_id = :game_id ORDER BY possession_id"
    return fetch_dataframe(query, {'game_id': game_id})

# ============================================
# PLAYER STATS OPERATIONS
# ============================================

def upsert_player_stats(game_id, player_id, stats):
    """Insert or update player stats for a game"""
    query = """
        INSERT INTO player_game_stats 
        (game_id, player_id, minutes_played, points, assists, 
         rebounds_offensive, rebounds_defensive, turnovers, steals, blocks, fouls)
        VALUES (:game_id, :player_id, :minutes, :points, :assists, 
                :reb_off, :reb_def, :turnovers, :steals, :blocks, :fouls)
        ON DUPLICATE KEY UPDATE
            minutes_played = VALUES(minutes_played),
            points = VALUES(points),
            assists = VALUES(assists),
            rebounds_offensive = VALUES(rebounds_offensive),
            rebounds_defensive = VALUES(rebounds_defensive),
            turnovers = VALUES(turnovers),
            steals = VALUES(steals),
            blocks = VALUES(blocks),
            fouls = VALUES(fouls)
    """
    execute_query(query, {
        'game_id': game_id,
        'player_id': player_id,
        'minutes': stats.get('minutes', 0),
        'points': stats.get('points', 0),
        'assists': stats.get('assists', 0),
        'reb_off': stats.get('rebounds_offensive', 0),
        'reb_def': stats.get('rebounds_defensive', 0),
        'turnovers': stats.get('turnovers', 0),
        'steals': stats.get('steals', 0),
        'blocks': stats.get('blocks', 0),
        'fouls': stats.get('fouls', 0)
    })

def get_player_stats(game_id):
    """Get all player stats for a game"""
    query = """
        SELECT pgs.*, p.player_name, p.jersey_number
        FROM player_game_stats pgs
        JOIN players p ON pgs.player_id = p.player_id
        WHERE pgs.game_id = :game_id
    """
    return fetch_dataframe(query, {'game_id': game_id})

# ============================================
# DETAILED POSSESSION OPERATIONS (Complex Model)
# ============================================

def add_detailed_possession(possession_data):
    """Add detailed possession record"""
    query = """
        INSERT INTO detailed_possessions 
        (game_id, quarter, time_elapsed_seconds, lineup, ball_advancement,
         shot_quality, shooter_id, shot_type, shot_result, outcome, 
         points_scored, momentum_state)
        VALUES (:game_id, :quarter, :time_elapsed, :lineup, :ball_adv,
                :shot_quality, :shooter_id, :shot_type, :shot_result, :outcome,
                :points, :momentum)
    """
    execute_query(query, {
        'game_id': possession_data['game_id'],
        'quarter': possession_data['quarter'],
        'time_elapsed': possession_data['time_elapsed'],
        'lineup': json.dumps(possession_data['lineup']),
        'ball_adv': possession_data.get('ball_advancement'),
        'shot_quality': possession_data.get('shot_quality'),
        'shooter_id': possession_data.get('shooter_id'),
        'shot_type': possession_data.get('shot_type'),
        'shot_result': possession_data.get('shot_result'),
        'outcome': possession_data.get('outcome'),
        'points': possession_data.get('points_scored', 0),
        'momentum': possession_data.get('momentum_state', 0)
    })

def get_detailed_possessions(game_id):
    """Get detailed possessions for a game"""
    query = "SELECT * FROM detailed_possessions WHERE game_id = :game_id ORDER BY time_elapsed_seconds"
    return fetch_dataframe(query, {'game_id': game_id})

# ============================================
# SHOT OPERATIONS
# ============================================

def add_shot(shot_data):
    """Add a shot record"""
    query = """
        INSERT INTO shots 
        (game_id, player_id, quarter, time_elapsed_seconds, shot_type, shot_quality, made)
        VALUES (:game_id, :player_id, :quarter, :time_elapsed, :shot_type, :quality, :made)
    """
    execute_query(query, {
        'game_id': shot_data['game_id'],
        'player_id': shot_data['player_id'],
        'quarter': shot_data['quarter'],
        'time_elapsed': shot_data['time_elapsed'],
        'shot_type': shot_data['shot_type'],
        'quality': shot_data['quality'],
        'made': shot_data['made']
    })

def get_shots(game_id=None, player_id=None):
    """Get shots, optionally filtered by game or player"""
    query = "SELECT s.*, p.player_name, p.jersey_number FROM shots s JOIN players p ON s.player_id = p.player_id WHERE 1=1"
    params = {}
    
    if game_id:
        query += " AND s.game_id = :game_id"
        params['game_id'] = game_id
    
    if player_id:
        query += " AND s.player_id = :player_id"
        params['player_id'] = player_id
    
    query += " ORDER BY s.game_id, s.time_elapsed_seconds"
    return fetch_dataframe(query, params if params else None)

# ============================================
# ANALYTICS QUERIES
# ============================================

def get_constraint_analysis(game_id):
    """Analyze where possessions are breaking down"""
    query = """
        SELECT failure_type, COUNT(*) as count
        FROM possessions
        WHERE game_id = :game_id AND outcome = 'FAILED'
        GROUP BY failure_type
        ORDER BY count DESC
    """
    return fetch_dataframe(query, {'game_id': game_id})

def get_lineup_performance(game_id=None):
    """Get lineup performance statistics"""
    query = """
        SELECT 
            lineup,
            COUNT(*) as possessions,
            SUM(CASE WHEN outcome = 'SCORE' THEN 1 ELSE 0 END) as scores,
            SUM(points_scored) as total_points
        FROM detailed_possessions
        WHERE 1=1
    """
    params = {}
    if game_id:
        query += " AND game_id = :game_id"
        params['game_id'] = game_id
    
    query += " GROUP BY lineup ORDER BY total_points DESC"
    return fetch_dataframe(query, params if params else None)

def get_player_shooting_stats(game_id=None):
    """Get shooting statistics by player"""
    query = """
        SELECT 
            p.player_name,
            p.jersey_number,
            s.shot_type,
            s.shot_quality,
            COUNT(*) as attempts,
            SUM(CASE WHEN s.made THEN 1 ELSE 0 END) as makes,
            ROUND(SUM(CASE WHEN s.made THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as fg_pct
        FROM shots s
        JOIN players p ON s.player_id = p.player_id
    """
    params = {}
    if game_id:
        query += " WHERE s.game_id = :game_id"
        params['game_id'] = game_id
    
    query += " GROUP BY p.player_id, s.shot_type, s.shot_quality ORDER BY p.player_name, s.shot_type"
    return fetch_dataframe(query, params if params else None)
