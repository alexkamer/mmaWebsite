# MMA Query AI Setup Guide (Agno Enhanced)

## Overview

The MMA Query feature provides a StatMuse-like interface where users can ask natural language questions about MMA fighters, fights, and statistics. The system now uses **Agno framework** with Azure OpenAI for enhanced agent capabilities, better error handling, and more sophisticated query processing.

## Setup Instructions

### 1. Install Dependencies

The Agno framework and OpenAI packages have been added to requirements.txt. Install them:

```bash
pip install -r requirements.txt
# Or install directly:
pip install -U openai agno
```

### 2. Azure OpenAI Configuration

1. **Create an Azure OpenAI resource** in the Azure portal
2. **Deploy a model** (GPT-4 recommended, GPT-3.5-turbo also works)
3. **Get your credentials** from the Azure portal:
   - API Key
   - Endpoint URL
   - Deployment name

### 3. Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Fill in your Azure OpenAI credentials in `.env`:
```bash
# Agno Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_actual_api_key_here
AZURE_OPENAI_ENDPOINT=https://azure-oai-east2.openai.azure.com/
AZURE_DEPLOYMENT=gpt-4-1

# Legacy variables (maintained for compatibility)  
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4-1
```

### 4. Test the Setup

1. Start the application:
```bash
uv run run.py
```

2. Navigate to: `http://localhost:5004/query`

3. Check the service health at: `http://localhost:5004/query/health`

## Features

### Natural Language Queries
Users can ask questions like:
- "What is Jon Jones's UFC record?"
- "Who has the most knockouts in heavyweight?"
- "Which weight class has the highest finishing rate?"
- "How often do betting favorites win?"

### Query Categories
The system handles:
- **Fighter Records**: Win/loss records, finishing rates, career stats
- **Head-to-Head**: Fighter vs fighter matchups and results
- **Division Analysis**: Weight class statistics and rankings
- **Event History**: Fight cards, venues, and results
- **Advanced Statistics**: Strike rates, takedown accuracy, performance metrics
- **Betting Analysis**: Odds analysis and favorite/underdog performance

### Safety Features
- SQL injection prevention
- Query result limits
- Input validation
- Error handling and graceful degradation

## Architecture

### Components

1. **MMAQueryService** (`mma_website/services/mma_query_service.py`)
   - Handles Azure OpenAI integration
   - Converts natural language to SQL
   - Processes database queries
   - Generates natural language responses

2. **Query Routes** (`mma_website/routes/query.py`)
   - API endpoints for query processing
   - Health checks and examples
   - Request validation

3. **Frontend Interface** (`templates/mma_query.html`)
   - Chat-like interface
   - Example questions
   - Real-time results display

### Database Schema Context

The system includes comprehensive schema documentation that helps the AI understand:
- Table relationships
- Column meanings
- Common query patterns
- MMA-specific terminology

### Query Flow

1. User enters natural language question
2. System generates SQL query using Azure OpenAI
3. Query is validated and executed safely
4. Results are processed and formatted
5. AI generates human-readable response
6. User sees both the answer and query details

## Example Interactions

### Fighter Record Query
**User:** "What is Conor McGregor's UFC record?"

**System Response:** 
> Conor McGregor has a UFC record of 10 wins and 4 losses. He has 8 knockout/TKO wins and 0 submission wins, showing his striking-heavy approach. His losses came against Nate Diaz (submission), Khabib Nurmagomedov (submission), and two losses to Dustin Poirier.

### Statistical Analysis Query
**User:** "Which weight class has the highest finishing rate?"

**System Response:**
> The heavyweight division has the highest finishing rate at 68.2%, with 456 finishes out of 669 total fights. This is followed by light heavyweight at 61.4% and women's bantamweight at 59.8%. Heavier weight classes tend to have higher finishing rates due to increased knockout power.

## Troubleshooting

### Common Issues

1. **"Azure OpenAI not configured" error**
   - Check that all environment variables are set correctly
   - Verify your Azure OpenAI resource is active
   - Ensure the deployment name matches your model deployment

2. **"Network error" on queries**
   - Check your Azure OpenAI endpoint URL
   - Verify API key is valid and not expired
   - Check network connectivity to Azure

3. **"Database error" responses**
   - Generated SQL query may be invalid
   - Check database connection
   - Review query complexity (model may need better prompting)

### Debug Mode

Enable detailed logging by setting Flask debug mode:
```bash
export FLASK_DEBUG=1
```

This will show:
- Generated SQL queries
- Azure OpenAI API calls
- Database query results
- Error details

## Cost Considerations

- Queries use Azure OpenAI API calls (2 calls per question)
- GPT-4 is more capable but more expensive than GPT-3.5-turbo
- Consider implementing caching for common queries
- Monitor usage in Azure portal

## Future Enhancements

Potential improvements:
- Query result caching
- User query history
- Saved/favorite queries
- Enhanced statistical visualizations
- Voice input support
- Multi-language support

## Support

For issues with:
- **Azure OpenAI setup**: Check Azure documentation
- **Database queries**: Review the schema context in the service
- **Frontend issues**: Check browser console for JavaScript errors
- **General errors**: Check Flask application logs