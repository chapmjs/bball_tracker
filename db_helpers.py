# db_helpers.py
# Database helper functions using Streamlit-native connection API

import pandas as pd
import json
from db_config import query_db, execute_db, insert_and_get_id

# ============================================
# TEAM OPERATIONS
# ============================================

def get_teams():
    """Get all teams"""
    query = "SELECT * FROM teams ORDER BY created_at DESC"
    return query_db(query, ttl=300)  # Cache for 5 minutes

def get_current_team_id():
    """Get the most recent team ID"""
    df = get_teams()
    if not df.empty:
        return int(df.iloc[0]['team_id'])
    else:
        # Create default team if none exists
        return create_team("My Team", "2024-25")

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
    return query_db(query, params={'team_id': team_id}, ttl=300)

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
    execute_db(query, {
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
        'game_date': str(game_date),
        'opponent': opponent,
        'location': location
    })

def get_game(game_id):
    """Get game details"""
    query = "SELECT * FROM games WHERE game_id = :game_id"
    df = query_db(query, params={'game_id': game_id}, ttl=60)
    return df.iloc[0].to_dict() if not df.empty else None

def update_game_score(game_id, score_us, score_them):
    """Update game score"""
    query = """
        UPDATE games 
        SET final_score_us = :score_us, final_score_them = :score_them
        WHERE game_id = :game_id
    """
    execute_db(query, {
        'game_id': game_id,
        'score_us': score_us,
        'score_them': score_them
    })

def complete_game(game_id):
    """Mark game as completed"""
    query = "UPDATE games SET game_completed = TRUE WHERE game_id = :game_id"
    execute_db(query, {'game_id': game_id})

def get_games(team_id, completed_only=False):
    """Get all games for a team"""
    if completed_only:
        query = """
            SELECT * FROM games 
            WHERE team_id = :team_id AND game_completed = TRUE
            ORDER BY game_date DESC
        """
    else:
        query = """
            SELECT * FROM games 
            WHERE team_id = :team_id
            ORDER BY game_date DESC
        """
    return query_db(query, params={'team_id': team_id}, ttl=60)

def get_active_game(team_id):
    """Get the current active (incomplete) game"""
    query = """
        SELECT * FROM games 
        WHERE team_id = :team_id AND game_completed = FALSE
        ORDER BY created_at DESC
        LIMIT 1
    """
    df = query_db(query, params={'team_id': team_id}, ttl=0)  # No cache for active game
    return df.iloc[0].to_dict() if not df.empty else None

# ============================================
# POSSESSION OPERATIONS
# ============================================

def add_possession(game_id, quarter, time_remaining, outcome, failure_type, players_on_court):
    """Add a possession"""
    query = """
        INSERT INTO possessions 
        (game_id, quarter, time_remaining, outcome, failure_type, players_on_court)
        VALUES (:game_id, :quarter, :time_remaining, :outcome, :failure_type, :players)
    """
    execute_db(query, {
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
    return query_db(query, params={'game_id': game_id}, ttl=60)

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
    execute_db(query, {
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
