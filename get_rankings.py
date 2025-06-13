from agno.models.azure.openai_chat import AzureOpenAI
from agno.agent import Agent
# from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.crawl4ai import Crawl4aiTools
from os import getenv
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json
from models import Fighter, Division, RankingsResponse

# Database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///data/mma.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

def create_rankings_table():
    """Create the ufc_rankings table if it doesn't exist."""
    db = get_db()
    
    # Drop existing table if it exists
    db.execute(text("DROP TABLE IF EXISTS ufc_rankings"))
    
    # Create new table with updated schema
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS ufc_rankings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            division TEXT,
            fighter_name TEXT NOT NULL,
            rank INTEGER,
            is_champion BOOLEAN DEFAULT FALSE,
            is_interim_champion BOOLEAN DEFAULT FALSE,
            is_p4p BOOLEAN DEFAULT FALSE,
            p4p_rank INTEGER,
            gender TEXT CHECK(gender IN ('M', 'F')),
            ranking_type TEXT NOT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    db.commit()

def store_rankings(rankings_data):
    db = get_db()
    current_time = datetime.now()
    
    # Clear existing rankings
    db.execute(text("DELETE FROM ufc_rankings"))
    
    # Store men's P4P rankings
    for fighter in rankings_data.mens_p4p:
        db.execute(text("""
            INSERT INTO ufc_rankings 
            (division, fighter_name, rank, is_champion, is_p4p, p4p_rank, gender, last_updated)
            VALUES (:division, :name, :rank, :is_champion, TRUE, :p4p_rank, 'M', :last_updated)
        """), {
            "division": fighter.division,
            "name": fighter.name,
            "rank": fighter.rank,
            "is_champion": fighter.is_champion,
            "p4p_rank": fighter.rank,
            "last_updated": current_time
        })
    
    # Store women's P4P rankings
    for fighter in rankings_data.womens_p4p:
        db.execute(text("""
            INSERT INTO ufc_rankings 
            (division, fighter_name, rank, is_champion, is_p4p, p4p_rank, gender, last_updated)
            VALUES (:division, :name, :rank, :is_champion, TRUE, :p4p_rank, 'F', :last_updated)
        """), {
            "division": fighter.division,
            "name": fighter.name,
            "rank": fighter.rank,
            "is_champion": fighter.is_champion,
            "p4p_rank": fighter.rank,
            "last_updated": current_time
        })
    
    # Store men's division rankings
    for division in rankings_data.mens_divisions:
        if division.champion:
            db.execute(text("""
                INSERT INTO ufc_rankings 
                (division, fighter_name, is_champion, gender, last_updated)
                VALUES (:division, :name, TRUE, 'M', :last_updated)
            """), {
                "division": division.name,
                "name": division.champion.name,
                "last_updated": current_time
            })
        
        if division.interim_champion:
            db.execute(text("""
                INSERT INTO ufc_rankings 
                (division, fighter_name, is_interim_champion, gender, last_updated)
                VALUES (:division, :name, TRUE, 'M', :last_updated)
            """), {
                "division": division.name,
                "name": division.interim_champion.name,
                "last_updated": current_time
            })
        
        for rank, fighter in enumerate(division.ranked_fighters, 1):
            db.execute(text("""
                INSERT INTO ufc_rankings 
                (division, fighter_name, rank, gender, last_updated)
                VALUES (:division, :name, :rank, 'M', :last_updated)
            """), {
                "division": division.name,
                "name": fighter.name,
                "rank": rank,
                "last_updated": current_time
            })
    
    # Store women's division rankings
    for division in rankings_data.womens_divisions:
        if division.champion:
            db.execute(text("""
                INSERT INTO ufc_rankings 
                (division, fighter_name, is_champion, gender, last_updated)
                VALUES (:division, :name, TRUE, 'F', :last_updated)
            """), {
                "division": division.name,
                "name": division.champion.name,
                "last_updated": current_time
            })
        
        if division.interim_champion:
            db.execute(text("""
                INSERT INTO ufc_rankings 
                (division, fighter_name, is_interim_champion, gender, last_updated)
                VALUES (:division, :name, TRUE, 'F', :last_updated)
            """), {
                "division": division.name,
                "name": division.interim_champion.name,
                "last_updated": current_time
            })
        
        for rank, fighter in enumerate(division.ranked_fighters, 1):
            db.execute(text("""
                INSERT INTO ufc_rankings 
                (division, fighter_name, rank, gender, last_updated)
                VALUES (:division, :name, :rank, 'F', :last_updated)
            """), {
                "division": division.name,
                "name": fighter.name,
                "rank": rank,
                "last_updated": current_time
            })
    
    db.commit()

def get_llm():
    return AzureOpenAI(
        api_key=getenv("AZURE_OPENAI_API_KEY"),
        api_version=getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        azure_endpoint=getenv("AZURE_OPENAI_ENDPOINT", "https://azure-oai-east2.openai.azure.com/"),
        azure_deployment="gpt-4-1"
    )

def parse_rankings_response(response):
    """Parse the LLM response into a RankingsResponse object."""
    try:
        # Extract the JSON part from the response
        json_str = response.split('```json\n')[1].split('\n```')[0]
        data = json.loads(json_str)
        
        # Convert the data into our models
        mens_p4p = [
            Fighter(
                name=name,
                rank=i+1,
                is_champion=False,
                division=None  # We'll need to look this up from divisions
            ) for i, name in enumerate(data['mens_pound_for_pound'])
        ]
        
        womens_p4p = [
            Fighter(
                name=name,
                rank=i+1,
                is_champion=False,
                division=None  # We'll need to look this up from divisions
            ) for i, name in enumerate(data['womens_pound_for_pound'])
        ]
        
        # Process men's divisions
        mens_divisions = []
        for div_name, div_data in data['divisions'].items():
            champion = Fighter(
                name=div_data['champion'],
                is_champion=True,
                division=div_name
            ) if 'champion' in div_data else None
            
            interim_champion = Fighter(
                name=div_data['interim_champion'],
                is_champion=True,
                division=div_name
            ) if 'interim_champion' in div_data else None
            
            ranked_fighters = [
                Fighter(
                    name=name,
                    rank=i+1,
                    is_champion=False,
                    division=div_name
                ) for i, name in enumerate(div_data['rankings'])
            ]
            
            mens_divisions.append(Division(
                name=div_name,
                champion=champion,
                interim_champion=interim_champion,
                ranked_fighters=ranked_fighters
            ))
        
        # Process women's divisions
        womens_divisions = []
        for div_name, div_data in data['womens_divisions'].items():
            champion = Fighter(
                name=div_data['champion'],
                is_champion=True,
                division=div_name
            ) if 'champion' in div_data else None
            
            interim_champion = Fighter(
                name=div_data['interim_champion'],
                is_champion=True,
                division=div_name
            ) if 'interim_champion' in div_data else None
            
            ranked_fighters = [
                Fighter(
                    name=name,
                    rank=i+1,
                    is_champion=False,
                    division=div_name
                ) for i, name in enumerate(div_data['rankings'])
            ]
            
            womens_divisions.append(Division(
                name=div_name,
                champion=champion,
                interim_champion=interim_champion,
                ranked_fighters=ranked_fighters
            ))
        
        return RankingsResponse(
            mens_p4p=mens_p4p,
            womens_p4p=womens_p4p,
            mens_divisions=mens_divisions,
            womens_divisions=womens_divisions,
            last_updated=datetime.now(),
            ranking_rules=["Voted on by a panel of media members", "Only active fighters are eligible"]
        )
    except Exception as e:
        print(f"Error parsing rankings response: {e}")
        raise

def store_fighter_ranking(name, division, rank, is_champion, is_interim_champion, is_p4p, p4p_rank, gender):
    """Store a single fighter's ranking in the database."""
    db = get_db()
    current_time = datetime.now()
    
    # Determine ranking type
    if is_p4p:
        ranking_type = f"{'Men' if gender == 'M' else 'Women'}'s Pound for Pound Rankings"
    elif is_champion:
        ranking_type = f"{division} Championship"
    elif is_interim_champion:
        ranking_type = f"{division} Interim Championship"
    else:
        ranking_type = f"{division} Rankings"
    
    try:
        db.execute(text("""
            INSERT INTO ufc_rankings 
            (division, fighter_name, rank, is_champion, is_interim_champion, is_p4p, p4p_rank, gender, ranking_type, last_updated)
            VALUES (:division, :name, :rank, :is_champion, :is_interim_champion, :is_p4p, :p4p_rank, :gender, :ranking_type, :last_updated)
        """), {
            "division": division,
            "name": name,
            "rank": rank,
            "is_champion": is_champion,
            "is_interim_champion": is_interim_champion,
            "is_p4p": is_p4p,
            "p4p_rank": p4p_rank,
            "gender": gender,
            "ranking_type": ranking_type,
            "last_updated": current_time
        })
        db.commit()
    except Exception as e:
        print(f"Error storing ranking for {name}: {e}")
        db.rollback()

def main():
    try:
        # Drop and recreate the rankings table
        print("Dropping and recreating rankings table...")
        create_rankings_table()
        
        # Initialize LLM and agent
        print("Initializing LLM and agent...")
        llm = get_llm()
        agent = Agent(
            tools=[Crawl4aiTools(max_length=None)],
            model=llm,
            show_tool_calls=True,
        )
        
        # Get rankings from UFC website with specific instructions for JSON format
        print("Fetching rankings from UFC website...")
        prompt = """Please use the crawl4ai tool to get the raw HTML content from https://www.ufc.com/rankings.
        Then, extract all the rankings data and format it as a JSON object with this exact structure:
        {
            "mens_p4p": [
                {"name": "Fighter Name", "rank": 1, "is_champion": true/false, "division": "Division Name"}
            ],
            "womens_p4p": [
                {"name": "Fighter Name", "rank": 1, "is_champion": true/false, "division": "Division Name"}
            ],
            "mens_divisions": [
                {
                    "name": "Division Name",
                    "champion": {"name": "Champion Name", "is_champion": true},
                    "interim_champion": {"name": "Interim Champion Name", "is_champion": true},
                    "ranked_fighters": [
                        {"name": "Fighter Name", "rank": 1, "is_champion": false}
                    ]
                }
            ],
            "womens_divisions": [
                {
                    "name": "Division Name",
                    "champion": {"name": "Champion Name", "is_champion": true},
                    "interim_champion": {"name": "Interim Champion Name", "is_champion": true},
                    "ranked_fighters": [
                        {"name": "Fighter Name", "rank": 1, "is_champion": false}
                    ]
                }
            ],
            "ranking_rules": [
                "Rule 1",
                "Rule 2"
            ]
        }
        
        Make sure to:
        1. Use the crawl4ai tool to get the raw HTML
        2. Parse the HTML to extract all rankings
        3. Format the data exactly as shown above
        4. Include all fighters in each division
        5. Mark champions and interim champions correctly
        6. Include the ranking rules from the page"""
        
        response = agent.run(prompt)
        
        # Extract JSON data from the response string
        print("Parsing rankings data...")
        json_str = response.content.split('```json\n')[1].split('\n```')[0]
        data = json.loads(json_str)
        
        # Store men's P4P rankings
        print("Storing men's P4P rankings...")
        for fighter in data['mens_p4p']:
            store_fighter_ranking(
                fighter['name'],
                fighter['division'],
                fighter['rank'],
                fighter['is_champion'],
                False,  # is_interim_champion
                True,   # is_p4p
                fighter['rank'],  # p4p_rank
                'M'     # gender
            )
        
        # Store women's P4P rankings
        print("Storing women's P4P rankings...")
        for fighter in data['womens_p4p']:
            store_fighter_ranking(
                fighter['name'],
                fighter['division'],
                fighter['rank'],
                fighter['is_champion'],
                False,  # is_interim_champion
                True,   # is_p4p
                fighter['rank'],  # p4p_rank
                'F'     # gender
            )
        
        # Store men's division rankings
        print("Storing men's division rankings...")
        for division in data['mens_divisions']:
            # Store champion
            if division['champion']:
                store_fighter_ranking(
                    division['champion']['name'],
                    division['name'],
                    None,  # rank
                    True,  # is_champion
                    False, # is_interim_champion
                    False, # is_p4p
                    None,  # p4p_rank
                    'M'    # gender
                )
            
            # Store interim champion
            if division['interim_champion']:
                store_fighter_ranking(
                    division['interim_champion']['name'],
                    division['name'],
                    None,  # rank
                    True,  # is_champion
                    True,  # is_interim_champion
                    False, # is_p4p
                    None,  # p4p_rank
                    'M'    # gender
                )
            
            # Store ranked fighters
            for fighter in division['ranked_fighters']:
                store_fighter_ranking(
                    fighter['name'],
                    division['name'],
                    fighter['rank'],
                    fighter['is_champion'],
                    False, # is_interim_champion
                    False, # is_p4p
                    None,  # p4p_rank
                    'M'    # gender
                )
        
        # Store women's division rankings
        print("Storing women's division rankings...")
        for division in data['womens_divisions']:
            # Store champion
            if division['champion']:
                store_fighter_ranking(
                    division['champion']['name'],
                    division['name'],
                    None,  # rank
                    True,  # is_champion
                    False, # is_interim_champion
                    False, # is_p4p
                    None,  # p4p_rank
                    'F'    # gender
                )
            
            # Store interim champion
            if division['interim_champion']:
                store_fighter_ranking(
                    division['interim_champion']['name'],
                    division['name'],
                    None,  # rank
                    True,  # is_champion
                    True,  # is_interim_champion
                    False, # is_p4p
                    None,  # p4p_rank
                    'F'    # gender
                )
            
            # Store ranked fighters
            for fighter in division['ranked_fighters']:
                store_fighter_ranking(
                    fighter['name'],
                    division['name'],
                    fighter['rank'],
                    fighter['is_champion'],
                    False, # is_interim_champion
                    False, # is_p4p
                    None,  # p4p_rank
                    'F'    # gender
                )
        
        print("Successfully updated UFC rankings in database.")
    except Exception as e:
        print(f"Error processing rankings: {e}")
        print("Raw response:", response.content)
        raise  # Re-raise the exception to see the full traceback

if __name__ == "__main__":
    main()







