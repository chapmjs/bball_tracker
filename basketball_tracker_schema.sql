-- basketball_tracker_schema.sql
CREATE DATABASE IF NOT EXISTS basketball_tracker;
USE basketball_tracker;

-- Teams/Seasons Management
CREATE TABLE teams (
    team_id INT PRIMARY KEY AUTO_INCREMENT,
    team_name VARCHAR(100) NOT NULL,
    season VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Players
CREATE TABLE players (
    player_id INT PRIMARY KEY AUTO_INCREMENT,
    team_id INT,
    player_name VARCHAR(100) NOT NULL,
    jersey_number VARCHAR(10),
    position VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

-- Games
CREATE TABLE games (
    game_id INT PRIMARY KEY AUTO_INCREMENT,
    team_id INT,
    game_date DATE NOT NULL,
    opponent VARCHAR(100) NOT NULL,
    location ENUM('Home', 'Away') NOT NULL,
    final_score_us INT DEFAULT 0,
    final_score_them INT DEFAULT 0,
    game_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(team_id),
    INDEX idx_game_date (game_date),
    INDEX idx_opponent (opponent)
);

-- Simple Possessions (for Simple Model)
CREATE TABLE possessions (
    possession_id INT PRIMARY KEY AUTO_INCREMENT,
    game_id INT NOT NULL,
    quarter INT,
    time_remaining VARCHAR(10),
    outcome ENUM('GOOD', 'NEUTRAL', 'FAILED') NOT NULL,
    failure_type VARCHAR(50),
    players_on_court JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    INDEX idx_game_outcome (game_id, outcome)
);

-- Player Game Stats
CREATE TABLE player_game_stats (
    stat_id INT PRIMARY KEY AUTO_INCREMENT,
    game_id INT NOT NULL,
    player_id INT NOT NULL,
    minutes_played INT DEFAULT 0,
    points INT DEFAULT 0,
    assists INT DEFAULT 0,
    rebounds_offensive INT DEFAULT 0,
    rebounds_defensive INT DEFAULT 0,
    turnovers INT DEFAULT 0,
    steals INT DEFAULT 0,
    blocks INT DEFAULT 0,
    fouls INT DEFAULT 0,
    plus_minus INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    UNIQUE KEY unique_player_game (game_id, player_id),
    INDEX idx_player (player_id)
);

-- Detailed Possessions (for Complex Model)
CREATE TABLE detailed_possessions (
    possession_id INT PRIMARY KEY AUTO_INCREMENT,
    game_id INT NOT NULL,
    quarter INT NOT NULL,
    time_elapsed_seconds INT NOT NULL,
    lineup JSON NOT NULL,
    ball_advancement VARCHAR(50),
    shot_quality VARCHAR(50),
    shooter_id INT,
    shot_type VARCHAR(50),
    shot_result VARCHAR(20),
    outcome VARCHAR(50),
    points_scored INT DEFAULT 0,
    momentum_state INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (shooter_id) REFERENCES players(player_id),
    INDEX idx_game_time (game_id, time_elapsed_seconds),
    INDEX idx_shooter (shooter_id)
);

-- Shots (for Shot Charts)
CREATE TABLE shots (
    shot_id INT PRIMARY KEY AUTO_INCREMENT,
    game_id INT NOT NULL,
    player_id INT NOT NULL,
    quarter INT NOT NULL,
    time_elapsed_seconds INT NOT NULL,
    shot_type VARCHAR(50) NOT NULL,
    shot_quality VARCHAR(50),
    made BOOLEAN NOT NULL,
    x_location DECIMAL(5,2),  -- For future shot chart visualization
    y_location DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    INDEX idx_game (game_id),
    INDEX idx_player (player_id)
);

-- Lineup Stints
CREATE TABLE lineup_stints (
    stint_id INT PRIMARY KEY AUTO_INCREMENT,
    game_id INT NOT NULL,
    lineup JSON NOT NULL,
    start_time_seconds INT NOT NULL,
    end_time_seconds INT,
    duration_seconds INT,
    points_for INT DEFAULT 0,
    points_against INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    INDEX idx_game (game_id)
);

-- Player Energy Tracking (for Complex Model)
CREATE TABLE player_energy_log (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    game_id INT NOT NULL,
    player_id INT NOT NULL,
    time_elapsed_seconds INT NOT NULL,
    energy_level DECIMAL(5,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    INDEX idx_game_player (game_id, player_id)
);

-- Create a default team for getting started
INSERT INTO teams (team_name, season) VALUES ('My Team', '2024-25');
