# Fight Ordering Update ✅

## Summary
Fights on the card detail page are now displayed in proper chronological order, matching how they appeared on the actual fight card.

## Changes Made

### 1. **Database Query Update**
**File**: `mma_website/routes/main.py` (lines 475-524)

Added `match_number` and `card_segment` to the query:

```sql
WITH first_odds AS (
    SELECT
        f.fight_id,
        f.match_number,        -- ADDED
        f.card_segment,        -- ADDED
        ...
    FROM fights f
    ...
)
SELECT
    fo.match_number,           -- ADDED
    fo.card_segment,           -- ADDED
    ...
FROM first_odds fo
...
ORDER BY fo.match_number ASC  -- CHANGED from fo.fight_id
```

**Key Change**: Ordering by `match_number ASC` instead of `fight_id`
- Lower match numbers = main card fights (fight #1 is the main event)
- Higher match numbers = prelims and early prelims

### 2. **Template Enhancement**
**File**: `templates/card_detail.html` (lines 78-110)

Added:
- **Section headers** for card segments (Main Card, Prelims, Early Prelims)
- **Fight number badges** (#1, #2, #3, etc.)
- **Visual icons** for each segment (🥊 Main Card, 📋 Prelims, ⚡ Early Prelims)

```jinja2
{% set current_segment = namespace(value='') %}
{% for fight in fights %}

<!-- Card Segment Header -->
{% if fight.card_segment and fight.card_segment != current_segment.value %}
    {% set current_segment.value = fight.card_segment %}
    <div class="mt-8 mb-4 border-b-2 border-gray-300 pb-2">
        <h3 class="text-xl font-bold text-gray-900">
            🥊 {{ fight.card_segment }}
        </h3>
    </div>
{% endif %}

<!-- Fight Number Badge -->
<span class="text-xs font-bold text-gray-500 bg-gray-200 px-2 py-1 rounded">
    #{{ fight.match_number }}
</span>
```

## Display Order

Fights now appear in this order:

### Main Card
- Fight #1 (Main Event) ← shown first
- Fight #2 (Co-Main Event)
- Fight #3
- Fight #4
- Fight #5
- Fight #6

### Prelims
- Fight #7
- Fight #8
- Fight #9
- Fight #10
- Fight #11
- Fight #12
- Fight #13

### Early Prelims (if present)
- Fight #14+

## Visual Improvements

1. **Section Headers**: Clear visual separation between Main Card, Prelims, and Early Prelims
2. **Fight Numbers**: Each fight shows its bout number (#1, #2, etc.)
3. **Better Organization**: Grouped by card segment for easy scanning
4. **Icon Indicators**: Emojis help identify sections at a glance

## User Experience

**Before**:
- Fights displayed in random order (by fight_id)
- No indication of which were main card vs prelims
- Difficult to follow the narrative of the event

**After**:
- ✅ Chronological order matching the actual event
- ✅ Clear section headers (Main Card, Prelims)
- ✅ Fight numbers for reference (#1, #2, etc.)
- ✅ Easy to see the flow of the card
- ✅ Main event prominently displayed first

## Example

**UFC Fight Night: Covington vs. Buckley**

```
🥊 Main Card
─────────────────
#1 Colby Covington vs Joaquin Buckley (Main Event)
#2 Co-Main Event Fight
#3 Featured Fight
...

📋 Prelims
─────────────────
#7 Prelim Fight
#8 Prelim Fight
...
```

## Technical Details

- `match_number`: Integer representing fight order (1 = main event)
- `card_segment`: String indicating card section ("Main Card", "Prelims", "Early Prelims")
- Order: ASC (ascending) to show main event first
- Grouping: Automatically creates headers when segment changes

## Testing

Tested with event ID 600049126:
- ✅ Fights display in correct order (#1-13)
- ✅ Section headers appear correctly
- ✅ Main Card fights shown before Prelims
- ✅ Fight numbers display accurately
- ✅ No database errors
- ✅ HTTP 200 response

## Files Modified

1. `mma_website/routes/main.py` - Updated SQL query with match_number ordering
2. `templates/card_detail.html` - Added section headers and fight number badges

## Conclusion

The card detail page now provides a natural, chronological view of fight cards that matches how the events actually unfolded. Users can easily see:
- Which fight was the main event
- The progression from main card to prelims
- The complete fight order with numbered badges

This makes the page more intuitive and useful for analyzing betting patterns across different positions on the card.
