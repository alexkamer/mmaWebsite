# ✅ System Checker - Card-by-Card View

## What's Built

A clean, actionable betting analytics page that shows **card-by-card** favorite vs underdog performance.

### Features:

1. **League Selector** - Choose UFC, PFL, or Bellator
2. **Year Selector** - View any year with available data
3. **Overview Stats** - Quick summary of overall performance
4. **Card-by-Card Breakdown** - Individual event analysis
5. **Visual Indicators** - Easy-to-spot upset-heavy events

---

## Sample Data (UFC 2024)

Here's what users will see:

### UFC 308: Topuria vs. Holloway (Oct 26, 2024)
- **8 favorites won** (30.8%)
- **18 underdogs won** (69.2%) 🔥
- **Status:** Upset Heavy night!

### UFC Fight Night: Hernandez vs. Pereira (Oct 19, 2024)
- **18 favorites won** (81.8%)
- **4 underdogs won** (18.2%) ✅
- **Status:** Chalk night - favorites dominated

### UFC Fight Night: Yan vs. Figueiredo (Nov 23, 2024)
- **13 favorites won** (50.0%)
- **13 underdogs won** (50.0%) ⚖️
- **Status:** Perfectly balanced

---

## What Each Card Shows:

For every event, users see:

1. **Event Name** - E.g., "UFC 310: Pantoja vs. Asakura"
2. **Date** - When it happened
3. **Total Fights** - How many fights on the card
4. **Favorites Won** - Count and percentage
5. **Underdogs Won** - Count and percentage
6. **Visual Bar** - Green (favs) vs Red (dogs) breakdown
7. **Event Tag** - "Upset Heavy", "Chalk Night", or "Balanced"

---

## Event Classifications:

### 🔥 Upset Heavy
- More underdogs won than favorites
- Great for betting underdogs that night
- Example: UFC 308 (18 upsets vs 8 favorites)

### ✅ Chalk Night
- Favorites won 2x+ more than underdogs
- "Chalk" = betting term for favorites
- Example: UFC Fight Night Hernandez vs Pereira (18 vs 4)

### ⚖️ Balanced
- Roughly equal performance
- Efficient market
- Example: UFC Fight Night Yan vs Figueiredo (13-13 split)

---

## Available Data:

### **UFC** (Best Coverage)
- 2025: 46 events (current year)
- 2024: 52 events ✅ Most complete
- 2023: 57 events
- 2022-2018: Full coverage
- **Recommendation:** Start with UFC 2024

### **PFL**
- 2025: 14 events
- 2024: 12 events
- 2023-2018: Good coverage

### **Bellator**
- 2024: 5 events
- 2023: 13 events
- Limited odds data

---

## How to Use:

```bash
# Start the app
uv run run.py

# Navigate to
http://127.0.0.1:5000/system-checker

# Default view: UFC 2025 (current year)
# Click year buttons to see past years
# Click league buttons to switch leagues
```

---

## Key Insights from UFC 2024:

Looking at the sample data above:

- **UFC 308 had 18 upsets** - Epic night for underdog bettors!
- **Most events are relatively balanced** - Market is efficient
- **Some nights are very chalk** - Favorites dominate
- **Patterns vary by event** - No single strategy works every time

---

## Visual Elements:

### Color Coding:
- **Green** = Favorites
- **Red** = Underdogs
- **Yellow** = Upset-heavy events
- **Blue** = Chalk/Balanced events

### Icons:
- 🔥 = Upset Heavy (dogs dominated)
- ✅ = Chalk Night (favs dominated)
- ⚖️ = Balanced (roughly equal)

---

## What Makes This Useful:

### For Bettors:
1. **See patterns** - Which events tend to have upsets?
2. **Track favorites** - Are they performing well recently?
3. **Historical context** - How did 2024 compare to 2023?
4. **Event-specific insights** - Some cards are unpredictable

### For Analysts:
1. **Event-level data** - Not just overall stats
2. **Chronological view** - See trends over time
3. **League comparison** - UFC vs PFL vs Bellator
4. **Year-over-year** - Is the sport getting more/less predictable?

---

## Technical Details:

### Calculations:
- Counts only fights with odds data
- Favorite/underdog determined by bookmaker designation
- Multiple bookmakers per fight create multiple lines
- Percentages calculated per event

### Data Quality:
- ✅ UFC 2024: 52 events with odds
- ✅ PFL 2024: 12 events with odds
- ⚠️ Bellator 2024: Only 5 events with odds

---

## What's Next?

Potential enhancements we can add:

1. **Odds Range Breakdown**
   - Show performance by odds level (-150, -200, -300, etc.)
   - Per event or overall

2. **Underdog ROI Calculator**
   - What if you bet $100 on every underdog?
   - Per event profitability

3. **Fight-by-Fight Detail**
   - Click an event to see each fight
   - Who upset whom?

4. **Export Functionality**
   - CSV download for analysis
   - Share specific events

---

## Status: ✅ Ready to Use

The page is clean, simple, and shows exactly what you requested:
- ✅ Per-card breakdown
- ✅ Current year data
- ✅ League selection
- ✅ Favorite vs underdog counts
- ✅ Visual indicators
- ✅ Easy to understand

**Try it now and let me know what you think!** 🚀
