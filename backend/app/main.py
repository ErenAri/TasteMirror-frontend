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
    elif language == "es":
        prompt = f"""
        CRITICAL INSTRUCTION: You MUST respond ENTIRELY in Spanish language.
        ALL cultural insights and recommendations must be in Spanish.
        
        {user_info}
        
        Basándote en el análisis de personalidad y preferencias de este usuario, proporciona recomendaciones culturales personalizadas para los siguientes países:
        
        Para cada país, devuelve un array JSON que contenga:
        - country (string) - nombre del país
        - culturalInsight (2-3 frases) - explicación detallada sobre la cultura en español
        - recommendation (string) - recomendación general (resumen corto)
        - music (string) - recomendaciones musicales (formato artista - canción)
        - movies (string) - recomendaciones de películas (títulos de películas)
        - personalizedReason (string) - 1-2 frases explicando por qué esta recomendación es adecuada para el usuario

        Países: {', '.join(countries)}

        REGLAS IMPORTANTES:
        - Todas las descripciones deben estar en español
        - Considera las películas, música y marcas favoritas del usuario
        - Proporciona DIFERENTES TIPOS de recomendaciones para cada país
        - Conecta con el culturalTwin del usuario
        - USA NOMBRES ESPECÍFICOS:
          * Música: "BTS - Dynamite", "BlackPink - How You Like That"
          * Películas: "Inception", "The Matrix", "Parasite", "Spirited Away"
        - Proporciona 3-4 recomendaciones musicales y 3-4 de películas para cada país
        - Solo responde con lista JSON válida
        """
    elif language == "fr":
        prompt = f"""
        CRITICAL INSTRUCTION: You MUST respond ENTIRELY in French language.
        ALL cultural insights and recommendations must be in French.
        
        {user_info}
        
        Basé sur l'analyse de personnalité et les préférences de cet utilisateur, fournissez des recommandations culturelles personnalisées pour les pays suivants:
        
        Pour chaque pays, retournez un array JSON contenant:
        - country (string) - nom du pays
        - culturalInsight (2-3 phrases) - explication détaillée sur la culture en français
        - recommendation (string) - recommandation générale (résumé court)
        - music (string) - recommandations musicales (format artiste - chanson)
        - movies (string) - recommandations de films (titres de films)
        - personalizedReason (string) - 1-2 phrases expliquant pourquoi cette recommandation convient à l'utilisateur

        Pays: {', '.join(countries)}

        RÈGLES IMPORTANTES:
        - Toutes les descriptions doivent être en français
        - Considérez les films, musiques et marques préférés de l'utilisateur
        - Fournissez DIFFÉRENTS TYPES de recommandations pour chaque pays
        - Connectez avec le culturalTwin de l'utilisateur
        - UTILISEZ DES NOMS SPÉCIFIQUES:
          * Musique: "BTS - Dynamite", "BlackPink - How You Like That"
          * Films: "Inception", "The Matrix", "Parasite", "Spirited Away"
        - Fournissez 3-4 recommandations musicales et 3-4 de films pour chaque pays
        - Répondez seulement avec une liste JSON valide
        """
    elif language == "de":
        prompt = f"""
        CRITICAL INSTRUCTION: You MUST respond ENTIRELY in German language.
        ALL cultural insights and recommendations must be in German.
        
        {user_info}
        
        Basierend auf der Persönlichkeitsanalyse und den Präferenzen dieses Benutzers, geben Sie personalisierte kulturelle Empfehlungen für die folgenden Länder:
        
        Für jedes Land geben Sie ein JSON-Array zurück, das enthält:
        - country (string) - Ländername
        - culturalInsight (2-3 Sätze) - detaillierte Erklärung über die Kultur auf Deutsch
        - recommendation (string) - allgemeine Empfehlung (kurze Zusammenfassung)
        - music (string) - Musikempfehlungen (Format Künstler - Song)
        - movies (string) - Filmempfehlungen (Filmtitel)
        - personalizedReason (string) - 1-2 Sätze, die erklären, warum diese Empfehlung für den Benutzer geeignet ist

        Länder: {', '.join(countries)}

        WICHTIGE REGELN:
        - Alle Beschreibungen müssen auf Deutsch sein
        - Berücksichtigen Sie die Lieblingsfilme, -musik und -marken des Benutzers
        - Geben Sie VERSCHIEDENE ARTEN von Empfehlungen für jedes Land
        - Verbinden Sie mit dem culturalTwin des Benutzers
        - VERWENDEN SIE SPEZIFISCHE NAMEN:
          * Musik: "BTS - Dynamite", "BlackPink - How You Like That"
          * Filme: "Inception", "The Matrix", "Parasite", "Spirited Away"
        - Geben Sie 3-4 Musik- und 3-4 Filmempfehlungen für jedes Land
        - Antworten Sie nur mit gültiger JSON-Liste
        """
    elif language == "it":
        prompt = f"""
        CRITICAL INSTRUCTION: You MUST respond ENTIRELY in Italian language.
        ALL cultural insights and recommendations must be in Italian.
        
        {user_info}
        
        Basandoti sull'analisi della personalità e le preferenze di questo utente, fornisci raccomandazioni culturali personalizzate per i seguenti paesi:
        
        Per ogni paese, restituisci un array JSON che contiene:
        - country (string) - nome del paese
        - culturalInsight (2-3 frasi) - spiegazione dettagliata sulla cultura in italiano
        - recommendation (string) - raccomandazione generale (riassunto breve)
        - music (string) - raccomandazioni musicali (formato artista - canzone)
        - movies (string) - raccomandazioni di film (titoli di film)
        - personalizedReason (string) - 1-2 frasi che spiegano perché questa raccomandazione è adatta all'utente

        Paesi: {', '.join(countries)}

        REGOLE IMPORTANTI:
        - Tutte le descrizioni devono essere in italiano
        - Considera i film, la musica e i marchi preferiti dell'utente
        - Fornisci TIPI DIVERSI di raccomandazioni per ogni paese
        - Connetti con il culturalTwin dell'utente
        - USA NOMI SPECIFICI:
          * Musica: "BTS - Dynamite", "BlackPink - How You Like That"
          * Film: "Inception", "The Matrix", "Parasite", "Spirited Away"
        - Fornisci 3-4 raccomandazioni musicali e 3-4 di film per ogni paese
        - Rispondi solo con lista JSON valida
        """
    elif language == "hi":
        prompt = f"""
        CRITICAL INSTRUCTION: You MUST respond ENTIRELY in Hindi language.
        ALL cultural insights and recommendations must be in Hindi.
        
        {user_info}
        
        इस उपयोगकर्ता के व्यक्तित्व विश्लेषण और प्राथमिकताओं के आधार पर, निम्नलिखित देशों के लिए व्यक्तिगत सांस्कृतिक सिफारिशें प्रदान करें:
        
        प्रत्येक देश के लिए, एक JSON array लौटाएं जिसमें शामिल हो:
        - country (string) - देश का नाम
        - culturalInsight (2-3 वाक्य) - हिंदी में संस्कृति के बारे में विस्तृत विवरण
        - recommendation (string) - सामान्य सिफारिश (संक्षिप्त सारांश)
        - music (string) - संगीत सिफारिशें (कलाकार - गीत प्रारूप)
        - movies (string) - फिल्म सिफारिशें (फिल्म शीर्षक)
        - personalizedReason (string) - 1-2 वाक्य जो बताते हैं कि यह सिफारिश उपयोगकर्ता के लिए उपयुक्त क्यों है

        देश: {', '.join(countries)}

        महत्वपूर्ण नियम:
        - सभी विवरण हिंदी में होने चाहिए
        - उपयोगकर्ता की पसंदीदा फिल्मों, संगीत और ब्रांडों पर विचार करें
        - प्रत्येक देश के लिए विभिन्न प्रकार की सिफारिशें प्रदान करें
        - उपयोगकर्ता के culturalTwin से जुड़ें
        - विशिष्ट नामों का उपयोग करें:
          * संगीत: "BTS - Dynamite", "BlackPink - How You Like That"
          * फिल्में: "Inception", "The Matrix", "Parasite", "Spirited Away"
        - प्रत्येक देश के लिए 3-4 संगीत और 3-4 फिल्म सिफारिशें प्रदान करें
        - केवल मान्य JSON सूची के साथ उत्तर दें
        """
    elif language == "zh":
        prompt = f"""
        CRITICAL INSTRUCTION: You MUST respond ENTIRELY in Chinese language.
        ALL cultural insights and recommendations must be in Chinese.
        
        {user_info}
        
        基于这个用户的个性分析和偏好，为以下国家提供个性化的文化推荐：
        
        对于每个国家，返回包含以下内容的JSON数组：
        - country (string) - 国家名称
        - culturalInsight (2-3句话) - 用中文详细解释文化
        - recommendation (string) - 一般推荐（简短摘要）
        - music (string) - 音乐推荐（艺术家-歌曲格式）
        - movies (string) - 电影推荐（电影标题）
        - personalizedReason (string) - 1-2句话解释为什么这个推荐适合用户

        国家：{', '.join(countries)}

        重要规则：
        - 所有描述必须用中文
        - 考虑用户喜欢的电影、音乐和品牌
        - 为每个国家提供不同类型的推荐
        - 与用户的culturalTwin建立联系
        - 使用具体名称：
          * 音乐："BTS - Dynamite", "BlackPink - How You Like That"
          * 电影："Inception", "The Matrix", "Parasite", "Spirited Away"
        - 为每个国家提供3-4个音乐和3-4个电影推荐
        - 只返回有效的JSON列表
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
        # Add system message to enforce language response
        system_message = f"Respond only in {LANGUAGE_MAPPING.get(language, 'English')}."
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )

        content = response.choices[0].message.content
        print(f"GPT response content: {content}")

        if not content:
            print("⚠️ GPT returned empty cultural map content")
            return {}

        try:
            # Try to fix common JSON issues
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            parsed = json.loads(content)
            print(f"Parsed JSON: {parsed}")
            result = {item["country"]: item for item in parsed if "country" in item}
            print(f"Final result: {result}")
            return result
        except Exception as e:
            print("❌ Failed to parse cultural map response:", e)
            print("Raw content:", content)
            # Try to fix the JSON manually
            try:
                # Remove any trailing commas and fix quotes
                content = content.replace(',]', ']').replace(',}', '}')
                # Fix common quote issues
                content = content.replace('",]', '"]').replace(',"', ',"')
                parsed = json.loads(content)
                result = {item["country"]: item for item in parsed if "country" in item}
                print(f"Fixed JSON result: {result}")
                return result
            except:
                print("❌ Could not fix JSON, using fallback")
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
        elif language == "es":
            return {
                "USA": {
                    "country": "USA",
                    "culturalInsight": "La cultura estadounidense se caracteriza por la diversidad y la innovación. La industria cinematográfica de Hollywood, los musicales de Broadway y varios géneros musicales contribuyen enormemente a la cultura mundial.",
                    "recommendation": "Películas de Hollywood y música rock",
                    "music": "Bruce Springsteen - Born to Run, Queen - Bohemian Rhapsody, Michael Jackson - Thriller",
                    "movies": "Inception, The Matrix, Interstellar, Avengers: Endgame, The Godfather",
                    "personalizedReason": "Ideal para tu personalidad creativa y de mente abierta"
                },
                "South Korea": {
                    "country": "South Korea",
                    "culturalInsight": "La cultura surcoreana es una mezcla perfecta de tecnología y valores tradicionales. La música K-Pop, las series K-drama y la ropa tradicional hanbok combinan valores modernos y tradicionales.",
                    "recommendation": "Música K-Pop y series K-drama",
                    "music": "BTS - Dynamite, BlackPink - How You Like That, IU - Blueming, Red Velvet - Psycho",
                    "movies": "Parasite, Squid Game, Train to Busan, Oldboy, My Sassy Girl",
                    "personalizedReason": "Adecuado para tu personalidad que ama la tecnología y los valores tradicionales"
                },
                "UK": {
                    "country": "UK",
                    "culturalInsight": "La cultura británica es el equilibrio perfecto entre tradición y modernidad. Tiene un rico patrimonio cultural con música rock británica, teatro de Shakespeare y cultura del té.",
                    "recommendation": "Música rock británica y teatro",
                    "music": "The Beatles - Hey Jude, Queen - Bohemian Rhapsody, Adele - Rolling in the Deep, Ed Sheeran - Shape of You",
                    "movies": "Serie de Harry Potter, Sherlock Holmes, James Bond, The King's Speech",
                    "personalizedReason": "Perfecto para tu personalidad que equilibra tradición y modernidad"
                },
                "Japan": {
                    "country": "Japan",
                    "culturalInsight": "La cultura japonesa es una síntesis de valores tradicionales y progreso tecnológico. Crea una cultura única con anime, manga, ceremonia tradicional del té y tecnología moderna.",
                    "recommendation": "Anime y manga",
                    "music": "BABYMETAL - Gimme Chocolate, ONE OK ROCK - The Beginning, Perfume - Polyrhythm",
                    "movies": "Spirited Away, Attack on Titan, Death Note, Your Name, Akira",
                    "personalizedReason": "Adecuado para tu personalidad que combina tecnología y arte"
                }
            }
        elif language == "fr":
            return {
                "USA": {
                    "country": "USA",
                    "culturalInsight": "La culture américaine se caractérise par la diversité et l'innovation. L'industrie cinématographique d'Hollywood, les comédies musicales de Broadway et divers genres musicaux contribuent grandement à la culture mondiale.",
                    "recommendation": "Films d'Hollywood et musique rock",
                    "music": "Bruce Springsteen - Born to Run, Queen - Bohemian Rhapsody, Michael Jackson - Thriller",
                    "movies": "Inception, The Matrix, Interstellar, Avengers: Endgame, The Godfather",
                    "personalizedReason": "Idéal pour votre personnalité créative et ouverte d'esprit"
                },
                "South Korea": {
                    "country": "South Korea",
                    "culturalInsight": "La culture sud-coréenne est un mélange parfait de technologie et de valeurs traditionnelles. La musique K-Pop, les séries K-drama et les vêtements traditionnels hanbok combinent valeurs modernes et traditionnelles.",
                    "recommendation": "Musique K-Pop et séries K-drama",
                    "music": "BTS - Dynamite, BlackPink - How You Like That, IU - Blueming, Red Velvet - Psycho",
                    "movies": "Parasite, Squid Game, Train to Busan, Oldboy, My Sassy Girl",
                    "personalizedReason": "Convenable pour votre personnalité qui aime la technologie et les valeurs traditionnelles"
                },
                "UK": {
                    "country": "UK",
                    "culturalInsight": "La culture britannique est l'équilibre parfait entre tradition et modernité. Elle a un riche patrimoine culturel avec la musique rock britannique, le théâtre de Shakespeare et la culture du thé.",
                    "recommendation": "Musique rock britannique et théâtre",
                    "music": "The Beatles - Hey Jude, Queen - Bohemian Rhapsody, Adele - Rolling in the Deep, Ed Sheeran - Shape of You",
                    "movies": "Série Harry Potter, Sherlock Holmes, James Bond, The King's Speech",
                    "personalizedReason": "Parfait pour votre personnalité qui équilibre tradition et modernité"
                },
                "Japan": {
                    "country": "Japan",
                    "culturalInsight": "La culture japonaise est une synthèse de valeurs traditionnelles et de progrès technologique. Elle crée une culture unique avec l'anime, le manga, la cérémonie traditionnelle du thé et la technologie moderne.",
                    "recommendation": "Anime et manga",
                    "music": "BABYMETAL - Gimme Chocolate, ONE OK ROCK - The Beginning, Perfume - Polyrhythm",
                    "movies": "Spirited Away, Attack on Titan, Death Note, Your Name, Akira",
                    "personalizedReason": "Convenable pour votre personnalité qui combine technologie et art"
                }
            }
        elif language == "de":
            return {
                "USA": {
                    "country": "USA",
                    "culturalInsight": "Die amerikanische Kultur ist geprägt von Vielfalt und Innovation. Die Hollywood-Filmindustrie, Broadway-Musicals und verschiedene Musikgenres tragen wesentlich zur Weltkultur bei.",
                    "recommendation": "Hollywood-Filme und Rockmusik",
                    "music": "Bruce Springsteen - Born to Run, Queen - Bohemian Rhapsody, Michael Jackson - Thriller",
                    "movies": "Inception, The Matrix, Interstellar, Avengers: Endgame, The Godfather",
                    "personalizedReason": "Ideal für deine kreative und weltoffene Persönlichkeit"
                },
                "South Korea": {
                    "country": "South Korea",
                    "culturalInsight": "Die südkoreanische Kultur ist eine perfekte Mischung aus Technologie und traditionellen Werten. K-Pop-Musik, K-Drama-Serien und traditionelle Hanbok-Kleidung verbinden moderne und traditionelle Werte.",
                    "recommendation": "K-Pop-Musik und K-Drama-Serien",
                    "music": "BTS - Dynamite, BlackPink - How You Like That, IU - Blueming, Red Velvet - Psycho",
                    "movies": "Parasite, Squid Game, Train to Busan, Oldboy, My Sassy Girl",
                    "personalizedReason": "Geeignet für deine Persönlichkeit, die Technologie und traditionelle Werte liebt"
                },
                "UK": {
                    "country": "UK",
                    "culturalInsight": "Die britische Kultur ist die perfekte Balance zwischen Tradition und Moderne. Sie hat ein reiches kulturelles Erbe mit britischem Rock, Shakespeare-Theater und Teekultur.",
                    "recommendation": "Britischer Rock und Theater",
                    "music": "The Beatles - Hey Jude, Queen - Bohemian Rhapsody, Adele - Rolling in the Deep, Ed Sheeran - Shape of You",
                    "movies": "Harry Potter-Serie, Sherlock Holmes, James Bond, The King's Speech",
                    "personalizedReason": "Perfekt für deine Persönlichkeit, die Tradition und Moderne ausbalanciert"
                },
                "Japan": {
                    "country": "Japan",
                    "culturalInsight": "Die japanische Kultur ist eine Synthese aus traditionellen Werten und technologischem Fortschritt. Sie schafft eine einzigartige Kultur mit Anime, Manga, traditioneller Teezeremonie und moderner Technologie.",
                    "recommendation": "Anime und Manga",
                    "music": "BABYMETAL - Gimme Chocolate, ONE OK ROCK - The Beginning, Perfume - Polyrhythm",
                    "movies": "Spirited Away, Attack on Titan, Death Note, Your Name, Akira",
                    "personalizedReason": "Geeignet für deine Persönlichkeit, die Technologie und Kunst verbindet"
                }
            }
        elif language == "it":
            return {
                "USA": {
                    "country": "USA",
                    "culturalInsight": "La cultura americana è caratterizzata da diversità e innovazione. L'industria cinematografica di Hollywood, i musical di Broadway e vari generi musicali contribuiscono enormemente alla cultura mondiale.",
                    "recommendation": "Film di Hollywood e musica rock",
                    "music": "Bruce Springsteen - Born to Run, Queen - Bohemian Rhapsody, Michael Jackson - Thriller",
                    "movies": "Inception, The Matrix, Interstellar, Avengers: Endgame, The Godfather",
                    "personalizedReason": "Ideale per la tua personalità creativa e di mente aperta"
                },
                "South Korea": {
                    "country": "South Korea",
                    "culturalInsight": "La cultura sudcoreana è una perfetta miscela di tecnologia e valori tradizionali. La musica K-Pop, le serie K-drama e l'abbigliamento tradizionale hanbok combinano valori moderni e tradizionali.",
                    "recommendation": "Musica K-Pop e serie K-drama",
                    "music": "BTS - Dynamite, BlackPink - How You Like That, IU - Blueming, Red Velvet - Psycho",
                    "movies": "Parasite, Squid Game, Train to Busan, Oldboy, My Sassy Girl",
                    "personalizedReason": "Adatto alla tua personalità che ama la tecnologia e i valori tradizionali"
                },
                "UK": {
                    "country": "UK",
                    "culturalInsight": "La cultura britannica è il perfetto equilibrio tra tradizione e modernità. Ha un ricco patrimonio culturale con la musica rock britannica, il teatro di Shakespeare e la cultura del tè.",
                    "recommendation": "Musica rock britannica e teatro",
                    "music": "The Beatles - Hey Jude, Queen - Bohemian Rhapsody, Adele - Rolling in the Deep, Ed Sheeran - Shape of You",
                    "movies": "Serie di Harry Potter, Sherlock Holmes, James Bond, The King's Speech",
                    "personalizedReason": "Perfetto per la tua personalità che bilancia tradizione e modernità"
                },
                "Japan": {
                    "country": "Japan",
                    "culturalInsight": "La cultura giapponese è una sintesi di valori tradizionali e progresso tecnologico. Crea una cultura unica con anime, manga, cerimonia tradizionale del tè e tecnologia moderna.",
                    "recommendation": "Anime e manga",
                    "music": "BABYMETAL - Gimme Chocolate, ONE OK ROCK - The Beginning, Perfume - Polyrhythm",
                    "movies": "Spirited Away, Attack on Titan, Death Note, Your Name, Akira",
                    "personalizedReason": "Adatto alla tua personalità che combina tecnologia e arte"
                }
            }
        elif language == "hi":
            return {
                "USA": {
                    "country": "USA",
                    "culturalInsight": "अमेरिकी संस्कृति विविधता और नवाचार की विशेषता है। हॉलीवुड फिल्म उद्योग, ब्रॉडवे म्यूजिकल और विभिन्न संगीत शैलियां विश्व संस्कृति में बहुत योगदान करती हैं।",
                    "recommendation": "हॉलीवुड फिल्में और रॉक संगीत",
                    "music": "Bruce Springsteen - Born to Run, Queen - Bohemian Rhapsody, Michael Jackson - Thriller",
                    "movies": "Inception, The Matrix, Interstellar, Avengers: Endgame, The Godfather",
                    "personalizedReason": "आपकी रचनात्मक और खुले दिमाग वाली व्यक्तित्व के लिए आदर्श"
                },
                "South Korea": {
                    "country": "South Korea",
                    "culturalInsight": "दक्षिण कोरियाई संस्कृति प्रौद्योगिकी और पारंपरिक मूल्यों का एक सही मिश्रण है। K-Pop संगीत, K-drama श्रृंखलाएं और पारंपरिक hanbok कपड़े आधुनिक और पारंपरिक मूल्यों को जोड़ते हैं।",
                    "recommendation": "K-Pop संगीत और K-drama श्रृंखलाएं",
                    "music": "BTS - Dynamite, BlackPink - How You Like That, IU - Blueming, Red Velvet - Psycho",
                    "movies": "Parasite, Squid Game, Train to Busan, Oldboy, My Sassy Girl",
                    "personalizedReason": "आपकी व्यक्तित्व के लिए उपयुक्त जो प्रौद्योगिकी और पारंपरिक मूल्यों से प्यार करती है"
                },
                "UK": {
                    "country": "UK",
                    "culturalInsight": "ब्रिटिश संस्कृति परंपरा और आधुनिकता का सही संतुलन है। इसमें ब्रिटिश रॉक संगीत, शेक्सपियर थिएटर और चाय संस्कृति के साथ समृद्ध सांस्कृतिक विरासत है।",
                    "recommendation": "ब्रिटिश रॉक संगीत और थिएटर",
                    "music": "The Beatles - Hey Jude, Queen - Bohemian Rhapsody, Adele - Rolling in the Deep, Ed Sheeran - Shape of You",
                    "movies": "Harry Potter श्रृंखला, Sherlock Holmes, James Bond, The King's Speech",
                    "personalizedReason": "आपकी व्यक्तित्व के लिए परफेक्ट जो परंपरा और आधुनिकता को संतुलित करती है"
                },
                "Japan": {
                    "country": "Japan",
                    "culturalInsight": "जापानी संस्कृति पारंपरिक मूल्यों और तकनीकी प्रगति का संश्लेषण है। यह एनीमे, मंगा, पारंपरिक चाय समारोह और आधुनिक प्रौद्योगिकी के साथ एक अनूठी संस्कृति बनाती है।",
                    "recommendation": "एनीमे और मंगा",
                    "music": "BABYMETAL - Gimme Chocolate, ONE OK ROCK - The Beginning, Perfume - Polyrhythm",
                    "movies": "Spirited Away, Attack on Titan, Death Note, Your Name, Akira",
                    "personalizedReason": "आपकी व्यक्तित्व के लिए उपयुक्त जो प्रौद्योगिकी और कला को जोड़ती है"
                }
            }
        elif language == "zh":
            return {
                "USA": {
                    "country": "USA",
                    "culturalInsight": "美国文化以多样性和创新为特征。好莱坞电影工业、百老汇音乐剧和各种音乐流派对世界文化做出了巨大贡献。",
                    "recommendation": "好莱坞电影和摇滚音乐",
                    "music": "Bruce Springsteen - Born to Run, Queen - Bohemian Rhapsody, Michael Jackson - Thriller",
                    "movies": "Inception, The Matrix, Interstellar, Avengers: Endgame, The Godfather",
                    "personalizedReason": "适合您富有创造力和开放思维的性格"
                },
                "South Korea": {
                    "country": "South Korea",
                    "culturalInsight": "韩国文化是技术与传统价值观的完美融合。K-Pop音乐、K-drama系列和传统韩服结合了现代和传统价值观。",
                    "recommendation": "K-Pop音乐和K-drama系列",
                    "music": "BTS - Dynamite, BlackPink - How You Like That, IU - Blueming, Red Velvet - Psycho",
                    "movies": "Parasite, Squid Game, Train to Busan, Oldboy, My Sassy Girl",
                    "personalizedReason": "适合热爱技术和传统价值观的您"
                },
                "UK": {
                    "country": "UK",
                    "culturalInsight": "英国文化是传统与现代的完美平衡。它拥有丰富的文化遗产，包括英国摇滚音乐、莎士比亚戏剧和茶文化。",
                    "recommendation": "英国摇滚音乐和戏剧",
                    "music": "The Beatles - Hey Jude, Queen - Bohemian Rhapsody, Adele - Rolling in the Deep, Ed Sheeran - Shape of You",
                    "movies": "哈利波特系列, Sherlock Holmes, James Bond, The King's Speech",
                    "personalizedReason": "完美适合平衡传统与现代的您"
                },
                "Japan": {
                    "country": "Japan",
                    "culturalInsight": "日本文化是传统价值观和技术进步的综合体。它通过动漫、漫画、传统茶道和现代技术创造了独特的文化。",
                    "recommendation": "动漫和漫画",
                    "music": "BABYMETAL - Gimme Chocolate, ONE OK ROCK - The Beginning, Perfume - Polyrhythm",
                    "movies": "Spirited Away, Attack on Titan, Death Note, Your Name, Akira",
                    "personalizedReason": "适合结合技术与艺术的您"
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
    
    # Tüm diller için doğru target language'ı belirle
    language_mapping = {
        "en": "English",
        "tr": "Turkish", 
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "hi": "Hindi",
        "zh": "Chinese",
        "it": "Italian"
    }
    
    target_language = language_mapping.get(language, "English")
    
    # API key kontrolü
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your-openai-api-key-here":
        print("⚠️ OpenAI API key not found, using fallback response")
        # Fallback response based on language with variation
        fallback_names = {
            "tr": ["Kültürel Keşifçi", "Dünya Vatandaşı", "Kültür Elçisi", "Sınırlar Ötesi", "Kültürel Yolcu", "Kültür Avcısı", "Dünya Gezgini", "Kültür Meraklısı", "Sınır Tanımayan", "Kültür Aşığı", "Kültür Kaşifi", "Dünya Seyyahı", "Kültür Ustası", "Sınır Gezgini", "Kültür Sanatçısı"],
            "en": ["Cultural Explorer", "Global Citizen", "Cultural Ambassador", "Border Crosser", "Cultural Traveler", "Culture Hunter", "World Wanderer", "Culture Enthusiast", "Boundary Breaker", "Culture Lover", "Cultural Pioneer", "World Nomad", "Culture Master", "Border Walker", "Cultural Artist"],
            "es": ["Explorador Cultural", "Ciudadano Global", "Embajador Cultural", "Cruzador de Fronteras", "Viajero Cultural", "Cazador de Cultura", "Nómada Mundial", "Entusiasta Cultural", "Rompedor de Límites", "Amante de la Cultura", "Pionero Cultural", "Nómada Mundial", "Maestro Cultural", "Caminante de Fronteras", "Artista Cultural"],
            "fr": ["Explorateur Culturel", "Citoyen du Monde", "Ambassadeur Culturel", "Traverseur de Frontières", "Voyageur Culturel", "Chasseur de Culture", "Nomade Mondial", "Passionné Culturel", "Briseur de Limites", "Amoureux de la Cultura", "Pionnier Culturel", "Nomade Mondial", "Maître Culturel", "Marcheur de Frontières", "Artiste Culturel"],
            "de": ["Kultureller Entdecker", "Weltbürger", "Kultur-Botschafter", "Grenzüberschreiter", "Kultureller Reisender", "Kultur-Jäger", "Welt-Nomade", "Kultur-Enthusiast", "Grenzen-Brecher", "Kultur-Liebhaber", "Kultureller Pionier", "Welt-Nomade", "Kultur-Meister", "Grenzen-Wanderer", "Kultur-Künstler"],
            "hi": ["सांस्कृतिक खोजकर्ता", "विश्व नागरिक", "सांस्कृतिक राजदूत", "सीमा पार करने वाला", "सांस्कृतिक यात्री", "संस्कृति शिकारी", "विश्व खानाबदोश", "सांस्कृतिक उत्साही", "सीमा तोड़ने वाला", "संस्कृति प्रेमी", "सांस्कृतिक अग्रदूत", "विश्व खानाबदोश", "सांस्कृतिक मास्टर", "सीमा चलने वाला", "सांस्कृतिक कलाकार"],
            "zh": ["文化探索者", "世界公民", "文化大使", "边界跨越者", "文化旅行者", "文化猎人", "世界游牧者", "文化爱好者", "界限打破者", "文化爱好者", "文化先驱", "世界游牧者", "文化大师", "边界行者", "文化艺术家"],
            "it": ["Esploratore Culturale", "Cittadino del Mondo", "Ambassadeur Culturale", "Attraversatore di Confini", "Viaggiatore Culturale", "Cacciatore di Cultura", "Nomade Mondiale", "Entusiasta Culturale", "Spezzatore di Limiti", "Amante della Cultura", "Pioniere Culturale", "Nomade Mondiale", "Maestro Culturale", "Camminatore di Confini", "Artista Culturale"]
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
        
        # Her dil için fallback response oluştur
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
        elif language == "es":
            fallback_response = {
                "personaName": fallback_names["es"][name_index],
                "traits": ["Creativo", "Curioso", "Social", "Dinámico", "Mente Abierta"],
                "culturalTwin": selected_celebrity,
                "description": "Una personalidad que valora la diversidad cultural y está abierta a nuevas experiencias. Ama explorar diferentes culturas, social y creativo por naturaleza.",
                "interests": ["Películas", "Música", "Viajes", "Tecnología"],
                "culturalDNAScore": {
                    "América del Norte": f"{30 + (variation % 20)}%",
                    "Europa": f"{20 + (variation % 15)}%",
                    "Asia": f"{25 + (variation % 15)}%",
                    "España": f"{15 + (variation % 10)}%"
                },
                "archetype": {
                    "name": "Explorador Cultural",
                    "description": "Personalidad de mente abierta que ama explorar diferentes culturas."
                }
            }
        elif language == "fr":
            fallback_response = {
                "personaName": fallback_names["fr"][name_index],
                "traits": ["Créatif", "Curieux", "Social", "Dynamique", "Ouvert d'esprit"],
                "culturalTwin": selected_celebrity,
                "description": "Une personnalité qui valorise la diversité culturelle et est ouverte aux nouvelles expériences. Aime explorer différentes cultures, social et créatif par nature.",
                "interests": ["Cinéma", "Musique", "Voyage", "Technologie"],
                "culturalDNAScore": {
                    "Amérique du Nord": f"{30 + (variation % 20)}%",
                    "Europe": f"{20 + (variation % 15)}%",
                    "Asie": f"{25 + (variation % 15)}%",
                    "France": f"{15 + (variation % 10)}%"
                },
                "archetype": {
                    "name": "Explorateur Culturel",
                    "description": "Personnalité ouverte d'esprit qui aime explorer différentes cultures."
                }
            }
        elif language == "de":
            fallback_response = {
                "personaName": fallback_names["de"][name_index],
                "traits": ["Kreativ", "Neugierig", "Sozial", "Dynamisch", "Aufgeschlossen"],
                "culturalTwin": selected_celebrity,
                "description": "Eine Persönlichkeit, die kulturelle Vielfalt schätzt und offen für neue Erfahrungen ist. Liebt es, verschiedene Kulturen zu erkunden, sozial und kreativ von Natur aus.",
                "interests": ["Film", "Musik", "Reisen", "Technologie"],
                "culturalDNAScore": {
                    "Nordamerika": f"{30 + (variation % 20)}%",
                    "Europa": f"{20 + (variation % 15)}%",
                    "Asien": f"{25 + (variation % 15)}%",
                    "Deutschland": f"{15 + (variation % 10)}%"
                },
                "archetype": {
                    "name": "Kultureller Entdecker",
                    "description": "Aufgeschlossene Persönlichkeit, die es liebt, verschiedene Kulturen zu erkunden."
                }
            }
        elif language == "hi":
            fallback_response = {
                "personaName": fallback_names["hi"][name_index],
                "traits": ["रचनात्मक", "जिज्ञासु", "सामाजिक", "गतिशील", "खुले विचारों वाला"],
                "culturalTwin": selected_celebrity,
                "description": "एक व्यक्तित्व जो सांस्कृतिक विविधता को महत्व देता है और नए अनुभवों के लिए खुला है। विभिन्न संस्कृतियों की खोज करना पसंद करता है, स्वभाव से सामाजिक और रचनात्मक।",
                "interests": ["फिल्म", "संगीत", "यात्रा", "प्रौद्योगिकी"],
                "culturalDNAScore": {
                    "उत्तरी अमेरिका": f"{30 + (variation % 20)}%",
                    "यूरोप": f"{20 + (variation % 15)}%",
                    "एशिया": f"{25 + (variation % 15)}%",
                    "भारत": f"{15 + (variation % 10)}%"
                },
                "archetype": {
                    "name": "सांस्कृतिक खोजकर्ता",
                    "description": "खुले विचारों वाला व्यक्तित्व जो विभिन्न संस्कृतियों की खोज करना पसंद करता है।"
                }
            }
        elif language == "zh":
            fallback_response = {
                "personaName": fallback_names["zh"][name_index],
                "traits": ["创造性", "好奇", "社交", "动态", "开放思想"],
                "culturalTwin": selected_celebrity,
                "description": "一个重视文化多样性并对新体验开放的人格。喜欢探索不同文化，天生具有社交性和创造性。",
                "interests": ["电影", "音乐", "旅行", "技术"],
                "culturalDNAScore": {
                    "北美": f"{30 + (variation % 20)}%",
                    "欧洲": f"{20 + (variation % 15)}%",
                    "亚洲": f"{25 + (variation % 15)}%",
                    "中国": f"{15 + (variation % 10)}%"
                },
                "archetype": {
                    "name": "文化探索者",
                    "description": "思想开放的人格，喜欢探索不同文化。"
                }
            }
        elif language == "it":
            fallback_response = {
                "personaName": fallback_names["it"][name_index],
                "traits": ["Creativo", "Curioso", "Sociale", "Dinamico", "Mente Aperta"],
                "culturalTwin": selected_celebrity,
                "description": "Una personalità che valorizza la diversità culturale ed è aperta a nuove esperienze. Ama esplorare diverse culture, sociale e creativo per natura.",
                "interests": ["Cinema", "Musica", "Viaggio", "Tecnologia"],
                "culturalDNAScore": {
                    "Nord America": f"{30 + (variation % 20)}%",
                    "Europa": f"{20 + (variation % 15)}%",
                    "Asia": f"{25 + (variation % 15)}%",
                    "Italia": f"{15 + (variation % 10)}%"
                },
                "archetype": {
                    "name": "Esploratore Culturale",
                    "description": "Personalità di mente aperta che ama esplorare diverse culture."
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
    Analyze the user's taste preferences and create a detailed cultural persona. 
    
    CRITICAL LANGUAGE REQUIREMENT: You MUST respond ENTIRELY in {target_language}. 
    - All text in the JSON response MUST be in {target_language}
    - personaName MUST be in {target_language}
    - traits array MUST contain traits in {target_language}
    - description MUST be in {target_language}
    - interests array MUST be in {target_language}
    - archetype name and description MUST be in {target_language}
    - culturalDNAScore region names can be in English (North America, Europe, etc.)
    
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

    Create a JSON response with the following structure (ALL TEXT VALUES MUST BE IN {target_language}):
    {{
        "personaName": "Creative name in {target_language} based on preferences and variation seed {variation}",
        "traits": ["trait1 in {target_language}", "trait2 in {target_language}", "trait3 in {target_language}", "trait4 in {target_language}", "trait5 in {target_language}"],
        "culturalTwin": "Choose a celebrity based on user preferences",
        "description": "2-3 sentence personality description in {target_language} that reflects the user's preferences",
        "interests": ["interest1 in {target_language}", "interest2 in {target_language}", "interest3 in {target_language}"],
        "culturalDNAScore": {{
            "region1": "percentage%",
            "region2": "percentage%",
            "region3": "percentage%",
            "region4": "percentage%"
        }},
        "archetype": {{
            "name": "archetype name in {target_language}",
            "description": "1 sentence description in {target_language}"
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
    - ALL TEXT IN THE JSON RESPONSE MUST BE IN {target_language}
    - Percentages must sum to 100%
    - Use variation to create unique results
    - CRITICAL: Each variation seed must produce a completely different result
    - CRITICAL: If target_language is "Turkish", write ALL text in Turkish
    - CRITICAL: If target_language is "English", write ALL text in English
    """

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Add system message to enforce language response
        system_message = f"Respond only in {target_language}."
        
        data = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
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
        
        # Get language from request body first, then fallback to Accept-Language header
        language = body.get("language", "en")
        
        # If no language in body, try to get from Accept-Language header
        if language == "en":
            accept_language = request.headers.get("accept-language", "")
            if accept_language:
                # Parse Accept-Language header (e.g., "tr-TR,tr;q=0.9,en;q=0.8")
                # Extract the first language code
                first_lang = accept_language.split(',')[0].split('-')[0].strip()
                if first_lang in LANGUAGE_MAPPING:
                    language = first_lang
                    print(f"🔍 DEBUG: Using Accept-Language header: {first_lang}")

        print(f"🔍 DEBUG: Final language selected: {language}")

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
