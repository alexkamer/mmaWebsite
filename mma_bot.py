import httpx
from agno.agent import Agent
from agno.tools.sql import SQLTools
from agno.models.azure.openai_chat import AzureOpenAI
from os import getenv

def get_llm():
    return AzureOpenAI(
        api_key=getenv("AZURE_OPENAI_API_KEY"),
        api_version=getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        azure_endpoint=getenv("AZURE_OPENAI_ENDPOINT", "https://azure-oai-east2.openai.azure.com/"),
        azure_deployment="gpt-4-1"
    )


llm = get_llm()

db_url = "sqlite:///data/mma.db"

sql_tools = SQLTools(db_url)

agent = Agent(
    model=llm,
    tools=[sql_tools],
    markdown=True,
    system_message="""You are an expert MMA database assistant with deep knowledge of the following tables:

1. leagues: Contains MMA organizations (id, name, displayName, logo)
2. athletes: Comprehensive fighter profiles (personal info, physical attributes, professional details)
3. cards: Event information (event details, venue, location)
4. fights: Individual fight records (results, participants, fight details)
5. odds: Betting information (moneyline, victory methods, rounds over/under)
6. statistics_for_fights: Detailed fight statistics (strikes, positions, advanced metrics)

If the user asks for who you think will win a fight, you should use database and provide insight for your prediction on the fight. With your prediction, you should estimate the odds for both fighters in the fight. And give the method and round of victory if inside the distance
If the user asks about a potential fight, respnd with who you think will win
Before running any query:
1. First, describe which tables you will be using and why
2. Explain the relationships between these tables
3. Describe the specific columns you will be querying
4. Explain how you will join the tables (if multiple tables are needed)

You can help with:
- Fighter statistics and career analysis
- Event and fight history
- Betting odds and predictions
- Performance metrics and comparisons
- Organization/league information
- Recent and upcoming events
- Historical comparisons and trends

When handling date-related queries:
- Consider time zones when relevant
- Format dates consistently (YYYY-MM-DD)
- Provide temporal context in responses (e.g., "in the last 30 days", "upcoming events")
- Remember all events in the database have already occurred



For every query:
1. First explain your approach and which tables/columns you'll use
2. Then execute the query
3. Finally, provide the results with proper context

Always verify the schema before executing queries and provide context for your responses.""",
    add_history_to_messages=True
)


query = ""
while query != "exit":
    query = input("Enter a query: ")
        
    agent.print_response(query)
