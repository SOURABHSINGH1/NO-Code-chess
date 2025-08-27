#!/usr/bin/env python3
"""
Focused testing to debug specific issues
"""

import requests
import json

BASE_URL = "https://strategic-chess-6.preview.emergentagent.com/api"

def test_move_validation():
    """Test move validation more carefully"""
    print("🔍 Testing Move Validation Logic")
    print("=" * 40)
    
    # Create a fresh game
    game_data = {"mode": "pvp", "white_player": "Alice", "black_player": "Bob"}
    response = requests.post(f"{BASE_URL}/games", json=game_data)
    
    if response.status_code != 200:
        print("❌ Failed to create game")
        return
        
    game_id = response.json()["id"]
    print(f"✅ Created game: {game_id}")
    
    # Test 1: Valid white pawn move
    move1 = {"game_id": game_id, "from_pos": "e2", "to_pos": "e4"}
    response = requests.post(f"{BASE_URL}/games/{game_id}/moves", json=move1)
    print(f"White e2-e4: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
    
    # Check turn after first move
    response = requests.get(f"{BASE_URL}/games/{game_id}")
    current_turn = response.json()["current_turn"]
    print(f"Turn after white move: {current_turn}")
    
    # Test 2: Try to move white piece again (should fail - wrong turn)
    invalid_move = {"game_id": game_id, "from_pos": "d2", "to_pos": "d4"}
    response = requests.post(f"{BASE_URL}/games/{game_id}/moves", json=invalid_move)
    print(f"White d2-d4 (wrong turn): {response.status_code} {'✅' if response.status_code == 400 else '❌'}")
    
    # Test 3: Valid black pawn move
    move2 = {"game_id": game_id, "from_pos": "e7", "to_pos": "e5"}
    response = requests.post(f"{BASE_URL}/games/{game_id}/moves", json=move2)
    print(f"Black e7-e5: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
    
    # Test 4: Valid white knight move
    move3 = {"game_id": game_id, "from_pos": "g1", "to_pos": "f3"}
    response = requests.post(f"{BASE_URL}/games/{game_id}/moves", json=move3)
    print(f"White g1-f3: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
    
    # Test 5: Invalid move (piece doesn't exist)
    invalid_move2 = {"game_id": game_id, "from_pos": "e4", "to_pos": "e5"}  # e5 is occupied by black pawn
    response = requests.post(f"{BASE_URL}/games/{game_id}/moves", json=invalid_move2)
    print(f"White e4-e5 (capture): {response.status_code} {'✅' if response.status_code == 400 else '❌'}")
    
    # Test 6: Test bishop move (should be blocked initially)
    move4 = {"game_id": game_id, "from_pos": "d7", "to_pos": "d6"}  # Black pawn move first
    response = requests.post(f"{BASE_URL}/games/{game_id}/moves", json=move4)
    print(f"Black d7-d6: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
    
    bishop_move = {"game_id": game_id, "from_pos": "f1", "to_pos": "a6"}  # Should be blocked
    response = requests.post(f"{BASE_URL}/games/{game_id}/moves", json=bishop_move)
    print(f"White f1-a6 (blocked): {response.status_code} {'✅' if response.status_code == 400 else '❌'}")

def test_check_detection():
    """Test check and checkmate detection"""
    print("\n🔍 Testing Check Detection")
    print("=" * 40)
    
    # This would require setting up specific positions
    # For now, just test that the engine can handle multiple moves
    game_data = {"mode": "pvp", "white_player": "Player1", "black_player": "Player2"}
    response = requests.post(f"{BASE_URL}/games", json=game_data)
    
    if response.status_code != 200:
        print("❌ Failed to create game")
        return
        
    game_id = response.json()["id"]
    
    # Play Scholar's Mate sequence (quick checkmate)
    moves = [
        ("e2", "e4"),  # White
        ("e7", "e5"),  # Black  
        ("d1", "h5"),  # White Queen
        ("b8", "c6"),  # Black Knight
        ("f1", "c4"),  # White Bishop
        ("g8", "f6"),  # Black Knight
        ("h5", "f7")   # White Queen checkmate
    ]
    
    for i, (from_pos, to_pos) in enumerate(moves):
        move = {"game_id": game_id, "from_pos": from_pos, "to_pos": to_pos}
        response = requests.post(f"{BASE_URL}/games/{game_id}/moves", json=move)
        
        if response.status_code == 200:
            print(f"Move {i+1} ({from_pos}-{to_pos}): ✅")
            
            # Check game status after each move
            game_response = requests.get(f"{BASE_URL}/games/{game_id}")
            if game_response.status_code == 200:
                game = game_response.json()
                if game.get("game_status") == "finished":
                    print(f"🏁 Game finished! Winner: {game.get('winner', 'None')}")
                    break
        else:
            print(f"Move {i+1} ({from_pos}-{to_pos}): ❌ Status {response.status_code}")
            if response.status_code == 400:
                print(f"   Error: {response.json().get('detail', 'Unknown error')}")

if __name__ == "__main__":
    test_move_validation()
    test_check_detection()