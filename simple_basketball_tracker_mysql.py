# simple_basketball_tracker_mysql.py
# Basketball tracker with Streamlit-native MySQL backend

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from db_config import test_connection, get_connection_info, show_connection_status
from db_helpers import *

st.set_page_config(page_title="Basketball QuickTrack (MySQL)", layout="wide")

# Test database connection on startup
if 'db_connected' not in st.session_state:
    st.session_state.db_connected = test_connection()

if not st.session_state.db_connected:
    st.error("⚠️ Cannot connect to database. Please check your configuration.")
    st.stop()

# Get current team
if 'team_id' not in st.session_state:
    team_id = get_current_team_id()
    if team_id is None:
        st.error("No team found. Creating default team...")
        team_id = create_team("My Team", "2024-25")
    st.session_state.team_id = team_id

team_id = st.session_state.team_id

# Sidebar
page = st.sidebar.radio("Navigate", ["🏀 Game Tracker", "👥 Manage Players", "📊 Analytics", "💾 Data Export"])

# Optional: Show connection status in sidebar
if st.sidebar.checkbox("Show DB Status", value=False):
    show_connection_status()

# ============================================
# PAGE 1: GAME TRACKER
# ============================================
if page == "🏀 Game Tracker":
    st.title("🏀 QuickTrack: Simple Basketball Tracking")
    
    # Check for active game
    active_game = get_active_game(team_id)
    
    if active_game is None:
        st.header("Start New Game")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            opponent = st.text_input("Opponent Name")
        with col2:
            game_date = st.date_input("Game Date", datetime.now())
        with col3:
            location = st.selectbox("Location", ["Home", "Away"])
        
        if st.button("🎯 Start Game", type="primary"):
            if opponent:
                game_id = create_game(team_id, game_date, opponent, location)
                st.success(f"Game created! Game ID: {game_id}")
                st.rerun()
            else:
                st.error("Please enter opponent name")
    
    else:
        # Active game tracking
        game_id = active_game['game_id']
        st.header(f"Game vs {active_game['opponent']} - {active_game['game_date']}")
        
        # Quick score update
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            our_score = st.number_input("Our Score", value=int(active_game['final_score_us']), min_value=0, step=1)
        with col2:
            their_score = st.number_input("Their Score", value=int(active_game['final_score_them']), min_value=0, step=1)
        with col3:
            quarter = st.selectbox("Quarter", [1, 2, 3, 4, "OT"])
        
        # Update score in real-time
        if our_score != active_game['final_score_us'] or their_score != active_game['final_score_them']:
            update_game_score(game_id, our_score, their_score)
        
        st.divider()
        
        # Lineup Selection
        st.subheader("Current Lineup (Select 5)")
        
        players_df = get_players(team_id)
        if players_df.empty:
            st.warning("⚠️ No players found. Please add players first in the 'Manage Players' section.")
            st.info("👉 Go to 'Manage Players' to add your team roster before starting to track the game.")
        else:
            lineup_cols = st.columns(5)
            selected_players = []
            
            for i, col in enumerate(lineup_cols):
                with col:
                    player_options = ["None"] + [f"{row['jersey_number']} - {row['player_name']}" 
                                                 for _, row in players_df.iterrows()]
                    selected = st.selectbox(f"Player {i+1}", player_options, key=f"lineup_{i}")
                    
                    if selected != "None":
                        player_id = players_df[players_df.apply(
                            lambda r: f"{r['jersey_number']} - {r['player_name']}" == selected, axis=1
                        )]['player_id'].iloc[0]
                        selected_players.append(int(player_id))
            
            st.divider()
            
            # POSSESSION TRACKING
            st.subheader("⚡ Track Possession")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("✅ GOOD\n(Score/OR/Open Shot)", use_container_width=True, type="primary"):
                    add_possession(game_id, quarter, None, "GOOD", None, selected_players)
                    st.success("✅ Good possession logged!")
                    st.rerun()
                    
            with col2:
                if st.button("⚠️ NEUTRAL\n(Forced Shot)", use_container_width=True):
                    add_possession(game_id, quarter, None, "NEUTRAL", None, selected_players)
                    st.warning("⚠️ Neutral possession logged")
                    st.rerun()
            
            with col3:
                failure_type = st.selectbox("If Failed, Why?", 
                    ["Turnover", "Ball_Advancement", "Shot_Selection", "Bad_Process"])
                if st.button("❌ FAILED\n(Bad Possession)", use_container_width=True):
                    add_possession(game_id, quarter, None, "FAILED", failure_type, selected_players)
                    st.error(f"❌ Failed possession logged: {failure_type}")
                    st.rerun()
            
            st.divider()
            
            # Quick Stats Entry
            with st.expander("📝 Quick Player Stats Entry"):
                st.write("Update player stats as the game progresses")
                
                player_options_full = [f"{row['jersey_number']} - {row['player_name']}" 
                                      for _, row in players_df.iterrows()]
                stat_player = st.selectbox("Select Player", player_options_full)
                selected_player_id = players_df[players_df.apply(
                    lambda r: f"{r['jersey_number']} - {r['player_name']}" == stat_player, axis=1
                )]['player_id'].iloc[0]
                
                # Get existing stats if any
                existing_stats = get_player_stats(game_id)
                player_existing = existing_stats[existing_stats['player_id'] == selected_player_id] if not existing_stats.empty else pd.DataFrame()
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    points = st.number_input("Points", min_value=0, step=1, 
                                           value=int(player_existing['points'].iloc[0]) if not player_existing.empty else 0)
                with col2:
                    assists = st.number_input("Assists", min_value=0, step=1,
                                            value=int(player_existing['assists'].iloc[0]) if not player_existing.empty else 0)
                with col3:
                    rebounds = st.number_input("Rebounds", min_value=0, step=1,
                                             value=int(player_existing['rebounds_offensive'].iloc[0] + player_existing['rebounds_defensive'].iloc[0]) if not player_existing.empty else 0)
                with col4:
                    turnovers = st.number_input("Turnovers", min_value=0, step=1,
                                              value=int(player_existing['turnovers'].iloc[0]) if not player_existing.empty else 0)
                
                col5, col6, col7, col8 = st.columns(4)
                with col5:
                    steals = st.number_input("Steals", min_value=0, step=1,
                                           value=int(player_existing['steals'].iloc[0]) if not player_existing.empty else 0)
                with col6:
                    blocks = st.number_input("Blocks", min_value=0, step=1,
                                           value=int(player_existing['blocks'].iloc[0]) if not player_existing.empty else 0)
                with col7:
                    fouls = st.number_input("Fouls", min_value=0, step=1,
                                          value=int(player_existing['fouls'].iloc[0]) if not player_existing.empty else 0)
                with col8:
                    minutes = st.number_input("Minutes", min_value=0, max_value=40, step=1,
                                            value=int(player_existing['minutes_played'].iloc[0]) if not player_existing.empty else 0)
                
                if st.button("Save Player Stats"):
                    stats = {
                        'minutes': minutes,
                        'points': points,
                        'assists': assists,
                        'rebounds_offensive': rebounds // 2,
                        'rebounds_defensive': rebounds - (rebounds // 2),
                        'turnovers': turnovers,
                        'steals': steals,
                        'blocks': blocks,
                        'fouls': fouls
                    }
                    upsert_player_stats(game_id, selected_player_id, stats)
                    st.success(f"Stats saved for {stat_player}")
                    st.rerun()
            
            st.divider()
            
            # Live Game Summary
            st.subheader("📈 Live Game Summary")
            
            possessions_df = get_possessions(game_id)
            
            if not possessions_df.empty:
                total_poss = len(possessions_df)
                good_poss = len(possessions_df[possessions_df['outcome'] == 'GOOD'])
                failed_poss = len(possessions_df[possessions_df['outcome'] == 'FAILED'])
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Possessions", total_poss)
                col2.metric("Possession Efficiency", f"{(good_poss/total_poss*100):.1f}%", 
                          delta=f"{(good_poss/total_poss*100)-60:.1f}% vs target")
                col3.metric("Waste Rate", f"{(failed_poss/total_poss*100):.1f}%",
                          delta=f"{25-(failed_poss/total_poss*100):.1f}% under target")
                col4.metric("Score Differential", our_score - their_score,
                          delta="Winning" if our_score > their_score else "Losing")
                
                # Constraint Analysis
                constraint_df = get_constraint_analysis(game_id)
                if not constraint_df.empty:
                    st.subheader("🎯 Your Constraint (Where Possessions Break Down)")
                    
                    fig = px.bar(constraint_df, x='failure_type', y='count',
                               labels={'failure_type': 'Failure Type', 'count': 'Count'},
                               title="Possession Breakdowns",
                               color='count',
                               color_continuous_scale='Reds')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.info(f"**🎯 CONSTRAINT: {constraint_df.iloc[0]['failure_type']}** - Focus practice here!")
            else:
                st.info("Start tracking possessions to see live analytics")
        
        # End Game
        st.divider()
        if st.button("🏁 End Game & Save", type="primary"):
            complete_game(game_id)
            st.success("✅ Game completed and saved!")
            st.balloons()
            st.rerun()

# ============================================
# PAGE 2: MANAGE PLAYERS
# ============================================
elif page == "👥 Manage Players":
    st.title("👥 Manage Players")
    
    st.subheader("Current Roster")
    
    players_df = get_players(team_id)
    if not players_df.empty:
        display_df = players_df[['jersey_number', 'player_name', 'position']].copy()
        display_df.columns = ['Number', 'Name', 'Position']
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No players added yet. Add your first player below!")
    
    st.divider()
    
    # Add new player
    with st.expander("➕ Add New Player", expanded=players_df.empty):
        col1, col2, col3 = st.columns(3)
        with col1:
            new_name = st.text_input("Player Name")
        with col2:
            new_number = st.text_input("Jersey Number")
        with col3:
            new_position = st.selectbox("Position", ["", "PG", "SG", "SF", "PF", "C"])
        
        if st.button("Add Player", type="primary"):
            if new_name and new_number:
                add_player(team_id, new_name, new_number, new_position if new_position else None)
                st.success(f"✅ Added {new_name} (#{new_number})")
                st.rerun()
            else:
                st.error("Please enter both name and number")

# ============================================
# PAGE 3: ANALYTICS
# ============================================
elif page == "📊 Analytics":
    st.title("📊 Game Analytics")
    
    games_df = get_games(team_id, completed_only=True)
    
    if games_df.empty:
        st.info("📊 No completed games yet. Finish tracking a game to see analytics!")
    else:
        # Game selector
        game_options = ["All Games"] + [f"{row['game_date']} vs {row['opponent']}" 
                                       for _, row in games_df.iterrows()]
        selected_game_str = st.selectbox("Select Game", game_options)
        
        if selected_game_str == "All Games":
            selected_game_id = None
        else:
            game_idx = game_options.index(selected_game_str) - 1
            selected_game_id = int(games_df.iloc[game_idx]['game_id'])
        
        # Possession Analysis
        if selected_game_id:
            possessions_df = get_possessions(selected_game_id)
        else:
            # Get all possessions for all completed games
            all_poss = []
            for _, game in games_df.iterrows():
                poss = get_possessions(game['game_id'])
                if not poss.empty:
                    all_poss.append(poss)
            possessions_df = pd.concat(all_poss) if all_poss else pd.DataFrame()
        
        if not possessions_df.empty:
            st.subheader("Possession Quality Analysis")
            
            outcome_counts = possessions_df['outcome'].value_counts()
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(values=outcome_counts.values, names=outcome_counts.index,
                           title="Possession Outcomes",
                           color=outcome_counts.index,
                           color_discrete_map={'GOOD': 'green', 'NEUTRAL': 'yellow', 'FAILED': 'red'})
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                total = len(possessions_df)
                good = len(possessions_df[possessions_df['outcome'] == 'GOOD'])
                failed = len(possessions_df[possessions_df['outcome'] == 'FAILED'])
                
                st.metric("Possession Efficiency", f"{(good/total*100):.1f}%")
                st.metric("Waste Rate", f"{(failed/total*100):.1f}%")
                st.metric("Total Possessions", total)
        
        # Player Performance
        if selected_game_id:
            stats_df = get_player_stats(selected_game_id)
        else:
            # Aggregate stats across all games
            all_stats = []
            for _, game in games_df.iterrows():
                stats = get_player_stats(game['game_id'])
                if not stats.empty:
                    all_stats.append(stats)
            stats_df = pd.concat(all_stats) if all_stats else pd.DataFrame()
            
            # Aggregate by player
            if not stats_df.empty:
                stats_df = stats_df.groupby(['player_id', 'player_name', 'jersey_number']).agg({
                    'minutes_played': 'sum',
                    'points': 'sum',
                    'assists': 'sum',
                    'rebounds_offensive': 'sum',
                    'rebounds_defensive': 'sum',
                    'turnovers': 'sum',
                    'steals': 'sum',
                    'blocks': 'sum',
                    'fouls': 'sum'
                }).reset_index()
        
        if not stats_df.empty:
            st.subheader("Player Performance")
            
            # Calculate metrics
            stats_df['total_rebounds'] = stats_df['rebounds_offensive'] + stats_df['rebounds_defensive']
            stats_df['net_impact'] = (
                stats_df['points'] + 
                stats_df['assists'] * 2 + 
                stats_df['total_rebounds'] + 
                stats_df['steals'] -
                stats_df['turnovers'] * 2 -
                stats_df['fouls']
            )
            stats_df['net_impact_per_10'] = (stats_df['net_impact'] / stats_df['minutes_played'] * 10).round(1)
            
            # Display table
            display_cols = ['player_name', 'minutes_played', 'points', 'assists', 'total_rebounds', 
                          'turnovers', 'steals', 'net_impact', 'net_impact_per_10']
            display_df = stats_df[display_cols].sort_values('net_impact', ascending=False)
            display_df.columns = ['Player', 'Min', 'Pts', 'Ast', 'Reb', 'TO', 'Stl', 'Impact', 'Impact/10']
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Chart
            fig = px.bar(stats_df.sort_values('net_impact_per_10', ascending=False).head(10),
                        x='player_name', y='net_impact_per_10',
                        title='Net Impact Rating per 10 Minutes (Top 10)',
                        labels={'net_impact_per_10': 'Impact per 10 min', 'player_name': 'Player'},
                        color='net_impact_per_10',
                        color_continuous_scale='RdYlGn')
            st.plotly_chart(fig, use_container_width=True)

# ============================================
# PAGE 4: DATA EXPORT
# ============================================
elif page == "💾 Data Export":
    st.title("💾 Data Export")
    
    st.subheader("Export Data for Analysis")
    
    games_df = get_games(team_id)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Download Games Data", use_container_width=True):
            if not games_df.empty:
                csv = games_df.to_csv(index=False)
                st.download_button("⬇️ Download CSV", csv, "games.csv", "text/csv",
                                 use_container_width=True)
            else:
                st.warning("No games data to export")
    
    with col2:
        if st.button("📥 Download All Possessions", use_container_width=True):
            all_poss = []
            for _, game in games_df.iterrows():
                poss = get_possessions(game['game_id'])
                if not poss.empty:
                    all_poss.append(poss)
            if all_poss:
                possessions_df = pd.concat(all_poss)
                csv = possessions_df.to_csv(index=False)
                st.download_button("⬇️ Download CSV", csv, "possessions.csv", "text/csv",
                                 use_container_width=True)
            else:
                st.warning("No possessions data to export")
    
    with col3:
        if st.button("📥 Download Player Stats", use_container_width=True):
            all_stats = []
            for _, game in games_df.iterrows():
                stats = get_player_stats(game['game_id'])
                if not stats.empty:
                    all_stats.append(stats)
            if all_stats:
                stats_df = pd.concat(all_stats)
                csv = stats_df.to_csv(index=False)
                st.download_button("⬇️ Download CSV", csv, "player_stats.csv", "text/csv",
                                 use_container_width=True)
            else:
                st.warning("No player stats to export")
    
    st.divider()
    
    st.subheader("📊 Current Data Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Games Recorded", len(games_df))
    
    # Count total possessions
    total_poss = 0
    for _, game in games_df.iterrows():
        poss = get_possessions(game['game_id'])
        total_poss += len(poss)
    col2.metric("Possessions Tracked", total_poss)
    
    # Count total stat entries
    total_stats = 0
    for _, game in games_df.iterrows():
        stats = get_player_stats(game['game_id'])
        total_stats += len(stats)
    col3.metric("Player Stats Entries", total_stats)
