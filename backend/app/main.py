from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import requests
from dotenv import load_dotenv
from openai import OpenAI
import traceback
from datetime import date
from urllib.parse import quote
from typing import Optional
import asyncio
import time

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = FastAPI(debug=True)

# Dil eşleştirme sözlüğü
LANGUAGE_MAPPING = {
    "en": "English",
    "tr": "Turkish",
    "es": "Spanish", 
    "fr": "French",
    "de": "German",
    "hi": "Hindi",
    "zh": "Chinese",
    "it": "Italian"
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class FormData(BaseModel):
    movies: str
    music: str
    brands: str
    gender: str
    language: Optional[str] = "en"  # Varsayılan İngilizce
    variation: Optional[int] = 0

# ✅ CulturalMap için AI fonksiyonu
def generate_cultural_map_insights(countries: list[str], language: str = "en", user_persona: dict | None = None) -> dict:
    print(f"=== GENERATE CULTURAL MAP INSIGHTS ===")
    print(f"Countries: {countries}")
    print(f"Language: {language}")
    print(f"User persona: {user_persona}")
    
    if not countries:
        print("No countries provided, returning empty dict")
        return {}

    target_language = LANGUAGE_MAPPING.get(language, "English")
    print(f"Target language: {target_language}")
    
    # Kullanıcı kişilik bilgilerini hazırla
    user_info = ""
    if user_persona:
        user_preferences = user_persona.get('user_preferences', {})
        if language == "tr":
            user_info = f"""
            Kullanıcı Kişilik Analizi:
            - Kişilik Adı: {user_persona.get('personaName', 'Bilinmeyen')}
            - Özellikler: {', '.join(user_persona.get('traits', []))}
            - Kültürel İkiz: {user_persona.get('culturalTwin', 'Bilinmeyen')}
            - Açıklama: {user_persona.get('description', 'Bilinmeyen')}
            - İlgi Alanları: {user_persona.get('insights', {}).get('likelyInterests', 'Bilinmeyen')}
            
            Kullanıcı Tercihleri:
            - Favori Filmler: {user_preferences.get('movies', 'Belirtilmemiş')}
            - Favori Müzik: {user_preferences.get('music', 'Belirtilmemiş')}
            - Favori Markalar: {user_preferences.get('brands', 'Belirtilmemiş')}
            - Cinsiyet: {user_preferences.get('gender', 'Belirtilmemiş')}
            """
        else:
            user_info = f"""
            User Personality Analysis:
            - Personality Name: {user_persona.get('personaName', 'Unknown')}
            - Traits: {', '.join(user_persona.get('traits', []))}
            - Cultural Twin: {user_persona.get('culturalTwin', 'Unknown')}
            - Description: {user_persona.get('description', 'Unknown')}
            - Interests: {user_persona.get('insights', {}).get('likelyInterests', 'Unknown')}
            
            User Preferences:
            - Favorite Movies: {user_preferences.get('movies', 'Not specified')}
            - Favorite Music: {user_preferences.get('music', 'Not specified')}
            - Favorite Brands: {user_preferences.get('brands', 'Not specified')}
            - Gender: {user_preferences.get('gender', 'Not specified')}
            """
    
    if language == "tr":
        prompt = f"""
        CRITICAL INSTRUCTION: You MUST respond ENTIRELY in Turkish language.
        ALL cultural insights and recommendations must be in Turkish.
        
        {user_info}
        
        Bu kullanıcının kişilik analizi ve tercihlerine göre, aşağıdaki ülkeler için kişiselleştirilmiş kültürel öneriler ver:
        
        Her ülke için şunları içeren bir JSON array döndür:
        - country (string) - ülke adı
        - culturalInsight (2-3 cümle) - Türkçe dilinde kültür hakkında detaylı açıklama
        - recommendation (string) - genel öneri (kısa özet)
        - music (string) - müzik önerileri (sanatçı - şarkı formatında)
        - movies (string) - film önerileri (film adları)
        - personalizedReason (string) - neden bu önerinin kullanıcıya uygun olduğunu açıklayan 1-2 cümle

        Ülkeler: {', '.join(countries)}

        ÖNEMLİ KURALLAR:
        - Tüm açıklamalar Türkçe dilinde olmalı
        - Kullanıcının favori filmlerini, müziklerini ve markalarını dikkate al
        - Her ülke için FARKLI TÜRDE öneriler ver
        - Kullanıcının culturalTwin'i ile ilgili bağlantılar kur
        - SPESİFİK İSİMLER KULLAN:
          * Müzik: "BTS - Dynamite", "BlackPink - How You Like That"
          * Filmler: "Inception", "The Matrix", "Parasite", "Spirited Away"
        - Her ülke için 3-4 müzik ve 3-4 film önerisi ver
        - Sadece geçerli JSON listesi döndür
        """
    else:
        prompt = f"""
        CRITICAL INSTRUCTION: You MUST respond ENTIRELY in English language.
        ALL cultural insights and recommendations must be in English.
        
        {user_info}
        
        Based on this user's personality analysis and preferences, provide personalized cultural recommendations for the following countries:
        
        For each country, return a JSON array containing:
        - country (string) - country name
        - culturalInsight (2-3 sentences) - detailed explanation about the culture in English
        - recommendation (string) - general recommendation (short summary)
        - music (string) - music recommendations (artist - song format)
        - movies (string) - movie recommendations (movie titles)
        - personalizedReason (string) - 1-2 sentences explaining why this recommendation is suitable for the user

        Countries: {', '.join(countries)}

        IMPORTANT RULES:
        - All descriptions must be in English
        - Consider the user's favorite movies, music, and brands
        - Provide DIFFERENT TYPES of recommendations for each country
        - Connect with the user's culturalTwin
        - USE SPECIFIC NAMES:
          * Music: "BTS - Dynamite", "BlackPink - How You Like That"
          * Movies: "Inception", "The Matrix", "Parasite", "Spirited Away"
        - Provide 3-4 music and 3-4 movie recommendations for each country
        - Only respond with valid JSON list
        """
    
    print(f"Prompt: {prompt}")

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )

        content = response.choices[0].message.content
        print(f"GPT response content: {content}")

        if not content:
            print("⚠️ GPT returned empty cultural map content")
            return {}

        try:
            parsed = json.loads(content)
            print(f"Parsed JSON: {parsed}")
            result = {item["country"]: item for item in parsed if "country" in item}
            print(f"Final result: {result}")
            return result
        except Exception as e:
            print("❌ Failed to parse cultural map response:", e)
            print("Raw content:", content)
            return {}
    except Exception as e:
        print(f"❌ GPT API Error for cultural map: {e}")
        # Fallback cultural map based on language
        if language == "tr":
            return {
                "USA": {
                    "country": "USA",
                    "culturalInsight": "Amerikan kültürü çeşitlilik ve yenilikçilikle karakterize edilir. Hollywood film endüstrisi, Broadway müzikalleri ve çeşitli müzik türleriyle dünya kültürüne büyük katkı sağlar.",
                    "recommendation": "Hollywood filmleri ve rock müziği",
                    "music": "Bruce Springsteen - Born to Run, Queen - Bohemian Rhapsody, Michael Jackson - Thriller",
                    "movies": "Inception, The Matrix, Interstellar, Avengers: Endgame, The Godfather",
                    "personalizedReason": "Yaratıcı ve açık fikirli kişiliğiniz için ideal"
                },
                "South Korea": {
                    "country": "South Korea",
                    "culturalInsight": "Güney Kore kültürü teknoloji ve geleneksel değerlerin mükemmel harmanıdır. K-Pop müziği, K-drama dizileri ve geleneksel hanbok kıyafetleri modern ve geleneksel değerleri birleştirir.",
                    "recommendation": "K-Pop müziği ve K-drama dizileri",
                    "music": "BTS - Dynamite, BlackPink - How You Like That, IU - Blueming, Red Velvet - Psycho",
                    "movies": "Parasite, Squid Game, Train to Busan, Oldboy, My Sassy Girl",
                    "personalizedReason": "Teknoloji ve geleneksel değerleri seven kişiliğinize uygun"
                },
                "UK": {
                    "country": "UK",
                    "culturalInsight": "İngiliz kültürü gelenek ve modernliğin mükemmel dengesidir. British rock müziği, Shakespeare tiyatrosu ve çay kültürü ile zengin bir kültürel mirasa sahiptir.",
                    "recommendation": "British rock müziği ve tiyatro",
                    "music": "The Beatles - Hey Jude, Queen - Bohemian Rhapsody, Adele - Rolling in the Deep, Ed Sheeran - Shape of You",
                    "movies": "Harry Potter serisi, Sherlock Holmes, James Bond, The King's Speech",
                    "personalizedReason": "Gelenek ve modernliği dengeleyen kişiliğiniz için mükemmel"
                },
                "Japan": {
                    "country": "Japan",
                    "culturalInsight": "Japon kültürü geleneksel değerler ve teknolojik ilerlemenin sentezidir. Anime, manga, geleneksel çay seremonisi ve modern teknoloji ile benzersiz bir kültür oluşturur.",
                    "recommendation": "Anime ve manga",
                    "music": "BABYMETAL - Gimme Chocolate, ONE OK ROCK - The Beginning, Perfume - Polyrhythm",
                    "movies": "Spirited Away, Attack on Titan, Death Note, Your Name, Akira",
                    "personalizedReason": "Teknoloji ve sanatı birleştiren kişiliğinize uygun"
                }
            }
        else:
            # English fallback
            return {
                "USA": {
                    "country": "USA",
                    "culturalInsight": "American culture is characterized by diversity and innovation. The Hollywood film industry, Broadway musicals, and various music genres contribute greatly to world culture.",
                    "recommendation": "Hollywood movies and rock music",
                    "music": "Bruce Springsteen - Born to Run, Queen - Bohemian Rhapsody, Michael Jackson - Thriller",
                    "movies": "Inception, The Matrix, Interstellar, Avengers: Endgame, The Godfather",
                    "personalizedReason": "Perfect for your creative and open-minded personality"
                },
                "South Korea": {
                    "country": "South Korea",
                    "culturalInsight": "South Korean culture is a perfect blend of technology and traditional values. K-Pop music, K-drama series, and traditional hanbok clothing combine modern and traditional values.",
                    "recommendation": "K-Pop music and K-drama series",
                    "music": "BTS - Dynamite, BlackPink - How You Like That, IU - Blueming, Red Velvet - Psycho",
                    "movies": "Parasite, Squid Game, Train to Busan, Oldboy, My Sassy Girl",
                    "personalizedReason": "Suitable for your personality that loves technology and traditional values"
                },
                "UK": {
                    "country": "UK",
                    "culturalInsight": "British culture is the perfect balance of tradition and modernity. British rock music, Shakespeare theater, and tea culture have a rich cultural heritage.",
                    "recommendation": "British rock music and theater",
                    "music": "The Beatles - Hey Jude, Queen - Bohemian Rhapsody, Adele - Rolling in the Deep, Ed Sheeran - Shape of You",
                    "movies": "Harry Potter series, Sherlock Holmes, James Bond, The King's Speech",
                    "personalizedReason": "Perfect for your personality that balances tradition and modernity"
                },
                "Japan": {
                    "country": "Japan",
                    "culturalInsight": "Japanese culture is a synthesis of traditional values and technological progress. Anime, manga, traditional tea ceremony, and modern technology create a unique culture.",
                    "recommendation": "Anime and manga",
                    "music": "BABYMETAL - Gimme Chocolate, ONE OK ROCK - The Beginning, Perfume - Polyrhythm",
                    "movies": "Spirited Away, Attack on Titan, Death Note, Your Name, Akira",
                    "personalizedReason": "Suitable for your personality that combines technology and art"
                }
            }

# Qloo autocomplete
def autocomplete_entity(query: str, entity_type: str = "artist") -> Optional[str]:
    # Hackathon API URL'i kullan
    base_url = os.getenv("QLOO_API_URL", "https://hackathon.api.qloo.com")
    key = os.getenv("QLOO_API_KEY")
    
    # API anahtarı yoksa fallback kullan
    if not key:
        print(f"⚠️ Qloo API key not configured, using fallback for: {query}")
        return None
        
    safe_query = quote(query)
    url = f"{base_url}/search?query={safe_query}"
    headers = {"x-api-key": key}

    try:
        response = requests.get(url, headers=headers, timeout=5)
        print(f"🔵 Autocomplete [{query}] → {response.status_code}")

        if response.status_code == 200:
            results = response.json().get("results", [])
            for r in results:
                if entity_type in r.get("type", "").lower():
                    return r.get("id", "")
    except Exception as e:
        print(f"⚠️ Qloo API error for {query}: {e}")
    
    print(f"⚠️ Qloo Autocomplete fallback activated for: {query}")
    return None

# Qloo trending
def get_qloo_trending(entity_id: Optional[str], entity_type: str = "artist") -> list:
    if not entity_id:
        return []

    # Hackathon API URL'i kullan
    base_url = os.getenv("QLOO_API_URL", "https://hackathon.api.qloo.com")
    key = os.getenv("QLOO_API_KEY")
    
    # API anahtarı yoksa boş liste döndür
    if not key:
        print(f"⚠️ Qloo API key not configured, returning empty trending for: {entity_id}")
        return []

    today = date.today()
    start_date = f"{today.year}-01-01"
    end_date = today.isoformat()

    url = (
        f"{base_url}/v2/insights?"
        f"filter.start_date={start_date}&"
        f"filter.end_date={end_date}&"
        f"filter.type=urn:entity:{entity_type}&"
        f"signal.interests.entities={entity_id}"
    )

    headers = {"x-api-key": key}
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        print("🟣 Trending response:", response.status_code)

        if response.status_code == 200:
            data = response.json()
            items = data.get("results", [])
            return [i.get("name", "Unknown") for i in items if "name" in i]
    except Exception as e:
        print(f"⚠️ Qloo API error for trending: {e}")
    
    return []

def generate_persona_from_taste(movies: str, music: str, brands: str, gender: str, language: str = "en", variation: int = 0) -> dict:
    """OpenAI GPT-4 ile kullanıcı persona'sı oluştur"""
    
    target_language = "Turkish" if language == "tr" else "English"
    
    # API key kontrolü
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your-openai-api-key-here":
        print("⚠️ OpenAI API key not found, using fallback response")
        # Fallback response based on language with variation
        fallback_names = {
            "tr": ["Kültürel Keşifçi", "Dünya Vatandaşı", "Kültür Elçisi", "Sınırlar Ötesi", "Kültürel Yolcu", "Kültür Avcısı", "Dünya Gezgini", "Kültür Meraklısı", "Sınır Tanımayan", "Kültür Aşığı", "Kültür Kaşifi", "Dünya Seyyahı", "Kültür Ustası", "Sınır Gezgini", "Kültür Sanatçısı"],
            "en": ["Cultural Explorer", "Global Citizen", "Cultural Ambassador", "Border Crosser", "Cultural Traveler", "Culture Hunter", "World Wanderer", "Culture Enthusiast", "Boundary Breaker", "Culture Lover", "Cultural Pioneer", "World Nomad", "Culture Master", "Border Walker", "Cultural Artist"]
        }
        fallback_twins = ["Tom Hanks", "Beyoncé", "Leonardo DiCaprio", "Taylor Swift", "BTS", "BlackPink", "Lady Gaga", "Brad Pitt", "Adele", "Johnny Depp", "Dua Lipa", "Ed Sheeran", "Ariana Grande", "Justin Bieber", "Drake", "Post Malone", "Billie Eilish", "The Weeknd", "Doja Cat", "Olivia Rodrigo", "Harry Styles", "Lana Del Rey", "Bad Bunny", "Kendrick Lamar", "The Weeknd", "Travis Scott", "Cardi B", "Megan Thee Stallion", "Lil Nas X", "Roddy Ricch"]
        
        name_index = variation % len(fallback_names.get(language, fallback_names["en"]))
        twin_index = variation % len(fallback_twins)
        
        # Generate celebrity based on user preferences
        user_preferences = f"Movies: {movies}, Music: {music}, Brands: {brands}, Gender: {gender}"
        if "iron man" in movies.lower() or "marvel" in movies.lower():
            selected_celebrity = "Robert Downey Jr."
        elif "rock" in music.lower() or "acdc" in music.lower():
            selected_celebrity = "Angus Young"
        elif "nike" in brands.lower():
            selected_celebrity = "Michael Jordan"
        else:
            celebrity_options = ["Tom Hanks", "Beyoncé", "Leonardo DiCaprio", "Taylor Swift", "Brad Pitt", "Adele", "Johnny Depp", "Ed Sheeran", "Ariana Grande", "Drake"]
            selected_celebrity = celebrity_options[variation % len(celebrity_options)]
        
        if language == "tr":
            fallback_response = {
                "personaName": fallback_names["tr"][name_index],
                "traits": ["Yaratıcı", "Meraklı", "Sosyal", "Dinamik", "Açık Fikirli"],
                "culturalTwin": selected_celebrity,
                "description": "Kültürel çeşitliliğe değer veren, yeni deneyimlere açık bir kişilik. Farklı kültürleri keşfetmeyi seven, sosyal ve yaratıcı bir yapıya sahip.",
                "interests": ["Film", "Müzik", "Seyahat", "Teknoloji"],
                "culturalDNAScore": {
                    "Kuzey Amerika": f"{30 + (variation % 20)}%",
                    "Avrupa": f"{20 + (variation % 15)}%",
                    "Asya": f"{25 + (variation % 15)}%",
                    "Türkiye": f"{15 + (variation % 10)}%"
                },
                "archetype": {
                    "name": "Kültürel Keşifçi",
                    "description": "Farklı kültürleri keşfetmeyi seven, açık fikirli kişilik."
                }
            }
        else:
            fallback_response = {
                "personaName": fallback_names["en"][name_index],
                "traits": ["Creative", "Curious", "Social", "Dynamic", "Open-minded"],
                "culturalTwin": selected_celebrity,
                "description": "A personality that values cultural diversity and is open to new experiences. Loves exploring different cultures, social and creative in nature.",
                "interests": ["Film", "Music", "Travel", "Technology"],
                "culturalDNAScore": {
                    "North America": f"{30 + (variation % 20)}%",
                    "Europe": f"{20 + (variation % 15)}%",
                    "Asia": f"{25 + (variation % 15)}%",
                    "Turkey": f"{15 + (variation % 10)}%"
                },
                "archetype": {
                    "name": "Cultural Explorer",
                    "description": "Open-minded personality who loves exploring different cultures."
                }
            }
        return fallback_response
    
    print(f"🔍 DEBUG: generate_persona_from_taste called with variation: {variation}")
    print(f"🔍 DEBUG: Input data - movies: {movies}, music: {music}, brands: {brands}, gender: {gender}")
    
    # Add more randomness to the prompt
    import random
    
    # Use variation to create different random choices each time
    random.seed(variation)
    
    # Generate completely random elements to make each prompt unique
    styles = ["creative", "analytical", "artistic", "scientific", "philosophical", "psychological", "sociological", "anthropological", "poetic", "narrative", "intuitive", "logical"]
    approaches = ["focus on personality", "emphasize cultural aspects", "highlight interests", "describe traits", "explore background", "analyze preferences", "examine choices", "interpret tastes", "delve into character", "uncover identity", "reveal essence", "capture spirit"]
    emotions = ["enthusiastic", "thoughtful", "curious", "passionate", "reflective", "inspired", "fascinated", "intrigued", "excited", "contemplative", "amazed", "delighted"]
    perspectives = ["modern", "traditional", "global", "local", "universal", "personal", "cultural", "social", "contemporary", "timeless", "progressive", "classic"]
    focuses = ["individual traits", "cultural connections", "personal interests", "social dynamics", "creative expression", "intellectual curiosity", "emotional depth", "spiritual awareness", "life philosophy", "worldview"]
    
    # Use variation to select different elements each time
    random_style = styles[variation % len(styles)]
    random_approach = approaches[variation % len(approaches)]
    random_emotion = emotions[variation % len(emotions)]
    random_perspective = perspectives[variation % len(perspectives)]
    random_focus = focuses[variation % len(focuses)]
    
    # Add random instructions to make each prompt completely different
    instruction_types = ['metaphors', 'analogies', 'descriptions', 'comparisons', 'stories', 'examples', 'symbols', 'archetypes']
    aspect_types = ['emotional', 'intellectual', 'social', 'creative', 'spiritual', 'practical', 'artistic', 'analytical']
    influence_types = ['modern', 'traditional', 'global', 'local', 'urban', 'rural', 'cosmopolitan', 'authentic']
    dimension_types = ['personal', 'cultural', 'social', 'artistic', 'professional', 'lifestyle', 'values', 'aspirations']
    perspective_types = ['positive', 'neutral', 'optimistic', 'realistic', 'idealistic', 'pragmatic', 'romantic']
    tone_types = ['conversational', 'formal', 'poetic', 'analytical', 'narrative', 'descriptive']
    
    random_instructions = [
        f"Use {instruction_types[variation % len(instruction_types)]} to describe the personality",
        f"Emphasize {aspect_types[variation % len(aspect_types)]} aspects",
        f"Consider {influence_types[variation % len(influence_types)]} influences",
        f"Focus on {dimension_types[variation % len(dimension_types)]} dimensions",
        f"Approach from a {perspective_types[variation % len(perspective_types)]} perspective",
        f"Write in a {tone_types[variation % len(tone_types)]} tone"
    ]
    
    # Let GPT choose the celebrity based on user preferences
    print(f"🔍 DEBUG: GPT will choose celebrity based on user preferences")
    print(f"🔍 DEBUG: Random style: {random_style}")
    print(f"🔍 DEBUG: Random approach: {random_approach}")
    print(f"🔍 DEBUG: Random emotion: {random_emotion}")
    print(f"🔍 DEBUG: Random perspective: {random_perspective}")
    print(f"🔍 DEBUG: Random focus: {random_focus}")
    print(f"🔍 DEBUG: Random instructions: {random_instructions}")
    
    prompt = f"""
    Analyze the user's taste preferences and create a detailed cultural persona. Respond in {target_language} only.
    
    VARIATION SEED: {variation} (Use this to create different results each time)
    ANALYSIS STYLE: {random_style}
    APPROACH: {random_approach}
    EMOTION: {random_emotion}
    PERSPECTIVE: {random_perspective}
    FOCUS: {random_focus}
    ADDITIONAL INSTRUCTIONS: {'; '.join(random_instructions)}
    
    CELEBRITY SELECTION: Choose a REAL famous person as culturalTwin based on the user's preferences.
    - The celebrity should match the user's movie, music, and brand preferences
    - Choose someone who represents similar cultural values and lifestyle
    - Use a REAL celebrity name (actor, musician, artist, athlete, etc.)
    - The celebrity should be well-known and recognizable

    USER PREFERENCES ANALYSIS:
    - Movies: {movies} (Analyze the user's movie preferences and what they reveal about personality)
    - Music: {music} (Analyze the user's music taste and what it indicates about their cultural background)
    - Brands: {brands} (Analyze the user's brand preferences and what they suggest about lifestyle and values)
    - Gender: {gender} (Consider gender identity in cultural context)
    
    ANALYSIS REQUIREMENTS:
    - The personaName MUST reflect the user's actual preferences (movies, music, brands)
    - The traits MUST be based on the user's specific choices
    - The description MUST explain how the user's preferences relate to their personality
    - The culturalDNAScore MUST reflect the cultural influences evident in the user's choices
    - The archetype MUST match the personality type suggested by the user's preferences

    Create a JSON response with the following structure (all values must be in {target_language}):
    {{
        "personaName": "Creative name based on preferences and variation seed {variation} (MUST be different for each variation)",
        "traits": ["trait1", "trait2", "trait3", "trait4", "trait5"],
        "culturalTwin": "Choose a celebrity based on user preferences",
        "description": "2-3 sentence personality description that reflects the user's preferences",
        "interests": ["interest1", "interest2", "interest3"],
        "culturalDNAScore": {{
            "region1": "percentage%",
            "region2": "percentage%",
            "region3": "percentage%",
            "region4": "percentage%"
        }},
        "archetype": {{
            "name": "archetype name",
            "description": "1 sentence description"
        }}
    }}

    IMPORTANT FOR culturalDNAScore:
    - Use REAL region/country names like: "North America", "Europe", "Asia", "Turkey", "USA", "UK", "Japan", "South Korea", "Germany", "France", "Italy", "Spain", "Canada", "Australia", "Brazil", "India", "China", "Russia"
    - DO NOT use generic terms like "Global", "Local", "Mixed"
    - Total of all percentages should equal 100%
    - Use 3-4 regions maximum
    - Examples: {{"North America": "35%", "Europe": "25%", "Asia": "25%", "Turkey": "15%"}} or {{"USA": "40%", "UK": "30%", "Japan": "20%", "South Korea": "10%"}}

    ANALYSIS INSTRUCTIONS:
    - Use variation seed {variation} to create different results each time
    - Vary personaName based on variation (use variation % 10 for different name patterns)
    - Adjust culturalDNAScore percentages based on variation (add/subtract 5-15% from each region)
    - Vary traits based on variation (use variation % 5 for different trait combinations)
    - Make each result unique while maintaining relevance to user preferences
    - IMPORTANT: Use the variation seed {variation} to ensure different results every time
    - CRITICAL: The personaName MUST be different for each variation seed
    - CRITICAL: The culturalDNAScore percentages MUST be different for each variation seed

    CELEBRITY SELECTION: Choose a REAL famous person as culturalTwin based on the user's preferences.
    - The celebrity should match the user's movie, music, and brand preferences
    - Choose someone who represents similar cultural values and lifestyle
    - Use a REAL celebrity name (actor, musician, artist, athlete, etc.)
    - The celebrity should be well-known and recognizable
    
    FINAL REMINDER:
    - culturalTwin MUST be a REAL famous person's name from the list above
    - DO NOT use "Unknown" or "Bilinmeyen"
    - All text must be in {target_language}
    - Percentages must sum to 100%
    - Use variation to create unique results
    - CRITICAL: Each variation seed must produce a completely different result
    """

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1200,  # Increased for more detailed responses
            "temperature": 1.0,  # Maximum temperature for maximum variety
            "top_p": 0.9,  # Add top_p for more randomness
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60  # 60 saniye timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"🔍 DEBUG: GPT response content: {content[:200]}...")  # Show first 200 chars
            return json.loads(content)
        else:
            print(f"❌ OpenAI API error: {response.status_code}")
            raise Exception(f"OpenAI API error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error in generate_persona_from_taste: {e}")
        
        # Fallback response based on language
        if language == "tr":
            fallback_response = {
                "personaName": "Kültürel Keşifçi",
                "traits": ["Yaratıcı", "Meraklı", "Sosyal", "Dinamik", "Açık Fikirli"],
                "culturalTwin": "Tom Hanks",
                "description": "Kültürel çeşitliliğe değer veren, yeni deneyimlere açık bir kişilik. Farklı kültürleri keşfetmeyi seven, sosyal ve yaratıcı bir yapıya sahip.",
                "interests": ["Film", "Müzik", "Seyahat", "Teknoloji"],
                "culturalDNAScore": {
                    "Kuzey Amerika": "35%",
                    "Avrupa": "25%",
                    "Asya": "25%",
                    "Türkiye": "15%"
                },
                "archetype": {
                    "name": "Kültürel Keşifçi",
                    "description": "Farklı kültürleri keşfetmeyi seven, açık fikirli kişilik."
                }
            }
        else:
            fallback_response = {
                "personaName": "Cultural Explorer",
                "traits": ["Creative", "Curious", "Social", "Dynamic", "Open-minded"],
                "culturalTwin": "Tom Hanks",
                "description": "A personality that values cultural diversity and is open to new experiences. Loves exploring different cultures, social and creative in nature.",
                "interests": ["Film", "Music", "Travel", "Technology"],
                "culturalDNAScore": {
                    "North America": "35%",
                    "Europe": "25%",
                    "Asia": "25%",
                    "Turkey": "15%"
                },
                "archetype": {
                    "name": "Cultural Explorer",
                    "description": "Open-minded personality who loves exploring different cultures."
                }
            }
        
        return fallback_response

# 🔍 Ana analiz endpoint'i
@app.post("/analyze")
async def analyze_profile(request: Request):
    try:
        body = await request.json()
        print("📨 Received body:", body)
        print("🔍 DEBUG: randomSeed from request:", body.get("randomSeed", "NOT FOUND"))
        print("🔍 DEBUG: variation from request:", body.get("variation", "NOT FOUND"))

        variation = body.get("variation", 0)
        language = body.get("language", "en")

        # Autocomplete
        music_id = autocomplete_entity(body["music"], entity_type="artist")
        movie_id = autocomplete_entity(body["movies"], entity_type="movie")
        brand_id = autocomplete_entity(body["brands"], entity_type="brand")

        # Qloo trending
        music_trends = get_qloo_trending(music_id, entity_type="artist")
        movie_trends = get_qloo_trending(movie_id, entity_type="movie")
        brand_trends = get_qloo_trending(brand_id, entity_type="brand")

        qloo_suggestions = music_trends + movie_trends + brand_trends

        # Get randomSeed for variation
        random_seed = body.get("randomSeed", 0)
        print(f"🔍 DEBUG: Using randomSeed as variation: {random_seed}")
        
        # GPT persona
        ai_result = generate_persona_from_taste(
            movies=body["movies"],
            music=body["music"],
            brands=body["brands"],
            gender=body["gender"],
            language=language,
            variation=random_seed  # Use randomSeed as variation
        )
        parsed = json.loads(json.dumps(ai_result)) # Ensure it's a dict
        
        # Debug: Log the language being used
        print(f"=== LANGUAGE DEBUG ===")
        print(f"Requested language: {language}")
        print(f"Target language: {LANGUAGE_MAPPING.get(language, 'English')}")
        print(f"Parsed persona language check: {parsed.get('personaName', 'Unknown')}")
        print(f"Parsed description language check: {parsed.get('description', 'Unknown')}")
        print(f"Parsed traits language check: {parsed.get('traits', [])}")
        print(f"Cultural Twin: {parsed.get('culturalTwin', 'Unknown')}")
        print(f"Cultural Twin type: {type(parsed.get('culturalTwin', 'Unknown'))}")
        print(f"=== END LANGUAGE DEBUG ===")

        # GPT country insights
        sample_countries = ["USA", "South Korea", "UK", "Japan", "Germany", "France", "Italy", "Spain", "Canada", "Australia", "Brazil", "India", "China", "Russia"]
        
        # Kullanıcı tercihlerini persona'ya ekle
        user_preferences = {
            "movies": body["movies"],
            "music": body["music"], 
            "brands": body["brands"],
            "gender": body["gender"]
        }
        
        # Parsed persona'ya kullanıcı tercihlerini ekle
        parsed_with_preferences = {**parsed, "user_preferences": user_preferences}
        
        country_insights = generate_cultural_map_insights(sample_countries, language=language, user_persona=parsed_with_preferences)
        
        # Debug: Log the country insights
        print("=== COUNTRY INSIGHTS DEBUG ===")
        print("Sample countries:", sample_countries)
        print("Generated insights:", country_insights)
        print("Insights type:", type(country_insights))
        print("Insights keys:", list(country_insights.keys()) if country_insights else "None")
        print("=== END COUNTRY INSIGHTS DEBUG ===")

        return {
            "result": json.dumps(parsed),
            "culturalTwin": parsed.get("culturalTwin", "Unknown"),
            "countryInsights": country_insights
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
