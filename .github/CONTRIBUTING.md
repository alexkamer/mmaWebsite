# Contributing to MMA Website

Thank you for your interest in contributing to the MMA Website project! This document provides guidelines for contributing.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mmaWebsite
   ```

2. **Install dependencies**
   ```bash
   # Using uv (recommended)
   uv sync

   # Or using pip
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up the database**
   ```bash
   # Run initial data collection
   uv run python scripts/update_data.py
   ```

5. **Run the application**
   ```bash
   uv run run.py
   ```

## Code Style

- Follow PEP 8 guidelines for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and single-purpose

## Project Structure

- `mma_website/` - Main application package (modular Flask app)
- `scripts/` - Data update and utility scripts
- `templates/` - HTML templates
- `static/` - CSS, JavaScript, images
- `docs/` - Documentation
- `tests/` - Test files (to be added)

## Making Changes

1. **Create a new branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, documented code
   - Test your changes locally
   - Update documentation if needed

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "Clear description of changes"
   ```

4. **Push and create a pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Areas for Contribution

### High Priority
- [ ] Add automated tests (pytest)
- [ ] Improve error handling in data collection scripts
- [ ] Mobile responsiveness improvements
- [ ] Performance optimizations

### Features
- [ ] User authentication and profiles
- [ ] Fighter comparison tools
- [ ] Advanced analytics dashboard
- [ ] Email notifications for events
- [ ] API rate limiting and caching

### Documentation
- [ ] API documentation
- [ ] Deployment guide
- [ ] Data model documentation
- [ ] Architecture diagrams

## Data Updates

If you're working on data collection:
- Test with a small dataset first
- Handle edge cases (missing data, malformed responses)
- Add logging for debugging
- Update documentation if changing data structure

## Testing

Currently, the project needs a test suite. If you'd like to contribute:
- Use `pytest` for testing framework
- Add tests for new features
- Ensure tests pass before submitting PR

## Questions?

Feel free to open an issue for:
- Bug reports
- Feature requests
- Questions about the codebase
- Suggestions for improvements

Thank you for contributing! 🥊
