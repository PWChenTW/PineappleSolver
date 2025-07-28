"""
Comprehensive test suite for Card domain model.
"""

import pytest
from src.core.domain.card import Card, Rank, Suit
from src.exceptions import InvalidInputError


class TestRank:
    """Test suite for Rank enum."""
    
    def test_rank_values(self):
        """Test rank integer values."""
        assert Rank.TWO.value == 0
        assert Rank.THREE.value == 1
        assert Rank.ACE.value == 12
    
    def test_rank_display(self):
        """Test rank display characters."""
        assert Rank.TWO.display == '2'
        assert Rank.TEN.display == 'T'
        assert Rank.JACK.display == 'J'
        assert Rank.QUEEN.display == 'Q'
        assert Rank.KING.display == 'K'
        assert Rank.ACE.display == 'A'
    
    def test_from_char_valid(self):
        """Test creating rank from valid characters."""
        assert Rank.from_char('2') == Rank.TWO
        assert Rank.from_char('9') == Rank.NINE
        assert Rank.from_char('T') == Rank.TEN
        assert Rank.from_char('t') == Rank.TEN  # Case insensitive
        assert Rank.from_char('J') == Rank.JACK
        assert Rank.from_char('Q') == Rank.QUEEN
        assert Rank.from_char('K') == Rank.KING
        assert Rank.from_char('A') == Rank.ACE
    
    def test_from_char_invalid(self):
        """Test creating rank from invalid characters."""
        with pytest.raises(InvalidInputError) as exc_info:
            Rank.from_char('')
        assert "must be a single character" in str(exc_info.value)
        
        with pytest.raises(InvalidInputError) as exc_info:
            Rank.from_char('10')  # Two characters
        assert "must be a single character" in str(exc_info.value)
        
        with pytest.raises(InvalidInputError):
            Rank.from_char('X')  # Invalid character
        
        with pytest.raises(InvalidInputError):
            Rank.from_char('1')  # Invalid digit
        
        # Test non-string input
        with pytest.raises(InvalidInputError):
            Rank.from_char(10)


class TestSuit:
    """Test suite for Suit enum."""
    
    def test_suit_values(self):
        """Test suit integer values."""
        assert Suit.CLUBS.value == 0
        assert Suit.DIAMONDS.value == 1
        assert Suit.HEARTS.value == 2
        assert Suit.SPADES.value == 3
    
    def test_suit_display(self):
        """Test suit display characters."""
        assert Suit.CLUBS.display == '♣'
        assert Suit.DIAMONDS.display == '♦'
        assert Suit.HEARTS.display == '♥'
        assert Suit.SPADES.display == '♠'
    
    def test_suit_char(self):
        """Test suit single character representation."""
        assert Suit.CLUBS.char == 'c'
        assert Suit.DIAMONDS.char == 'd'
        assert Suit.HEARTS.char == 'h'
        assert Suit.SPADES.char == 's'
    
    def test_from_char_valid(self):
        """Test creating suit from valid characters."""
        # Test ASCII characters
        assert Suit.from_char('c') == Suit.CLUBS
        assert Suit.from_char('C') == Suit.CLUBS  # Case insensitive
        assert Suit.from_char('d') == Suit.DIAMONDS
        assert Suit.from_char('h') == Suit.HEARTS
        assert Suit.from_char('s') == Suit.SPADES
        
        # Test Unicode symbols
        assert Suit.from_char('♣') == Suit.CLUBS
        assert Suit.from_char('♦') == Suit.DIAMONDS
        assert Suit.from_char('♥') == Suit.HEARTS
        assert Suit.from_char('♠') == Suit.SPADES
    
    def test_from_char_invalid(self):
        """Test creating suit from invalid characters."""
        with pytest.raises(InvalidInputError) as exc_info:
            Suit.from_char('')
        assert "must be a single character" in str(exc_info.value)
        
        with pytest.raises(InvalidInputError):
            Suit.from_char('cd')  # Two characters
        
        with pytest.raises(InvalidInputError):
            Suit.from_char('x')  # Invalid character
        
        # Test non-string input
        with pytest.raises(InvalidInputError):
            Suit.from_char(1)


class TestCard:
    """Test suite for Card class."""
    
    def test_card_initialization(self):
        """Test card initialization with value."""
        card = Card(0)  # 2 of clubs
        assert card.value == 0
        assert card.rank == Rank.TWO
        assert card.suit == Suit.CLUBS
        assert not card.is_joker
        
        card = Card(51)  # Ace of spades
        assert card.value == 51
        assert card.rank == Rank.ACE
        assert card.suit == Suit.SPADES
    
    def test_card_initialization_invalid(self):
        """Test card initialization with invalid values."""
        with pytest.raises(InvalidInputError) as exc_info:
            Card(-1)
        assert "between 0 and 52" in str(exc_info.value)
        
        with pytest.raises(InvalidInputError):
            Card(53)
        
        with pytest.raises(InvalidInputError) as exc_info:
            Card("0")  # String instead of int
        assert "must be an integer" in str(exc_info.value)
        
        with pytest.raises(InvalidInputError):
            Card(1.5)  # Float instead of int
    
    def test_joker(self):
        """Test joker card."""
        joker = Card(52)
        assert joker.is_joker
        assert joker.rank is None
        assert joker.suit is None
        assert str(joker) == "Joker"
    
    def test_from_rank_suit(self):
        """Test creating card from rank and suit."""
        card = Card.from_rank_suit(Rank.ACE, Suit.SPADES)
        assert card.rank == Rank.ACE
        assert card.suit == Suit.SPADES
        assert card.value == 51
        
        card = Card.from_rank_suit(Rank.TWO, Suit.CLUBS)
        assert card.rank == Rank.TWO
        assert card.suit == Suit.CLUBS
        assert card.value == 0
    
    def test_from_rank_suit_invalid(self):
        """Test creating card from invalid rank/suit."""
        with pytest.raises(InvalidInputError) as exc_info:
            Card.from_rank_suit("A", Suit.SPADES)  # String instead of Rank
        assert "must be a Rank instance" in str(exc_info.value)
        
        with pytest.raises(InvalidInputError) as exc_info:
            Card.from_rank_suit(Rank.ACE, "s")  # String instead of Suit
        assert "must be a Suit instance" in str(exc_info.value)
    
    def test_from_string_valid(self):
        """Test creating card from valid string."""
        card = Card.from_string("As")
        assert card.rank == Rank.ACE
        assert card.suit == Suit.SPADES
        
        card = Card.from_string("2c")
        assert card.rank == Rank.TWO
        assert card.suit == Suit.CLUBS
        
        card = Card.from_string("Th")
        assert card.rank == Rank.TEN
        assert card.suit == Suit.HEARTS
        
        # Test with whitespace
        card = Card.from_string("  Kd  ")
        assert card.rank == Rank.KING
        assert card.suit == Suit.DIAMONDS
        
        # Test joker
        joker = Card.from_string("JOKER")
        assert joker.is_joker
        
        joker = Card.from_string("joker")  # Case insensitive
        assert joker.is_joker
    
    def test_from_string_invalid(self):
        """Test creating card from invalid string."""
        with pytest.raises(InvalidInputError) as exc_info:
            Card.from_string(123)  # Not a string
        assert "must be a string" in str(exc_info.value)
        
        with pytest.raises(InvalidInputError) as exc_info:
            Card.from_string("")  # Empty string
        assert "cannot be empty" in str(exc_info.value)
        
        with pytest.raises(InvalidInputError) as exc_info:
            Card.from_string("A")  # Missing suit
        assert "must be 2 characters" in str(exc_info.value)
        
        with pytest.raises(InvalidInputError):
            Card.from_string("Ax")  # Invalid suit
        
        with pytest.raises(InvalidInputError):
            Card.from_string("Xs")  # Invalid rank
    
    def test_string_representation(self):
        """Test string representation of cards."""
        card = Card.from_string("As")
        assert str(card) == "AS"
        
        card = Card.from_string("2c")
        assert str(card) == "2C"
        
        card = Card.from_string("Th")
        assert str(card) == "TH"
        
        joker = Card(52)
        assert str(joker) == "Joker"
    
    def test_repr(self):
        """Test debug representation."""
        card = Card.from_string("As")
        assert repr(card) == "Card('AS')"
        
        joker = Card(52)
        assert repr(joker) == "Card('Joker')"
    
    def test_equality(self):
        """Test card equality."""
        card1 = Card.from_string("As")
        card2 = Card.from_string("As")
        card3 = Card.from_string("Ah")
        
        assert card1 == card2
        assert card1 != card3
        assert card1 != "As"  # Not equal to string
        assert card1 != 51  # Not equal to int
    
    def test_hash(self):
        """Test card hashing for use in sets/dicts."""
        card1 = Card.from_string("As")
        card2 = Card.from_string("As")
        card3 = Card.from_string("Ah")
        
        # Same cards have same hash
        assert hash(card1) == hash(card2)
        
        # Can be used in sets
        card_set = {card1, card2, card3}
        assert len(card_set) == 2  # card1 and card2 are the same
        
        # Can be used as dict keys
        card_dict = {card1: "ace of spades"}
        assert card_dict[card2] == "ace of spades"
    
    def test_comparison(self):
        """Test card comparison."""
        card1 = Card(0)  # 2 of clubs
        card2 = Card(1)  # 2 of diamonds
        card3 = Card(51)  # Ace of spades
        
        assert card1 < card2
        assert card2 < card3
        assert not card3 < card1
        
        # Test comparison with non-Card
        with pytest.raises(TypeError):
            card1 < "2c"
        
        with pytest.raises(TypeError):
            card1 < 0
    
    def test_deck_creation(self):
        """Test creating a standard deck."""
        # Standard deck without jokers
        deck = Card.deck()
        assert len(deck) == 52
        assert all(isinstance(card, Card) for card in deck)
        assert all(not card.is_joker for card in deck)
        
        # Deck with one joker
        deck = Card.deck(num_jokers=1)
        assert len(deck) == 53
        assert sum(card.is_joker for card in deck) == 1
        
        # Deck with two jokers
        deck = Card.deck(num_jokers=2)
        assert len(deck) == 54
        assert sum(card.is_joker for card in deck) == 2
    
    def test_deck_creation_invalid(self):
        """Test creating deck with invalid parameters."""
        with pytest.raises(InvalidInputError) as exc_info:
            Card.deck(num_jokers=-1)
        assert "between 0 and 2" in str(exc_info.value)
        
        with pytest.raises(InvalidInputError):
            Card.deck(num_jokers=3)
        
        with pytest.raises(InvalidInputError) as exc_info:
            Card.deck(num_jokers="1")  # String instead of int
        assert "must be an integer" in str(exc_info.value)
    
    def test_to_dict(self):
        """Test converting card to dictionary."""
        # Standard card
        card = Card.from_string("As")
        data = card.to_dict()
        assert data["type"] == "standard"
        assert data["rank"] == "ACE"
        assert data["suit"] == "SPADES"
        assert data["value"] == 51
        assert data["string"] == "AS"
        
        # Joker
        joker = Card(52)
        data = joker.to_dict()
        assert data["type"] == "joker"
        assert data["value"] == 52
    
    def test_from_dict_valid(self):
        """Test creating card from valid dictionary."""
        # From string
        data = {"type": "standard", "string": "As"}
        card = Card.from_dict(data)
        assert card.rank == Rank.ACE
        assert card.suit == Suit.SPADES
        
        # From rank and suit
        data = {"type": "standard", "rank": "ACE", "suit": "SPADES"}
        card = Card.from_dict(data)
        assert card.rank == Rank.ACE
        assert card.suit == Suit.SPADES
        
        # From value
        data = {"type": "standard", "value": 51}
        card = Card.from_dict(data)
        assert card.rank == Rank.ACE
        assert card.suit == Suit.SPADES
        
        # Joker
        data = {"type": "joker"}
        joker = Card.from_dict(data)
        assert joker.is_joker
    
    def test_from_dict_invalid(self):
        """Test creating card from invalid dictionary."""
        with pytest.raises(InvalidInputError) as exc_info:
            Card.from_dict("not a dict")
        assert "must be a dictionary" in str(exc_info.value)
        
        with pytest.raises(InvalidInputError) as exc_info:
            Card.from_dict({})  # Missing type
        assert "Invalid card data format" in str(exc_info.value)
        
        with pytest.raises(InvalidInputError):
            Card.from_dict({"type": "invalid"})
        
        with pytest.raises(InvalidInputError):
            Card.from_dict({"type": "standard"})  # Missing card data
        
        with pytest.raises(InvalidInputError):
            Card.from_dict({"type": "standard", "rank": "INVALID", "suit": "SPADES"})
    
    def test_round_trip_serialization(self):
        """Test that to_dict and from_dict are inverses."""
        cards = [
            Card.from_string("As"),
            Card.from_string("2c"),
            Card.from_string("Th"),
            Card(52)  # Joker
        ]
        
        for original in cards:
            data = original.to_dict()
            restored = Card.from_dict(data)
            assert original == restored