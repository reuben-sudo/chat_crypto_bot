import re
import requests
import json
import nltk
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import time

# Download required NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    print("Downloading NLTK data...")
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag

@dataclass
class CryptoData:
    """Data class to represent cryptocurrency information"""
    price_trend: str
    market_cap: str
    energy_use: str
    sustainability_score: str
    current_price: float = 0.0
    price_change_24h: float = 0.0
    
    def get_sustainability_numeric_score(self) -> Optional[int]:
        """Extract numeric sustainability score"""
        try:
            return int(self.sustainability_score.split('/')[0])
        except (ValueError, IndexError):
            return None

class CryptoBuddy:
    def __init__(self):
        # Static data as fallback
        self.crypto_data = {
            "Bitcoin": CryptoData("rising", "high", "high", "3/10"),
            "Ethereum": CryptoData("stable", "high", "medium", "6/10"),
            "Cardano": CryptoData("rising", "medium", "low", "8/10"),
            "Solana": CryptoData("rising", "high", "low", "7/10"),
            "Polygon": CryptoData("stable", "medium", "low", "9/10")
        }
        
        # CoinGecko API mapping
        self.crypto_api_ids = {
            "Bitcoin": "bitcoin",
            "Ethereum": "ethereum", 
            "Cardano": "cardano",
            "Solana": "solana",
            "Polygon": "matic-network"
        }
        
        # NLP setup
        try:
            self.stop_words = set(stopwords.words('english'))
        except:
            self.stop_words = set()
        
        # Enhanced patterns for better NLP
        self.patterns = {
            'greeting': [r'\b(hello|hi|hey|good morning|good afternoon|greetings)\b'],
            'thanks': [r'\b(thank you|thanks|thx|appreciate|grateful)\b'],
            'sustainable': [r'\b(sustainable|eco-friendly|green|environment|clean|carbon|renewable)\b'],
            'profitable': [r'\b(profitable|profit|money|earning|trending up|rising|bull|gains|returns)\b'],
            'long_term': [r'\b(long.?term|future|invest for|hold|hodl|years|decade)\b'],
            'price': [r'\b(price|cost|value|worth|current|now|today)\b'],
            'market_cap': [r'\b(market cap|market capitalization|size|volume)\b'],
            'energy': [r'\b(energy|power|consumption|efficient|mining|proof)\b',
                      r'\b(electricity|watts|carbon footprint)\b'],
            'exit': [r'\b(exit|quit|bye|goodbye|stop|end)\b'],
            'help': [r'\b(help|what can you|commands|options)\b'],
            'compare': [r'\b(compare|versus|vs|difference|better)\b'],
            'recommendation': [r'\b(recommend|suggest|advice|best|top|should i)\b']
        }
        
        # Ethics disclaimer
        self.ethics_disclaimer = "\n\n⚠️ **IMPORTANT**: Crypto investments are highly risky and volatile. This is for educational purposes only. Always do your own research and consult with financial advisors before making investment decisions!"
    
    def fetch_real_time_data(self) -> bool:
        """Fetch real-time data from CoinGecko API"""
        try:
            api_ids = list(self.crypto_api_ids.values())
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': ','.join(api_ids),
                'vs_currencies': 'usd',
                'include_24hr_change': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Update crypto data with real-time prices
            for crypto_name, api_id in self.crypto_api_ids.items():
                if api_id in data:
                    self.crypto_data[crypto_name].current_price = data[api_id]['usd']
                    self.crypto_data[crypto_name].price_change_24h = data[api_id].get('usd_24h_change', 0)
                    
                    # Update price trend based on 24h change
                    change = data[api_id].get('usd_24h_change', 0)
                    if change > 5:
                        self.crypto_data[crypto_name].price_trend = "rising"
                    elif change < -5:
                        self.crypto_data[crypto_name].price_trend = "falling"
                    else:
                        self.crypto_data[crypto_name].price_trend = "stable"
            
            return True
            
        except Exception as e:
            print(f"📡 Could not fetch real-time data: {str(e)}")
            print("📊 Using fallback data...")
            return False
    
    def extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms using NLP"""
        try:
            # Tokenize and remove stopwords
            tokens = word_tokenize(text.lower())
            filtered_tokens = [word for word in tokens if word.isalpha() and word not in self.stop_words]
            
            # POS tagging to identify nouns and adjectives
            pos_tags = pos_tag(filtered_tokens)
            key_terms = [word for word, pos in pos_tags if pos.startswith(('NN', 'JJ', 'VB'))]
            
            return key_terms
        except:
            # Fallback to simple word extraction
            words = re.findall(r'\b\w+\b', text.lower())
            return [word for word in words if len(word) > 2 and word not in {'the', 'and', 'or', 'but', 'for', 'with'}]
    
    def analyze_intent(self, user_input: str) -> Dict[str, float]:
        """Analyze user intent using NLP"""
        intent_scores = {}
        key_terms = self.extract_key_terms(user_input)
        
        # Score each intent based on pattern matching and key terms
        for intent, patterns in self.patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, user_input, re.IGNORECASE):
                    score += 1
            
            # Boost score based on key terms
            intent_keywords = {
                'sustainable': ['green', 'eco', 'environment', 'carbon', 'clean'],
                'profitable': ['profit', 'money', 'gain', 'bull', 'earn'],
                'long_term': ['future', 'hold', 'long', 'invest', 'years'],
                'price': ['price', 'cost', 'value', 'current'],
                'compare': ['compare', 'versus', 'better', 'difference']
            }
            
            if intent in intent_keywords:
                for term in key_terms:
                    if term in intent_keywords[intent]:
                        score += 0.5
            
            if score > 0:
                intent_scores[intent] = score
        
        return intent_scores
    
    def match_pattern(self, user_input: str, pattern_key: str) -> bool:
        """Check if user input matches any pattern for given key"""
        patterns = self.patterns.get(pattern_key, [])
        for pattern in patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return True
        return False
    
    def get_sustainable_cryptos(self, min_score: int = 7) -> List[Tuple[str, int]]:
        """Get cryptos with sustainability score above threshold"""
        sustainable = []
        for name, data in self.crypto_data.items():
            score = data.get_sustainability_numeric_score()
            if score and score >= min_score:
                sustainable.append((name, score))
        return sorted(sustainable, key=lambda x: x[1], reverse=True)
    
    def get_rising_cryptos(self) -> List[str]:
        """Get cryptos with rising price trend"""
        return [name for name, data in self.crypto_data.items() 
                if data.price_trend == "rising"]
    
    def get_crypto_with_prices(self, crypto_name: str) -> Optional[str]:
        """Get detailed information about a specific crypto with real-time prices"""
        crypto_name_title = crypto_name.title()
        if crypto_name_title in self.crypto_data:
            data = self.crypto_data[crypto_name_title]
            response = f"📊 {crypto_name_title} Details:\n"
            
            if data.current_price > 0:
                response += f"💰 Current Price: ${data.current_price:,.2f}\n"
                change_emoji = "🟢" if data.price_change_24h >= 0 else "🔴"
                response += f"{change_emoji} 24h Change: {data.price_change_24h:+.2f}%\n"
            
            response += (f"📈 Price Trend: {data.price_trend.title()}\n"
                        f"🏢 Market Cap: {data.market_cap.title()}\n"
                        f"⚡ Energy Use: {data.energy_use.title()}\n"
                        f"🌱 Sustainability Score: {data.sustainability_score}")
            
            return response
        return None
    
    def handle_sustainability_query(self) -> str:
        """Handle sustainability-related queries"""
        sustainable_cryptos = self.get_sustainable_cryptos()
        if sustainable_cryptos:
            best_crypto, best_score = sustainable_cryptos[0]
            response = f"🌱 For sustainability, I recommend {best_crypto}! "
            response += f"It has an excellent sustainability score of {self.crypto_data[best_crypto].sustainability_score}.\n"
            
            if len(sustainable_cryptos) > 1:
                others = [f"{name} ({score}/10)" for name, score in sustainable_cryptos[1:]]
                response += f"Other eco-friendly options: {', '.join(others)}"
            
            return response + self.ethics_disclaimer
        return "I couldn't find highly sustainable options in my current data. Consider asking about energy-efficient cryptos!"
    
    def handle_profitability_query(self) -> str:
        """Handle profitability-related queries with real-time data"""
        rising_cryptos = self.get_rising_cryptos()
        
        if rising_cryptos:
            response = f"📈 Cryptos showing rising trends: {', '.join(rising_cryptos)}.\n"
            
            # Add real-time price info if available
            for crypto in rising_cryptos[:3]:  # Top 3
                data = self.crypto_data[crypto]
                if data.current_price > 0:
                    change_emoji = "🟢" if data.price_change_24h >= 0 else "🔴"
                    response += f"• {crypto}: ${data.current_price:,.2f} {change_emoji}{data.price_change_24h:+.2f}%\n"
            
            return response + self.ethics_disclaimer
        return "Currently no cryptos show a clear rising trend. Market conditions change rapidly!"
    
    def handle_comparison_query(self, user_input: str) -> str:
        """Handle comparison queries between cryptos"""
        mentioned_cryptos = []
        for crypto_name in self.crypto_data.keys():
            if crypto_name.lower() in user_input.lower():
                mentioned_cryptos.append(crypto_name)
        
        if len(mentioned_cryptos) >= 2:
            response = f"🔍 Comparing {' vs '.join(mentioned_cryptos)}:\n\n"
            
            for crypto in mentioned_cryptos:
                data = self.crypto_data[crypto]
                response += f"**{crypto}:**\n"
                if data.current_price > 0:
                    response += f"💰 Price: ${data.current_price:,.2f} ({data.price_change_24h:+.2f}%)\n"
                response += f"🌱 Sustainability: {data.sustainability_score}\n"
                response += f"⚡ Energy Use: {data.energy_use}\n\n"
            
            return response + self.ethics_disclaimer
        
        return "To compare cryptos, please mention at least 2 cryptocurrency names in your question!"
    
    def get_response(self, user_input: str) -> str:
        """Generate response based on user input using NLP analysis"""
        user_input = user_input.strip()
        
        # Check for exit
        if self.match_pattern(user_input, 'exit'):
            return "EXIT"
        
        # Analyze intent using NLP
        intent_scores = self.analyze_intent(user_input)
        
        # Handle based on highest scoring intent
        if intent_scores:
            top_intent = max(intent_scores.items(), key=lambda x: x[1])[0]
            
            if top_intent == 'greeting':
                return "👋 Hello! I'm CryptoBuddy, your crypto investment advisor with real-time data! I can help you with sustainable, profitable, or long-term crypto recommendations. What interests you?"
            
            elif top_intent == 'thanks':
                return "🙏 You're very welcome! Feel free to ask more questions about crypto investments!"
            
            elif top_intent == 'help':
                return ("🤖 I can help you with:\n"
                       "• 🌱 Sustainable/eco-friendly cryptos\n"
                       "• 📈 Profitable/trending cryptos (with real-time prices!)\n"
                       "• 🚀 Long-term investment advice\n"
                       "• 📊 Specific crypto details\n"
                       "• 🔍 Compare different cryptocurrencies\n"
                       "\nJust ask me naturally - I understand conversational language!")
            
            elif top_intent == 'compare':
                return self.handle_comparison_query(user_input)
            
            elif top_intent == 'sustainable':
                return self.handle_sustainability_query()
            
            elif top_intent == 'profitable':
                return self.handle_profitability_query()
            
            elif top_intent == 'price':
                # Check if asking about specific crypto
                for crypto_name in self.crypto_data.keys():
                    if crypto_name.lower() in user_input.lower():
                        return self.get_crypto_with_prices(crypto_name) + self.ethics_disclaimer
                
                # General price info
                response = "📊 Current Crypto Prices:\n"
                for name, data in self.crypto_data.items():
                    if data.current_price > 0:
                        change_emoji = "🟢" if data.price_change_24h >= 0 else "🔴"
                        response += f"• {name}: ${data.current_price:,.2f} {change_emoji}{data.price_change_24h:+.2f}%\n"
                
                return response + self.ethics_disclaimer
        
        # Check for specific crypto inquiry
        for crypto_name in self.crypto_data.keys():
            if crypto_name.lower() in user_input.lower():
                return self.get_crypto_with_prices(crypto_name) + self.ethics_disclaimer
        
        # Default response
        return ("🤖 I'm CryptoBuddy with real-time crypto data! Ask me about:\n"
               "• Sustainable cryptos\n"
               "• Profitable opportunities\n" 
               "• Current prices\n"
               "• Comparisons between cryptos\n"
               "\nTry asking naturally - I understand conversational language!" + self.ethics_disclaimer)
    
    def chat(self):
        """Main chat loop"""
        print("=" * 60)
        print("🚀 Welcome to CryptoBuddy v2.0! 🚀")
        print("Your AI-powered crypto advisor with real-time data & NLP")
        print("=" * 60)
        
        # Fetch real-time data on startup
        print("📡 Fetching real-time crypto data...")
        if self.fetch_real_time_data():
            print("✅ Real-time data loaded successfully!")
        else:
            print("⚠️ Using fallback data - real-time features limited")
        
        print("\nType 'exit', 'quit', or 'bye' to end the conversation")
        print("=" * 60)
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if not user_input:
                    print("🤖 CryptoBuddy: Please ask me something about crypto investments!")
                    continue
                
                response = self.get_response(user_input)
                
                if response == "EXIT":
                    print("🤖 CryptoBuddy: Thanks for chatting! Remember - always do your own research! 🚀💰")
                    break
                
                print(f"🤖 CryptoBuddy: {response}")
                
                # Refresh data periodically (every 10 queries)
                if hasattr(self, 'query_count'):
                    self.query_count += 1
                    if self.query_count % 10 == 0:
                        print("\n📡 Refreshing real-time data...")
                        self.fetch_real_time_data()
                else:
                    self.query_count = 1
                
            except KeyboardInterrupt:
                print("\n🤖 CryptoBuddy: Goodbye! 👋")
                break
            except Exception as e:
                print(f"🤖 CryptoBuddy: Sorry, I encountered an error: {str(e)}")
                print("Please try asking your question again!")

def main():
    """Main function to run the chatbot"""
    crypto_buddy = CryptoBuddy()
    crypto_buddy.chat()

if __name__ == "__main__":
    main()