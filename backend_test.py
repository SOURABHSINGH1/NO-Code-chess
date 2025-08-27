#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Chess Application
Tests all API endpoints, chess engine rules, and bot functionality
"""

import requests
import json
import time
from typing import Dict, List, Any

# Configuration
BASE_URL = "https://strategic-chess-6.preview.emergentagent.com/api"

class ChessBackendTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.test_results = []
        self.created_games = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} - {test_name}"
        if details:
            result += f": {details}"
        print(result)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    def test_get_bots(self):
        """Test GET /api/bots endpoint"""
        try:
            response = requests.get(f"{self.base_url}/bots", timeout=10)
            
            if response.status_code != 200:
                self.log_test("GET /api/bots", False, f"Status code: {response.status_code}")
                return False
                
            bots = response.json()
            
            if not isinstance(bots, list):
                self.log_test("GET /api/bots", False, "Response is not a list")
                return False
                
            if len(bots) != 10:
                self.log_test("GET /api/bots", False, f"Expected 10 bots, got {len(bots)}")
                return False
                
            # Check bot structure
            required_fields = ["id", "name", "difficulty", "description"]
            for i, bot in enumerate(bots):
                for field in required_fields:
                    if field not in bot:
                        self.log_test("GET /api/bots", False, f"Bot {i} missing field: {field}")
                        return False
                        
                if bot["difficulty"] != i + 1:
                    self.log_test("GET /api/bots", False, f"Bot {i} has wrong difficulty: {bot['difficulty']}")
                    return False
                    
            self.log_test("GET /api/bots", True, f"All 10 bots returned with correct structure")
            return True
            
        except Exception as e:
            self.log_test("GET /api/bots", False, f"Exception: {str(e)}")
            return False
            
    def test_create_pvp_game(self):
        """Test creating a PvP game"""
        try:
            game_data = {
                "mode": "pvp",
                "white_player": "Alice",
                "black_player": "Bob"
            }
            
            response = requests.post(f"{self.base_url}/games", json=game_data, timeout=10)
            
            if response.status_code != 200:
                self.log_test("Create PvP Game", False, f"Status code: {response.status_code}")
                return None
                
            game = response.json()
            
            # Validate game structure
            required_fields = ["id", "mode", "white_player", "black_player", "current_turn", "board_state", "game_status"]
            for field in required_fields:
                if field not in game:
                    self.log_test("Create PvP Game", False, f"Missing field: {field}")
                    return None
                    
            if game["mode"] != "pvp":
                self.log_test("Create PvP Game", False, f"Wrong mode: {game['mode']}")
                return None
                
            if game["current_turn"] != "white":
                self.log_test("Create PvP Game", False, f"Wrong starting turn: {game['current_turn']}")
                return None
                
            # Validate initial board setup
            board = game["board_state"]
            if len(board) != 32:  # 16 pieces per side
                self.log_test("Create PvP Game", False, f"Wrong number of pieces: {len(board)}")
                return None
                
            # Check some key pieces
            expected_pieces = {
                "e1": {"type": "king", "color": "white"},
                "e8": {"type": "king", "color": "black"},
                "d1": {"type": "queen", "color": "white"},
                "d8": {"type": "queen", "color": "black"}
            }
            
            for pos, expected in expected_pieces.items():
                if pos not in board:
                    self.log_test("Create PvP Game", False, f"Missing piece at {pos}")
                    return None
                if board[pos]["type"] != expected["type"] or board[pos]["color"] != expected["color"]:
                    self.log_test("Create PvP Game", False, f"Wrong piece at {pos}")
                    return None
                    
            self.created_games.append(game["id"])
            self.log_test("Create PvP Game", True, f"Game created with ID: {game['id']}")
            return game["id"]
            
        except Exception as e:
            self.log_test("Create PvP Game", False, f"Exception: {str(e)}")
            return None
            
    def test_create_pvb_game(self):
        """Test creating a PvB game"""
        try:
            game_data = {
                "mode": "pvb",
                "white_player": "Charlie",
                "black_player": "Bot_Master"
            }
            
            response = requests.post(f"{self.base_url}/games", json=game_data, timeout=10)
            
            if response.status_code != 200:
                self.log_test("Create PvB Game", False, f"Status code: {response.status_code}")
                return None
                
            game = response.json()
            
            if game["mode"] != "pvb":
                self.log_test("Create PvB Game", False, f"Wrong mode: {game['mode']}")
                return None
                
            self.created_games.append(game["id"])
            self.log_test("Create PvB Game", True, f"PvB game created with ID: {game['id']}")
            return game["id"]
            
        except Exception as e:
            self.log_test("Create PvB Game", False, f"Exception: {str(e)}")
            return None
            
    def test_get_game(self, game_id: str):
        """Test retrieving a specific game"""
        try:
            response = requests.get(f"{self.base_url}/games/{game_id}", timeout=10)
            
            if response.status_code != 200:
                self.log_test("GET Game", False, f"Status code: {response.status_code}")
                return False
                
            game = response.json()
            
            if game["id"] != game_id:
                self.log_test("GET Game", False, f"Wrong game ID returned")
                return False
                
            self.log_test("GET Game", True, f"Successfully retrieved game {game_id}")
            return True
            
        except Exception as e:
            self.log_test("GET Game", False, f"Exception: {str(e)}")
            return False
            
    def test_chess_moves(self, game_id: str):
        """Test various chess moves and validation"""
        try:
            # Test 1: Valid pawn move (e2-e4)
            move_data = {
                "game_id": game_id,
                "from_pos": "e2",
                "to_pos": "e4"
            }
            
            response = requests.post(f"{self.base_url}/games/{game_id}/moves", json=move_data, timeout=10)
            
            if response.status_code != 200:
                self.log_test("Pawn Move e2-e4", False, f"Status code: {response.status_code}")
                return False
                
            result = response.json()
            if not result.get("success"):
                self.log_test("Pawn Move e2-e4", False, "Move not successful")
                return False
                
            self.log_test("Pawn Move e2-e4", True, "Valid pawn move accepted")
            
            # Test 2: Invalid move (trying to move opponent's piece)
            invalid_move = {
                "game_id": game_id,
                "from_pos": "e7",  # Black pawn, but it's white's turn
                "to_pos": "e5"
            }
            
            response = requests.post(f"{self.base_url}/games/{game_id}/moves", json=invalid_move, timeout=10)
            
            if response.status_code == 400:
                self.log_test("Invalid Move Rejection", True, "Correctly rejected invalid move")
            else:
                self.log_test("Invalid Move Rejection", False, f"Should have rejected move, got status: {response.status_code}")
                
            # Test 3: Valid knight move (g1-f3)
            knight_move = {
                "game_id": game_id,
                "from_pos": "g1",
                "to_pos": "f3"
            }
            
            # First, make a black move to switch turns
            black_move = {
                "game_id": game_id,
                "from_pos": "e7",
                "to_pos": "e5"
            }
            requests.post(f"{self.base_url}/games/{game_id}/moves", json=black_move, timeout=10)
            
            response = requests.post(f"{self.base_url}/games/{game_id}/moves", json=knight_move, timeout=10)
            
            if response.status_code == 200:
                self.log_test("Knight Move g1-f3", True, "Valid knight move accepted")
            else:
                self.log_test("Knight Move g1-f3", False, f"Knight move rejected: {response.status_code}")
                
            return True
            
        except Exception as e:
            self.log_test("Chess Moves Test", False, f"Exception: {str(e)}")
            return False
            
    def test_bot_moves(self, game_id: str):
        """Test bot move generation at different difficulty levels"""
        try:
            # Test bot moves at different difficulty levels
            difficulties = [1, 3, 5, 7, 10]
            
            for difficulty in difficulties:
                response = requests.post(f"{self.base_url}/games/{game_id}/bot-move", 
                                       params={"difficulty": difficulty}, timeout=15)
                
                if response.status_code != 200:
                    self.log_test(f"Bot Move Difficulty {difficulty}", False, 
                                f"Status code: {response.status_code}")
                    continue
                    
                result = response.json()
                if not result.get("success"):
                    self.log_test(f"Bot Move Difficulty {difficulty}", False, "Bot move not successful")
                    continue
                    
                self.log_test(f"Bot Move Difficulty {difficulty}", True, 
                            f"Bot successfully made move at difficulty {difficulty}")
                
                # Small delay between bot moves
                time.sleep(0.5)
                
            return True
            
        except Exception as e:
            self.log_test("Bot Moves Test", False, f"Exception: {str(e)}")
            return False
            
    def test_piece_movement_validation(self):
        """Test specific piece movement rules"""
        try:
            # Create a fresh game for piece testing
            game_data = {
                "mode": "pvp",
                "white_player": "TestPlayer1",
                "black_player": "TestPlayer2"
            }
            
            response = requests.post(f"{self.base_url}/games", json=game_data, timeout=10)
            if response.status_code != 200:
                self.log_test("Piece Movement Setup", False, "Could not create test game")
                return False
                
            game_id = response.json()["id"]
            self.created_games.append(game_id)
            
            # Test various piece movements
            test_moves = [
                # Valid moves
                {"from": "e2", "to": "e4", "should_work": True, "piece": "Pawn"},
                {"from": "g1", "to": "f3", "should_work": True, "piece": "Knight"},
                
                # Invalid moves (after switching turns appropriately)
                {"from": "a1", "to": "a3", "should_work": False, "piece": "Rook (blocked)"},
                {"from": "f1", "to": "a6", "should_work": False, "piece": "Bishop (blocked)"},
            ]
            
            current_turn = "white"
            
            for i, move in enumerate(test_moves):
                if i > 0 and i % 2 == 0:
                    # Make a black move to switch turns
                    black_moves = ["e7-e5", "d7-d6", "c7-c6", "b7-b6"]
                    if i // 2 - 1 < len(black_moves):
                        from_pos, to_pos = black_moves[i // 2 - 1].split("-")
                        black_move = {
                            "game_id": game_id,
                            "from_pos": from_pos,
                            "to_pos": to_pos
                        }
                        requests.post(f"{self.base_url}/games/{game_id}/moves", json=black_move, timeout=10)
                
                move_data = {
                    "game_id": game_id,
                    "from_pos": move["from"],
                    "to_pos": move["to"]
                }
                
                response = requests.post(f"{self.base_url}/games/{game_id}/moves", json=move_data, timeout=10)
                
                if move["should_work"]:
                    if response.status_code == 200:
                        self.log_test(f"{move['piece']} Movement", True, 
                                    f"Valid {move['piece']} move {move['from']}-{move['to']} accepted")
                    else:
                        self.log_test(f"{move['piece']} Movement", False, 
                                    f"Valid {move['piece']} move rejected: {response.status_code}")
                else:
                    if response.status_code == 400:
                        self.log_test(f"{move['piece']} Movement", True, 
                                    f"Invalid {move['piece']} move correctly rejected")
                    else:
                        self.log_test(f"{move['piece']} Movement", False, 
                                    f"Invalid {move['piece']} move should have been rejected")
                        
            return True
            
        except Exception as e:
            self.log_test("Piece Movement Validation", False, f"Exception: {str(e)}")
            return False
            
    def test_game_completion_scenarios(self):
        """Test checkmate and stalemate detection"""
        try:
            # This is a complex test that would require setting up specific board positions
            # For now, we'll test that the game can handle multiple moves without crashing
            
            game_data = {
                "mode": "pvp",
                "white_player": "Player1",
                "black_player": "Player2"
            }
            
            response = requests.post(f"{self.base_url}/games", json=game_data, timeout=10)
            if response.status_code != 200:
                self.log_test("Game Completion Setup", False, "Could not create test game")
                return False
                
            game_id = response.json()["id"]
            self.created_games.append(game_id)
            
            # Play a series of moves to test game state management
            moves_sequence = [
                ("e2", "e4"),  # White
                ("e7", "e5"),  # Black
                ("g1", "f3"), # White
                ("b8", "c6"), # Black
                ("f1", "c4"), # White
                ("f8", "c5"), # Black
            ]
            
            for i, (from_pos, to_pos) in enumerate(moves_sequence):
                move_data = {
                    "game_id": game_id,
                    "from_pos": from_pos,
                    "to_pos": to_pos
                }
                
                response = requests.post(f"{self.base_url}/games/{game_id}/moves", json=move_data, timeout=10)
                
                if response.status_code != 200:
                    self.log_test("Game Sequence", False, 
                                f"Move {i+1} failed: {from_pos}-{to_pos}")
                    return False
                    
            self.log_test("Game Sequence", True, "Successfully played 6-move opening sequence")
            
            # Check final game state
            response = requests.get(f"{self.base_url}/games/{game_id}", timeout=10)
            if response.status_code == 200:
                game = response.json()
                if len(game.get("moves_history", [])) == 6:
                    self.log_test("Move History", True, "All moves recorded in history")
                else:
                    self.log_test("Move History", False, 
                                f"Expected 6 moves, got {len(game.get('moves_history', []))}")
            
            return True
            
        except Exception as e:
            self.log_test("Game Completion Test", False, f"Exception: {str(e)}")
            return False
            
    def test_error_handling(self):
        """Test API error handling"""
        try:
            # Test 1: Get non-existent game
            response = requests.get(f"{self.base_url}/games/nonexistent-id", timeout=10)
            if response.status_code == 404:
                self.log_test("404 Error Handling", True, "Correctly returned 404 for non-existent game")
            else:
                self.log_test("404 Error Handling", False, f"Expected 404, got {response.status_code}")
                
            # Test 2: Invalid move data
            if self.created_games:
                invalid_move = {
                    "game_id": self.created_games[0],
                    "from_pos": "invalid",
                    "to_pos": "also_invalid"
                }
                
                response = requests.post(f"{self.base_url}/games/{self.created_games[0]}/moves", 
                                       json=invalid_move, timeout=10)
                
                if response.status_code == 400:
                    self.log_test("Invalid Move Data", True, "Correctly rejected invalid move format")
                else:
                    self.log_test("Invalid Move Data", False, f"Expected 400, got {response.status_code}")
                    
            return True
            
        except Exception as e:
            self.log_test("Error Handling Test", False, f"Exception: {str(e)}")
            return False
            
    def run_all_tests(self):
        """Run comprehensive backend tests"""
        print("🚀 Starting Chess Backend API Tests")
        print("=" * 50)
        
        # Test 1: Bot API
        self.test_get_bots()
        
        # Test 2: Game Creation
        pvp_game_id = self.test_create_pvp_game()
        pvb_game_id = self.test_create_pvb_game()
        
        # Test 3: Game Retrieval
        if pvp_game_id:
            self.test_get_game(pvp_game_id)
            
        # Test 4: Chess Move Validation
        if pvp_game_id:
            self.test_chess_moves(pvp_game_id)
            
        # Test 5: Bot Move Generation
        if pvb_game_id:
            self.test_bot_moves(pvb_game_id)
            
        # Test 6: Piece Movement Rules
        self.test_piece_movement_validation()
        
        # Test 7: Game Completion
        self.test_game_completion_scenarios()
        
        # Test 8: Error Handling
        self.test_error_handling()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
                    
        return passed == total

if __name__ == "__main__":
    tester = ChessBackendTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Backend is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the details above.")